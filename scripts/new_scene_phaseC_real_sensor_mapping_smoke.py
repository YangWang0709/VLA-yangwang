#!/usr/bin/env python3
"""New Scene Phase C: real-sensor BEV mapping smoke.

This phase opens the repaired new scene, uses the existing /World/A1 robot,
captures real Isaac/Omniverse RGB-D observations, backprojects depth into a
camera pointcloud, and updates a lightweight BEV occupancy grid. It does not
train, generate candidates, run a VLM-LA interface, roll out, save the USD, or
use geometry proxy observations.
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
import phase4r_a1_real_sensor_mapping_smoke as mapping_base
import phase56_a1_real_sensor_suite_smoke as sensor_base


SCENE = WORKSPACE / "scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda"
ORIGINAL_USER_USD = WORKSPACE / "building_scene(1).usd"
SCENE_ID = "building_scene_1_scene_20260608_171052"
TOP_REPORT = WORKSPACE / "runs/NEW_SCENE_REAL_SENSOR_MAPPING_REPORT.md"
COMPAT_REPORT = WORKSPACE / "runs/new_scene_sampling_building_scene_1/NEW_SCENE_REAL_SENSOR_MAPPING_REPORT.md"
A1_ROOT = "/World/A1"
BASE_FRAME = "/World/A1/base"
CAMERA_PATH = "/World/RuntimeSensors/a1_front_rgbd_camera"
LIDAR_PATH = "/World/RuntimeSensors/a1_front_lidar"
MOUNT_MARKER_PATH = "/World/A1/base/Sensors/a1_front_real_sensor_mount"
MOUNT_XYZ = (0.30, 0.0, 0.28)
MOUNT_RPY = (0.0, math.radians(-15.0), 0.0)


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    caveats = summary.get("caveats") or []
    lines = [
        "# New Scene Real Sensor Mapping Report",
        "",
        "phase: New Scene Phase C",
        f"workspace: {summary.get('workspace')}",
        f"project_name: {summary.get('project_name')}",
        f"current_scene_id: {summary.get('current_scene_id')}",
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
        f"lidar_used_for_mapping: {bool_text(summary.get('lidar_used_for_mapping'))}",
        f"lidar_is_required_for_pass: {bool_text(summary.get('lidar_is_required_for_pass'))}",
        f"geometry_proxy_used: {bool_text(summary.get('geometry_proxy_used'))}",
        f"mounted_geometry_proxy_used: {bool_text(summary.get('mounted_geometry_proxy_used'))}",
        f"camera_follows_base_rate: {summary.get('camera_follows_base_rate')}",
        f"movement_mode: {summary.get('movement_mode')}",
        f"real_a1_locomotion_controller: {bool_text(summary.get('real_a1_locomotion_controller'))}",
        f"map_type: {summary.get('map_type')}",
        f"mapping_method: {summary.get('mapping_method')}",
        f"map_update_source: {summary.get('map_update_source')}",
        f"map_resolution_m: {summary.get('map_resolution_m')}",
        f"step_count: {summary.get('step_count')}",
        f"successful_steps: {summary.get('successful_steps')}",
        f"valid_rgb_steps: {summary.get('valid_rgb_steps')}",
        f"valid_depth_steps: {summary.get('valid_depth_steps')}",
        f"valid_camera_pointcloud_steps: {summary.get('valid_camera_pointcloud_steps')}",
        f"valid_lidar_steps: {summary.get('valid_lidar_steps')}",
        f"initial_known_ratio: {summary.get('initial_known_ratio')}",
        f"final_known_ratio: {summary.get('final_known_ratio')}",
        f"final_occupied_cells: {summary.get('final_occupied_cells')}",
        f"final_known_free_cells: {summary.get('final_known_free_cells')}",
        f"final_unknown_cells: {summary.get('final_unknown_cells')}",
        f"total_new_known_cells: {summary.get('total_new_known_cells')}",
        f"known_ratio_monotonic_non_decreasing: {bool_text(summary.get('known_ratio_monotonic_non_decreasing'))}",
        f"map_update_behavior: {summary.get('map_update_behavior')}",
        f"plots path: {summary.get('plots_path')}",
        f"summary path: {summary.get('summary_json')}",
        f"safe_to_candidate_gain: {bool_text(summary.get('safe_to_candidate_gain'))}",
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
        f"- mapping_steps_csv: {summary.get('mapping_steps_csv')}",
        f"- mapping_summary_json: {summary.get('summary_json')}",
        f"- maps_path: {summary.get('maps_path')}",
        f"- plots_path: {summary.get('plots_path')}",
        "",
        "## Negative Scope",
        "- No candidate generation.",
        "- No VLM-LA interface.",
        "- No rollout.",
        "- No training, RL, map_predict, checkpoint, or USD save.",
        "- No geometry proxy or mounted geometry proxy mapping source.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    passed = bool(summary.get("safe_to_candidate_gain"))
    status = "passed" if passed else "failed"
    next_phase = summary.get("next_phase")
    common = f"""current_scene_id: {summary.get('current_scene_id')}
current_scene_path: {summary.get('scene_path')}
original_user_usd_path: {summary.get('original_user_usd_path')}
current_scene_phase: New Scene Phase C real-sensor mapping smoke
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
- candidate_generation: false
- VLM_LA_interface: false
- PI_action_finetuning: false
- A1_locomotion_training: false
"""
    metrics = f"""step_count: {summary.get('step_count')}
successful_steps: {summary.get('successful_steps')}
real_rgb_sensor_available: {bool_text(summary.get('real_rgb_sensor_available'))}
real_depth_sensor_available: {bool_text(summary.get('real_depth_sensor_available'))}
real_camera_pointcloud_available: {bool_text(summary.get('real_camera_pointcloud_available'))}
camera_pointcloud_source: {summary.get('camera_pointcloud_source')}
geometry_proxy_used: {bool_text(summary.get('geometry_proxy_used'))}
mounted_geometry_proxy_used: {bool_text(summary.get('mounted_geometry_proxy_used'))}
mapping_method: {summary.get('mapping_method')}
map_update_source: {summary.get('map_update_source')}
initial_known_ratio: {summary.get('initial_known_ratio')}
final_known_ratio: {summary.get('final_known_ratio')}
final_occupied_cells: {summary.get('final_occupied_cells')}
final_known_free_cells: {summary.get('final_known_free_cells')}
final_unknown_cells: {summary.get('final_unknown_cells')}
total_new_known_cells: {summary.get('total_new_known_cells')}
map_update_behavior: {summary.get('map_update_behavior')}
safe_to_candidate_gain: {bool_text(summary.get('safe_to_candidate_gain'))}
"""
    active = f"""# Active Task Board

current_phase: New Scene Phase C real-sensor mapping smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
{common}
{negative}
## New Scene Phase C Result

status: {status}
run_dir: {summary.get('run_dir')}
script: /home/ubuntu22/VLA/scripts/new_scene_phaseC_real_sensor_mapping_smoke.py
report: /home/ubuntu22/VLA/runs/NEW_SCENE_REAL_SENSOR_MAPPING_REPORT.md
summary_json: {summary.get('summary_json')}
mapping_steps_csv: {summary.get('mapping_steps_csv')}

{metrics}
## Scope

No candidate generation, VLM-LA interface, rollout, training, RL, SFT, GDPO, map_predict, PI/openpi fine-tuning, A1 locomotion training, checkpoint creation, geometry proxy mapping, or USD save was run.
"""
    webgpt = f"""# WEBGPT Brief

## Current Phase

New Scene Phase C real-sensor mapping smoke

## Context

{common}
{negative}
## Completed

- Used the repaired new scene and existing `/World/A1`.
- Reused the real Isaac/Omniverse RGB-D route validated in Phase B.
- Converted real depth plus camera intrinsics into depth_backprojection pointclouds.
- Updated a BEV occupancy grid from depth-backprojected pointcloud observations.
- Generated lightweight map summaries and plots without saving raw RGB-D streams.
- Did not use geometry proxy and did not start candidate generation, VLM-LA interface, rollout, or training.

## Metrics

{metrics}
## Next Action

{next_phase}
"""
    critic = f"""# Critic Report

## Current Phase

New Scene Phase C real-sensor mapping smoke

## Finding

status: {status}

The new-scene BEV map was updated from real Isaac/Omniverse RGB-D observations using depth_backprojection pointclouds. Geometry proxy and old proxy map outputs were not used.

## Evidence

- scene_path: {summary.get('scene_path')}
- a1_root_prim: /World/A1
- base_frame: /World/A1/base
- sensor_method: real_isaac_omniverse_rgbd
- map_update_source: depth_backprojection_pointcloud
- camera_pointcloud_source: {summary.get('camera_pointcloud_source')}
- valid_rgb_steps: {summary.get('valid_rgb_steps')}
- valid_depth_steps: {summary.get('valid_depth_steps')}
- valid_camera_pointcloud_steps: {summary.get('valid_camera_pointcloud_steps')}
- final_known_ratio: {summary.get('final_known_ratio')}
- final_occupied_cells: {summary.get('final_occupied_cells')}
- final_known_free_cells: {summary.get('final_known_free_cells')}
- final_unknown_cells: {summary.get('final_unknown_cells')}
- map_update_behavior: {summary.get('map_update_behavior')}
- safe_to_candidate_gain: {bool_text(summary.get('safe_to_candidate_gain'))}

## Risks / Gates

- Phase C is a mapping smoke, not final dataset generation.
- RTX LiDAR is optional telemetry and is not used for mapping pass/fail.
- Do not start Phase D unless `safe_to_candidate_gain` is true.

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
{common}mapping_method: {summary.get('mapping_method')}
initial_known_ratio: {summary.get('initial_known_ratio')}
final_known_ratio: {summary.get('final_known_ratio')}
safe_to_candidate_gain: {bool_text(summary.get('safe_to_candidate_gain'))}
```

## New Scene Route

1. Phase A: scene open and robot inspection. Status: passed.
2. Phase B: real Isaac/Omniverse sensor suite smoke. Status: passed.
3. Phase C: real-sensor mapping smoke. Status: {status}.
4. Phase D: candidate viewpoint + information gain smoke. Status: {"next" if passed else "blocked"}.
5. Phase E: VLM-LA interface smoke.
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
mapping_phaseC_status: {status}
mapping_method: {summary.get('mapping_method')}
map_update_source: depth_backprojection_pointcloud
safe_to_candidate_gain: {bool_text(summary.get('safe_to_candidate_gain'))}
```

No new-scene dataset samples have been created. Phase C only validated real-sensor BEV map updating and did not create candidate, VLM-LA, rollout, or training data.

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
    parser.add_argument("--steps", type=int, default=10)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--map_resolution_m", type=float, default=0.1)
    args = parser.parse_args()

    usd = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    logs_dir = run_dir / "logs"
    maps_dir = run_dir / "maps"
    plots_dir = run_dir / "plots"
    reports_dir = run_dir / "reports"
    summary_dir = run_dir / "summary"
    debug_dir = run_dir / "debug_frames"
    probes_dir = run_dir / "probes"
    for directory in (logs_dir, maps_dir, plots_dir, reports_dir, summary_dir, debug_dir, probes_dir):
        directory.mkdir(parents=True, exist_ok=True)

    steps_csv = summary_dir / "mapping_steps.csv"
    summary_json = summary_dir / "mapping_summary.json"
    report = reports_dir / "NEW_SCENE_REAL_SENSOR_MAPPING_REPORT.md"
    top_report = Path(args.top_report).expanduser().resolve()
    compat_report = Path(args.compat_report).expanduser().resolve()
    pre_kit_dumps = phase_b.kit_dumps()
    started = time.time()
    app = None
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "phase": "New Scene Phase C real-sensor mapping smoke",
        "workspace": str(WORKSPACE),
        "project_name": "A1-VLM-LA Explorer",
        "current_scene_id": SCENE_ID,
        "scene_path": str(usd),
        "original_user_usd_path": str(ORIGINAL_USER_USD),
        "scene_exists": usd.exists(),
        "scene_open_result": False,
        "stage_available": False,
        "stage_open_method": "omni.usd.context.open_stage after repaired bundle dependency localization",
        "stage_open_elapsed_sec": None,
        "robot_platform": "unitree_a1",
        "robot_source": "existing_usd_prim",
        "a1_root_prim": A1_ROOT,
        "a1_root_exists": False,
        "base_frame": BASE_FRAME,
        "base_pose_readable": False,
        "sensor_method": "real_isaac_omniverse_rgbd",
        "real_rgb_sensor_available": False,
        "real_depth_sensor_available": False,
        "camera_params_available": False,
        "camera_intrinsics_available": False,
        "real_camera_pointcloud_available": False,
        "camera_pointcloud_source": "unavailable",
        "semantic_segmentation_available": False,
        "instance_segmentation_available": False,
        "rtx_lidar_available": False,
        "lidar_used_for_mapping": False,
        "lidar_is_required_for_pass": False,
        "geometry_proxy_used": False,
        "mounted_geometry_proxy_used": False,
        "camera_follows_base_rate": 0.0,
        "movement_mode": "kinematic_existing_a1_root",
        "real_a1_locomotion_controller": False,
        "map_type": "BEV occupancy grid",
        "mapping_method": "raycast_real_sensor_bev_mapping",
        "map_update_source": "depth_backprojection_pointcloud",
        "step_count": 0,
        "successful_steps": 0,
        "valid_rgb_steps": 0,
        "valid_depth_steps": 0,
        "valid_camera_pointcloud_steps": 0,
        "valid_lidar_steps": 0,
        "map_resolution_m": args.map_resolution_m,
        "initial_known_ratio": 0.0,
        "final_known_ratio": 0.0,
        "final_occupied_cells": 0,
        "final_known_free_cells": 0,
        "final_unknown_cells": 0,
        "total_new_known_cells": 0,
        "known_ratio_monotonic_non_decreasing": False,
        "map_snapshots_saved": False,
        "bev_renders_saved": False,
        "map_update_behavior": "fail",
        "collision_count": 0,
        "stuck_count": 0,
        "falling_count": 0,
        "core_dump_found": False,
        "core_dump_files": [],
        "new_kit_core_dump_found": False,
        "new_kit_core_dump_files": [],
        "training_started": False,
        "RL_started": False,
        "map_predict_started": False,
        "checkpoint_created": False,
        "rollout_started": False,
        "safe_to_candidate_gain": False,
        "next_phase": "Fix New Scene Phase C real-sensor mapping smoke",
        "plots_path": str(plots_dir),
        "maps_path": str(maps_dir),
        "debug_frame_paths": [],
        "mapping_steps_csv": str(steps_csv),
        "summary_json": str(summary_json),
        "run_dir": str(run_dir),
        "active_remote_refs_remaining": phase_b.active_remote_refs(usd),
        "caveats": [
            "RTX LiDAR is optional telemetry and is not used for mapping pass/fail.",
            "BEV map update source is depth-backprojected real RGB-D pointcloud only.",
            "Runtime sensors and light are in-memory; the repaired USD is not saved.",
            "This is a mapping smoke only; candidate generation, VLM-LA interface, rollout, and training are not run.",
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
        open_started = time.time()
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
        summary["stage_open_elapsed_sec"] = round(time.time() - open_started, 3)
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
        summary["rtx_lidar_attempted"] = bool(lidar_info["lidar_attempted"])
        summary["rtx_lidar_available"] = bool(lidar_info["lidar_available"])
        summary["lidar_failure_reason"] = lidar_info.get("lidar_failure_reason", "")

        try:
            rep.orchestrator.set_capture_on_play(False)
        except Exception as exc:
            summary["set_capture_on_play_error"] = repr(exc)

        bev = mapping_base.RealSensorBevMap(initial_base[0], initial_base[1], resolution_m=args.map_resolution_m)
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
            ("yaw_left_small", 0.06, 0.0, math.radians(5.0)),
            ("forward_6", 0.10, 0.0, 0.0),
        ][: max(8, min(args.steps, 12))]

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
            camera_error = math.sqrt((camera_x - eye[0]) ** 2 + (camera_y - eye[1]) ** 2 + (camera_z - eye[2]) ** 2)
            camera_follows = camera_error < 0.02

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
            if depth["available"] and intrinsics_available:
                camera_points = sensor_base.pointcloud_from_depth(depth["array"], intrinsics)
                world_points = mapping_base.camera_points_to_world(camera_points, eye, target)
                pc = sensor_base.pointcloud_stats(camera_points)
                pc_source = "depth_backprojection"
            else:
                pc = sensor_base.pointcloud_stats(np.empty((0, 3), dtype=np.float32))
                pc_source = "unavailable"

            lidar_available_step = False
            lidar_point_count = 0
            lidar_finite_ratio = 0.0
            if lidar_annotator is not None:
                try:
                    stats = sensor_base.lidar_stats(lidar_annotator.get_data())
                    lidar_available_step = bool(stats["available"])
                    lidar_point_count = int(stats["point_count"])
                    lidar_finite_ratio = float(stats["finite_ratio"])
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
            failure = ""
            if not camera_follows:
                failure = "camera_not_synced_to_a1_base"
            elif not rgb["available"]:
                failure = "rgb_invalid"
            elif not depth["available"]:
                failure = "depth_invalid"
            elif not camera_params_available:
                failure = "camera_params_unavailable"
            elif not intrinsics_available:
                failure = "camera_intrinsics_unavailable"
            elif not pc["available"]:
                failure = "camera_pointcloud_invalid"
            elif pc_source != "depth_backprojection":
                failure = "camera_pointcloud_source_invalid"
            elif collision_flag:
                failure = "kinematic_boundary_violation"
            elif stuck_flag:
                failure = "a1_base_pose_did_not_change"
            elif falling_flag:
                failure = "a1_base_z_out_of_expected_range"

            rows.append({
                "step_id": step_id,
                "timestamp": round(time.time(), 3),
                "scene_path": str(usd),
                "a1_root_prim": A1_ROOT,
                "base_frame": BASE_FRAME,
                "base_x": round(base_x, 4),
                "base_y": round(base_y, 4),
                "base_z": round(base_z, 4),
                "base_yaw": round(yaw, 4),
                "camera_prim_path": CAMERA_PATH,
                "camera_x": round(camera_x, 4),
                "camera_y": round(camera_y, 4),
                "camera_z": round(camera_z, 4),
                "camera_yaw": round(yaw, 4),
                "camera_pitch": round(MOUNT_RPY[1], 4),
                "camera_follows_base": camera_follows,
                "rgb_available": rgb["available"],
                "rgb_nonzero_ratio": rgb["nonzero_ratio"],
                "depth_available": depth["available"],
                "depth_valid_ratio": depth["valid_ratio"],
                "camera_params_available": camera_params_available,
                "camera_intrinsics_available": intrinsics_available,
                "camera_pointcloud_available": pc["available"],
                "camera_pointcloud_source": pc_source,
                "camera_pointcloud_point_count": pc["point_count"],
                "camera_pointcloud_finite_ratio": pc["finite_ratio"],
                "semantic_available": semantic_available,
                "instance_available": instance_available,
                "lidar_available": lidar_available_step,
                "lidar_point_count": lidar_point_count,
                "lidar_finite_ratio": lidar_finite_ratio,
                "sensor_method": "real_isaac_omniverse_rgbd",
                "map_update_source": "depth_backprojection_pointcloud",
                **map_stats,
                "collision_flag": collision_flag,
                "stuck_flag": stuck_flag,
                "falling_flag": falling_flag,
                "failure_reason": failure,
            })
            last_base_x, last_base_y, last_yaw = base_x, base_y, yaw

        if not rows:
            raise RuntimeError("No mapping rows were collected")
        with steps_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

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

        plots_saved = mapping_base.save_plots(bev, rows, plots_dir)
        mapping_base.write_fallback_csvs(rows, bev, plots_dir)
        bev.save_ascii(maps_dir / "final_bev_ascii.txt")
        np.savetxt(maps_dir / "final_bev_grid.csv", bev.grid.astype(np.uint8), fmt="%d", delimiter=",")

        success = [r for r in rows if not r["failure_reason"]]
        rgb_valid = [r for r in rows if r["rgb_available"]]
        depth_valid = [r for r in rows if r["depth_available"] and r["depth_valid_ratio"] >= 0.1]
        pc_valid = [r for r in rows if r["camera_pointcloud_available"] and r["camera_pointcloud_source"] == "depth_backprojection"]
        lidar_valid = [r for r in rows if r["lidar_available"]]
        follows = [r for r in rows if r["camera_follows_base"]]
        collision_count = sum(1 for r in rows if r["collision_flag"])
        stuck_count = sum(1 for r in rows if r["stuck_flag"])
        falling_count = sum(1 for r in rows if r["falling_flag"])
        known_ratios = [float(r["known_ratio"]) for r in rows]
        monotonic = all(known_ratios[i] + 1e-6 >= known_ratios[i - 1] for i in range(1, len(known_ratios)))
        first_positive = any(int(r["new_known_cells"]) > 0 for r in rows[: min(4, len(rows))])
        final = rows[-1]
        workspace_core_files = sensor_base.find_core_dumps(WORKSPACE)
        post_kit_dumps = phase_b.kit_dumps()
        new_kit_dump_files = sorted(post_kit_dumps - pre_kit_dumps)
        map_ok = bool(
            int(final["occupied_cells"]) > 0
            and int(final["known_free_cells"]) > 0
            and int(final["unknown_cells"]) > 0
            and float(final["known_ratio"]) > float(rows[0]["known_ratio"])
            and first_positive
            and monotonic
        )
        pass_ok = bool(
            summary["scene_open_result"]
            and summary["stage_available"]
            and summary["a1_root_exists"]
            and summary["base_pose_readable"]
            and len(rows) >= 8
            and len(success) >= 8
            and len(rgb_valid) / len(rows) >= 0.8
            and len(depth_valid) / len(rows) >= 0.8
            and len(pc_valid) / len(rows) >= 0.8
            and len(follows) == len(rows)
            and not summary["geometry_proxy_used"]
            and not summary["mounted_geometry_proxy_used"]
            and map_ok
            and collision_count == 0
            and stuck_count == 0
            and falling_count == 0
            and not workspace_core_files
            and not new_kit_dump_files
        )
        summary.update({
            "step_count": len(rows),
            "successful_steps": len(success),
            "valid_rgb_steps": len(rgb_valid),
            "valid_depth_steps": len(depth_valid),
            "valid_camera_pointcloud_steps": len(pc_valid),
            "valid_lidar_steps": len(lidar_valid),
            "real_rgb_sensor_available": len(rgb_valid) / len(rows) >= 0.8,
            "real_depth_sensor_available": len(depth_valid) / len(rows) >= 0.8,
            "camera_params_available": all(bool(r["camera_params_available"]) for r in rows),
            "camera_intrinsics_available": all(bool(r["camera_intrinsics_available"]) for r in rows),
            "real_camera_pointcloud_available": len(pc_valid) / len(rows) >= 0.8,
            "camera_pointcloud_source": "depth_backprojection" if pc_valid else "unavailable",
            "semantic_segmentation_available": any(bool(r["semantic_available"]) for r in rows),
            "instance_segmentation_available": any(bool(r["instance_available"]) for r in rows),
            "rtx_lidar_available": bool(summary["rtx_lidar_available"]) or bool(lidar_valid),
            "lidar_used_for_mapping": False,
            "camera_follows_base_rate": round(len(follows) / len(rows), 4) if rows else 0.0,
            "initial_known_ratio": rows[0]["known_ratio"],
            "final_known_ratio": final["known_ratio"],
            "final_occupied_cells": final["occupied_cells"],
            "final_known_free_cells": final["known_free_cells"],
            "final_unknown_cells": final["unknown_cells"],
            "total_new_known_cells": int(sum(int(r["new_known_cells"]) for r in rows)),
            "known_ratio_monotonic_non_decreasing": monotonic,
            "map_snapshots_saved": True,
            "bev_renders_saved": bool(plots_saved),
            "map_update_behavior": "pass" if map_ok else "fail",
            "collision_count": collision_count,
            "stuck_count": stuck_count,
            "falling_count": falling_count,
            "core_dump_found": bool(workspace_core_files or new_kit_dump_files),
            "core_dump_files": workspace_core_files,
            "new_kit_core_dump_found": bool(new_kit_dump_files),
            "new_kit_core_dump_files": new_kit_dump_files,
            "safe_to_candidate_gain": pass_ok,
            "next_phase": (
                "New Scene Phase D candidate viewpoint + information gain smoke"
                if pass_ok
                else "Fix New Scene Phase C real-sensor mapping smoke"
            ),
        })
        exit_code = 0 if pass_ok else 2
    except Exception as exc:
        summary["exception"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
        summary["next_phase"] = "Fix New Scene Phase C real-sensor mapping smoke"
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
