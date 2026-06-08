#!/usr/bin/env python3
"""New Scene Phase H: dataset quality audit and human review packet.

This reads the New Scene Phase G rollout artifacts and creates review-only
quality summaries. It does not train, run VLM inference, modify Phase G rows,
modify USD files, or mark data as training-ready.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


WORKSPACE = Path("/home/ubuntu22/VLA")
RUNS = WORKSPACE / "runs"
PHASE = "New Scene Phase H dataset quality audit"
SOURCE_PHASE = "New Scene Phase G long rollout data collection"
PROJECT_NAME = "A1-VLM-LA Explorer"
MAIN_GOAL = "A1-VLM-LA Explorer for 3D Active Exploration"
SCENE_ID = "building_scene_1_scene_20260608_171052"
SCENE = WORKSPACE / "scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda"
ROBOT_PLATFORM = "unitree_a1"
ROBOT_SOURCE = "existing_usd_prim"
A1_ROOT = "/World/A1"
BASE_FRAME = "/World/A1/base"
SENSOR_METHOD = "real_isaac_omniverse_rgbd"
CAMERA_POINTCLOUD_SOURCE = "depth_backprojection"
OUTPUT_CONTRACT = "Go to candidate <id>."
LABEL_SOURCE = "classical_argmax_information_gain_minus_path_cost"
RECOMMENDED_NEXT_PHASE = "manual_review_before_sft_preparation"
TOP_REPORT = RUNS / "NEW_SCENE_DATASET_QUALITY_REPORT.md"
TOP_CHECKLIST = RUNS / "HUMAN_REVIEW_NEW_SCENE_DATASET_CHECKLIST.md"
PHASE_G_REPORT = RUNS / "NEW_SCENE_VLM_LA_LONG_ROLLOUT_REPORT.md"


def bool_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def finite_float(value: Any, default: float | None = None) -> float | None:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def int_value(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def rate(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def default_run_dir() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return RUNS / f"new_scene_building_scene_1_phaseH_dataset_quality_audit_{timestamp}"


def parse_source_run_from_report() -> Path:
    if PHASE_G_REPORT.exists():
        for line in PHASE_G_REPORT.read_text(encoding="utf-8").splitlines():
            if line.startswith("- run_dir:"):
                return Path(line.split(":", 1)[1].strip())
            if line.startswith("run_dir:"):
                return Path(line.split(":", 1)[1].strip())
    candidates = sorted(RUNS.glob("new_scene_building_scene_1_phaseG_long_rollout_20*"), reverse=True)
    for candidate in candidates:
        if candidate.is_dir() and not candidate.name.endswith("_smoke"):
            return candidate
    raise FileNotFoundError("Unable to locate New Scene Phase G run_dir")


def sample_key(sample: dict[str, Any]) -> tuple[int, int] | None:
    sample_id = str(sample.get("sample_id", ""))
    match = re.search(r"start(\d+)_step(\d+)", sample_id)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2))


def parsed_candidate_id(text: str) -> int | None:
    match = re.fullmatch(r"\s*Go to candidate (\d+)\.\s*", text or "")
    return int(match.group(1)) if match else None


def freeform_action_like(text: str) -> bool:
    lowered = (text or "").lower()
    banned = ["x=", "y=", "coordinate", "velocity", "joint", "move(", "[", "]", "{", "}"]
    return any(token in lowered for token in banned)


def path_exists_under(source_run: Path, relative_path: str | None) -> bool:
    if not relative_path:
        return False
    return (source_run / relative_path).exists()


def selected_candidate(rows: list[dict[str, str]], selected_id: int) -> dict[str, str] | None:
    for row in rows:
        if int_value(row.get("candidate_id"), -1) == selected_id:
            return row
    return None


def classify_sample(
    source_run: Path,
    step: dict[str, str],
    sample: dict[str, Any],
    candidates: list[dict[str, str]],
    selected: dict[str, str] | None,
    path_cost_unique_count: int,
) -> dict[str, Any]:
    reject: list[str] = []
    warning: list[str] = []

    start_id = int_value(step.get("start_id"), -1)
    step_id = int_value(step.get("step_id"), -1)
    selected_id = int_value(step.get("selected_candidate_id"), -1)
    target_language = step.get("target_language", "")

    # Sensor quality.
    if sample.get("geometry_proxy_used") is not False or bool_value(step.get("geometry_proxy_used")):
        reject.append("geometry_proxy_used")
    if sample.get("mounted_geometry_proxy_used") is not False or bool_value(step.get("mounted_geometry_proxy_used")):
        reject.append("mounted_geometry_proxy_used")
    if sample.get("sensor_method") != SENSOR_METHOD or step.get("sensor_method") != SENSOR_METHOD:
        reject.append("sensor_method_mismatch")
    if sample.get("camera_pointcloud_source") not in {CAMERA_POINTCLOUD_SOURCE, "isaac_pointcloud_annotator"}:
        reject.append("camera_pointcloud_source_invalid")
    if step.get("camera_pointcloud_source") not in {CAMERA_POINTCLOUD_SOURCE, "isaac_pointcloud_annotator"}:
        reject.append("step_camera_pointcloud_source_invalid")
    if not bool_value(step.get("depth_available")):
        reject.append("depth_unavailable")
    if not bool_value(step.get("camera_pointcloud_available")):
        reject.append("camera_pointcloud_unavailable")
    depth_valid_ratio = finite_float(step.get("depth_valid_ratio"), -1.0)
    if depth_valid_ratio is None or depth_valid_ratio < 0:
        reject.append("depth_valid_ratio_missing")
    elif depth_valid_ratio < 0.5:
        reject.append("depth_severe_invalid")
    elif depth_valid_ratio < 0.65:
        warning.append("low_depth_valid_ratio")
    if int_value(step.get("pointcloud_point_count")) <= 0:
        reject.append("pointcloud_empty")
    if sample.get("rgb_image") and not bool_value(step.get("rgb_available")):
        warning.append("rgb_invalid_but_debug_rgb_path_present")

    # Map quality.
    known_before = finite_float(step.get("known_ratio_before"))
    known_after = finite_float(step.get("known_ratio_after"))
    known_delta = finite_float(step.get("known_ratio_delta"), 0.0)
    if known_before is None or known_after is None:
        reject.append("known_ratio_nan_or_missing")
    elif known_after + 1e-6 < known_before:
        reject.append("known_ratio_decreased")
    occupied_cells = int_value(step.get("occupied_cells"))
    known_free_cells = int_value(step.get("known_free_cells"))
    unknown_cells = int_value(step.get("unknown_cells"))
    if known_free_cells <= 0:
        reject.append("known_free_cells_zero")
    if unknown_cells <= 0:
        reject.append("unknown_cells_zero")
    if occupied_cells <= 0:
        if known_free_cells > 0 and unknown_cells > 0:
            warning.append("occupied_cells_zero")
        else:
            reject.append("bev_map_empty")
    if sample.get("bev_image"):
        if not path_exists_under(source_run, sample.get("bev_image")):
            warning.append("bev_image_path_missing")
    elif not sample.get("map_stats"):
        reject.append("bev_image_and_map_metadata_missing")
    if known_delta is not None and known_delta <= 0 and not step.get("failure_reason"):
        warning.append("non_positive_known_ratio_delta")

    # Candidate quality.
    candidate_count = int_value(step.get("candidate_count"))
    valid_candidate_count = int_value(step.get("valid_candidate_count"))
    positive_gain_count = int_value(step.get("positive_gain_candidate_count"))
    if candidate_count < 1 or not candidates:
        reject.append("candidate_table_missing")
    elif candidate_count < 16:
        reject.append("candidate_count_below_16")
    if valid_candidate_count < 1:
        reject.append("no_valid_candidate")
    elif valid_candidate_count < 4:
        warning.append("low_valid_candidate_count")
    if positive_gain_count == 0:
        if step.get("failure_reason"):
            warning.append("zero_positive_gain_candidates_with_reason")
        else:
            warning.append("zero_positive_gain_candidates")
    if selected_id < 0:
        reject.append("selected_candidate_id_missing")
    if selected is None:
        reject.append("selected_candidate_not_in_candidate_table")
    else:
        if not bool_value(selected.get("is_valid")):
            reject.append("selected_candidate_invalid")
        if not bool_value(selected.get("is_reachable")):
            reject.append("selected_candidate_unreachable")
        if bool_value(selected.get("collision_risk")):
            reject.append("selected_candidate_collision_risk")
        if not bool_value(selected.get("selected_by_classical")):
            reject.append("selected_by_classical_false")
        if selected.get("path_cost") in {None, ""}:
            reject.append("selected_path_cost_missing")
        if selected.get("information_gain") in {None, ""}:
            reject.append("selected_information_gain_missing")
        if selected.get("score") in {None, ""}:
            reject.append("selected_score_missing")
    if path_cost_unique_count <= 1:
        warning.append("path_cost_globally_constant")

    # Label and language quality.
    parsed_id = parsed_candidate_id(target_language)
    if not target_language:
        reject.append("target_language_missing")
    elif freeform_action_like(target_language):
        reject.append("freeform_action_output")
    elif parsed_id is None:
        reject.append("target_language_format_invalid")
    elif parsed_id != selected_id:
        reject.append("parsed_id_mismatch_selected_candidate_id")
    if not bool_value(step.get("parse_success")):
        reject.append("parse_failed")
    if not bool_value(step.get("validation_success")):
        reject.append("validation_failed")
    if not bool_value(step.get("target_pose_lookup_success")):
        reject.append("target_pose_lookup_failed")
    if sample.get("label_source") not in {LABEL_SOURCE, "classical_argmax_information_gain_minus_path_cost"}:
        warning.append("label_source_missing_or_nonstandard")

    # Closed-loop behavior quality.
    if not bool_value(step.get("movement_success")):
        if step.get("failure_reason"):
            warning.append("movement_failed_with_reason")
        else:
            reject.append("movement_failed_without_reason")
    if bool_value(step.get("collision_flag")):
        reject.append("collision_flag")
    if bool_value(step.get("falling_flag")):
        reject.append("falling_flag")
    if bool_value(step.get("stuck_flag")):
        if step.get("failure_reason"):
            warning.append("stuck_flag_with_reason")
        else:
            reject.append("stuck_without_reason")
    if bool_value(step.get("fallback_used")):
        warning.append("fallback_used")
    if step.get("failure_reason"):
        warning.append(f"recorded_failure_reason:{step.get('failure_reason')}")

    reject = sorted(set(reject))
    warning = sorted(set(warning))
    status = "reject" if reject else "warning" if warning else "pass"
    return {
        "sample_id": sample.get("sample_id"),
        "start_id": start_id,
        "step_id": step_id,
        "quality_status": status,
        "quality_flags": reject + warning,
        "reject_reason": ";".join(reject) if reject else None,
        "warning_reason": ";".join(warning) if warning else None,
        "target_language": target_language,
        "selected_candidate_id": selected_id,
        "known_ratio_before": known_before,
        "known_ratio_after": known_after,
        "known_ratio_delta": known_delta,
        "candidate_count": candidate_count,
        "valid_candidate_count": valid_candidate_count,
        "positive_gain_candidate_count": positive_gain_count,
        "depth_valid_ratio": depth_valid_ratio,
        "pointcloud_point_count": int_value(step.get("pointcloud_point_count")),
        "rgb_available": bool_value(step.get("rgb_available")),
        "depth_available": bool_value(step.get("depth_available")),
        "camera_pointcloud_available": bool_value(step.get("camera_pointcloud_available")),
        "movement_success": bool_value(step.get("movement_success")),
        "collision_flag": bool_value(step.get("collision_flag")),
        "stuck_flag": bool_value(step.get("stuck_flag")),
        "falling_flag": bool_value(step.get("falling_flag")),
        "sample": sample,
    }


def split_quality_rows(audited: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    accepted = [row for row in audited if row["quality_status"] == "pass"]
    warning = [row for row in audited if row["quality_status"] == "warning"]
    rejected = [row for row in audited if row["quality_status"] == "reject"]
    return accepted, warning, rejected


def make_flag_summary(audited: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counter: Counter[str] = Counter()
    for row in audited:
        for flag in row["quality_flags"]:
            counter[flag] += 1
    if not counter:
        return [{"reason": "none", "count": 0, "rate": 0.0}]
    total = len(audited)
    return [{"reason": reason, "count": count, "rate": rate(count, total)} for reason, count in counter.most_common()]


def filter_reasons(flag_summary: list[dict[str, Any]], audited: list[dict[str, Any]], field: str) -> list[dict[str, Any]]:
    reason_set: set[str] = set()
    for row in audited:
        value = row.get(field)
        if value:
            reason_set.update(str(value).split(";"))
    return [row for row in flag_summary if row["reason"] in reason_set and row["reason"] != "none"]


def make_start_summary(audited: list[dict[str, Any]], phase_g_start_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in audited:
        grouped[int(row["start_id"])].append(row)
    phase_g_by_start = {int_value(row.get("start_id")): row for row in phase_g_start_rows}
    out: list[dict[str, Any]] = []
    for start_id in sorted(grouped):
        rows = grouped[start_id]
        accepted = sum(1 for row in rows if row["quality_status"] == "pass")
        warning = sum(1 for row in rows if row["quality_status"] == "warning")
        rejected = sum(1 for row in rows if row["quality_status"] == "reject")
        status = "reject" if rejected else "warning" if warning else "pass"
        source = phase_g_by_start.get(start_id, {})
        out.append(
            {
                "start_id": start_id,
                "quality_status": status,
                "sample_count": len(rows),
                "accepted_sample_count": accepted,
                "warning_sample_count": warning,
                "rejected_sample_count": rejected,
                "acceptance_rate": rate(accepted, len(rows)),
                "warning_rate": rate(warning, len(rows)),
                "rejection_rate": rate(rejected, len(rows)),
                "final_known_ratio": source.get("final_known_ratio", rows[-1].get("known_ratio_after")),
                "known_ratio_gain": source.get("known_ratio_gain", ""),
                "action_count": source.get("action_count", len(rows)),
                "phaseG_failure_count": source.get("failure_count", ""),
                "phaseG_stop_reason": source.get("stop_reason", ""),
            }
        )
    return out


def save_plots(run_dir: Path, audited: list[dict[str, Any]], start_summary: list[dict[str, Any]], candidate_rows: list[dict[str, str]]) -> bool:
    plots = run_dir / "plots"
    plots.mkdir(parents=True, exist_ok=True)
    status_counts = Counter(row["quality_status"] for row in audited)
    flag_summary = make_flag_summary(audited)
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        write_csv(
            plots / "accepted_warning_rejected_counts.csv",
            [{"status": key, "count": value} for key, value in status_counts.items()],
            ["status", "count"],
        )
        return False

    plt.figure(figsize=(5, 4))
    plt.bar(["accepted", "warning", "rejected"], [status_counts.get("pass", 0), status_counts.get("warning", 0), status_counts.get("reject", 0)])
    plt.ylabel("sample count")
    plt.title("Accepted / Warning / Rejected")
    plt.tight_layout()
    plt.savefig(plots / "accepted_warning_rejected_counts.png", dpi=120)
    plt.close()

    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in audited:
        grouped[int(row["start_id"])].append(row)
    plt.figure(figsize=(8, 5))
    for start_id, rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda item: int(item["step_id"]))
        plt.plot([int(row["step_id"]) for row in rows], [float(row["known_ratio_after"]) for row in rows], marker="o", linewidth=1.2, label=f"start {start_id:03d}")
    plt.xlabel("step")
    plt.ylabel("known ratio")
    plt.title("Known ratio by start")
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=7, ncol=2)
    plt.tight_layout()
    plt.savefig(plots / "known_ratio_by_start.png", dpi=120)
    plt.close()

    ordered = sorted(start_summary, key=lambda row: int(row["start_id"]))
    start_ids = [int(row["start_id"]) for row in ordered]
    plt.figure(figsize=(7, 4))
    plt.bar(start_ids, [float(row["final_known_ratio"]) for row in ordered])
    plt.xlabel("start")
    plt.ylabel("final known ratio")
    plt.title("Final known ratio by start")
    plt.tight_layout()
    plt.savefig(plots / "final_known_ratio_by_start.png", dpi=120)
    plt.close()

    plt.figure(figsize=(7, 4))
    plt.bar(start_ids, [int(float(row["action_count"])) for row in ordered])
    plt.xlabel("start")
    plt.ylabel("action count")
    plt.title("Action count by start")
    plt.tight_layout()
    plt.savefig(plots / "action_count_by_start.png", dpi=120)
    plt.close()

    values = {
        "candidate_score_distribution.png": ([finite_float(row.get("score")) for row in candidate_rows], "Candidate score distribution", "score"),
        "information_gain_distribution.png": ([finite_float(row.get("information_gain")) for row in candidate_rows], "Information gain distribution", "information gain"),
        "path_cost_distribution.png": ([finite_float(row.get("path_cost")) for row in candidate_rows], "Path cost distribution", "path cost"),
    }
    for filename, (raw_values, title, xlabel) in values.items():
        clean = [value for value in raw_values if value is not None]
        plt.figure(figsize=(7, 4))
        plt.hist(clean, bins=30)
        plt.xlabel(xlabel)
        plt.ylabel("count")
        plt.title(title)
        plt.tight_layout()
        plt.savefig(plots / filename, dpi=120)
        plt.close()

    top_flags = flag_summary[:12]
    plt.figure(figsize=(9, max(4, len(top_flags) * 0.35)))
    plt.barh([row["reason"] for row in reversed(top_flags)], [int(row["count"]) for row in reversed(top_flags)])
    plt.xlabel("count")
    plt.title("Quality flag counts")
    plt.tight_layout()
    plt.savefig(plots / "failure_reason_counts.png", dpi=120)
    plt.close()
    return True


def make_dataset_summary(
    run_dir: Path,
    source_run: Path,
    phase_g_summary: dict[str, Any],
    manifest: dict[str, Any],
    audited: list[dict[str, Any]],
    start_summary: list[dict[str, Any]],
    flag_summary: list[dict[str, Any]],
    plots_saved: bool,
) -> dict[str, Any]:
    accepted, warning, rejected = split_quality_rows(audited)
    real_sensor = sum(
        1
        for row in audited
        if row["depth_available"]
        and row["camera_pointcloud_available"]
        and row["sample"].get("sensor_method") == SENSOR_METHOD
        and row["sample"].get("geometry_proxy_used") is False
        and row["sample"].get("mounted_geometry_proxy_used") is False
    )
    return {
        "phase": PHASE,
        "workspace": str(WORKSPACE),
        "project_name": PROJECT_NAME,
        "main_goal": MAIN_GOAL,
        "source_phase": SOURCE_PHASE,
        "source_run_dir": str(source_run),
        "scene_id": SCENE_ID,
        "scene_path": str(SCENE),
        "robot_platform": ROBOT_PLATFORM,
        "robot_source": ROBOT_SOURCE,
        "a1_root_prim": A1_ROOT,
        "base_frame": BASE_FRAME,
        "sensor_method": SENSOR_METHOD,
        "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE,
        "geometry_proxy_used": False,
        "mounted_geometry_proxy_used": False,
        "output_contract": OUTPUT_CONTRACT,
        "label_source": LABEL_SOURCE,
        "total_samples": len(audited),
        "manifest_sample_count": manifest.get("sample_count"),
        "accepted_sample_count": len(accepted),
        "warning_sample_count": len(warning),
        "rejected_sample_count": len(rejected),
        "acceptance_rate": rate(len(accepted), len(audited)),
        "warning_rate": rate(len(warning), len(audited)),
        "rejection_rate": rate(len(rejected), len(audited)),
        "start_count": phase_g_summary.get("start_count"),
        "completed_start_count": phase_g_summary.get("completed_start_count"),
        "starts_with_failures": phase_g_summary.get("starts_with_failures"),
        "parse_success_rate": phase_g_summary.get("parse_success_rate"),
        "validation_success_rate": phase_g_summary.get("validation_success_rate"),
        "movement_success_rate": phase_g_summary.get("movement_success_rate"),
        "real_sensor_sample_rate": rate(real_sensor, len(audited)),
        "rgb_valid_rate": phase_g_summary.get("real_rgb_sensor_valid_rate"),
        "depth_valid_rate": phase_g_summary.get("real_depth_sensor_valid_rate"),
        "camera_pointcloud_valid_rate": phase_g_summary.get("real_camera_pointcloud_valid_rate"),
        "average_final_known_ratio": phase_g_summary.get("average_final_known_ratio"),
        "average_known_ratio_gain": phase_g_summary.get("average_known_ratio_gain"),
        "main_warning_reasons": filter_reasons(flag_summary, audited, "warning_reason")[:10],
        "main_reject_reasons": filter_reasons(flag_summary, audited, "reject_reason")[:10],
        "training_ready": False,
        "requires_human_review": True,
        "recommended_next_phase": RECOMMENDED_NEXT_PHASE,
        "safe_to_prepare_sft_without_manual_review": False,
        "run_dir": str(run_dir),
        "accepted_samples_path": str(run_dir / "quality/accepted_samples.jsonl"),
        "warning_samples_path": str(run_dir / "quality/warning_samples.jsonl"),
        "rejected_samples_path": str(run_dir / "quality/rejected_samples.jsonl"),
        "dataset_quality_summary_path": str(run_dir / "summary/dataset_quality_summary.json"),
        "start_quality_summary_path": str(run_dir / "summary/start_quality_summary.csv"),
        "failure_reason_summary_path": str(run_dir / "summary/failure_reason_summary.csv"),
        "plots_path": str(run_dir / "plots"),
        "plots_saved": plots_saved,
    }


def write_checklist(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Human Review New Scene Dataset Checklist",
        "",
        "## Review Scope",
        "",
        f"- source_run_dir: {summary['source_run_dir']}",
        f"- sample_count: {summary['total_samples']}",
        f"- accepted_sample_count: {summary['accepted_sample_count']}",
        f"- warning_sample_count: {summary['warning_sample_count']}",
        f"- rejected_sample_count: {summary['rejected_sample_count']}",
        f"- robot_platform: {summary['robot_platform']}",
        f"- scene_path: {summary['scene_path']}",
        f"- sensor_method: {summary['sensor_method']}",
        f"- output_contract: {summary['output_contract']}",
        "- training_ready: false",
        "- requires_human_review: true",
        "",
        "## Required Manual Checks",
        "",
        "1. BEV candidate render is clear.",
        "2. Candidate id matches the candidate table.",
        "3. Selected candidate is near unknown exploration space.",
        "4. `target_language` is correct: `Go to candidate <id>.`",
        "5. Warning/reject volume is acceptable.",
        "6. RGB/depth/pointcloud are from real Isaac/Omniverse sensors.",
        "7. No geometry proxy data is present.",
        "8. A1 trajectory is continuous.",
        "9. No collision, stuck, or falling is present.",
        "10. Repeated viewpoints or spinning-in-place behavior are not excessive.",
        "11. Decide whether the data can enter VLM SFT dataset preparation.",
        "",
        "## Review Decision Template",
        "",
        "- approve_for_sft_preparation: yes/no/unsure",
        "- approve_for_gdpo_preparation: yes/no/unsure",
        "- need_more_rollout_data: yes/no",
        "- need_sensor_fix: yes/no",
        "- need_candidate_fix: yes/no",
        "- reviewer_notes:",
        "",
        "## Audit Output Paths",
        "",
        f"- dataset_quality_summary: {summary['dataset_quality_summary_path']}",
        f"- start_quality_summary: {summary['start_quality_summary_path']}",
        f"- failure_reason_summary: {summary['failure_reason_summary_path']}",
        f"- accepted_samples: {summary['accepted_samples_path']}",
        f"- warning_samples: {summary['warning_samples_path']}",
        f"- rejected_samples: {summary['rejected_samples_path']}",
        f"- plots_path: {summary['plots_path']}",
        "",
        "## Guardrail",
        "",
        "This packet does not approve training. `training_ready` remains false until a human reviewer explicitly approves a later preparation phase.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_report(path: Path, summary: dict[str, Any]) -> None:
    warning_reasons = ", ".join(f"{row['reason']} ({row['count']})" for row in summary["main_warning_reasons"]) or "none"
    reject_reasons = ", ".join(f"{row['reason']} ({row['count']})" for row in summary["main_reject_reasons"]) or "none"
    lines = [
        "# New Scene Dataset Quality Report",
        "",
        "phase: New Scene Phase H",
        "source phase: New Scene Phase G",
        f"source run_dir: {summary['source_run_dir']}",
        f"scene_path: {summary['scene_path']}",
        f"robot_platform: {summary['robot_platform']}",
        f"sensor_method: {summary['sensor_method']}",
        f"camera_pointcloud_source: {summary['camera_pointcloud_source']}",
        f"geometry_proxy_used: {str(summary['geometry_proxy_used']).lower()}",
        f"mounted_geometry_proxy_used: {str(summary['mounted_geometry_proxy_used']).lower()}",
        f"total_samples: {summary['total_samples']}",
        f"accepted_sample_count: {summary['accepted_sample_count']}",
        f"warning_sample_count: {summary['warning_sample_count']}",
        f"rejected_sample_count: {summary['rejected_sample_count']}",
        f"acceptance_rate: {summary['acceptance_rate']}",
        f"warning_rate: {summary['warning_rate']}",
        f"rejection_rate: {summary['rejection_rate']}",
        f"parse_success_rate: {summary['parse_success_rate']}",
        f"validation_success_rate: {summary['validation_success_rate']}",
        f"movement_success_rate: {summary['movement_success_rate']}",
        f"real_sensor_sample_rate: {summary['real_sensor_sample_rate']}",
        f"average_final_known_ratio: {summary['average_final_known_ratio']}",
        f"main warning reasons: {warning_reasons}",
        f"main rejection reasons: {reject_reasons}",
        f"plots path: {summary['plots_path']}",
        f"accepted samples path: {summary['accepted_samples_path']}",
        f"warning samples path: {summary['warning_samples_path']}",
        f"rejected samples path: {summary['rejected_samples_path']}",
        "training_ready: false",
        "requires_human_review: true",
        f"recommended_next_phase: {summary['recommended_next_phase']}",
        "",
        "## Interpretation",
        "",
        "- Automated audit completed without modifying Phase G source rows.",
        "- Accepted samples pass all automated quality gates.",
        "- Warning samples require manual attention but are not automatically rejected.",
        "- Rejected samples must not enter SFT/GDPO preparation unless manually repaired and re-audited.",
        "- This report keeps `training_ready: false`; a human review decision is required before SFT preparation.",
        "",
        "## Negative Scope",
        "",
        "- No training, SFT, GDPO, RL, map_predict, real VLM inference, checkpoint creation, or USD save.",
        "- No repaired USD bundle, dependencies, mesh, texture, raw RGB-D, npz/hdf5, checkpoint, or core dump is included.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    current_phase = "New Scene Phase H dataset quality audit / human review packet"
    common = f"""current_scene_id: {SCENE_ID}
current_scene_path: {SCENE}
current_scene_phase: {current_phase}
source_dataset: New Scene Phase G rollout
source_run_dir: {summary['source_run_dir']}
robot_platform: {ROBOT_PLATFORM}
robot_source: {ROBOT_SOURCE}
a1_root_prim: {A1_ROOT}
base_frame: {BASE_FRAME}
sensor_method: {SENSOR_METHOD}
camera_pointcloud_source: {CAMERA_POINTCLOUD_SOURCE}
vlm_output_mode: pseudo_from_classical_selector
output_contract: {OUTPUT_CONTRACT}
training_ready: false
requires_human_review: true
next_phase: Manual review result required before SFT preparation
"""
    negative = """negative_scope:
- training: false
- RL: false
- SFT: false
- GDPO: false
- map_predict: false
- real_VLM_inference: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- checkpoint_created: false
"""
    metrics = f"""total_samples: {summary['total_samples']}
accepted_sample_count: {summary['accepted_sample_count']}
warning_sample_count: {summary['warning_sample_count']}
rejected_sample_count: {summary['rejected_sample_count']}
acceptance_rate: {summary['acceptance_rate']}
warning_rate: {summary['warning_rate']}
rejection_rate: {summary['rejection_rate']}
parse_success_rate: {summary['parse_success_rate']}
validation_success_rate: {summary['validation_success_rate']}
movement_success_rate: {summary['movement_success_rate']}
real_sensor_sample_rate: {summary['real_sensor_sample_rate']}
average_final_known_ratio: {summary['average_final_known_ratio']}
"""

    (RUNS / "ACTIVE_TASK_BOARD.md").write_text(
        f"""# Active Task Board

current_phase: {current_phase}
workspace: {WORKSPACE}
main_goal: {MAIN_GOAL}
{common}
{negative}

## New Scene Phase H Result

status: completed
run_dir: {summary['run_dir']}
script: {WORKSPACE / 'scripts/new_scene_phaseH_dataset_quality_audit.py'}
quality_report: {TOP_REPORT}
human_review_checklist: {TOP_CHECKLIST}
dataset_quality_summary: {summary['dataset_quality_summary_path']}
start_quality_summary: {summary['start_quality_summary_path']}
failure_reason_summary: {summary['failure_reason_summary_path']}

{metrics}

## Scope

Phase H only audited New Scene Phase G rollout data and generated a human review
packet. It did not train, run real VLM inference, modify Phase G source rows,
save USD files, or mark the data training-ready.
""",
        encoding="utf-8",
    )

    (RUNS / "WEBGPT_BRIEF.md").write_text(
        f"""# WEBGPT Brief

## Current Phase

{current_phase}

## Context

{common}
{negative}

## Completed

- Audited New Scene Phase G real-sensor rollout samples.
- Split samples into accepted, warning, and rejected sets.
- Generated dataset quality summary, start quality summary, failure reason summary, plots, and a human review checklist.
- Kept `training_ready: false` and `requires_human_review: true`.

## Metrics

{metrics}

## Next Action

Manual review result required before SFT preparation.
""",
        encoding="utf-8",
    )

    (RUNS / "CRITIC_REPORT.md").write_text(
        f"""# Critic Report

## Current Phase

{current_phase}

## Finding

status: completed

The Phase H audit read New Scene Phase G rollout artifacts and produced a
review packet without modifying original data. No training, real VLM inference,
geometry proxy, Go2 label, or USD save was used. The dataset remains not
training-ready until manual review.

## Evidence

- source_run_dir: {summary['source_run_dir']}
- quality_report: {TOP_REPORT}
- human_review_checklist: {TOP_CHECKLIST}
- total_samples: {summary['total_samples']}
- accepted_sample_count: {summary['accepted_sample_count']}
- warning_sample_count: {summary['warning_sample_count']}
- rejected_sample_count: {summary['rejected_sample_count']}
- real_sensor_sample_rate: {summary['real_sensor_sample_rate']}
- parse_success_rate: {summary['parse_success_rate']}
- validation_success_rate: {summary['validation_success_rate']}
- movement_success_rate: {summary['movement_success_rate']}

## Gate

Manual review result required before SFT preparation.

training: false
RL: false
SFT: false
GDPO: false
map_predict: false
real_VLM_inference: false
USD_modified_or_saved: false
""",
        encoding="utf-8",
    )

    (RUNS / "VLM_LA_EXPLORER_PLAN.md").write_text(
        f"""# VLM-LA Explorer Plan

## Method Name

{PROJECT_NAME}

Full route name:

{MAIN_GOAL}

## Output Contract

`{OUTPUT_CONTRACT}`

## Current New Scene

```yaml
{common}phaseH_status: completed
```

## New Scene Route

1. Phase A: scene open and robot inspection. Status: passed.
2. Phase B: real Isaac/Omniverse sensor suite smoke. Status: passed.
3. Phase C: real-sensor mapping smoke. Status: passed.
4. Phase D: candidate viewpoint + information gain smoke. Status: passed.
5. Phase E: VLM-LA interface smoke. Status: passed.
6. Phase F: short closed-loop smoke. Status: passed.
7. Phase G: long rollout data collection. Status: passed.
8. Phase H: dataset quality audit and human review packet. Status: completed.
9. SFT preparation: blocked until manual review approval.

## Phase H Gate

{metrics}

## Negative Scope

training: false
RL: false
SFT: false
GDPO: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
real_VLM_inference: false
training_ready: false
""",
        encoding="utf-8",
    )

    (RUNS / "VLM_LA_DATASET_SPEC.md").write_text(
        f"""# VLM-LA Dataset Spec

## Project Route

{MAIN_GOAL}

## Current New Scene Dataset Status

```yaml
{common}dataset_quality_summary: {summary['dataset_quality_summary_path']}
human_review_checklist: {TOP_CHECKLIST}
phaseH_status: completed
```

## Phase H Audit Outputs

- accepted_samples: {summary['accepted_samples_path']}
- warning_samples: {summary['warning_samples_path']}
- rejected_samples: {summary['rejected_samples_path']}
- start_quality_summary: {summary['start_quality_summary_path']}
- failure_reason_summary: {summary['failure_reason_summary_path']}

## Quality Metrics

{metrics}

## Training Gate

training_ready: false
requires_human_review: true

Do not use new-scene data for SFT, GDPO, RL, or any training until a later
explicit human review approves preparation.
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source_run", default="")
    parser.add_argument("--run_dir", default="")
    args = parser.parse_args()

    source_run = Path(args.source_run).expanduser().resolve() if args.source_run else parse_source_run_from_report().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve() if args.run_dir else default_run_dir()
    for name in ["logs", "quality", "reports", "summary", "plots", "accepted", "warning", "rejected"]:
        (run_dir / name).mkdir(parents=True, exist_ok=True)

    required = {
        "rollout_summary": source_run / "summary/rollout_summary.json",
        "rollout_steps": source_run / "summary/rollout_steps.csv",
        "candidate_summary": source_run / "summary/candidate_summary.csv",
        "samples": source_run / "samples/vlm_la_samples.jsonl",
        "manifest": source_run / "samples/dataset_manifest.json",
    }
    missing = [str(path) for path in required.values() if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing Phase G inputs: " + ", ".join(missing))

    phase_g_summary = read_json(required["rollout_summary"])
    steps = read_csv(required["rollout_steps"])
    candidate_rows = read_csv(required["candidate_summary"])
    samples = read_jsonl(required["samples"])
    manifest = read_json(required["manifest"])
    start_rows = read_csv(source_run / "summary/start_summary.csv") if (source_run / "summary/start_summary.csv").exists() else []

    samples_by_key = {sample_key(sample): sample for sample in samples if sample_key(sample) is not None}
    candidates_by_step: dict[tuple[int, int], list[dict[str, str]]] = defaultdict(list)
    for row in candidate_rows:
        candidates_by_step[(int_value(row.get("start_id")), int_value(row.get("step_id")))].append(row)
    path_cost_values = {row.get("path_cost") for row in candidate_rows if row.get("path_cost") not in {None, ""}}

    audited: list[dict[str, Any]] = []
    for step in steps:
        key = (int_value(step.get("start_id")), int_value(step.get("step_id")))
        sample = samples_by_key.get(key)
        if sample is None:
            sample = {
                "sample_id": f"missing_start{key[0]:03d}_step{key[1]:03d}",
                "sensor_method": None,
                "geometry_proxy_used": None,
                "mounted_geometry_proxy_used": None,
            }
        candidates = candidates_by_step.get(key, [])
        selected = selected_candidate(candidates, int_value(step.get("selected_candidate_id"), -1))
        audited.append(classify_sample(source_run, step, sample, candidates, selected, len(path_cost_values)))

    accepted, warning_rows, rejected = split_quality_rows(audited)
    write_jsonl(run_dir / "quality/accepted_samples.jsonl", accepted)
    write_jsonl(run_dir / "quality/warning_samples.jsonl", warning_rows)
    write_jsonl(run_dir / "quality/rejected_samples.jsonl", rejected)

    flag_summary = make_flag_summary(audited)
    start_summary = make_start_summary(audited, start_rows)
    plots_saved = save_plots(run_dir, audited, start_summary, candidate_rows)
    dataset_summary = make_dataset_summary(run_dir, source_run, phase_g_summary, manifest, audited, start_summary, flag_summary, plots_saved)

    write_json(run_dir / "summary/dataset_quality_summary.json", dataset_summary)
    write_csv(
        run_dir / "summary/start_quality_summary.csv",
        start_summary,
        [
            "start_id",
            "quality_status",
            "sample_count",
            "accepted_sample_count",
            "warning_sample_count",
            "rejected_sample_count",
            "acceptance_rate",
            "warning_rate",
            "rejection_rate",
            "final_known_ratio",
            "known_ratio_gain",
            "action_count",
            "phaseG_failure_count",
            "phaseG_stop_reason",
        ],
    )
    write_csv(run_dir / "summary/failure_reason_summary.csv", flag_summary, ["reason", "count", "rate"])

    run_report = run_dir / "reports/NEW_SCENE_DATASET_QUALITY_REPORT.md"
    run_checklist = run_dir / "reports/HUMAN_REVIEW_NEW_SCENE_DATASET_CHECKLIST.md"
    write_report(run_report, dataset_summary)
    write_report(TOP_REPORT, dataset_summary)
    write_checklist(run_checklist, dataset_summary)
    write_checklist(TOP_CHECKLIST, dataset_summary)
    write_status_files(dataset_summary)

    print(json.dumps(dataset_summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
