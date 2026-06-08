#!/usr/bin/env python3
"""New-scene Phase A: Isaac headless USD Stage.Open plus A1 inspection.

This is a structural gate only. It starts Isaac headless so the USD libraries
and schemas are available, opens the selected scene with pxr.Usd.Stage.Open,
traverses the stage, and writes small reports. It does not save the USD stage,
run sensors, map, generate candidates, roll out, or train anything.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import traceback
from collections import Counter
from pathlib import Path
from typing import Any


WORKSPACE = Path("/home/ubuntu22/VLA")
EXACT_A1_PATHS = (
    "/World/A1",
    "/World/a1",
    "/World/UnitreeA1",
    "/World/unitree_a1",
)
ROBOT_KEYWORDS = ("a1", "unitree", "robot", "quadruped", "dog", "base_link", "base", "trunk")
BASE_KEYWORDS = ("base_link", "base", "trunk")
SENSOR_KEYWORDS = ("camera", "lidar", "depth", "rgb", "sensor", "laser", "imu")


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def find_core_dumps(workspace: Path) -> list[str]:
    matches: list[str] = []
    skip_dirs = {".git", "scenes", "__pycache__"}
    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for name in files:
            low = name.lower()
            if low == "core" or low.startswith("core.") or low.endswith(".core") or low.endswith(".dmp"):
                matches.append(str(Path(root) / name))
                if len(matches) >= 20:
                    return matches
    return matches


def _score_candidate(path: str, type_name: str, child_count: int, has_articulation: bool, matched: list[str]) -> int:
    low = path.lower()
    score = 0
    if path in EXACT_A1_PATHS:
        score += 400
    if "/a1" in low or "a1" in matched:
        score += 180
    if "unitree" in low:
        score += 120
    if has_articulation:
        score += 120
    if "robot" in low:
        score += 70
    if "quadruped" in low or "dog" in low:
        score += 50
    if "base_link" in low:
        score += 25
    elif "base" in low or "trunk" in low:
        score += 18
    if type_name == "Xform":
        score += 12
    score += min(child_count, 20)
    score -= min(path.count("/"), 16)
    return score


def inspect_stage(stage: Any, usd_physics: Any) -> dict[str, Any]:
    prims = list(stage.Traverse())
    type_counts: Counter[str] = Counter()
    summary_counts = {
        "Mesh": 0,
        "Cube": 0,
        "Material": 0,
        "Camera": 0,
        "Light": 0,
        "ArticulationRoot": 0,
        "PhysicsJoint": 0,
    }
    articulation_paths: set[str] = set()
    robot_candidates: list[dict[str, Any]] = []
    base_candidates: list[dict[str, Any]] = []
    camera_prims: list[str] = []
    lidar_prims: list[str] = []
    sensor_prims: list[str] = []

    for prim in prims:
        path = str(prim.GetPath())
        name = prim.GetName()
        type_name = prim.GetTypeName() or "UNDEFINED"
        low = f"{path} {name} {type_name}".lower()
        child_count = len(list(prim.GetChildren()))
        type_counts[type_name] += 1
        if type_name in summary_counts:
            summary_counts[type_name] += 1
        if "Light" in type_name:
            summary_counts["Light"] += 1
        if "Joint" in type_name:
            summary_counts["PhysicsJoint"] += 1
        try:
            has_articulation = bool(prim.HasAPI(usd_physics.ArticulationRootAPI))
        except Exception:
            has_articulation = False
        if has_articulation:
            articulation_paths.add(path)

        if type_name == "Camera" or "camera" in low:
            camera_prims.append(path)
        if "lidar" in low or "laser" in low or type_name.lower() == "lidar":
            lidar_prims.append(path)
        if any(keyword in low for keyword in SENSOR_KEYWORDS):
            sensor_prims.append(path)

        matched = [keyword for keyword in ROBOT_KEYWORDS if keyword in low]
        if has_articulation:
            matched.append("articulation_root")
        if not matched:
            continue
        item = {
            "path": path,
            "name": name,
            "type": type_name,
            "matched_keywords": sorted(set(matched)),
            "child_count": child_count,
            "has_articulation_root_api": has_articulation,
        }
        item["score"] = _score_candidate(path, type_name, child_count, has_articulation, item["matched_keywords"])
        robot_candidates.append(item)
        if any(keyword in low for keyword in BASE_KEYWORDS):
            base_candidates.append(item)

    robot_candidates.sort(key=lambda item: (-int(item["score"]), item["path"]))
    base_candidates.sort(key=lambda item: (-int(item["score"]), item["path"]))
    summary_counts["ArticulationRoot"] = len(articulation_paths)

    exact_a1 = [item for item in robot_candidates if item["path"] in EXACT_A1_PATHS]
    a1_named = [
        item
        for item in robot_candidates
        if "a1" in item["path"].lower() or "a1" in item["matched_keywords"]
    ]
    selected_a1_root = None
    if exact_a1:
        selected_a1_root = exact_a1[0]["path"]
    elif a1_named:
        selected_a1_root = sorted(
            a1_named,
            key=lambda item: (
                not bool(item["has_articulation_root_api"]),
                item["type"] != "Xform",
                -int(item["score"]),
                item["path"].count("/"),
            ),
        )[0]["path"]

    selected_base = None
    if selected_a1_root:
        in_root_base = [item for item in base_candidates if item["path"].startswith(selected_a1_root)]
        exact_base_path = f"{selected_a1_root}/base"
        exact_base = [item for item in in_root_base if item["path"] == exact_base_path]
        selected_base = exact_base[0]["path"] if exact_base else (in_root_base[0]["path"] if in_root_base else None)

    return {
        "prim_count": len(prims),
        "prim_type_counts": dict(summary_counts),
        "all_prim_type_counts": dict(sorted(type_counts.items())),
        "a1_found": selected_a1_root is not None,
        "a1_root_prim": selected_a1_root,
        "a1_base_frame_candidate": selected_base,
        "robot_candidate_prims": robot_candidates[:80],
        "base_candidate_prims": base_candidates[:40],
        "existing_camera_prims": camera_prims[:80],
        "existing_lidar_prims": lidar_prims[:80],
        "existing_sensor_prims": sensor_prims[:120],
    }


def write_report(path: Path, data: dict[str, Any]) -> None:
    lines: list[str] = []
    lines.append("# New Scene Open And Robot Inspection Report")
    lines.append("")
    lines.append("phase: New Scene Phase A")
    lines.append(f"workspace: {data['workspace']}")
    lines.append(f"current_scene_id: {data['scene_id']}")
    lines.append(f"NEW_SCENE_PATH: {data['scene_path']}")
    lines.append(f"original_user_usd_path: {data['original_user_usd_path']}")
    lines.append(f"scene_selection_reason: {data['scene_selection_reason']}")
    lines.append(f"scene_exists: {bool_text(data['scene_exists'])}")
    lines.append(f"scene_size_bytes: {data['scene_size_bytes']}")
    lines.append(f"scene_mtime: {data['scene_mtime']}")
    lines.append(f"stage_open_method: {data['stage_open_method']}")
    lines.append(f"stage_open_elapsed_sec: {data['stage_open_elapsed_sec']}")
    lines.append(f"open_stage_result: {bool_text(data['open_stage_result'])}")
    lines.append(f"stage_available: {bool_text(data['stage_available'])}")
    lines.append(f"prim_count: {data['prim_count']}")
    lines.append(f"core_dump_found: {bool_text(data['core_dump_found'])}")
    lines.append(f"robot_platform: {data['robot_platform']}")
    lines.append(f"robot_source: {data['robot_source']}")
    lines.append(f"a1_root_prim: {data['a1_root_prim'] or 'null'}")
    lines.append(f"a1_base_frame_candidate: {data['a1_base_frame_candidate'] or 'null'}")
    lines.append(f"safe_to_real_sensor_smoke: {bool_text(data['safe_to_real_sensor_smoke'])}")
    lines.append(f"formal_sampling_started: {bool_text(data['formal_sampling_started'])}")
    lines.append(f"next_action: {data['next_action']}")
    lines.append("")
    lines.append("## Bundle Handling")
    lines.append("")
    lines.append("- The original user USD was not modified or overwritten.")
    lines.append("- The selected Phase A entry is a localized repaired bundle copy.")
    lines.append("- The remote Unitree A1 reference was replaced by a local dependency copy inside the ignored bundle.")
    lines.append("")
    lines.append("## Prim Counts")
    lines.append("")
    for key, value in data["prim_type_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## A1 / Robot Candidate Prims")
    lines.append("")
    if data["robot_candidate_prims"]:
        for item in data["robot_candidate_prims"][:40]:
            matched = ",".join(item["matched_keywords"])
            lines.append(
                f"- score={item['score']} type={item['type']} articulation={bool_text(item['has_articulation_root_api'])} "
                f"keywords={matched} path={item['path']}"
            )
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Existing Camera Prims")
    lines.append("")
    for item in data["existing_camera_prims"] or ["none"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Existing Lidar Prims")
    lines.append("")
    for item in data["existing_lidar_prims"] or ["none"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Existing Sensor-Like Prims")
    lines.append("")
    for item in data["existing_sensor_prims"][:40] or ["none"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Negative Scope")
    lines.append("")
    lines.append("- training: false")
    lines.append("- RL: false")
    lines.append("- SFT: false")
    lines.append("- GDPO: false")
    lines.append("- map_predict: false")
    lines.append("- PI_finetuning: false")
    lines.append("- A1_locomotion_training: false")
    lines.append("- rollout: false")
    lines.append("- real_sensor_smoke_started: false")
    lines.append("- USD_modified_or_saved: false")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", required=True)
    parser.add_argument("--scene-id", required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--selection-reason", required=True)
    parser.add_argument("--original-user-usd", default="/home/ubuntu22/VLA/building_scene(1).usd")
    args = parser.parse_args()

    usd_path = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    summary_dir = run_dir / "summary"
    summary_dir.mkdir(parents=True, exist_ok=True)
    report_path = run_dir / "NEW_SCENE_OPEN_AND_ROBOT_INSPECTION_REPORT.md"
    summary_path = summary_dir / "open_and_robot_inspection_summary.json"

    stat = usd_path.stat() if usd_path.exists() else None
    data: dict[str, Any] = {
        "phase": "New Scene Phase A",
        "workspace": str(WORKSPACE),
        "scene_id": args.scene_id,
        "scene_path": str(usd_path),
        "original_user_usd_path": args.original_user_usd,
        "scene_selection_reason": args.selection_reason,
        "scene_exists": usd_path.exists(),
        "scene_size_bytes": stat.st_size if stat else None,
        "scene_mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)) if stat else None,
        "run_dir": str(run_dir),
        "report_path": str(report_path),
        "summary_json_path": str(summary_path),
        "stage_open_method": "pxr.Usd.Stage.Open after Isaac headless startup",
        "stage_open_elapsed_sec": None,
        "open_stage_result": False,
        "stage_available": False,
        "prim_count": 0,
        "prim_type_counts": {"Mesh": 0, "Cube": 0, "Material": 0, "Camera": 0, "Light": 0, "ArticulationRoot": 0, "PhysicsJoint": 0},
        "all_prim_type_counts": {},
        "core_dump_found": False,
        "core_dump_paths": [],
        "robot_platform": "pending_user_confirmation",
        "robot_source": "not_found",
        "a1_root_prim": None,
        "a1_base_frame_candidate": None,
        "robot_candidate_prims": [],
        "base_candidate_prims": [],
        "existing_camera_prims": [],
        "existing_lidar_prims": [],
        "existing_sensor_prims": [],
        "safe_to_real_sensor_smoke": False,
        "formal_sampling_started": False,
        "next_action": "blocked_until_scene_opens_and_a1_is_found",
        "exception": None,
        "traceback": None,
        "training": False,
        "RL": False,
        "SFT": False,
        "GDPO": False,
        "map_predict": False,
        "PI_finetuning": False,
        "A1_locomotion_training": False,
        "rollout": False,
        "USD_modified_or_saved": False,
    }

    app = None
    exit_code = 1
    try:
        if not usd_path.exists():
            raise FileNotFoundError(str(usd_path))
        from isaacsim import SimulationApp

        app = SimulationApp({"headless": True})
        from pxr import Usd, UsdPhysics

        started = time.time()
        stage = Usd.Stage.Open(str(usd_path))
        data["stage_open_elapsed_sec"] = round(time.time() - started, 3)
        data["stage_available"] = stage is not None
        data["open_stage_result"] = stage is not None
        if stage is not None:
            data.update(inspect_stage(stage, UsdPhysics))

        core_paths = find_core_dumps(WORKSPACE)
        data["core_dump_paths"] = core_paths
        data["core_dump_found"] = bool(core_paths)

        if data["open_stage_result"] and data["stage_available"] and data["prim_count"] > 0 and data["a1_root_prim"] and not data["core_dump_found"]:
            data["robot_platform"] = "unitree_a1"
            data["robot_source"] = "existing_usd_prim"
            data["safe_to_real_sensor_smoke"] = True
            data["next_action"] = "continue_to_new_scene_phaseB_real_sensor_smoke"
            exit_code = 0
        elif data["robot_candidate_prims"]:
            data["robot_platform"] = "pending_user_confirmation"
            data["robot_source"] = "candidate_robot_prim_but_not_verified_a1"
            data["next_action"] = "stop_and_wait_for_user_to_confirm_robot_platform"
            exit_code = 3
        else:
            data["next_action"] = "stop_no_a1_or_robot_prim_found"
            exit_code = 4
    except Exception as exc:
        data["exception"] = repr(exc)
        data["traceback"] = traceback.format_exc()
        data["next_action"] = "stop_scene_open_or_inspection_failed"
        exit_code = 1
    finally:
        summary_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        write_report(report_path, data)
        print(json.dumps(data, indent=2, ensure_ascii=False), flush=True)
        if app is not None:
            try:
                app.close()
            except Exception as exc:
                print(f"simulation_app.close failed: {exc!r}", file=sys.stderr)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
