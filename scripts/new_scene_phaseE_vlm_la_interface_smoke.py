#!/usr/bin/env python3
"""New Scene Phase E VLM-LA interface smoke.

This script reads New Scene Phase D real-sensor candidate artifacts, generates
pseudo VLM commands of the form "Go to candidate <id>.", parses and validates
them, maps candidate IDs back to target poses, and verifies fallback behavior
for invalid outputs.

It does not start Isaac, run real VLM inference, move A1, map, generate
candidates, train, save USD, or create large artifacts.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


WORKSPACE = Path("/home/ubuntu22/VLA")
RUNS = WORKSPACE / "runs"
PROJECT_NAME = "A1-VLM-LA Explorer"
MAIN_GOAL = "A1-VLM-LA Explorer for 3D Active Exploration"
PHASE = "New Scene Phase E VLM-LA interface smoke"
SCENE_PATH = WORKSPACE / "scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda"
ORIGINAL_USER_USD_PATH = WORKSPACE / "building_scene(1).usd"
CURRENT_SCENE_ID = "building_scene_1_scene_20260608_171052"
OUTPUT_CONTRACT = "Go to candidate <id>."
ROBOT_PLATFORM = "unitree_a1"
ROBOT_SOURCE = "existing_usd_prim"
A1_ROOT = "/World/A1"
BASE_FRAME = "/World/A1/base"
SENSOR_METHOD = "real_isaac_omniverse_rgbd"
CAMERA_POINTCLOUD_SOURCE = "depth_backprojection"
MAP_UPDATE_SOURCE = "depth_backprojection_pointcloud"
CANDIDATE_DATA_SOURCE = "new_scene_phaseD_real_sensor"
TOP_REPORT = RUNS / "NEW_SCENE_VLM_LA_INTERFACE_REPORT.md"
COMPAT_DIR = RUNS / "new_scene_sampling_building_scene_1"
COMPAT_REPORT = COMPAT_DIR / "NEW_SCENE_VLM_LA_INTERFACE_REPORT.md"


def bool_from_csv(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def rate(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def parse_path_from_report(report: Path, key: str) -> Path | None:
    text = read_text_if_exists(report)
    patterns = (
        re.compile(rf"^\s*{re.escape(key)}:\s*(.+?)\s*$"),
        re.compile(rf"^\s*-\s*{re.escape(key)}:\s*(.+?)\s*$"),
    )
    for line in text.splitlines():
        for pattern in patterns:
            match = pattern.match(line)
            if match:
                value = match.group(1).strip()
                if value:
                    return Path(value)
    return None


def default_run_dir() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return RUNS / f"new_scene_building_scene_1_phaseE_vlm_la_interface_{timestamp}"


def find_phaseD_run(explicit_run_dir: str | None = None) -> Path:
    if explicit_run_dir:
        run_dir = Path(explicit_run_dir).expanduser().resolve()
        if run_dir.exists():
            return run_dir
        raise FileNotFoundError(f"explicit Phase D run_dir not found: {run_dir}")

    report = RUNS / "NEW_SCENE_CANDIDATE_GAIN_REPORT.md"
    report_run = parse_path_from_report(report, "run_dir")
    if report_run and report_run.exists():
        return report_run

    summary_path = parse_path_from_report(report, "candidate_summary path")
    if summary_path and summary_path.exists():
        return summary_path.parent.parent

    matches = sorted(
        RUNS.glob("new_scene_building_scene_1_phaseD_candidate_gain_*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if matches:
        return matches[0]
    raise FileNotFoundError("No New Scene Phase D candidate run directory found")


def load_phaseD_artifacts(run_dir: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    summary_path = run_dir / "summary/candidate_summary.json"
    csv_path = run_dir / "summary/candidate_summary.csv"
    steps_path = run_dir / "summary/candidate_steps.jsonl"
    if not summary_path.exists() or not csv_path.exists() or not steps_path.exists():
        raise FileNotFoundError(f"New Scene Phase D candidate artifacts incomplete under {run_dir}")

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    rows = list(csv.DictReader(csv_path.open(newline="", encoding="utf-8-sig")))
    steps = [json.loads(line) for line in steps_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not rows or not steps:
        raise RuntimeError("New Scene Phase D candidate artifacts are empty")
    return summary, rows, steps


def candidate_key(step_id: int, candidate_id: int) -> tuple[int, int]:
    return int(step_id), int(candidate_id)


def build_candidate_index(
    rows: list[dict[str, Any]],
) -> tuple[dict[tuple[int, int], dict[str, Any]], dict[int, dict[str, Any]], dict[int, list[dict[str, Any]]]]:
    by_key: dict[tuple[int, int], dict[str, Any]] = {}
    selected_by_step: dict[int, dict[str, Any]] = {}
    rows_by_step: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        step_id = int(row["step_id"])
        candidate_id = int(row["candidate_id"])
        by_key[candidate_key(step_id, candidate_id)] = row
        rows_by_step.setdefault(step_id, []).append(row)
        if bool_from_csv(row.get("selected_by_classical")):
            selected_by_step[step_id] = row
    return by_key, selected_by_step, rows_by_step


def parse_language_command(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if not raw:
        return {"parse_success": False, "selected_candidate_id": None, "error": "empty_command"}

    lower = raw.lower()
    if re.search(r"\bv\s*=", lower) or re.search(r"\bomega\s*=", lower):
        return {"parse_success": False, "selected_candidate_id": None, "error": "velocity_output_not_allowed"}
    if "joint" in lower or "hip" in lower or "knee" in lower or "ankle" in lower:
        return {"parse_success": False, "selected_candidate_id": None, "error": "joint_action_output_not_allowed"}
    if re.search(r"\bx\s*=", lower) or re.search(r"\by\s*=", lower) or re.search(r"\byaw\s*=", lower):
        return {"parse_success": False, "selected_candidate_id": None, "error": "free_coordinate_output_not_allowed"}

    if raw.startswith("{"):
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return {"parse_success": False, "selected_candidate_id": None, "error": "malformed_json"}
        if not isinstance(payload, dict):
            return {"parse_success": False, "selected_candidate_id": None, "error": "json_payload_not_object"}
        if any(key in payload for key in ("x", "y", "z", "yaw", "v", "omega", "linear_velocity", "angular_velocity")):
            return {"parse_success": False, "selected_candidate_id": None, "error": "free_coordinate_or_velocity_json_not_allowed"}
        command = str(payload.get("command", "")).strip().lower()
        if command != "go_to_candidate":
            return {"parse_success": False, "selected_candidate_id": None, "error": "unsupported_json_command"}
        candidate_id = payload.get("selected_candidate_id")
        if isinstance(candidate_id, bool) or not isinstance(candidate_id, int):
            return {"parse_success": False, "selected_candidate_id": None, "error": "json_candidate_id_missing_or_not_int"}
        return {"parse_success": True, "selected_candidate_id": candidate_id, "error": None}

    match = re.search(r"\bgo\s+to\s+candidate\s+(\d+)\b", raw, flags=re.IGNORECASE)
    if match:
        return {"parse_success": True, "selected_candidate_id": int(match.group(1)), "error": None}
    return {"parse_success": False, "selected_candidate_id": None, "error": "missing_candidate_id_or_contract_mismatch"}


def validate_candidate_id(
    candidate_id: int | None,
    step_id: int,
    candidate_index: dict[tuple[int, int], dict[str, Any]],
) -> dict[str, Any]:
    exists = candidate_id is not None and candidate_key(step_id, int(candidate_id)) in candidate_index
    row = candidate_index.get(candidate_key(step_id, int(candidate_id))) if exists and candidate_id is not None else None
    is_valid_candidate = bool_from_csv(row.get("is_valid")) if row else False
    is_reachable = bool_from_csv(row.get("is_reachable")) if row else False
    collision_risk_ok = not bool_from_csv(row.get("collision_risk")) if row else False
    valid = bool(exists and is_valid_candidate and is_reachable and collision_risk_ok)
    if valid:
        reason = "pass"
    elif not exists:
        reason = "candidate_id_not_found"
    elif not is_valid_candidate:
        reason = "candidate_marked_invalid"
    elif not is_reachable:
        reason = "candidate_unreachable"
    elif not collision_risk_ok:
        reason = "candidate_collision_risk"
    else:
        reason = "candidate_validation_failed"
    return {
        "valid": valid,
        "exists": bool(exists),
        "is_valid_candidate": bool(is_valid_candidate),
        "is_reachable": bool(is_reachable),
        "collision_risk_ok": bool(collision_risk_ok),
        "reason": reason,
    }


def target_pose(row: dict[str, Any] | None) -> dict[str, float] | None:
    if row is None:
        return None
    try:
        return {
            "x": round(float(row["x"]), 4),
            "y": round(float(row["y"]), 4),
            "z": round(float(row["z"]), 4),
            "yaw": round(float(row["yaw"]), 4),
        }
    except Exception:
        return None


def selected_candidate_for_step(step_id: int, selected_by_step: dict[int, dict[str, Any]]) -> dict[str, Any]:
    if step_id not in selected_by_step:
        raise RuntimeError(f"no classical selected candidate for step {step_id}")
    return selected_by_step[step_id]


def make_test_cases(step_id: int, selected_id: int, rows_for_step: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tests = [
        {"test_case": "legal_pseudo_vlm_command", "input_command": f"Go to candidate {selected_id}.", "expected": "legal"},
        {"test_case": "legal_lowercase_command", "input_command": f"go to candidate {selected_id}", "expected": "legal"},
        {
            "test_case": "legal_explanation_command",
            "input_command": f"Go to candidate {selected_id} because it faces unknown space.",
            "expected": "legal",
        },
        {
            "test_case": "legal_json_command",
            "input_command": json.dumps({"command": "go_to_candidate", "selected_candidate_id": selected_id}),
            "expected": "legal",
        },
        {"test_case": "missing_id", "input_command": "Go to the unexplored room.", "expected": "illegal"},
        {"test_case": "move_forward", "input_command": "Move forward.", "expected": "illegal"},
        {"test_case": "out_of_range_id", "input_command": "Go to candidate 999.", "expected": "illegal"},
        {"test_case": "coordinate_output", "input_command": "{\"x\": 1.2, \"y\": 3.4, \"yaw\": 1.57}", "expected": "illegal"},
        {"test_case": "velocity_output", "input_command": "v=0.2, omega=0.1", "expected": "illegal"},
        {"test_case": "joint_action_output", "input_command": "Set A1 hip joint to 0.3.", "expected": "illegal"},
        {"test_case": "malformed_json", "input_command": "{\"command\": \"go_to_candidate\", \"selected_candidate_id\": }", "expected": "illegal"},
        {"test_case": "textual_number_id", "input_command": "Go to candidate seven.", "expected": "illegal"},
    ]

    invalid = next((r for r in rows_for_step if not bool_from_csv(r.get("is_valid"))), None)
    if invalid:
        tests.append(
            {
                "test_case": "invalid_candidate_id",
                "input_command": f"Go to candidate {int(invalid['candidate_id'])}.",
                "expected": "illegal",
            }
        )

    unreachable = next((r for r in rows_for_step if not bool_from_csv(r.get("is_reachable"))), None)
    if unreachable:
        tests.append(
            {
                "test_case": "unreachable_candidate_id",
                "input_command": f"Go to candidate {int(unreachable['candidate_id'])}.",
                "expected": "illegal",
            }
        )
    return tests


def evaluate_command(
    step_id: int,
    test: dict[str, Any],
    candidate_index: dict[tuple[int, int], dict[str, Any]],
    selected_by_step: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    parsed = parse_language_command(test["input_command"])
    parsed_id = parsed["selected_candidate_id"]
    validation = validate_candidate_id(parsed_id, step_id, candidate_index)
    selected_row = selected_candidate_for_step(step_id, selected_by_step)
    fallback_id = int(selected_row["candidate_id"])
    fallback_pose = target_pose(selected_row)
    fallback_used = not (parsed["parse_success"] and validation["valid"])
    fallback_reason = None
    final_id = parsed_id
    final_pose = None

    if fallback_used:
        fallback_reason = parsed["error"] or validation["reason"]
        final_id = fallback_id
        final_pose = fallback_pose
    else:
        final_pose = target_pose(candidate_index[candidate_key(step_id, int(parsed_id))])

    expected = test["expected"]
    if expected == "legal":
        interface_passed = bool(parsed["parse_success"] and validation["valid"] and final_pose is not None and not fallback_used)
    else:
        interface_passed = bool(fallback_used and fallback_pose is not None and final_id == fallback_id)

    return {
        "phase": PHASE,
        "step_id": step_id,
        "test_case": test["test_case"],
        "expected_behavior": expected,
        "input_command": test["input_command"],
        "parse_success": bool(parsed["parse_success"]),
        "parsed_candidate_id": parsed_id,
        "parse_error": parsed["error"],
        "candidate_exists": validation["exists"],
        "candidate_valid": validation["is_valid_candidate"],
        "candidate_reachable": validation["is_reachable"],
        "candidate_collision_risk_ok": validation["collision_risk_ok"],
        "validation_reason": validation["reason"],
        "target_pose": final_pose,
        "fallback_used": bool(fallback_used),
        "fallback_reason": fallback_reason,
        "fallback_selected_candidate_id": fallback_id,
        "final_selected_candidate_id": final_id,
        "final_interface_command": f"Go to candidate {final_id}." if final_id is not None else None,
        "interface_passed": bool(interface_passed),
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def write_test_case_csv(path: Path, records: list[dict[str, Any]]) -> None:
    fields = [
        "step_id",
        "test_case",
        "expected_behavior",
        "input_command",
        "parse_success",
        "parsed_candidate_id",
        "candidate_exists",
        "candidate_valid",
        "candidate_reachable",
        "candidate_collision_risk_ok",
        "fallback_used",
        "fallback_reason",
        "fallback_selected_candidate_id",
        "final_selected_candidate_id",
        "final_interface_command",
        "interface_passed",
    ]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def summarize(
    run_dir: Path,
    phaseD_run_dir: Path,
    phaseD_summary: dict[str, Any],
    records: list[dict[str, Any]],
    summary_jsonl: Path,
) -> dict[str, Any]:
    legal = [r for r in records if r["expected_behavior"] == "legal"]
    illegal = [r for r in records if r["expected_behavior"] == "illegal"]
    legal_parse = [r for r in legal if r["parse_success"]]
    legal_valid = [
        r
        for r in legal
        if r["candidate_exists"] and r["candidate_valid"] and r["candidate_reachable"] and r["candidate_collision_risk_ok"]
    ]
    target_lookup = [r for r in records if r["target_pose"] is not None]
    illegal_ok = [r for r in illegal if r["fallback_used"] and r["interface_passed"]]

    free_coordinate_allowed = any(r["test_case"] == "coordinate_output" and not r["fallback_used"] for r in records)
    velocity_allowed = any(r["test_case"] == "velocity_output" and not r["fallback_used"] for r in records)
    joint_allowed = any(r["test_case"] == "joint_action_output" and not r["fallback_used"] for r in records)
    malformed_rejected = all(r["fallback_used"] for r in records if r["test_case"] == "malformed_json")
    invalid_cases = [r for r in records if r["test_case"] == "invalid_candidate_id"]
    unreachable_cases = [r for r in records if r["test_case"] == "unreachable_candidate_id"]
    invalid_fallback = bool(invalid_cases) and all(r["fallback_used"] and r["interface_passed"] for r in invalid_cases)
    unreachable_fallback = bool(unreachable_cases) and all(r["fallback_used"] and r["interface_passed"] for r in unreachable_cases)
    final_contract_ok = all(
        r["final_interface_command"] and re.match(r"^Go to candidate \d+\.$", r["final_interface_command"])
        for r in records
    )
    phaseD_ok = bool(phaseD_summary.get("safe_to_interface"))

    pass_ok = bool(
        phaseD_ok
        and legal
        and illegal
        and len(legal_parse) == len(legal)
        and len(legal_valid) == len(legal)
        and len(target_lookup) == len(records)
        and len(illegal_ok) == len(illegal)
        and not free_coordinate_allowed
        and not velocity_allowed
        and not joint_allowed
        and malformed_rejected
        and invalid_fallback
        and unreachable_fallback
        and final_contract_ok
    )

    return {
        "phase": PHASE,
        "workspace": str(WORKSPACE),
        "project_name": PROJECT_NAME,
        "main_goal": MAIN_GOAL,
        "current_scene_id": CURRENT_SCENE_ID,
        "scene_path": str(SCENE_PATH),
        "original_user_usd_path": str(ORIGINAL_USER_USD_PATH),
        "robot_platform": ROBOT_PLATFORM,
        "robot_source": ROBOT_SOURCE,
        "a1_root_prim": A1_ROOT,
        "base_frame": BASE_FRAME,
        "sensor_method": SENSOR_METHOD,
        "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE,
        "map_update_source": MAP_UPDATE_SOURCE,
        "candidate_data_source": CANDIDATE_DATA_SOURCE,
        "output_contract": OUTPUT_CONTRACT,
        "phaseD_run_dir": str(phaseD_run_dir),
        "phaseD_candidate_data_used": True,
        "phaseD_safe_to_interface": phaseD_ok,
        "legal_command_count": len(legal),
        "legal_parse_success_count": len(legal_parse),
        "legal_parse_success_rate": rate(len(legal_parse), len(legal)),
        "legal_validation_success_count": len(legal_valid),
        "legal_validation_success_rate": rate(len(legal_valid), len(legal)),
        "illegal_test_count": len(illegal),
        "illegal_reject_or_fallback_count": len(illegal_ok),
        "illegal_reject_or_fallback_rate": rate(len(illegal_ok), len(illegal)),
        "target_pose_lookup_success_count": len(target_lookup),
        "target_pose_lookup_success_rate": rate(len(target_lookup), len(records)),
        "fallback_test_passed": bool(len(illegal_ok) == len(illegal) and invalid_fallback and unreachable_fallback),
        "fallback_behavior": "pass" if len(illegal_ok) == len(illegal) and invalid_fallback and unreachable_fallback else "fail",
        "invalid_candidate_fallback_tested": bool(invalid_cases),
        "invalid_candidate_fallback_passed": bool(invalid_fallback),
        "unreachable_candidate_fallback_tested": bool(unreachable_cases),
        "unreachable_candidate_fallback_passed": bool(unreachable_fallback),
        "free_coordinate_output_allowed": bool(free_coordinate_allowed),
        "velocity_output_allowed": bool(velocity_allowed),
        "joint_action_output_allowed": bool(joint_allowed),
        "malformed_output_rejected": bool(malformed_rejected),
        "final_interface_output_contract_ok": bool(final_contract_ok),
        "training_started": False,
        "RL_started": False,
        "SFT_started": False,
        "GDPO_started": False,
        "map_predict_started": False,
        "checkpoint_created": False,
        "rollout_started": False,
        "A1_moved": False,
        "mapping_started": False,
        "candidate_generation_started": False,
        "real_vlm_inference_started": False,
        "safe_to_closed_loop": pass_ok,
        "next_phase": "New Scene Phase F short closed-loop smoke" if pass_ok else "Fix New Scene Phase E VLM-LA interface smoke",
        "run_dir": str(run_dir),
        "vlm_la_interface_smoke_jsonl": str(summary_jsonl),
        "parse_summary_json": str(run_dir / "summary/parse_summary.json"),
        "test_cases_csv": str(run_dir / "test_cases/interface_test_cases.csv"),
        "top_report": str(TOP_REPORT),
        "compat_report": str(COMPAT_REPORT),
        "caveats": [
            "This is pseudo VLM output interface validation, not real VLM inference.",
            "Candidate data is read from New Scene Phase D real-sensor artifacts; no new candidates are generated.",
            "Fallback uses the Phase D classical selected candidate for the same step.",
            "No A1 movement, mapping, rollout, training, or USD save is performed.",
        ],
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# New Scene VLM-LA Interface Report",
        "",
        "phase: New Scene Phase E",
        f"workspace: {WORKSPACE}",
        f"project_name: {PROJECT_NAME}",
        f"scene_path: {SCENE_PATH}",
        f"robot_platform: {ROBOT_PLATFORM}",
        f"robot_source: {ROBOT_SOURCE}",
        f"a1_root_prim: {A1_ROOT}",
        f"base_frame: {BASE_FRAME}",
        f"sensor_method: {SENSOR_METHOD}",
        f"camera_pointcloud_source: {CAMERA_POINTCLOUD_SOURCE}",
        f"candidate_data_source: {CANDIDATE_DATA_SOURCE}",
        f"output_contract: {OUTPUT_CONTRACT}",
        f"phaseD_candidate_data_used: {bool_text(summary.get('phaseD_candidate_data_used'))}",
        f"legal_command_count: {summary.get('legal_command_count')}",
        f"legal_parse_success_rate: {summary.get('legal_parse_success_rate')}",
        f"legal_validation_success_rate: {summary.get('legal_validation_success_rate')}",
        f"target_pose_lookup_success_rate: {summary.get('target_pose_lookup_success_rate')}",
        f"illegal_test_count: {summary.get('illegal_test_count')}",
        f"illegal_reject_or_fallback_rate: {summary.get('illegal_reject_or_fallback_rate')}",
        f"fallback_behavior: {summary.get('fallback_behavior')}",
        f"free_coordinate_output_allowed: {bool_text(summary.get('free_coordinate_output_allowed'))}",
        f"velocity_output_allowed: {bool_text(summary.get('velocity_output_allowed'))}",
        f"joint_action_output_allowed: {bool_text(summary.get('joint_action_output_allowed'))}",
        f"malformed_output_rejected: {bool_text(summary.get('malformed_output_rejected'))}",
        f"final_interface_output_contract_ok: {bool_text(summary.get('final_interface_output_contract_ok'))}",
        f"safe_to_closed_loop: {bool_text(summary.get('safe_to_closed_loop'))}",
        "training: false",
        "RL: false",
        "map_predict: false",
        "PI_finetuning: false",
        "A1_locomotion_training: false",
        "rollout_started: false",
        "",
        "## Caveats",
        "",
    ]
    for caveat in summary.get("caveats", []):
        lines.append(f"- {caveat}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- run_dir: {summary.get('run_dir')}",
            f"- phaseD_run_dir: {summary.get('phaseD_run_dir')}",
            f"- vlm_la_interface_smoke_jsonl: {summary.get('vlm_la_interface_smoke_jsonl')}",
            f"- parse_summary_json: {summary.get('parse_summary_json')}",
            f"- test_cases_csv: {summary.get('test_cases_csv')}",
            "",
            "## Negative Scope",
            "",
            "- No real VLM inference or fine-tuning.",
            "- No closed-loop, rollout, A1 movement, mapping, or candidate generation.",
            "- No training, RL, SFT, GDPO, map_predict, checkpoint, or USD modification.",
            "- No geometry proxy and no old-scene candidate data.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_failure_reports(run_dir: Path, summary: dict[str, Any]) -> None:
    report_path = run_dir / "reports/NEW_SCENE_VLM_LA_INTERFACE_REPORT.md"
    write_report(report_path, summary)
    write_report(TOP_REPORT, summary)
    write_report(COMPAT_REPORT, summary)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run_dir", default=None)
    parser.add_argument("--phaseD_run_dir", default=None)
    args = parser.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve() if args.run_dir else default_run_dir()
    for sub in ["logs", "interface", "reports", "summary", "test_cases"]:
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    COMPAT_DIR.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "phase": PHASE,
        "workspace": str(WORKSPACE),
        "project_name": PROJECT_NAME,
        "scene_path": str(SCENE_PATH),
        "robot_platform": ROBOT_PLATFORM,
        "robot_source": ROBOT_SOURCE,
        "a1_root_prim": A1_ROOT,
        "sensor_method": SENSOR_METHOD,
        "candidate_data_source": CANDIDATE_DATA_SOURCE,
        "output_contract": OUTPUT_CONTRACT,
        "phaseD_candidate_data_used": False,
        "safe_to_closed_loop": False,
        "run_dir": str(run_dir),
    }
    exit_code = 1
    started = time.time()
    try:
        phaseD_run_dir = find_phaseD_run(args.phaseD_run_dir)
        phaseD_summary, rows, steps = load_phaseD_artifacts(phaseD_run_dir)
        candidate_index, selected_by_step, rows_by_step = build_candidate_index(rows)
        for step in steps:
            step_id = int(step["step_id"])
            selected_row = selected_candidate_for_step(step_id, selected_by_step)
            selected_id = int(selected_row["candidate_id"])
            for test in make_test_cases(step_id, selected_id, rows_by_step.get(step_id, [])):
                records.append(evaluate_command(step_id, test, candidate_index, selected_by_step))

        jsonl_path = run_dir / "summary/vlm_la_interface_smoke.jsonl"
        test_csv = run_dir / "test_cases/interface_test_cases.csv"
        write_jsonl(jsonl_path, records)
        write_test_case_csv(test_csv, records)
        summary = summarize(run_dir, phaseD_run_dir, phaseD_summary, records, jsonl_path)
        exit_code = 0 if summary["safe_to_closed_loop"] else 2
    except Exception as exc:
        summary.update(
            {
                "exception": repr(exc),
                "traceback": traceback.format_exc(),
                "phaseD_candidate_data_used": False,
                "safe_to_closed_loop": False,
                "next_phase": "Fix New Scene Phase E VLM-LA interface smoke",
                "caveats": ["Phase E failed before all interface checks completed."],
            }
        )
        exit_code = 1
    finally:
        summary["elapsed_sec"] = round(time.time() - started, 3)
        (run_dir / "summary/parse_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        write_failure_reports(run_dir, summary)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
