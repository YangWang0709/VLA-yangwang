#!/usr/bin/env python3
"""New Scene Phase D: candidate viewpoint + information gain smoke.

This phase opens the repaired new scene, uses the existing /World/A1 robot,
updates a BEV partial map from real Isaac/Omniverse RGB-D depth
backprojection, generates candidate viewpoints, and scores them with a
classical information-gain heuristic. It does not train, run VLM inference,
enter the VLM-LA interface, roll out, save the USD, or use geometry proxy data.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np


WORKSPACE = Path("/home/ubuntu22/VLA")
SCRIPT_DIR = WORKSPACE / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import new_scene_phaseB_real_sensor_smoke as phase_b
import phase5r_a1_real_sensor_candidate_gain_smoke as candidate_base
import phase56_a1_real_sensor_suite_smoke as sensor_base
from phase4r_a1_real_sensor_mapping_smoke import RealSensorBevMap, camera_points_to_world


PHASE = "New Scene Phase D candidate viewpoint + information gain smoke"
SCENE = WORKSPACE / "scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda"
ORIGINAL_USER_USD = WORKSPACE / "building_scene(1).usd"
SCENE_ID = "building_scene_1_scene_20260608_171052"
TOP_REPORT = WORKSPACE / "runs/NEW_SCENE_CANDIDATE_GAIN_REPORT.md"
COMPAT_REPORT = WORKSPACE / "runs/new_scene_sampling_building_scene_1/NEW_SCENE_CANDIDATE_GAIN_REPORT.md"
A1_ROOT = "/World/A1"
BASE_FRAME = "/World/A1/base"
CAMERA_PATH = "/World/RuntimeSensors/a1_front_rgbd_camera"
LIDAR_PATH = "/World/RuntimeSensors/a1_front_lidar"
MOUNT_MARKER_PATH = "/World/A1/base/Sensors/a1_front_real_sensor_mount"
MOUNT_XYZ = (0.30, 0.0, 0.28)
MOUNT_RPY = (0.0, math.radians(-15.0), 0.0)
SENSOR_METHOD = "real_isaac_omniverse_rgbd"
CAMERA_POINTCLOUD_SOURCE = "depth_backprojection"
MAP_TYPE = "BEV occupancy grid"
MAPPING_METHOD = "raycast_real_sensor_bev_mapping"
MAP_UPDATE_SOURCE = "depth_backprojection_pointcloud"
CANDIDATE_SAMPLING_METHOD = "radial_24_candidates_3_radii_8_angles_around_a1_base"
PATH_COST_METHOD = "astar_bev_grid_unknown_penalty"
INFORMATION_GAIN_METHOD = "real_sensor_bev_unknown_visibility"
SCORE_FORMULA = "score = information_gain - 0.2 * path_cost - 1.0 * collision_penalty - 200.0 * invalid_penalty"


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def finite(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return default
    return out if math.isfinite(out) else default


def write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    caveats = summary.get("caveats") or []
    lines = [
        "# New Scene Candidate Gain Report",
        "",
        "phase: New Scene Phase D",
        f"workspace: {summary.get('workspace')}",
        f"project_name: {summary.get('project_name')}",
        f"scene_path: {summary.get('scene_path')}",
        f"robot_platform: {summary.get('robot_platform')}",
        f"robot_source: {summary.get('robot_source')}",
        f"a1_root_prim: {summary.get('a1_root_prim')}",
        f"base_frame: {summary.get('base_frame')}",
        f"sensor_method: {summary.get('sensor_method')}",
        f"real_rgb_sensor_available: {bool_text(summary.get('real_rgb_sensor_available'))}",
        f"real_depth_sensor_available: {bool_text(summary.get('real_depth_sensor_available'))}",
        f"camera_params_available: {bool_text(summary.get('camera_params_available'))}",
        f"camera_intrinsics_available: {bool_text(summary.get('camera_intrinsics_available'))}",
        f"real_camera_pointcloud_available: {bool_text(summary.get('real_camera_pointcloud_available'))}",
        f"camera_pointcloud_source: {summary.get('camera_pointcloud_source')}",
        f"semantic_segmentation_available: {bool_text(summary.get('semantic_segmentation_available'))}",
        f"instance_segmentation_available: {bool_text(summary.get('instance_segmentation_available'))}",
        f"rtx_lidar_available: {bool_text(summary.get('rtx_lidar_available'))}",
        f"lidar_used_for_candidate_gain: {bool_text(summary.get('lidar_used_for_candidate_gain'))}",
        f"lidar_is_required_for_pass: {bool_text(summary.get('lidar_is_required_for_pass'))}",
        f"geometry_proxy_used: {bool_text(summary.get('geometry_proxy_used'))}",
        f"mounted_geometry_proxy_used: {bool_text(summary.get('mounted_geometry_proxy_used'))}",
        f"map_type: {summary.get('map_type')}",
        f"mapping_method: {summary.get('mapping_method')}",
        f"map_update_source: {summary.get('map_update_source')}",
        f"candidate_sampling_method: {summary.get('candidate_sampling_method')}",
        f"path_cost_method: {summary.get('path_cost_method')}",
        f"information_gain_method: {summary.get('information_gain_method')}",
        f"score_formula: {summary.get('score_formula')}",
        f"step_count: {summary.get('step_count')}",
        f"candidate_count_per_step: {summary.get('candidate_count_per_step')}",
        f"total_candidate_rows: {summary.get('total_candidate_rows')}",
        f"valid_candidate_ratio: {summary.get('valid_candidate_ratio')}",
        f"positive_gain_candidate_ratio: {summary.get('positive_gain_candidate_ratio')}",
        f"selected_candidate_valid_rate: {summary.get('selected_candidate_valid_rate')}",
        f"selected_is_top_score_rate: {summary.get('selected_is_top_score_rate')}",
        f"path_cost_constant: {bool_text(summary.get('path_cost_constant'))}",
        f"min_path_cost: {summary.get('min_path_cost')}",
        f"max_path_cost: {summary.get('max_path_cost')}",
        f"min_information_gain: {summary.get('min_information_gain')}",
        f"max_information_gain: {summary.get('max_information_gain')}",
        f"failure_count: {summary.get('failure_count')}",
        f"BEV candidate render path: {summary.get('bev_candidate_render_path')}",
        f"candidate_summary path: {summary.get('candidate_summary_csv')}",
        f"candidate_steps path: {summary.get('candidate_steps_jsonl')}",
        f"safe_to_interface: {bool_text(summary.get('safe_to_interface'))}",
        f"core_dump_found: {bool_text(summary.get('core_dump_found'))}",
        f"new_kit_core_dump_found: {bool_text(summary.get('new_kit_core_dump_found'))}",
        f"training: {bool_text(summary.get('training_started'))}",
        f"RL: {bool_text(summary.get('RL_started'))}",
        f"map_predict: {bool_text(summary.get('map_predict_started'))}",
        "PI_finetuning: false",
        "A1_locomotion_training: false",
        f"rollout_started: {bool_text(summary.get('rollout_started'))}",
        "",
        "## Caveats",
    ]
    lines.extend([f"- {item}" for item in caveats] or ["- none"])
    lines.extend([
        "",
        "## Artifacts",
        f"- run_dir: {summary.get('run_dir')}",
        f"- candidate_summary_csv: {summary.get('candidate_summary_csv')}",
        f"- candidate_steps_jsonl: {summary.get('candidate_steps_jsonl')}",
        f"- candidate_summary_json: {summary.get('summary_json')}",
        "",
        "## Negative Scope",
        "- No VLM-LA interface.",
        "- No rollout.",
        "- No training, RL, map_predict, checkpoint, or USD save.",
        "- No geometry proxy or mounted geometry proxy candidate gain source.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    passed = bool(summary.get("safe_to_interface"))
    status = "passed" if passed else "failed"
    next_phase = summary.get("next_phase")
    common = f"""current_scene_id: {summary.get('current_scene_id')}
current_scene_path: {summary.get('scene_path')}
original_user_usd_path: {summary.get('original_user_usd_path')}
current_scene_phase: New Scene Phase D candidate viewpoint + information gain smoke
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
map_update_source: depth_backprojection_pointcloud
output_contract: Go to candidate <id>.
training_ready: false
requires_human_review: true
next_phase: {next_phase}
"""
    negative = """negative_scope:
- training: false
- RL: false
- SFT: false
- GDPO: false
- map_predict: false
- rollout: false
- VLM_LA_interface: false
- PI_action_finetuning: false
- A1_locomotion_training: false
"""
    metrics = f"""step_count: {summary.get('step_count')}
candidate_count_per_step: {summary.get('candidate_count_per_step')}
total_candidate_rows: {summary.get('total_candidate_rows')}
valid_candidate_ratio: {summary.get('valid_candidate_ratio')}
positive_gain_candidate_ratio: {summary.get('positive_gain_candidate_ratio')}
selected_candidate_valid_rate: {summary.get('selected_candidate_valid_rate')}
selected_is_top_score_rate: {summary.get('selected_is_top_score_rate')}
path_cost_constant: {bool_text(summary.get('path_cost_constant'))}
min_path_cost: {summary.get('min_path_cost')}
max_path_cost: {summary.get('max_path_cost')}
min_information_gain: {summary.get('min_information_gain')}
max_information_gain: {summary.get('max_information_gain')}
failure_count: {summary.get('failure_count')}
safe_to_interface: {bool_text(summary.get('safe_to_interface'))}
"""
    active = f"""# Active Task Board

current_phase: New Scene Phase D candidate viewpoint + information gain smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
{common}
{negative}
## New Scene Phase D Result

status: {status}
run_dir: {summary.get('run_dir')}
script: /home/ubuntu22/VLA/scripts/new_scene_phaseD_candidate_gain_smoke.py
report: /home/ubuntu22/VLA/runs/NEW_SCENE_CANDIDATE_GAIN_REPORT.md
summary_json: {summary.get('summary_json')}
candidate_summary_csv: {summary.get('candidate_summary_csv')}
candidate_steps_jsonl: {summary.get('candidate_steps_jsonl')}

{metrics}
## Scope

No VLM-LA interface, rollout, training, RL, SFT, GDPO, map_predict, PI/openpi fine-tuning, A1 locomotion training, checkpoint creation, geometry proxy, or USD save was run.
"""
    webgpt = f"""# WEBGPT Brief

## Current Phase

New Scene Phase D candidate viewpoint + information gain smoke

## Context

{common}
{negative}
## Completed

- Used the repaired new scene and existing `/World/A1`.
- Reused the real Isaac/Omniverse RGB-D route and Phase C BEV mapping logic.
- Generated radial candidate viewpoints at each decision step.
- Scored candidates with A* BEV path cost, real-sensor BEV unknown visibility, and a classical score formula.
- Wrote candidate tables, per-step JSONL, and BEV candidate overlays.
- Did not run VLM inference, VLM-LA interface, rollout, or training.

## Metrics

{metrics}
## Next Action

{next_phase}
"""
    critic = f"""# Critic Report

## Current Phase

New Scene Phase D candidate viewpoint + information gain smoke

## Finding

status: {status}

Candidate viewpoint generation and classical information gain scoring used the new-scene real RGB-D/depth_backprojection BEV map. No Go2 label, old scene data, proxy map, or geometry proxy was used.

## Evidence

- scene_path: {summary.get('scene_path')}
- a1_root_prim: /World/A1
- sensor_method: real_isaac_omniverse_rgbd
- map_update_source: depth_backprojection_pointcloud
- candidate_sampling_method: {summary.get('candidate_sampling_method')}
- path_cost_method: {summary.get('path_cost_method')}
- information_gain_method: {summary.get('information_gain_method')}
- candidate_count_per_step: {summary.get('candidate_count_per_step')}
- valid_candidate_ratio: {summary.get('valid_candidate_ratio')}
- positive_gain_candidate_ratio: {summary.get('positive_gain_candidate_ratio')}
- selected_is_top_score_rate: {summary.get('selected_is_top_score_rate')}
- safe_to_interface: {bool_text(summary.get('safe_to_interface'))}

## Risks / Gates

- This is classical candidate-gain smoke, not VLM inference.
- Phase E may consume the candidate id contract but should not train or roll out.
- Do not start Phase E unless `safe_to_interface` is true.

training: false
RL: false
SFT: false
GDPO: false
rollout: false
USD_modified_or_saved: false
"""
    plan = f"""# VLM-LA Explorer Plan

## Method Name

A1-VLM-LA Explorer

Full route name:

A1-VLM-LA Explorer for 3D Active Exploration

## Output Contract

`Go to candidate <id>.`

## Current New Scene

```yaml
{common}candidate_sampling_method: {summary.get('candidate_sampling_method')}
path_cost_method: {summary.get('path_cost_method')}
information_gain_method: {summary.get('information_gain_method')}
safe_to_interface: {bool_text(summary.get('safe_to_interface'))}
```

## New Scene Route

1. Phase A: scene open and robot inspection. Status: passed.
2. Phase B: real Isaac/Omniverse sensor suite smoke. Status: passed.
3. Phase C: real-sensor mapping smoke. Status: passed.
4. Phase D: candidate viewpoint + information gain smoke. Status: {status}.
5. Phase E: VLM-LA interface smoke. Status: {"next" if passed else "blocked"}.
6. Phase F: short closed-loop smoke.
7. Phase G: long rollout data collection.
8. Phase H: dataset quality audit and human review packet.

## Negative Scope

training: false
RL: false
SFT: false
GDPO: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout: false
"""
    dataset = f"""# VLM-LA Dataset Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Current New Scene Dataset Status

```yaml
{common}sensor_phaseB_status: passed
mapping_phaseC_status: passed
candidate_phaseD_status: {status}
candidate_sampling_method: {summary.get('candidate_sampling_method')}
safe_to_interface: {bool_text(summary.get('safe_to_interface'))}
```

No new-scene dataset samples have been created. Phase D only validated classical candidate gain tables and did not create VLM-LA interface samples, rollout samples, or training data.

## Required New Scene Sample Metadata

Future Phase G samples, only after Phase B-F pass, must include:

- real RGB/depth metadata
- depth_backprojection pointcloud stats
- BEV map/candidate render reference
- candidate table reference
- selected_candidate_id
- target_language: `Go to candidate <id>.`
- parser and validator result
- target pose
- movement result
- map stats
- failure reason if any

## Training Gate

training_ready: false
requires_human_review: true

Do not use new-scene data for SFT, GDPO, RL, or any training until a later explicit human review approves preparation.
"""
    for path, text in {
        WORKSPACE / "runs/ACTIVE_TASK_BOARD.md": active,
        WORKSPACE / "runs/WEBGPT_BRIEF.md": webgpt,
        WORKSPACE / "runs/CRITIC_REPORT.md": critic,
        WORKSPACE / "runs/VLM_LA_EXPLORER_PLAN.md": plan,
        WORKSPACE / "runs/VLM_LA_DATASET_SPEC.md": dataset,
    }.items():
        path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", default=str(SCENE))
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--top_report", default=str(TOP_REPORT))
    parser.add_argument("--compat_report", default=str(COMPAT_REPORT))
    parser.add_argument("--steps", type=int, default=6)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--map_resolution_m", type=float, default=0.1)
    args = parser.parse_args()

    usd = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    logs_dir = run_dir / "logs"
    candidates_dir = run_dir / "candidates"
    bev_renders_dir = run_dir / "bev_renders"
    plots_dir = run_dir / "plots"
    reports_dir = run_dir / "reports"
    summary_dir = run_dir / "summary"
    debug_dir = run_dir / "debug_frames"
    for directory in (logs_dir, candidates_dir, bev_renders_dir, plots_dir, reports_dir, summary_dir, debug_dir):
        directory.mkdir(parents=True, exist_ok=True)

    candidate_csv = summary_dir / "candidate_summary.csv"
    candidate_steps_jsonl = summary_dir / "candidate_steps.jsonl"
    summary_json = summary_dir / "candidate_summary.json"
    report = reports_dir / "NEW_SCENE_CANDIDATE_GAIN_REPORT.md"
    top_report = Path(args.top_report).expanduser().resolve()
    compat_report = Path(args.compat_report).expanduser().resolve()
    pre_kit_dumps = phase_b.kit_dumps()
    started = time.time()
    app = None
    rows: list[dict[str, Any]] = []
    step_rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "phase": PHASE,
        "workspace": str(WORKSPACE),
        "project_name": "A1-VLM-LA Explorer",
        "current_scene_id": SCENE_ID,
        "scene_path": str(usd),
        "original_user_usd_path": str(ORIGINAL_USER_USD),
        "scene_exists": usd.exists(),
        "scene_open_result": False,
        "stage_available": False,
        "robot_platform": "unitree_a1",
        "robot_source": "existing_usd_prim",
        "a1_root_prim": A1_ROOT,
        "a1_root_exists": False,
        "base_frame": BASE_FRAME,
        "base_pose_readable": False,
        "sensor_method": SENSOR_METHOD,
        "real_rgb_sensor_available": False,
        "real_depth_sensor_available": False,
        "camera_params_available": False,
        "camera_intrinsics_available": False,
        "real_camera_pointcloud_available": False,
        "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE,
        "semantic_segmentation_available": False,
        "instance_segmentation_available": False,
        "rtx_lidar_available": False,
        "lidar_used_for_candidate_gain": False,
        "lidar_is_required_for_pass": False,
        "geometry_proxy_used": False,
        "mounted_geometry_proxy_used": False,
        "map_type": MAP_TYPE,
        "mapping_method": MAPPING_METHOD,
        "map_update_source": MAP_UPDATE_SOURCE,
        "candidate_sampling_method": CANDIDATE_SAMPLING_METHOD,
        "path_cost_method": PATH_COST_METHOD,
        "information_gain_method": INFORMATION_GAIN_METHOD,
        "score_formula": SCORE_FORMULA,
        "step_count": 0,
        "candidate_count_per_step": 0,
        "total_candidate_rows": 0,
        "valid_candidate_ratio": 0.0,
        "positive_gain_candidate_ratio": 0.0,
        "selected_candidate_valid_rate": 0.0,
        "selected_is_top_score_rate": 0.0,
        "path_cost_constant": True,
        "min_path_cost": None,
        "max_path_cost": None,
        "min_information_gain": None,
        "max_information_gain": None,
        "failure_count": 0,
        "safe_to_interface": False,
        "next_phase": "Fix New Scene Phase D candidate gain smoke",
        "training_started": False,
        "RL_started": False,
        "map_predict_started": False,
        "checkpoint_created": False,
        "rollout_started": False,
        "core_dump_found": False,
        "core_dump_files": [],
        "new_kit_core_dump_found": False,
        "new_kit_core_dump_files": [],
        "bev_candidate_render_path": str(bev_renders_dir),
        "bev_renders_dir": str(bev_renders_dir),
        "candidate_summary_csv": str(candidate_csv),
        "candidate_steps_jsonl": str(candidate_steps_jsonl),
        "summary_json": str(summary_json),
        "run_dir": str(run_dir),
        "caveats": [
            "Candidate gain is classical scoring, not VLM inference or VLM-LA interface.",
            "BEV map and candidate gains use depth-backprojected real RGB-D pointclouds from the new scene.",
            "RTX LiDAR and segmentation are optional telemetry and are not required for pass/fail.",
            "Runtime sensors and light are in-memory; the repaired USD is not saved.",
        ],
        "exception": None,
        "traceback": None,
        "elapsed_sec": None,
    }
    exit_code = 1

    try:
        if not usd.exists():
            raise FileNotFoundError(str(usd))
        sensor_base.CAMERA_PATH = CAMERA_PATH
        sensor_base.LIDAR_PATH = LIDAR_PATH
        sensor_base.MOUNT_MARKER_PATH = MOUNT_MARKER_PATH
        sensor_base.MOUNT_XYZ = MOUNT_XYZ
        sensor_base.MOUNT_RPY = MOUNT_RPY

        from isaacsim import SimulationApp

        app = SimulationApp({"headless": True})
        import omni.replicator.core as rep
        import omni.usd
        from pxr import UsdGeom, UsdPhysics

        context = omni.usd.get_context()
        summary["open_stage_raw_result"] = repr(context.open_stage(str(usd)))
        stage = None
        deadline = time.time() + 120.0
        while time.time() < deadline:
            app.update()
            stage = context.get_stage()
            if stage is not None and stage.GetPrimAtPath(A1_ROOT).IsValid() and stage.GetPrimAtPath(BASE_FRAME).IsValid():
                break
            time.sleep(0.1)
        if stage is None:
            stage = context.get_stage()
        if stage is None:
            raise RuntimeError("Stage unavailable after open_stage")
        summary["scene_open_result"] = True
        summary["stage_available"] = True

        root = stage.GetPrimAtPath(A1_ROOT)
        base = stage.GetPrimAtPath(BASE_FRAME)
        if not root or not root.IsValid():
            raise RuntimeError("Existing USD A1 prim /World/A1 was not found")
        if not base or not base.IsValid():
            raise RuntimeError("Existing USD base frame /World/A1/base was not found")
        summary["a1_root_exists"] = True
        summary["a1_has_articulation_root_api"] = bool(root.HasAPI(UsdPhysics.ArticulationRootAPI))

        sensor_base.create_runtime_prims(stage, args.width, args.height)
        camera_prim = stage.GetPrimAtPath(CAMERA_PATH)
        light_prim = stage.GetPrimAtPath(sensor_base.LIGHT_PATH)
        if not camera_prim or not camera_prim.IsValid():
            raise RuntimeError("Runtime RGB-D camera prim was not created")

        cache = UsdGeom.XformCache()
        initial_root = sensor_base.world_translation(cache, root)
        initial_base = sensor_base.world_translation(cache, base)
        summary["initial_root_pose_xyz"] = [round(v, 6) for v in initial_root]
        summary["initial_base_pose_xyz"] = [round(v, 6) for v in initial_base]
        summary["base_pose_readable"] = True
        ops = {op.GetName(): op for op in UsdGeom.Xformable(root).GetOrderedXformOps()}
        initial_orient = ops["xformOp:orient"].Get() if "xformOp:orient" in ops else None

        eye, target = sensor_base.expected_sensor_pose(initial_base[0], initial_base[1], initial_base[2], 0.0)
        sensor_base.set_world_look_at(camera_prim, eye, target)
        if light_prim and light_prim.IsValid():
            sensor_base.set_world_translate(light_prim, (initial_base[0], initial_base[1], initial_base[2] + 2.5))

        render_product = rep.create.render_product(CAMERA_PATH, (int(args.width), int(args.height)))
        camera_annotators, annotator_errors = sensor_base.attach_camera_annotators(rep, render_product)
        summary["camera_annotator_errors"] = annotator_errors
        required = {"rgb", "distance_to_image_plane", "camera_params"}
        if not required.issubset(camera_annotators):
            raise RuntimeError(f"Required RGB-D camera annotators unavailable: {annotator_errors}")

        lidar_info = sensor_base.try_create_lidar(stage, rep, eye, target)
        lidar_annotator = lidar_info.pop("lidar_annotator", None)
        summary["rtx_lidar_available"] = bool(lidar_info["lidar_available"])
        summary["lidar_failure_reason"] = lidar_info.get("lidar_failure_reason", "")

        try:
            rep.orchestrator.set_capture_on_play(False)
        except Exception as exc:
            summary["set_capture_on_play_error"] = repr(exc)

        bev = RealSensorBevMap(initial_base[0], initial_base[1], resolution_m=args.map_resolution_m)
        initial_stats = bev.stats()
        root_x, root_y, root_z = initial_root
        yaw = 0.0
        last_base_x, last_base_y, last_yaw = initial_base[0], initial_base[1], 0.0
        first_rgb: np.ndarray | None = None
        last_rgb: np.ndarray | None = None
        first_depth: np.ndarray | None = None
        last_depth: np.ndarray | None = None

        actions = [
            ("initial_pose", 0.0, 0.0, 0.0),
            ("forward_1", 0.14, 0.0, 0.0),
            ("yaw_left", 0.08, 0.0, math.radians(8.0)),
            ("forward_2", 0.14, 0.0, 0.0),
            ("lateral_left", 0.04, 0.08, 0.0),
            ("forward_3", 0.12, 0.0, 0.0),
            ("yaw_right", 0.08, 0.0, math.radians(-7.0)),
            ("forward_4", 0.12, 0.0, 0.0),
            ("lateral_right", 0.04, -0.08, 0.0),
            ("forward_5", 0.10, 0.0, 0.0),
        ][: max(5, min(args.steps, 10))]

        for step_id, (_action, forward, lateral, dyaw) in enumerate(actions):
            yaw += dyaw
            root_x += math.cos(yaw) * forward - math.sin(yaw) * lateral
            root_y += math.sin(yaw) * forward + math.cos(yaw) * lateral
            sensor_base.set_root_pose(root, (root_x, root_y, root_z), yaw, initial_orient)
            for _ in range(2):
                app.update()

            cache = UsdGeom.XformCache()
            base_x, base_y, base_z = sensor_base.world_translation(cache, base)
            eye, target = sensor_base.expected_sensor_pose(base_x, base_y, base_z, yaw)
            sensor_base.set_world_look_at(camera_prim, eye, target)
            if light_prim and light_prim.IsValid():
                sensor_base.set_world_translate(light_prim, (base_x, base_y, base_z + 2.5))
            lidar_prim = stage.GetPrimAtPath(LIDAR_PATH)
            if lidar_prim and lidar_prim.IsValid():
                sensor_base.set_world_look_at(lidar_prim, eye, target)

            for _ in range(3):
                app.update()
                try:
                    rep.orchestrator.step()
                except Exception as exc:
                    summary.setdefault("orchestrator_step_errors", []).append(repr(exc))
                app.update()

            cache = UsdGeom.XformCache()
            camera_x, camera_y, camera_z = sensor_base.world_translation(cache, camera_prim)
            rgb = sensor_base.rgb_stats(camera_annotators["rgb"].get_data())
            depth = sensor_base.depth_stats(camera_annotators["distance_to_image_plane"].get_data())
            camera_params_data = camera_annotators["camera_params"].get_data()
            camera_params_available = isinstance(camera_params_data, dict) and bool(camera_params_data)
            intrinsics_available, intrinsics = sensor_base.intrinsics_from_camera_params(
                camera_params_data,
                depth["width"] or int(args.width),
                depth["height"] or int(args.height),
            )
            world_points = np.empty((0, 3), dtype=np.float32)
            pc_stats = sensor_base.pointcloud_stats(np.empty((0, 3), dtype=np.float32))
            if depth["available"] and intrinsics_available:
                camera_points = sensor_base.pointcloud_from_depth(depth["array"], intrinsics)
                world_points = camera_points_to_world(camera_points, eye, target)
                pc_stats = sensor_base.pointcloud_stats(camera_points)

            lidar_available_step = False
            lidar_point_count = 0
            if lidar_annotator is not None:
                try:
                    stats = sensor_base.lidar_stats(lidar_annotator.get_data())
                    lidar_available_step = bool(stats["available"])
                    lidar_point_count = int(stats["point_count"])
                except Exception as exc:
                    summary.setdefault("lidar_read_errors", []).append(repr(exc))

            semantic_available = False
            instance_available = False
            if "semantic_segmentation" in camera_annotators:
                try:
                    semantic_available = sensor_base.segmentation_available(camera_annotators["semantic_segmentation"].get_data())
                except Exception as exc:
                    summary.setdefault("semantic_errors", []).append(repr(exc))
            if "instance_segmentation" in camera_annotators:
                try:
                    instance_available = sensor_base.segmentation_available(camera_annotators["instance_segmentation"].get_data())
                except Exception as exc:
                    summary.setdefault("instance_errors", []).append(repr(exc))

            map_stats = bev.update(base_x, base_y, yaw, camera_x, camera_y, camera_z, world_points)
            base_pose = {"x": base_x, "y": base_y, "z": base_z, "yaw": yaw}
            scored = candidate_base.score_candidates(bev, base_pose)
            selected = [row for row in scored if row["selected_by_classical"]]
            selected_id = int(selected[0]["candidate_id"]) if selected else None
            sensor_failure = ""
            if not rgb["available"]:
                sensor_failure = "rgb_invalid"
            elif not depth["available"]:
                sensor_failure = "depth_invalid"
            elif not camera_params_available:
                sensor_failure = "camera_params_unavailable"
            elif not intrinsics_available:
                sensor_failure = "camera_intrinsics_unavailable"
            elif not pc_stats["available"]:
                sensor_failure = "camera_pointcloud_invalid"
            elif selected_id is None:
                sensor_failure = "no_valid_positive_gain_candidate"

            for row in scored:
                row["step_id"] = step_id
                rows.append(row)
            candidate_base.write_step_candidate_csv(candidates_dir / f"candidate_step_{step_id:03d}.csv", scored)

            render_rel = f"bev_renders/candidate_overlay_step_{step_id:03d}.png"
            render_path = run_dir / render_rel
            if not candidate_base.render_candidate_overlay(bev, step_id, base_pose, (camera_x, camera_y, camera_z), scored, render_path):
                render_rel = f"bev_renders/candidate_overlay_step_{step_id:03d}.txt"
                render_path = run_dir / render_rel
                candidate_base.write_overlay_ascii(render_path, bev, scored, selected_id)

            if step_id == 0:
                first_rgb = rgb["array"]
                first_depth = depth["array"]
            last_rgb = rgb["array"]
            last_depth = depth["array"]

            moved = math.hypot(base_x - last_base_x, base_y - last_base_y)
            yaw_change = abs(yaw - last_yaw)
            collision_flag = abs(base_x - initial_base[0]) > 2.0 or abs(base_y - initial_base[1]) > 2.0
            stuck_flag = step_id > 0 and moved < 0.005 and yaw_change < 0.005
            falling_flag = base_z < 0.2 or base_z > 1.5 or abs(base_z - initial_base[2]) > 0.6
            if collision_flag:
                sensor_failure = sensor_failure or "kinematic_boundary_violation"
            elif stuck_flag:
                sensor_failure = sensor_failure or "a1_base_pose_did_not_change"
            elif falling_flag:
                sensor_failure = sensor_failure or "a1_base_z_out_of_expected_range"

            valid_count = sum(1 for r in scored if r["is_valid"] and r["is_reachable"])
            positive_gain_count = sum(1 for r in scored if int(r["information_gain"]) > 0)
            step_rows.append({
                "phase": PHASE,
                "step_id": step_id,
                "timestamp": round(time.time(), 3),
                "scene_path": str(usd),
                "a1_root_prim": A1_ROOT,
                "base_frame": BASE_FRAME,
                "sensor_method": SENSOR_METHOD,
                "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE,
                "geometry_proxy_used": False,
                "mounted_geometry_proxy_used": False,
                "base_pose": {"x": round(base_x, 4), "y": round(base_y, 4), "z": round(base_z, 4), "yaw": round(yaw, 4)},
                "map_stats": {
                    "known_ratio": map_stats["known_ratio"],
                    "occupied_cells": map_stats["occupied_cells"],
                    "known_free_cells": map_stats["known_free_cells"],
                    "unknown_cells": map_stats["unknown_cells"],
                },
                "candidate_count": len(scored),
                "valid_candidate_count": valid_count,
                "positive_gain_candidate_count": positive_gain_count,
                "selected_candidate_id": selected_id,
                "selected_score": selected[0]["score"] if selected else None,
                "failure_reason": sensor_failure or None,
                "bev_candidate_render": render_rel,
                "rgb_available": rgb["available"],
                "depth_available": depth["available"],
                "camera_params_available": camera_params_available,
                "camera_intrinsics_available": intrinsics_available,
                "camera_pointcloud_available": pc_stats["available"],
                "semantic_available": semantic_available,
                "instance_available": instance_available,
                "lidar_available": lidar_available_step,
                "lidar_point_count": lidar_point_count,
                "collision_flag": collision_flag,
                "stuck_flag": stuck_flag,
                "falling_flag": falling_flag,
            })
            last_base_x, last_base_y, last_yaw = base_x, base_y, yaw

        with candidate_csv.open("w", newline="", encoding="utf-8") as f:
            fieldnames = [
                "step_id", "candidate_id", "base_x", "base_y", "base_z", "base_yaw",
                "x", "y", "z", "yaw", "dx", "dy", "dyaw", "distance_to_robot",
                "is_valid", "is_reachable", "collision_risk", "collision_penalty",
                "path_cost", "path_cost_method", "visible_unknown_cells", "information_gain",
                "information_gain_method", "score", "selected_by_classical", "failure_reason",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        with candidate_steps_jsonl.open("w", encoding="utf-8") as f:
            for step_row in step_rows:
                f.write(json.dumps(step_row, ensure_ascii=False) + "\n")

        debug_paths = []
        for name, array, saver in [
            ("first_rgb.png", first_rgb, sensor_base.save_rgb_png),
            ("last_rgb.png", last_rgb, sensor_base.save_rgb_png),
            ("first_depth_vis.png", first_depth, sensor_base.save_depth_vis),
            ("last_depth_vis.png", last_depth, sensor_base.save_depth_vis),
        ]:
            out = debug_dir / name
            if saver(array, out):
                debug_paths.append(str(out))
        summary["debug_frame_paths"] = debug_paths

        workspace_core_files = sensor_base.find_core_dumps(WORKSPACE)
        new_kit_dump_files = sorted(phase_b.kit_dumps() - pre_kit_dumps)
        selected_rows = [r for r in rows if r["selected_by_classical"]]
        valid_rows = [r for r in rows if r["is_valid"] and r["is_reachable"]]
        positive_rows = [r for r in rows if int(r["information_gain"]) > 0]
        path_costs = [finite(r["path_cost"], float("nan")) for r in rows if r["path_cost"] is not None]
        path_costs = [v for v in path_costs if math.isfinite(v)]
        gains = [int(r["information_gain"]) for r in rows]
        candidate_counts = [int(r["candidate_count"]) for r in step_rows]
        valid_step_counts = [int(r["valid_candidate_count"]) for r in step_rows]
        positive_step_counts = [int(r["positive_gain_candidate_count"]) for r in step_rows]
        selected_valid = [
            r for r in selected_rows
            if r["is_valid"] and r["is_reachable"] and int(r["information_gain"]) > 0
        ]
        top_score_matches = 0
        selected_steps = 0
        for step_id in sorted({int(r["step_id"]) for r in rows}):
            step_candidates = [r for r in rows if int(r["step_id"]) == step_id]
            selectable = [r for r in step_candidates if r["is_valid"] and r["is_reachable"] and int(r["information_gain"]) > 0]
            selected = [r for r in step_candidates if r["selected_by_classical"]]
            if not selected:
                continue
            selected_steps += 1
            best = max(selectable, key=lambda r: (float(r["score"]), int(r["information_gain"]), -int(r["candidate_id"]))) if selectable else None
            if best is not None and int(best["candidate_id"]) == int(selected[0]["candidate_id"]):
                top_score_matches += 1

        successful_steps = [
            r for r in step_rows
            if not r["failure_reason"]
            and int(r["candidate_count"]) >= 16
            and int(r["valid_candidate_count"]) > 0
        ]
        rgb_valid = [r for r in step_rows if r["rgb_available"]]
        depth_valid = [r for r in step_rows if r["depth_available"]]
        pc_valid = [r for r in step_rows if r["camera_pointcloud_available"]]
        path_cost_constant = len(path_costs) > 1 and (max(path_costs) - min(path_costs)) < 1e-6
        failure_count = len(step_rows) - len(successful_steps)
        pass_ok = bool(
            summary["scene_open_result"]
            and summary["stage_available"]
            and summary["a1_root_exists"]
            and summary["base_pose_readable"]
            and len(step_rows) >= 5
            and len(successful_steps) >= 5
            and min(candidate_counts or [0]) >= 16
            and min(valid_step_counts or [0]) > 0
            and any(count > 0 for count in positive_step_counts)
            and len(rgb_valid) / len(step_rows) >= 0.8
            and len(depth_valid) / len(step_rows) >= 0.8
            and len(pc_valid) / len(step_rows) >= 0.8
            and selected_steps > 0
            and top_score_matches == selected_steps
            and path_costs
            and not path_cost_constant
            and gains
            and max(gains) > min(gains)
            and max(gains) > 0
            and len(selected_valid) == len(selected_rows)
            and not workspace_core_files
            and not new_kit_dump_files
            and summary["geometry_proxy_used"] is False
            and summary["mounted_geometry_proxy_used"] is False
        )

        final_stats = bev.stats()
        summary.update({
            "step_count": len(step_rows),
            "successful_steps": len(successful_steps),
            "candidate_count_per_step": candidate_counts[0] if candidate_counts and len(set(candidate_counts)) == 1 else candidate_counts,
            "total_candidate_rows": len(rows),
            "valid_candidate_ratio": round(len(valid_rows) / len(rows), 4) if rows else 0.0,
            "positive_gain_candidate_ratio": round(len(positive_rows) / len(rows), 4) if rows else 0.0,
            "selected_candidate_valid_rate": round(len(selected_valid) / len(selected_rows), 4) if selected_rows else 0.0,
            "selected_is_top_score_rate": round(top_score_matches / selected_steps, 4) if selected_steps else 0.0,
            "path_cost_constant": bool(path_cost_constant),
            "min_path_cost": round(min(path_costs), 4) if path_costs else None,
            "max_path_cost": round(max(path_costs), 4) if path_costs else None,
            "min_information_gain": min(gains) if gains else None,
            "max_information_gain": max(gains) if gains else None,
            "failure_count": failure_count,
            "real_rgb_sensor_available": len(rgb_valid) / len(step_rows) >= 0.8 if step_rows else False,
            "real_depth_sensor_available": len(depth_valid) / len(step_rows) >= 0.8 if step_rows else False,
            "camera_params_available": all(bool(r["camera_params_available"]) for r in step_rows),
            "camera_intrinsics_available": all(bool(r["camera_intrinsics_available"]) for r in step_rows),
            "real_camera_pointcloud_available": len(pc_valid) / len(step_rows) >= 0.8 if step_rows else False,
            "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE if pc_valid else "unavailable",
            "semantic_segmentation_available": any(bool(r["semantic_available"]) for r in step_rows),
            "instance_segmentation_available": any(bool(r["instance_available"]) for r in step_rows),
            "rtx_lidar_available": bool(summary["rtx_lidar_available"]) or any(bool(r["lidar_available"]) for r in step_rows),
            "lidar_used_for_candidate_gain": False,
            "map_resolution_m": float(args.map_resolution_m),
            "initial_known_ratio": initial_stats.get("known_ratio"),
            "final_known_ratio": final_stats.get("known_ratio"),
            "final_occupied_cells": final_stats.get("occupied_cells"),
            "final_known_free_cells": final_stats.get("known_free_cells"),
            "final_unknown_cells": final_stats.get("unknown_cells"),
            "map_update_behavior": "pass" if final_stats.get("known_ratio", 0.0) > initial_stats.get("known_ratio", -1.0) else "flat",
            "core_dump_found": bool(workspace_core_files or new_kit_dump_files),
            "core_dump_files": workspace_core_files,
            "new_kit_core_dump_found": bool(new_kit_dump_files),
            "new_kit_core_dump_files": new_kit_dump_files,
            "safe_to_interface": pass_ok,
            "next_phase": "New Scene Phase E VLM-LA interface smoke" if pass_ok else "Fix New Scene Phase D candidate gain smoke",
        })
        exit_code = 0 if pass_ok else 2
    except Exception as exc:
        summary["exception"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
        summary["next_phase"] = "Fix New Scene Phase D candidate gain smoke"
        exit_code = 1
    finally:
        summary["elapsed_sec"] = round(time.time() - started, 3)
        summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        write_report(report, summary)
        write_report(top_report, summary)
        write_report(compat_report, summary)
        write_status_files(summary)
        if app is not None:
            try:
                app.close()
            except Exception as exc:
                print(f"simulation_app.close failed: {exc!r}", file=sys.stderr)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
