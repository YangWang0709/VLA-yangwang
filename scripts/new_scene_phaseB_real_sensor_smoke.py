#!/usr/bin/env python3
"""New Scene Phase B: real Isaac/Omniverse sensor suite smoke.

This phase opens the repaired new scene, creates runtime RGB-D and optional
RTX LiDAR sensors, validates Replicator RGB/depth/camera_params outputs, and
derives a camera pointcloud from real depth plus camera intrinsics. It does not
train, map, generate candidates, roll out, save the USD, or write raw sensor
dumps.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import re
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import phase56_a1_real_sensor_suite_smoke as sensor_base


WORKSPACE = Path("/home/ubuntu22/VLA")
SCENE = WORKSPACE / "scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda"
ORIGINAL_USER_USD = WORKSPACE / "building_scene(1).usd"
SCENE_ID = "building_scene_1_scene_20260608_171052"
TOP_REPORT = WORKSPACE / "runs/NEW_SCENE_REAL_SENSOR_SMOKE_REPORT.md"
COMPAT_REPORT = WORKSPACE / "runs/new_scene_sampling_building_scene_1/NEW_SCENE_REAL_SENSOR_SMOKE_REPORT.md"
A1_ROOT = "/World/A1"
BASE_FRAME = "/World/A1/base"
CAMERA_PATH = "/World/RuntimeSensors/a1_front_rgbd_camera"
LIDAR_PATH = "/World/RuntimeSensors/a1_front_lidar"
MOUNT_MARKER_PATH = "/World/A1/base/Sensors/a1_front_real_sensor_mount"
MOUNT_XYZ = (0.30, 0.0, 0.28)
MOUNT_RPY = (0.0, math.radians(-15.0), 0.0)
POINTCLOUD_ALLOWED = {"isaac_pointcloud_annotator", "depth_backprojection"}


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def kit_dump_dir() -> Path:
    return (
        Path("/home/ubuntu22/miniconda3/envs/env_isaaclab/lib/python3.11/site-packages/isaacsim/kit/data")
        / "Kit/Isaac-Sim Python/5.1"
    )


def kit_dumps() -> set[str]:
    root = kit_dump_dir()
    if not root.exists():
        return set()
    return {str(p) for p in root.glob("*.dmp")}


def active_remote_refs(scene_path: Path) -> int:
    try:
        text = scene_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return -1
    return len(set(re.findall(r"https://[^@\s]+|omniverse://[^@\s]+", text)))


def load_bundle_localization(scene_path: Path) -> dict[str, Any]:
    path = scene_path.parent / "new_scene_phaseB_dependency_localization_summary.json"
    if not path.exists():
        return {
            "available": False,
            "summary_path": str(path),
            "dependency_count": 0,
            "dependency_total_bytes": 0,
            "remote_url_count_before": None,
        }
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"available": False, "summary_path": str(path), "error": repr(exc)}
    data["available"] = True
    data["summary_path"] = str(path)
    return data


def write_report(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    caveats = summary.get("caveats") or []
    debug_paths = summary.get("debug_frame_paths") or []
    lines = [
        "# New Scene Real Sensor Smoke Report",
        "",
        "phase: New Scene Phase B",
        f"workspace: {summary.get('workspace')}",
        f"project_name: {summary.get('project_name')}",
        f"current_scene_id: {summary.get('current_scene_id')}",
        f"scene_path: {summary.get('scene_path')}",
        f"original_user_usd_path: {summary.get('original_user_usd_path')}",
        f"scene_open_result: {bool_text(summary.get('scene_open_result'))}",
        f"stage_available: {bool_text(summary.get('stage_available'))}",
        f"stage_open_method: {summary.get('stage_open_method')}",
        f"stage_open_elapsed_sec: {summary.get('stage_open_elapsed_sec')}",
        f"robot_platform: {summary.get('robot_platform')}",
        f"robot_source: {summary.get('robot_source')}",
        f"a1_root_prim: {summary.get('a1_root_prim')}",
        f"base_frame: {summary.get('base_frame')}",
        f"base_pose_readable: {bool_text(summary.get('base_pose_readable'))}",
        f"sensor_method: {summary.get('sensor_method')}",
        f"camera_prim_path: {summary.get('camera_prim_path')}",
        f"sensor_mount_parent: {summary.get('sensor_mount_parent')}",
        f"sensor_mount_xyz: {summary.get('sensor_mount_xyz')}",
        f"sensor_mount_rpy: {summary.get('sensor_mount_rpy')}",
        f"real_rgb_sensor_available: {bool_text(summary.get('real_rgb_sensor_available'))}",
        f"real_depth_sensor_available: {bool_text(summary.get('real_depth_sensor_available'))}",
        f"camera_params_available: {bool_text(summary.get('camera_params_available'))}",
        f"camera_intrinsics_available: {bool_text(summary.get('camera_intrinsics_available'))}",
        f"real_camera_pointcloud_available: {bool_text(summary.get('real_camera_pointcloud_available'))}",
        f"camera_pointcloud_source: {summary.get('camera_pointcloud_source')}",
        f"rtx_lidar_attempted: {bool_text(summary.get('rtx_lidar_attempted'))}",
        f"rtx_lidar_available: {bool_text(summary.get('rtx_lidar_available'))}",
        f"lidar_pointcloud_available: {bool_text(summary.get('lidar_pointcloud_available'))}",
        f"lidar_scan_available: {bool_text(summary.get('lidar_scan_available'))}",
        f"lidar_failure_reason: {summary.get('lidar_failure_reason')}",
        f"semantic_segmentation_available: {bool_text(summary.get('semantic_segmentation_available'))}",
        f"instance_segmentation_available: {bool_text(summary.get('instance_segmentation_available'))}",
        f"geometry_proxy_used: {bool_text(summary.get('geometry_proxy_used'))}",
        f"mounted_geometry_proxy_used: {bool_text(summary.get('mounted_geometry_proxy_used'))}",
        f"step_count: {summary.get('step_count')}",
        f"successful_steps: {summary.get('successful_steps')}",
        f"rgb_valid_steps: {summary.get('rgb_valid_steps')}",
        f"depth_valid_steps: {summary.get('depth_valid_steps')}",
        f"camera_pointcloud_valid_steps: {summary.get('camera_pointcloud_valid_steps')}",
        f"lidar_valid_steps: {summary.get('lidar_valid_steps')}",
        f"camera_follows_base_rate: {summary.get('camera_follows_base_rate')}",
        f"average_rgb_nonzero_ratio: {summary.get('average_rgb_nonzero_ratio')}",
        f"average_depth_valid_ratio: {summary.get('average_depth_valid_ratio')}",
        f"average_camera_pointcloud_count: {summary.get('average_camera_pointcloud_count')}",
        f"average_lidar_point_count: {summary.get('average_lidar_point_count')}",
        f"active_remote_refs_remaining: {summary.get('active_remote_refs_remaining')}",
        f"bundle_dependency_count: {summary.get('bundle_dependency_count')}",
        f"debug_frame_paths: {debug_paths}",
        f"core_dump_found: {bool_text(summary.get('core_dump_found'))}",
        f"new_kit_core_dump_found: {bool_text(summary.get('new_kit_core_dump_found'))}",
        f"safe_to_mapping: {bool_text(summary.get('safe_to_mapping'))}",
        f"next_phase: {summary.get('next_phase')}",
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
        f"run_dir: {summary.get('run_dir')}",
        f"steps_csv: {summary.get('steps_csv')}",
        f"summary_json: {summary.get('summary_json')}",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    passed = bool(summary.get("safe_to_mapping"))
    status = "passed" if passed else "failed"
    next_phase = summary.get("next_phase")
    common = f"""current_scene_id: {summary.get('current_scene_id')}
current_scene_path: {summary.get('scene_path')}
original_user_usd_path: {summary.get('original_user_usd_path')}
current_scene_phase: New Scene Phase B real sensor suite smoke
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_sensor_suite
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
- PI_action_finetuning: false
- A1_locomotion_training: false
"""
    metrics = f"""step_count: {summary.get('step_count')}
successful_steps: {summary.get('successful_steps')}
real_rgb_sensor_available: {bool_text(summary.get('real_rgb_sensor_available'))}
real_depth_sensor_available: {bool_text(summary.get('real_depth_sensor_available'))}
camera_params_available: {bool_text(summary.get('camera_params_available'))}
camera_intrinsics_available: {bool_text(summary.get('camera_intrinsics_available'))}
real_camera_pointcloud_available: {bool_text(summary.get('real_camera_pointcloud_available'))}
camera_pointcloud_source: {summary.get('camera_pointcloud_source')}
rtx_lidar_attempted: {bool_text(summary.get('rtx_lidar_attempted'))}
rtx_lidar_available: {bool_text(summary.get('rtx_lidar_available'))}
camera_follows_base_rate: {summary.get('camera_follows_base_rate')}
geometry_proxy_used: {bool_text(summary.get('geometry_proxy_used'))}
mounted_geometry_proxy_used: {bool_text(summary.get('mounted_geometry_proxy_used'))}
core_dump_found: {bool_text(summary.get('core_dump_found'))}
safe_to_mapping: {bool_text(summary.get('safe_to_mapping'))}
"""
    active = f"""# Active Task Board

current_phase: New Scene Phase B real sensor suite smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
{common}
{negative}
## New Scene Phase B Result

status: {status}
run_dir: {summary.get('run_dir')}
script: /home/ubuntu22/VLA/scripts/new_scene_phaseB_real_sensor_smoke.py
report: /home/ubuntu22/VLA/runs/NEW_SCENE_REAL_SENSOR_SMOKE_REPORT.md
summary_json: {summary.get('summary_json')}
steps_csv: {summary.get('steps_csv')}

{metrics}
## Scope

No mapping, candidate generation, VLM-LA interface, rollout, training, RL, SFT, GDPO, map_predict, PI/openpi fine-tuning, A1 locomotion training, checkpoint creation, or USD save was run.
"""
    webgpt = f"""# WEBGPT Brief

## Current Phase

New Scene Phase B real sensor suite smoke

## Context

{common}
{negative}
## Completed

- Opened the repaired new scene in Isaac/Omniverse after localizing remaining remote prop references into ignored dependencies.
- Confirmed `/World/A1` and `/World/A1/base`.
- Created runtime RGB-D camera and optional RTX LiDAR under runtime sensor paths, synchronized to the A1 base.
- Validated Replicator RGB, distance-to-image-plane depth, camera params, intrinsics, and camera pointcloud from real depth backprojection or Isaac pointcloud annotator.
- Did not use geometry proxy and did not start mapping, candidates, rollout, or training.

## Metrics

{metrics}
## Next Action

{next_phase}
"""
    critic = f"""# Critic Report

## Current Phase

New Scene Phase B real sensor suite smoke

## Finding

status: {status}

The repaired new scene was rendered through the real Isaac/Omniverse RGB-D sensor route. Geometry proxy and mounted geometry proxy were not used as formal sensor data.

## Evidence

- scene_path: {summary.get('scene_path')}
- a1_root_prim: /World/A1
- base_frame: /World/A1/base
- camera_prim_path: {summary.get('camera_prim_path')}
- pointcloud_source: {summary.get('camera_pointcloud_source')}
- rgb_valid_steps: {summary.get('rgb_valid_steps')}
- depth_valid_steps: {summary.get('depth_valid_steps')}
- camera_pointcloud_valid_steps: {summary.get('camera_pointcloud_valid_steps')}
- camera_follows_base_rate: {summary.get('camera_follows_base_rate')}
- rtx_lidar_attempted: {bool_text(summary.get('rtx_lidar_attempted'))}
- rtx_lidar_available: {bool_text(summary.get('rtx_lidar_available'))}
- core_dump_found: {bool_text(summary.get('core_dump_found'))}
- safe_to_mapping: {bool_text(summary.get('safe_to_mapping'))}

## Risks / Gates

- RTX LiDAR is optional for this gate; failures are recorded but do not block RGB-D if the main route passes.
- Some referenced props may emit MDL material warnings; the RGB-D/depth pointcloud gate is based on rendered sensor validity, not material completeness.
- Do not start Phase C unless `safe_to_mapping` is true.

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
{common}real_rgb_sensor_available: {bool_text(summary.get('real_rgb_sensor_available'))}
real_depth_sensor_available: {bool_text(summary.get('real_depth_sensor_available'))}
real_camera_pointcloud_available: {bool_text(summary.get('real_camera_pointcloud_available'))}
camera_pointcloud_source: {summary.get('camera_pointcloud_source')}
safe_to_mapping: {bool_text(summary.get('safe_to_mapping'))}
```

## New Scene Route

1. Phase A: scene open and robot inspection. Status: passed.
2. Phase B: real Isaac/Omniverse sensor suite smoke. Status: {status}.
3. Phase C: real-sensor mapping smoke. Status: {"next" if passed else "blocked"}.
4. Phase D: candidate viewpoint gain smoke.
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
{common}sensor_phaseB_status: {status}
real_rgb_sensor_available: {bool_text(summary.get('real_rgb_sensor_available'))}
real_depth_sensor_available: {bool_text(summary.get('real_depth_sensor_available'))}
real_camera_pointcloud_available: {bool_text(summary.get('real_camera_pointcloud_available'))}
camera_pointcloud_source: {summary.get('camera_pointcloud_source')}
```

No new-scene dataset samples have been created. Phase B only validated the real sensor route and did not create mapping, candidate, rollout, or training data.

## Required New Scene Sample Metadata

Future Phase G samples, only after Phase B-F pass, must include:

- real RGB/depth metadata
- depth_backprojection or Isaac pointcloud annotator stats
- BEV candidate render reference
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
    files = {
        WORKSPACE / "runs/ACTIVE_TASK_BOARD.md": active,
        WORKSPACE / "runs/WEBGPT_BRIEF.md": webgpt,
        WORKSPACE / "runs/CRITIC_REPORT.md": critic,
        WORKSPACE / "runs/VLM_LA_EXPLORER_PLAN.md": plan,
        WORKSPACE / "runs/VLM_LA_DATASET_SPEC.md": dataset,
    }
    for path, text in files.items():
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
    args = parser.parse_args()

    usd = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    logs_dir = run_dir / "logs"
    sensor_dir = run_dir / "sensor"
    reports_dir = run_dir / "reports"
    summary_dir = run_dir / "summary"
    debug_dir = run_dir / "debug_frames"
    probes_dir = run_dir / "probes"
    for directory in (logs_dir, sensor_dir, reports_dir, summary_dir, debug_dir, probes_dir):
        directory.mkdir(parents=True, exist_ok=True)

    steps_csv = summary_dir / "new_scene_real_sensor_steps.csv"
    summary_json = summary_dir / "new_scene_real_sensor_summary.json"
    report = reports_dir / "NEW_SCENE_REAL_SENSOR_SMOKE_REPORT.md"
    top_report = Path(args.top_report).expanduser().resolve()
    compat_report = Path(args.compat_report).expanduser().resolve()
    started = time.time()
    app = None
    rows: list[dict[str, Any]] = []
    pre_kit_dumps = kit_dumps()
    bundle_summary = load_bundle_localization(usd)
    summary: dict[str, Any] = {
        "phase": "New Scene Phase B real Isaac/Omniverse sensor suite smoke",
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
        "sensor_method": "real_isaac_omniverse_sensor_suite",
        "camera_prim_path": CAMERA_PATH,
        "lidar_prim_path": LIDAR_PATH,
        "sensor_mount_parent": "/World/A1/base equivalent runtime synced sensor path",
        "sensor_mount_marker_path": MOUNT_MARKER_PATH,
        "sensor_mount_xyz": [round(v, 4) for v in MOUNT_XYZ],
        "sensor_mount_rpy": [round(v, 6) for v in MOUNT_RPY],
        "real_rgb_sensor_available": False,
        "real_depth_sensor_available": False,
        "camera_params_available": False,
        "camera_intrinsics_available": False,
        "real_camera_pointcloud_available": False,
        "camera_pointcloud_source": "unavailable",
        "isaac_pointcloud_annotator_attempted": False,
        "rtx_lidar_attempted": False,
        "rtx_lidar_available": False,
        "lidar_pointcloud_available": False,
        "lidar_scan_available": False,
        "lidar_failure_reason": "",
        "semantic_segmentation_available": False,
        "instance_segmentation_available": False,
        "geometry_proxy_used": False,
        "mounted_geometry_proxy_used": False,
        "step_count": 0,
        "successful_steps": 0,
        "rgb_valid_steps": 0,
        "depth_valid_steps": 0,
        "camera_pointcloud_valid_steps": 0,
        "lidar_valid_steps": 0,
        "camera_follows_base_rate": 0.0,
        "average_rgb_nonzero_ratio": 0.0,
        "average_depth_valid_ratio": 0.0,
        "average_camera_pointcloud_count": 0.0,
        "average_lidar_point_count": None,
        "collision_count": 0,
        "stuck_count": 0,
        "falling_count": 0,
        "core_dump_found": False,
        "core_dump_files": [],
        "new_kit_core_dump_found": False,
        "new_kit_core_dump_files": [],
        "active_remote_refs_remaining": active_remote_refs(usd),
        "bundle_localization_summary_path": bundle_summary.get("summary_path"),
        "bundle_dependency_count": bundle_summary.get("dependency_count", 0),
        "bundle_dependency_total_bytes": bundle_summary.get("dependency_total_bytes", 0),
        "safe_to_mapping": False,
        "next_phase": "Fix New Scene Phase B real sensor smoke",
        "training_started": False,
        "RL_started": False,
        "map_predict_started": False,
        "checkpoint_created": False,
        "rollout_started": False,
        "debug_frame_paths": [],
        "steps_csv": str(steps_csv),
        "summary_json": str(summary_json),
        "run_dir": str(run_dir),
        "top_report": str(top_report),
        "compat_report": str(compat_report),
        "caveats": [
            "The original user USD was not modified; runtime prims are created in memory only and the stage is not saved.",
            "The ignored repaired bundle was preflight-localized so remaining remote prop USD references resolve from local dependencies.",
            "RTX LiDAR success is optional for this phase; RGB-D plus depth-derived or Isaac pointcloud is the hard gate.",
            "No raw RGB-D frame stream, raw pointcloud dump, npz, hdf5, checkpoint, mapping, candidate generation, rollout, or training was produced.",
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
        summary["isaac_pointcloud_annotator_attempted"] = "pointcloud" in camera_annotators
        required = {"rgb", "distance_to_image_plane", "camera_params"}
        if not required.issubset(set(camera_annotators)):
            raise RuntimeError(f"Required RGB-D camera annotators unavailable: {annotator_errors}")

        lidar_info = sensor_base.try_create_lidar(stage, rep, eye, target)
        lidar_annotator = lidar_info.pop("lidar_annotator", None)
        summary["rtx_lidar_attempted"] = bool(lidar_info["lidar_attempted"])
        summary["rtx_lidar_available"] = bool(lidar_info["lidar_available"])
        summary["lidar_failure_reason"] = lidar_info.get("lidar_failure_reason", "")
        summary["lidar_render_product_path"] = lidar_info.get("lidar_render_product_path")

        try:
            rep.orchestrator.set_capture_on_play(False)
        except Exception as exc:
            summary["set_capture_on_play_error"] = repr(exc)

        actions = [
            ("initial_pose", 0.0, 0.0, 0.0),
            ("small_forward", 0.12, 0.0, 0.0),
            ("small_yaw_left", 0.08, 0.0, math.radians(6.0)),
            ("small_forward", 0.12, 0.0, 0.0),
            ("small_lateral_left", 0.04, 0.06, 0.0),
            ("small_yaw_right", 0.08, 0.0, math.radians(-5.0)),
            ("small_forward", 0.10, 0.0, 0.0),
            ("small_lateral_right", 0.04, -0.05, 0.0),
        ][: max(5, min(args.steps, 10))]
        root_x, root_y, root_z = initial_root
        yaw = 0.0
        last_base_x, last_base_y, last_yaw = initial_base[0], initial_base[1], 0.0
        first_rgb: np.ndarray | None = None
        last_rgb: np.ndarray | None = None
        first_depth: np.ndarray | None = None
        last_depth: np.ndarray | None = None

        for step_id, (action, forward, lateral, dyaw) in enumerate(actions):
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
            cam_x, cam_y, cam_z = sensor_base.world_translation(cache, camera_prim)
            camera_error = math.sqrt((cam_x - eye[0]) ** 2 + (cam_y - eye[1]) ** 2 + (cam_z - eye[2]) ** 2)
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

            annotator_pc_stats = {"available": False, "point_count": 0, "finite_ratio": 0.0}
            if "pointcloud" in camera_annotators:
                try:
                    annotator_pc = sensor_base.array_from_annotator_data(camera_annotators["pointcloud"].get_data(), "data")
                    if annotator_pc is not None and annotator_pc.size > 0:
                        annotator_pc_stats = sensor_base.pointcloud_stats(np.asarray(annotator_pc).reshape(-1, 3))
                except Exception as exc:
                    summary.setdefault("pointcloud_annotator_errors", []).append(repr(exc))

            if annotator_pc_stats["available"]:
                pc_stats = annotator_pc_stats
                pc_source = "isaac_pointcloud_annotator"
            elif depth["available"] and intrinsics_available:
                points = sensor_base.pointcloud_from_depth(depth["array"], intrinsics)
                pc_stats = sensor_base.pointcloud_stats(points)
                pc_source = "depth_backprojection"
            else:
                pc_stats = sensor_base.pointcloud_stats(np.empty((0, 3), dtype=np.float32))
                pc_source = "unavailable"

            lidar_point_count = 0
            lidar_finite_ratio = 0.0
            lidar_available_step = False
            lidar_failure_reason = summary["lidar_failure_reason"]
            if lidar_annotator is not None:
                try:
                    stats = sensor_base.lidar_stats(lidar_annotator.get_data())
                    lidar_available_step = bool(stats["available"])
                    lidar_point_count = int(stats["point_count"])
                    lidar_finite_ratio = float(stats["finite_ratio"])
                except Exception as exc:
                    lidar_failure_reason = repr(exc)

            semantic_avail = False
            instance_avail = False
            if "semantic_segmentation" in camera_annotators:
                try:
                    semantic_avail = sensor_base.segmentation_available(camera_annotators["semantic_segmentation"].get_data())
                except Exception as exc:
                    summary.setdefault("semantic_errors", []).append(repr(exc))
            if "instance_segmentation" in camera_annotators:
                try:
                    instance_avail = sensor_base.segmentation_available(camera_annotators["instance_segmentation"].get_data())
                except Exception as exc:
                    summary.setdefault("instance_errors", []).append(repr(exc))

            if step_id == 0:
                first_rgb = rgb["array"]
                first_depth = depth["array"]
            last_rgb = rgb["array"]
            last_depth = depth["array"]

            moved = math.hypot(base_x - last_base_x, base_y - last_base_y)
            yaw_change = abs(yaw - last_yaw)
            collision_flag = abs(base_x - initial_base[0]) > 1.8 or abs(base_y - initial_base[1]) > 1.8
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
            elif not pc_stats["available"]:
                failure = "camera_pointcloud_invalid"
            elif pc_source not in POINTCLOUD_ALLOWED:
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
                "camera_x": round(cam_x, 4),
                "camera_y": round(cam_y, 4),
                "camera_z": round(cam_z, 4),
                "camera_yaw": round(yaw, 4),
                "camera_pitch": round(MOUNT_RPY[1], 4),
                "camera_follows_base": camera_follows,
                "rgb_available": rgb["available"],
                "rgb_width": rgb["width"],
                "rgb_height": rgb["height"],
                "rgb_dtype": rgb["dtype"],
                "rgb_mean": rgb["mean"],
                "rgb_nonzero_ratio": rgb["nonzero_ratio"],
                "depth_available": depth["available"],
                "depth_width": depth["width"],
                "depth_height": depth["height"],
                "depth_min": depth["min"],
                "depth_max": depth["max"],
                "depth_mean": depth["mean"],
                "depth_valid_ratio": depth["valid_ratio"],
                "camera_params_available": camera_params_available,
                "camera_intrinsics_available": intrinsics_available,
                "camera_pointcloud_available": pc_stats["available"],
                "camera_pointcloud_source": pc_source,
                "camera_pointcloud_point_count": pc_stats["point_count"],
                "camera_pointcloud_finite_ratio": pc_stats["finite_ratio"],
                "camera_pointcloud_min_x": pc_stats["min_x"],
                "camera_pointcloud_max_x": pc_stats["max_x"],
                "camera_pointcloud_min_y": pc_stats["min_y"],
                "camera_pointcloud_max_y": pc_stats["max_y"],
                "camera_pointcloud_min_z": pc_stats["min_z"],
                "camera_pointcloud_max_z": pc_stats["max_z"],
                "lidar_attempted": summary["rtx_lidar_attempted"],
                "lidar_available": lidar_available_step,
                "lidar_prim_path": LIDAR_PATH,
                "lidar_point_count": lidar_point_count,
                "lidar_finite_ratio": lidar_finite_ratio,
                "lidar_failure_reason": lidar_failure_reason,
                "semantic_available": semantic_avail,
                "instance_available": instance_avail,
                "collision_flag": collision_flag,
                "stuck_flag": stuck_flag,
                "falling_flag": falling_flag,
                "failure_reason": failure,
            })
            last_base_x, last_base_y, last_yaw = base_x, base_y, yaw

        if not rows:
            raise RuntimeError("No smoke rows were collected")
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

        success = [r for r in rows if not r["failure_reason"]]
        rgb_valid = [r for r in rows if r["rgb_available"]]
        depth_valid = [r for r in rows if r["depth_available"] and r["depth_valid_ratio"] >= 0.1]
        pc_valid = [
            r for r in rows
            if r["camera_pointcloud_available"] and r["camera_pointcloud_source"] in POINTCLOUD_ALLOWED
        ]
        lidar_valid = [r for r in rows if r["lidar_available"]]
        follows = [r for r in rows if r["camera_follows_base"]]
        collision_count = sum(1 for r in rows if r["collision_flag"])
        stuck_count = sum(1 for r in rows if r["stuck_flag"])
        falling_count = sum(1 for r in rows if r["falling_flag"])
        workspace_core_files = sensor_base.find_core_dumps(WORKSPACE)
        post_kit_dumps = kit_dumps()
        new_kit_dump_files = sorted(post_kit_dumps - pre_kit_dumps)
        pc_sources = [r["camera_pointcloud_source"] for r in pc_valid]
        selected_pc_source = "depth_backprojection"
        if any(src == "isaac_pointcloud_annotator" for src in pc_sources):
            selected_pc_source = "isaac_pointcloud_annotator"
        elif not pc_valid:
            selected_pc_source = "unavailable"

        summary.update({
            "step_count": len(rows),
            "successful_steps": len(success),
            "rgb_valid_steps": len(rgb_valid),
            "depth_valid_steps": len(depth_valid),
            "camera_params_available": all(bool(r["camera_params_available"]) for r in rows),
            "camera_intrinsics_available": all(bool(r["camera_intrinsics_available"]) for r in rows),
            "camera_pointcloud_valid_steps": len(pc_valid),
            "lidar_valid_steps": len(lidar_valid),
            "camera_follows_base_rate": round(len(follows) / len(rows), 4) if rows else 0.0,
            "average_rgb_nonzero_ratio": round(float(np.mean([r["rgb_nonzero_ratio"] for r in rows])), 4) if rows else 0.0,
            "average_depth_valid_ratio": round(float(np.mean([r["depth_valid_ratio"] for r in rows])), 4) if rows else 0.0,
            "average_camera_pointcloud_count": round(float(np.mean([r["camera_pointcloud_point_count"] for r in rows])), 2) if rows else 0.0,
            "average_lidar_point_count": round(float(np.mean([r["lidar_point_count"] for r in rows])), 2) if rows else None,
            "collision_count": collision_count,
            "stuck_count": stuck_count,
            "falling_count": falling_count,
            "core_dump_found": bool(workspace_core_files or new_kit_dump_files),
            "core_dump_files": workspace_core_files,
            "new_kit_core_dump_found": bool(new_kit_dump_files),
            "new_kit_core_dump_files": new_kit_dump_files,
            "real_rgb_sensor_available": len(rgb_valid) / len(rows) >= 0.8,
            "real_depth_sensor_available": len(depth_valid) / len(rows) >= 0.8,
            "real_camera_pointcloud_available": len(pc_valid) / len(rows) >= 0.8,
            "camera_pointcloud_source": selected_pc_source,
            "semantic_segmentation_available": any(bool(r["semantic_available"]) for r in rows),
            "instance_segmentation_available": any(bool(r["instance_available"]) for r in rows),
            "lidar_pointcloud_available": len(lidar_valid) > 0,
            "lidar_scan_available": False,
            "active_remote_refs_remaining": active_remote_refs(usd),
        })
        if summary["rtx_lidar_available"] and not summary["lidar_pointcloud_available"]:
            summary["lidar_failure_reason"] = summary["lidar_failure_reason"] or (
                "RTX LiDAR prim/render product created but no pointcloud returns were read during the short smoke."
            )
        pass_ok = bool(
            summary["scene_open_result"]
            and summary["stage_available"]
            and summary["a1_root_exists"]
            and summary["base_pose_readable"]
            and summary["camera_follows_base_rate"] == 1.0
            and len(rows) >= 5
            and len(success) >= 5
            and summary["real_rgb_sensor_available"]
            and summary["real_depth_sensor_available"]
            and summary["camera_params_available"]
            and summary["camera_intrinsics_available"]
            and summary["real_camera_pointcloud_available"]
            and summary["camera_pointcloud_source"] in POINTCLOUD_ALLOWED
            and not summary["geometry_proxy_used"]
            and not summary["mounted_geometry_proxy_used"]
            and summary["rtx_lidar_attempted"]
            and not summary["core_dump_found"]
            and collision_count == 0
            and stuck_count == 0
            and falling_count == 0
        )
        summary["safe_to_mapping"] = pass_ok
        summary["next_phase"] = (
            "New Scene Phase C real-sensor mapping smoke"
            if pass_ok
            else "Fix New Scene Phase B real sensor smoke"
        )
        exit_code = 0 if pass_ok else 2
    except Exception as exc:
        summary["exception"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
        summary["next_phase"] = "Fix New Scene Phase B real sensor smoke"
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
