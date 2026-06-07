#!/usr/bin/env python3
"""Phase 8 A1 real-sensor VLM-LA long rollout data collection.

This opens the primary USD read-only, uses the existing /World/A1 prim and the
real Isaac/Omniverse RGB-D route, collects multi-start closed-loop rollout
samples, and labels each decision with the pseudo VLM command:

    Go to candidate <id>.

It does not train, run real VLM inference, use geometry proxies, save the USD,
or create checkpoints.
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

from phase4r_a1_real_sensor_mapping_smoke import RealSensorBevMap  # noqa: E402
from phase5r_a1_real_sensor_candidate_gain_smoke import (  # noqa: E402
    CANDIDATE_SAMPLING_METHOD,
    INFORMATION_GAIN_METHOD,
    MAP_TYPE,
    MAPPING_METHOD,
    MAP_UPDATE_SOURCE,
    PATH_COST_METHOD,
    SCORE_FORMULA,
    render_candidate_overlay,
    score_candidates,
)
from phase6_vlm_la_interface_smoke import (  # noqa: E402
    candidate_key,
    parse_language_command,
    target_pose,
    validate_candidate_id,
)
from phase7_a1_vlm_la_closed_loop_smoke import (  # noqa: E402
    CAMERA_POINTCLOUD_SOURCE,
    MOVEMENT_MODE,
    OUTPUT_CONTRACT,
    SENSOR_METHOD,
    VLM_OUTPUT_MODE,
    capture_observation,
    candidate_index_for_step,
    move_a1_kinematic,
    selected_candidate,
)
from phase56_a1_real_sensor_suite_smoke import (  # noqa: E402
    A1_ROOT,
    BASE_FRAME,
    CAMERA_PATH,
    LIDAR_PATH,
    SCENE,
    attach_camera_annotators,
    bool_text,
    create_runtime_prims,
    expected_sensor_pose,
    find_core_dumps,
    save_depth_vis,
    save_rgb_png,
    set_root_pose,
    set_world_look_at,
    set_world_translate,
    try_create_lidar,
    world_translation,
)


PHASE = "Phase 8 A1 primary-scene VLM-LA long rollout data collection"
TOP_REPORT = WORKSPACE / "runs/A1_VLM_LA_LONG_ROLLOUT_REPORT.md"
PROJECT_NAME = "A1-VLM-LA Explorer"
MAIN_GOAL = "A1-VLM-LA Explorer for 3D Active Exploration"
ROBOT_PLATFORM = "unitree_a1"
ROBOT_SOURCE = "existing_usd_prim"
LABEL_SOURCE = "classical_argmax_information_gain_minus_path_cost"
PROMPT = "Select the best next viewpoint for active exploration."


ROLLOUT_STEP_FIELDS = [
    "start_id",
    "step_id",
    "timestamp",
    "pre_base_x",
    "pre_base_y",
    "pre_base_z",
    "pre_base_yaw",
    "post_base_x",
    "post_base_y",
    "post_base_z",
    "post_base_yaw",
    "rgb_available",
    "depth_available",
    "camera_pointcloud_available",
    "depth_valid_ratio",
    "pointcloud_point_count",
    "known_ratio_before",
    "known_ratio_after",
    "known_ratio_delta",
    "occupied_cells",
    "known_free_cells",
    "unknown_cells",
    "candidate_count",
    "valid_candidate_count",
    "positive_gain_candidate_count",
    "selected_candidate_id",
    "selected_score",
    "selected_information_gain",
    "selected_path_cost",
    "target_language",
    "parse_success",
    "validation_success",
    "target_pose_lookup_success",
    "movement_success",
    "fallback_used",
    "fallback_reason",
    "collision_flag",
    "stuck_flag",
    "falling_flag",
    "failure_reason",
]


CANDIDATE_FIELDS = [
    "start_id",
    "step_id",
    "candidate_id",
    "base_x",
    "base_y",
    "base_z",
    "base_yaw",
    "x",
    "y",
    "z",
    "yaw",
    "dx",
    "dy",
    "dyaw",
    "distance_to_robot",
    "is_valid",
    "is_reachable",
    "collision_risk",
    "collision_penalty",
    "path_cost",
    "path_cost_method",
    "visible_unknown_cells",
    "information_gain",
    "information_gain_method",
    "score",
    "selected_by_classical",
    "failure_reason",
]


def rate(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 6) if values else 0.0


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def rel(path: Path, run_dir: Path) -> str:
    return str(path.relative_to(run_dir))


def bool_from_any(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def start_pose_plan(base_xyz: tuple[float, float, float], start_count: int) -> list[dict[str, float | int]]:
    offsets = [
        (0.0, 0.0, 0.0),
        (0.45, 0.0, 0.25),
        (-0.45, 0.0, -0.25),
        (0.0, 0.45, 0.5),
        (0.0, -0.45, -0.5),
        (0.65, 0.35, 0.75),
        (-0.65, 0.35, -0.75),
        (0.65, -0.35, 1.0),
        (-0.65, -0.35, -1.0),
        (0.0, 0.8, 1.25),
    ]
    while len(offsets) < start_count:
        idx = len(offsets)
        radius = 0.4 + 0.08 * idx
        angle = idx * 1.618
        offsets.append((math.cos(angle) * radius, math.sin(angle) * radius, angle))
    starts = []
    for start_id, (dx, dy, yaw) in enumerate(offsets[:start_count]):
        starts.append({
            "start_id": start_id,
            "x": round(base_xyz[0] + dx, 4),
            "y": round(base_xyz[1] + dy, 4),
            "z": round(base_xyz[2], 4),
            "yaw": round(yaw, 4),
        })
    return starts


def candidate_for_sample(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": int(row["candidate_id"]),
        "x": float(row["x"]),
        "y": float(row["y"]),
        "z": float(row["z"]),
        "yaw": float(row["yaw"]),
        "is_valid": bool_from_any(row["is_valid"]),
        "is_reachable": bool_from_any(row["is_reachable"]),
        "path_cost": row["path_cost"],
        "information_gain": float(row["information_gain"]),
        "score": float(row["score"]),
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def save_plots(run_dir: Path, rows: list[dict[str, Any]], start_rows: list[dict[str, Any]]) -> bool:
    plots_dir = run_dir / "plots"
    plots_dir.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        write_csv(
            plots_dir / "known_ratio_by_start.csv",
            [
                {
                    "start_id": r["start_id"],
                    "step_id": r["step_id"],
                    "known_ratio_after": r["known_ratio_after"],
                }
                for r in rows
            ],
            ["start_id", "step_id", "known_ratio_after"],
        )
        write_csv(plots_dir / "start_summary_for_plots.csv", start_rows, list(start_rows[0].keys()) if start_rows else [])
        return False

    by_start: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        by_start.setdefault(int(row["start_id"]), []).append(row)

    plt.figure(figsize=(8, 5))
    for start_id, group in sorted(by_start.items()):
        plt.plot(
            [int(r["step_id"]) for r in group],
            [float(r["known_ratio_after"]) for r in group],
            marker="o",
            linewidth=1.2,
            label=f"start {start_id:03d}",
        )
    plt.xlabel("step")
    plt.ylabel("known ratio")
    plt.title("Known ratio by start")
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=7, ncol=2)
    plt.tight_layout()
    plt.savefig(plots_dir / "known_ratio_by_start.png", dpi=120)
    plt.close()

    ordered = sorted(start_rows, key=lambda r: int(r["start_id"]))
    ids = [int(r["start_id"]) for r in ordered]
    plt.figure(figsize=(7, 4))
    plt.bar(ids, [float(r["final_known_ratio"]) for r in ordered])
    plt.xlabel("start")
    plt.ylabel("final known ratio")
    plt.title("Final known ratio by start")
    plt.tight_layout()
    plt.savefig(plots_dir / "final_known_ratio_by_start.png", dpi=120)
    plt.close()

    plt.figure(figsize=(7, 4))
    plt.bar(ids, [int(r["action_count"]) for r in ordered])
    plt.xlabel("start")
    plt.ylabel("action count")
    plt.title("Action count by start")
    plt.tight_layout()
    plt.savefig(plots_dir / "action_count_by_start.png", dpi=120)
    plt.close()

    plt.figure(figsize=(7, 4))
    plt.bar(ids, [int(r["failure_count"]) for r in ordered])
    plt.xlabel("start")
    plt.ylabel("failure count")
    plt.title("Failure count by start")
    plt.tight_layout()
    plt.savefig(plots_dir / "failure_count_by_start.png", dpi=120)
    plt.close()

    plt.figure(figsize=(6, 6))
    for start_id, group in sorted(by_start.items()):
        xs = [float(group[0]["pre_base_x"])] + [float(r["post_base_x"]) for r in group]
        ys = [float(group[0]["pre_base_y"])] + [float(r["post_base_y"]) for r in group]
        plt.plot(xs, ys, marker="o", linewidth=1.2, label=f"start {start_id:03d}")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Robot XY trajectories")
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=7, ncol=2)
    plt.tight_layout()
    plt.savefig(plots_dir / "robot_xy_trajectories.png", dpi=120)
    plt.close()
    return True


def build_summary(usd: Path, run_dir: Path, start_count: int, max_actions: int) -> dict[str, Any]:
    return {
        "phase": PHASE,
        "workspace": str(WORKSPACE),
        "project_name": PROJECT_NAME,
        "main_goal": MAIN_GOAL,
        "robot_platform": ROBOT_PLATFORM,
        "robot_source": ROBOT_SOURCE,
        "a1_root_prim": A1_ROOT,
        "base_frame": BASE_FRAME,
        "scene_path": str(usd),
        "scene_exists": usd.exists(),
        "sensor_method": SENSOR_METHOD,
        "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE,
        "geometry_proxy_used": False,
        "mounted_geometry_proxy_used": False,
        "movement_mode": MOVEMENT_MODE,
        "vlm_output_mode": VLM_OUTPUT_MODE,
        "real_vlm_inference": False,
        "output_contract": OUTPUT_CONTRACT,
        "map_type": MAP_TYPE,
        "mapping_method": MAPPING_METHOD,
        "map_update_source": MAP_UPDATE_SOURCE,
        "candidate_sampling_method": CANDIDATE_SAMPLING_METHOD,
        "path_cost_method": PATH_COST_METHOD,
        "information_gain_method": INFORMATION_GAIN_METHOD,
        "score_formula": SCORE_FORMULA,
        "label_source": LABEL_SOURCE,
        "start_count": int(start_count),
        "max_actions_per_start": int(max_actions),
        "training_started": False,
        "RL_started": False,
        "map_predict_started": False,
        "checkpoint_created": False,
        "PI_finetuning": False,
        "A1_locomotion_training": False,
        "run_dir": str(run_dir),
        "safe_to_continue_phase9": False,
        "exception": None,
        "traceback": None,
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# A1 VLM-LA Long Rollout Report",
        "",
        "phase: Phase 8",
        f"workspace: {summary.get('workspace')}",
        f"project_name: {summary.get('project_name')}",
        f"robot_platform: {summary.get('robot_platform')}",
        f"robot_source: {summary.get('robot_source')}",
        f"scene_path: {summary.get('scene_path')}",
        f"sensor_method: {summary.get('sensor_method')}",
        f"camera_pointcloud_source: {summary.get('camera_pointcloud_source')}",
        f"real_rgb_sensor_available: {bool_text(summary.get('real_rgb_sensor_available'))}",
        f"real_depth_sensor_available: {bool_text(summary.get('real_depth_sensor_available'))}",
        f"real_camera_pointcloud_available: {bool_text(summary.get('real_camera_pointcloud_available'))}",
        f"real_rgb_sensor_valid_rate: {summary.get('real_rgb_sensor_valid_rate')}",
        f"real_depth_sensor_valid_rate: {summary.get('real_depth_sensor_valid_rate')}",
        f"real_camera_pointcloud_valid_rate: {summary.get('real_camera_pointcloud_valid_rate')}",
        f"geometry_proxy_used: {bool_text(summary.get('geometry_proxy_used'))}",
        f"mounted_geometry_proxy_used: {bool_text(summary.get('mounted_geometry_proxy_used'))}",
        f"vlm_output_mode: {summary.get('vlm_output_mode')}",
        f"real_vlm_inference: {bool_text(summary.get('real_vlm_inference'))}",
        f"output_contract: {summary.get('output_contract')}",
        f"start_count: {summary.get('start_count')}",
        f"completed_start_count: {summary.get('completed_start_count')}",
        f"total_action_count: {summary.get('total_action_count')}",
        f"candidate_rows: {summary.get('candidate_rows')}",
        f"vlm_la_sample_count: {summary.get('vlm_la_sample_count')}",
        f"average_final_known_ratio: {summary.get('average_final_known_ratio')}",
        f"average_known_ratio_gain: {summary.get('average_known_ratio_gain')}",
        f"parse_success_rate: {summary.get('parse_success_rate')}",
        f"validation_success_rate: {summary.get('validation_success_rate')}",
        f"movement_success_rate: {summary.get('movement_success_rate')}",
        f"starts_with_failures: {summary.get('starts_with_failures')}",
        f"collision_count: {summary.get('collision_count')}",
        f"stuck_count: {summary.get('stuck_count')}",
        f"falling_count: {summary.get('falling_count')}",
        f"dataset_manifest path: {summary.get('dataset_manifest_path')}",
        f"vlm_la_samples path: {summary.get('vlm_la_samples_path')}",
        f"rollout_summary path: {summary.get('rollout_summary_path')}",
        f"candidate_summary path: {summary.get('candidate_summary_path')}",
        f"plots path: {summary.get('plots_path')}",
        f"safe_to_continue_phase9: {bool_text(summary.get('safe_to_continue_phase9'))}",
        f"caveats: {summary.get('caveats')}",
        "training: false",
        "RL: false",
        "map_predict: false",
        "PI_finetuning: false",
        "A1_locomotion_training: false",
        "checkpoint_created: false",
        "",
        "## Evidence",
        "",
        f"- run_dir: {summary.get('run_dir')}",
        f"- rollout_steps_csv: {summary.get('rollout_steps_csv')}",
        f"- start_summary_csv: {summary.get('start_summary_csv')}",
        f"- command_log_jsonl: {summary.get('command_log_jsonl')}",
        f"- parse_log_jsonl: {summary.get('parse_log_jsonl')}",
        "- The primary USD was opened read-only and was not saved or overwritten.",
        "- RGB-D observations came from Isaac/Omniverse Replicator annotators.",
        "- Pointclouds came from depth backprojection using camera intrinsics.",
        "- Pseudo VLM labels were generated by the classical candidate selector.",
        "",
        "## Negative Scope",
        "",
        "- No VLM training, RL, map_predict training, PI/openpi fine-tuning, or A1 locomotion training.",
        "- No real VLM inference.",
        "- No geometry proxy or mounted geometry proxy.",
        "- No checkpoint or core dump is included.",
        "- Samples require Phase 9 human review before any training use.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", default=str(SCENE))
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--top_report", default=str(TOP_REPORT))
    parser.add_argument("--start_count", type=int, default=10)
    parser.add_argument("--max_actions_per_start", type=int, default=8)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--map_resolution_m", type=float, default=0.2)
    parser.add_argument("--map_width_m", type=float, default=16.0)
    parser.add_argument("--map_height_m", type=float, default=16.0)
    parser.add_argument("--save_debug_every", type=int, default=1)
    args = parser.parse_args()

    usd = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    dirs = {
        "logs": run_dir / "logs",
        "rollout": run_dir / "rollout",
        "samples": run_dir / "samples",
        "bev_renders": run_dir / "bev_renders",
        "debug_frames": run_dir / "debug_frames",
        "commands": run_dir / "commands",
        "parsing": run_dir / "parsing",
        "candidates": run_dir / "candidates",
        "maps": run_dir / "maps",
        "plots": run_dir / "plots",
        "reports": run_dir / "reports",
        "summary": run_dir / "summary",
    }
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)
    for start_id in range(int(args.start_count)):
        (run_dir / f"start_{start_id:03d}").mkdir(parents=True, exist_ok=True)

    summary = build_summary(usd, run_dir, int(args.start_count), int(args.max_actions_per_start))
    steps_csv = dirs["summary"] / "rollout_steps.csv"
    candidates_csv = dirs["summary"] / "candidate_summary.csv"
    start_summary_csv = dirs["summary"] / "start_summary.csv"
    summary_json = dirs["summary"] / "rollout_summary.json"
    samples_jsonl = dirs["samples"] / "vlm_la_samples.jsonl"
    manifest_json = dirs["samples"] / "dataset_manifest.json"
    command_log = dirs["commands"] / "command_log.jsonl"
    parse_log = dirs["parsing"] / "parse_log.jsonl"
    report = dirs["reports"] / "A1_VLM_LA_LONG_ROLLOUT_REPORT.md"

    app = None
    rows: list[dict[str, Any]] = []
    candidate_rows_all: list[dict[str, Any]] = []
    samples: list[dict[str, Any]] = []
    command_rows: list[dict[str, Any]] = []
    parse_rows: list[dict[str, Any]] = []
    start_rows: list[dict[str, Any]] = []
    exit_code = 1
    started = time.time()

    try:
        if not usd.exists():
            raise FileNotFoundError(str(usd))

        from isaacsim import SimulationApp

        app = SimulationApp({"headless": True})
        import omni.replicator.core as rep
        import omni.usd
        from pxr import UsdGeom, UsdPhysics

        context = omni.usd.get_context()
        summary["open_stage_raw_result"] = repr(context.open_stage(str(usd)))
        stage = None
        deadline = time.time() + 180.0
        while time.time() < deadline:
            app.update()
            stage = context.get_stage()
            if stage is not None and list(stage.Traverse()):
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

        create_runtime_prims(stage, int(args.width), int(args.height))
        camera_prim = stage.GetPrimAtPath(CAMERA_PATH)
        light_prim = stage.GetPrimAtPath("/World/RuntimeSensors/phase56_runtime_fill_light")
        if not camera_prim or not camera_prim.IsValid():
            raise RuntimeError("Runtime RGB-D camera prim was not created")

        cache = UsdGeom.XformCache()
        initial_root_xyz = world_translation(cache, root)
        initial_base_xyz = world_translation(cache, base)
        summary["initial_root_pose_xyz"] = [round(v, 6) for v in initial_root_xyz]
        summary["initial_base_pose_xyz"] = [round(v, 6) for v in initial_base_xyz]
        summary["base_pose_readable"] = True
        ops = {op.GetName(): op for op in UsdGeom.Xformable(root).GetOrderedXformOps()}
        initial_orient = ops["xformOp:orient"].Get() if "xformOp:orient" in ops else None

        eye, target = expected_sensor_pose(initial_base_xyz[0], initial_base_xyz[1], initial_base_xyz[2], 0.0)
        set_world_look_at(camera_prim, eye, target)
        if light_prim and light_prim.IsValid():
            set_world_translate(light_prim, (initial_base_xyz[0], initial_base_xyz[1], initial_base_xyz[2] + 2.5))
        render_product = rep.create.render_product(CAMERA_PATH, (int(args.width), int(args.height)))
        camera_annotators, annotator_errors = attach_camera_annotators(rep, render_product)
        summary["camera_annotator_errors"] = annotator_errors
        required = {"rgb", "distance_to_image_plane", "camera_params"}
        if not required.issubset(camera_annotators):
            raise RuntimeError(f"Required RGB-D camera annotators unavailable: {annotator_errors}")
        lidar_info = try_create_lidar(stage, rep, eye, target)
        lidar_annotator = lidar_info.pop("lidar_annotator", None)
        summary["rtx_lidar_available"] = bool(lidar_info.get("lidar_available"))
        summary["rtx_lidar_attempted"] = bool(lidar_info.get("lidar_attempted"))
        summary["lidar_failure_reason"] = lidar_info.get("lidar_failure_reason", "")
        try:
            rep.orchestrator.set_capture_on_play(False)
        except Exception as exc:
            summary["set_capture_on_play_error"] = repr(exc)

        start_plan = start_pose_plan(initial_base_xyz, int(args.start_count))
        for start in start_plan:
            start_id = int(start["start_id"])
            start_dir = run_dir / f"start_{start_id:03d}"
            yaw = float(start["yaw"])
            root_xyz = (
                initial_root_xyz[0] + (float(start["x"]) - initial_base_xyz[0]),
                initial_root_xyz[1] + (float(start["y"]) - initial_base_xyz[1]),
                initial_root_xyz[2],
            )
            set_root_pose(root, root_xyz, yaw, initial_orient)
            for _ in range(4):
                app.update()

            cache = UsdGeom.XformCache()
            base_xyz = world_translation(cache, base)
            bev = RealSensorBevMap(
                base_xyz[0],
                base_xyz[1],
                width_m=float(args.map_width_m),
                height_m=float(args.map_height_m),
                resolution_m=float(args.map_resolution_m),
            )
            start_initial_known = 0.0
            start_last_known = 0.0
            start_failures = 0
            start_steps = 0
            start_stop_reason = ""

            for step_id in range(int(args.max_actions_per_start)):
                cache = UsdGeom.XformCache()
                pre_base = world_translation(cache, base)
                pre_yaw = yaw
                pre_obs = capture_observation(
                    app,
                    rep,
                    stage,
                    camera_prim,
                    light_prim,
                    camera_annotators,
                    lidar_annotator,
                    (pre_base[0], pre_base[1], pre_base[2], pre_yaw),
                    bev,
                )
                known_ratio_before = float(pre_obs["map_stats"]["known_ratio"])

                base_pose = {"x": pre_base[0], "y": pre_base[1], "z": pre_base[2], "yaw": pre_yaw}
                step_candidates = score_candidates(bev, base_pose)
                for candidate in step_candidates:
                    candidate["start_id"] = start_id
                    candidate["step_id"] = step_id
                chosen = selected_candidate(step_candidates)
                fallback_used = False
                fallback_reason = ""
                if chosen is None:
                    selectable = [r for r in step_candidates if bool_from_any(r.get("is_valid")) and bool_from_any(r.get("is_reachable"))]
                    if selectable:
                        chosen = max(selectable, key=lambda r: (float(r["score"]), int(r["information_gain"]), -int(r["candidate_id"])))
                        chosen["selected_by_classical"] = True
                        fallback_used = True
                        fallback_reason = "no_positive_gain_candidate_used_best_valid_reachable"
                    elif step_candidates:
                        chosen = max(step_candidates, key=lambda r: float(r["score"]))
                        chosen["selected_by_classical"] = True
                        fallback_used = True
                        fallback_reason = "no_valid_reachable_candidate_used_best_score"
                    else:
                        start_stop_reason = "no_candidates_generated"
                        break

                selected_id = int(chosen["candidate_id"])
                target_language = f"Go to candidate {selected_id}."
                indexed = candidate_index_for_step(step_id, step_candidates)
                parsed = parse_language_command(target_language)
                validation = validate_candidate_id(parsed["selected_candidate_id"], step_id, indexed)
                lookup = target_pose(indexed.get(candidate_key(step_id, int(parsed["selected_candidate_id"])))) if parsed["parse_success"] else None
                if not (parsed["parse_success"] and validation["valid"] and lookup):
                    fallback_used = True
                    fallback_reason = parsed["error"] or validation["reason"] or "target_pose_lookup_failed"
                    lookup = target_pose(chosen)
                    parsed["selected_candidate_id"] = selected_id

                bev_image = dirs["bev_renders"] / f"start_{start_id:03d}_step_{step_id:03d}_bev_candidates.png"
                render_candidate_overlay(
                    bev,
                    step_id,
                    base_pose,
                    (pre_obs["sensor_pose"]["x"], pre_obs["sensor_pose"]["y"], pre_obs["sensor_pose"]["z"]),
                    step_candidates,
                    bev_image,
                )
                step_candidate_csv = dirs["candidates"] / f"start_{start_id:03d}_step_{step_id:03d}_candidates.csv"
                write_csv(step_candidate_csv, step_candidates, CANDIDATE_FIELDS)

                rgb_path: Path | None = None
                depth_path: Path | None = None
                if int(args.save_debug_every) > 0 and step_id % int(args.save_debug_every) == 0:
                    rgb_path = dirs["debug_frames"] / f"start_{start_id:03d}_step_{step_id:03d}_rgb.png"
                    depth_path = dirs["debug_frames"] / f"start_{start_id:03d}_step_{step_id:03d}_depth_vis.png"
                    save_rgb_png(pre_obs["rgb"]["array"], rgb_path)
                    save_depth_vis(pre_obs["depth"]["array"], depth_path)

                if lookup is None:
                    start_stop_reason = "target_pose_lookup_failed"
                    start_failures += 1
                    break

                root_xyz, yaw = move_a1_kinematic(root, initial_orient, root_xyz, pre_base, lookup)
                for _ in range(3):
                    app.update()

                cache = UsdGeom.XformCache()
                post_base = world_translation(cache, base)
                post_obs = capture_observation(
                    app,
                    rep,
                    stage,
                    camera_prim,
                    light_prim,
                    camera_annotators,
                    lidar_annotator,
                    (post_base[0], post_base[1], post_base[2], yaw),
                    bev,
                )
                known_ratio_after = float(post_obs["map_stats"]["known_ratio"])
                distance_to_target = math.hypot(post_base[0] - float(lookup["x"]), post_base[1] - float(lookup["y"]))
                moved_distance = math.hypot(post_base[0] - pre_base[0], post_base[1] - pre_base[1])
                movement_success = bool(distance_to_target <= 0.45 and moved_distance > 0.02)
                collision_flag = bool_from_any(chosen.get("collision_risk")) or not bool_from_any(chosen.get("is_valid"))
                stuck_flag = bool(moved_distance < 0.02)
                falling_flag = bool(post_base[2] < 0.2 or post_base[2] > 1.5 or abs(post_base[2] - initial_base_xyz[2]) > 0.6)
                failure_reason = ""
                if pre_obs["failure_reason"]:
                    failure_reason = f"pre_{pre_obs['failure_reason']}"
                elif post_obs["failure_reason"]:
                    failure_reason = f"post_{post_obs['failure_reason']}"
                elif not parsed["parse_success"]:
                    failure_reason = "parse_failed"
                elif not validation["valid"]:
                    failure_reason = validation["reason"]
                elif not movement_success:
                    failure_reason = "movement_not_within_target_tolerance"
                elif collision_flag:
                    failure_reason = "selected_candidate_collision_or_invalid"
                elif stuck_flag:
                    failure_reason = "a1_base_pose_did_not_move"
                elif falling_flag:
                    failure_reason = "a1_base_z_out_of_expected_range"

                if failure_reason:
                    start_failures += 1

                row = {
                    "start_id": start_id,
                    "step_id": step_id,
                    "timestamp": round(time.time(), 3),
                    "pre_base_x": round(pre_base[0], 4),
                    "pre_base_y": round(pre_base[1], 4),
                    "pre_base_z": round(pre_base[2], 4),
                    "pre_base_yaw": round(pre_yaw, 4),
                    "post_base_x": round(post_base[0], 4),
                    "post_base_y": round(post_base[1], 4),
                    "post_base_z": round(post_base[2], 4),
                    "post_base_yaw": round(yaw, 4),
                    "rgb_available": bool(pre_obs["rgb"]["available"] and post_obs["rgb"]["available"]),
                    "depth_available": bool(pre_obs["depth"]["available"] and post_obs["depth"]["available"]),
                    "camera_pointcloud_available": bool(pre_obs["camera_pointcloud"]["available"] and post_obs["camera_pointcloud"]["available"]),
                    "depth_valid_ratio": round(float(pre_obs["depth"]["valid_ratio"]), 4),
                    "pointcloud_point_count": int(pre_obs["camera_pointcloud"]["point_count"]),
                    "known_ratio_before": round(known_ratio_before, 6),
                    "known_ratio_after": round(known_ratio_after, 6),
                    "known_ratio_delta": round(known_ratio_after - start_last_known, 6),
                    "occupied_cells": int(post_obs["map_stats"]["occupied_cells"]),
                    "known_free_cells": int(post_obs["map_stats"]["known_free_cells"]),
                    "unknown_cells": int(post_obs["map_stats"]["unknown_cells"]),
                    "candidate_count": len(step_candidates),
                    "valid_candidate_count": sum(1 for r in step_candidates if bool_from_any(r.get("is_valid")) and bool_from_any(r.get("is_reachable"))),
                    "positive_gain_candidate_count": sum(1 for r in step_candidates if int(r.get("information_gain", 0)) > 0),
                    "selected_candidate_id": selected_id,
                    "selected_score": round(float(chosen["score"]), 4),
                    "selected_information_gain": int(chosen["information_gain"]),
                    "selected_path_cost": chosen["path_cost"],
                    "target_language": target_language,
                    "parse_success": bool(parsed["parse_success"]),
                    "validation_success": bool(validation["valid"]),
                    "target_pose_lookup_success": lookup is not None,
                    "movement_success": bool(movement_success),
                    "fallback_used": bool(fallback_used),
                    "fallback_reason": fallback_reason,
                    "collision_flag": bool(collision_flag),
                    "stuck_flag": bool(stuck_flag),
                    "falling_flag": bool(falling_flag),
                    "failure_reason": failure_reason,
                }
                rows.append(row)
                candidate_rows_all.extend(step_candidates)

                sample_id = f"home_like_scene_v1_a1_start{start_id:03d}_step{step_id:03d}"
                sample = {
                    "sample_id": sample_id,
                    "robot_platform": ROBOT_PLATFORM,
                    "robot_source": ROBOT_SOURCE,
                    "scene_path": str(usd),
                    "sensor_method": SENSOR_METHOD,
                    "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE,
                    "geometry_proxy_used": False,
                    "mounted_geometry_proxy_used": False,
                    "bev_image": rel(bev_image, run_dir) if bev_image.exists() else None,
                    "rgb_image": rel(rgb_path, run_dir) if rgb_path and rgb_path.exists() else None,
                    "depth_image": rel(depth_path, run_dir) if depth_path and depth_path.exists() else None,
                    "robot_pose": {
                        "x": round(pre_base[0], 4),
                        "y": round(pre_base[1], 4),
                        "z": round(pre_base[2], 4),
                        "yaw": round(pre_yaw, 4),
                    },
                    "sensor_pose": pre_obs["sensor_pose"],
                    "map_stats": {
                        "known_ratio": round(known_ratio_before, 6),
                        "occupied_cells": int(pre_obs["map_stats"]["occupied_cells"]),
                        "known_free_cells": int(pre_obs["map_stats"]["known_free_cells"]),
                        "unknown_cells": int(pre_obs["map_stats"]["unknown_cells"]),
                        "observed_count_sum": int(pre_obs["map_stats"]["observed_count_sum"]),
                        "map_update_source": MAP_UPDATE_SOURCE,
                    },
                    "candidates": [candidate_for_sample(c) for c in step_candidates],
                    "prompt": PROMPT,
                    "target_language": target_language,
                    "selected_candidate_id": selected_id,
                    "label_source": LABEL_SOURCE,
                    "training": False,
                }
                samples.append(sample)
                command_rows.append({
                    "sample_id": sample_id,
                    "start_id": start_id,
                    "step_id": step_id,
                    "target_language": target_language,
                    "output_contract": OUTPUT_CONTRACT,
                    "vlm_output_mode": VLM_OUTPUT_MODE,
                    "real_vlm_inference": False,
                    "training": False,
                })
                parse_rows.append({
                    "sample_id": sample_id,
                    "start_id": start_id,
                    "step_id": step_id,
                    "input_command": target_language,
                    "parse_success": bool(parsed["parse_success"]),
                    "parsed_candidate_id": parsed["selected_candidate_id"],
                    "candidate_exists": bool(validation["exists"]),
                    "candidate_valid": bool(validation["is_valid_candidate"]),
                    "candidate_reachable": bool(validation["is_reachable"]),
                    "target_pose_lookup_success": lookup is not None,
                    "fallback_used": bool(fallback_used),
                    "fallback_reason": fallback_reason,
                })

                start_last_known = known_ratio_after
                start_steps += 1
                if known_ratio_after >= 0.95:
                    start_stop_reason = "coverage_saturated"
                    break
                if failure_reason:
                    start_stop_reason = failure_reason
                    break

            bev.save_ascii(dirs["maps"] / f"start_{start_id:03d}_final_bev_ascii.txt")
            start_group = [r for r in rows if int(r["start_id"]) == start_id]
            final_known = float(start_group[-1]["known_ratio_after"]) if start_group else start_initial_known
            start_rows.append({
                "start_id": start_id,
                "planned_start_x": start["x"],
                "planned_start_y": start["y"],
                "planned_start_z": start["z"],
                "planned_start_yaw": start["yaw"],
                "action_count": len(start_group),
                "failure_count": sum(1 for r in start_group if r["failure_reason"]),
                "final_known_ratio": round(final_known, 6),
                "known_ratio_gain": round(final_known - start_initial_known, 6),
                "stop_reason": start_stop_reason,
            })

        if not rows:
            raise RuntimeError("No rollout steps were collected")

        write_csv(steps_csv, rows, ROLLOUT_STEP_FIELDS)
        write_csv(candidates_csv, candidate_rows_all, CANDIDATE_FIELDS)
        write_csv(start_summary_csv, start_rows, list(start_rows[0].keys()))
        write_jsonl(samples_jsonl, samples)
        write_jsonl(command_log, command_rows)
        write_jsonl(parse_log, parse_rows)
        plots_saved = save_plots(run_dir, rows, start_rows)

        completed_start_count = sum(1 for r in start_rows if int(r["action_count"]) >= 2)
        starts_with_failures = sum(1 for r in start_rows if int(r["failure_count"]) > 0)
        parse_success = sum(1 for r in rows if bool(r["parse_success"]))
        validation_success = sum(1 for r in rows if bool(r["validation_success"]))
        movement_success = sum(1 for r in rows if bool(r["movement_success"]))
        rgb_available_count = sum(1 for r in rows if bool(r["rgb_available"]))
        depth_available_count = sum(1 for r in rows if bool(r["depth_available"]))
        camera_pointcloud_available_count = sum(1 for r in rows if bool(r["camera_pointcloud_available"]))
        collision_count = sum(1 for r in rows if bool(r["collision_flag"]))
        stuck_count = sum(1 for r in rows if bool(r["stuck_flag"]))
        falling_count = sum(1 for r in rows if bool(r["falling_flag"]))
        core_files = find_core_dumps(WORKSPACE)
        final_known = [float(r["final_known_ratio"]) for r in start_rows]
        known_gains = [float(r["known_ratio_gain"]) for r in start_rows]
        movement_rate = rate(movement_success, len(rows))
        pass_ok = bool(
            summary.get("scene_open_result")
            and summary.get("a1_root_exists")
            and summary["geometry_proxy_used"] is False
            and summary["mounted_geometry_proxy_used"] is False
            and int(args.start_count) >= 10
            and len(start_rows) >= 10
            and completed_start_count >= 10
            and len(rows) >= 20
            and samples
            and len(candidate_rows_all) >= len(rows) * 16
            and rate(parse_success, len(rows)) >= 0.99
            and rate(validation_success, len(rows)) >= 0.95
            and movement_rate >= 0.8
            and rate(rgb_available_count, len(rows)) >= 0.95
            and rate(depth_available_count, len(rows)) >= 0.99
            and rate(camera_pointcloud_available_count, len(rows)) >= 0.99
            and all(str(r["target_language"]).startswith("Go to candidate ") for r in rows)
            and collision_count == 0
            and stuck_count == 0
            and falling_count == 0
            and not core_files
        )

        manifest = {
            "dataset_name": "a1_vlm_la_real_sensor_rollout_v0",
            "sample_format": "vlm_la_jsonl",
            "sample_file": "samples/vlm_la_samples.jsonl",
            "robot_platform": ROBOT_PLATFORM,
            "sensor_method": SENSOR_METHOD,
            "label_source": LABEL_SOURCE,
            "output_contract": OUTPUT_CONTRACT,
            "training_ready": False,
            "requires_human_review": True,
            "sample_count": len(samples),
        }
        manifest_json.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

        summary.update({
            "completed_start_count": completed_start_count,
            "total_action_count": len(rows),
            "total_step_rows": len(rows),
            "candidate_rows": len(candidate_rows_all),
            "vlm_la_sample_count": len(samples),
            "average_final_known_ratio": mean(final_known),
            "average_known_ratio_gain": mean(known_gains),
            "parse_success_rate": rate(parse_success, len(rows)),
            "validation_success_rate": rate(validation_success, len(rows)),
            "movement_success_rate": movement_rate,
            "starts_with_failures": starts_with_failures,
            "collision_count": collision_count,
            "stuck_count": stuck_count,
            "falling_count": falling_count,
            "real_rgb_sensor_available": rgb_available_count > 0,
            "real_depth_sensor_available": depth_available_count > 0,
            "real_camera_pointcloud_available": camera_pointcloud_available_count > 0,
            "real_rgb_sensor_valid_rate": rate(rgb_available_count, len(rows)),
            "real_depth_sensor_valid_rate": rate(depth_available_count, len(rows)),
            "real_camera_pointcloud_valid_rate": rate(camera_pointcloud_available_count, len(rows)),
            "training_started": False,
            "RL_started": False,
            "map_predict_started": False,
            "checkpoint_created": False,
            "plots_saved": bool(plots_saved),
            "core_dump_found": bool(core_files),
            "core_dump_files": core_files,
            "dataset_manifest_path": str(manifest_json),
            "vlm_la_samples_path": str(samples_jsonl),
            "rollout_summary_path": str(summary_json),
            "candidate_summary_path": str(candidates_csv),
            "rollout_steps_csv": str(steps_csv),
            "start_summary_csv": str(start_summary_csv),
            "command_log_jsonl": str(command_log),
            "parse_log_jsonl": str(parse_log),
            "plots_path": str(dirs["plots"]),
            "safe_to_continue_phase9": pass_ok,
            "caveats": [
                "Pseudo VLM commands are generated by the classical selector; no real VLM inference was run.",
                "A1 movement uses kinematic root updates; no A1 locomotion controller was trained or used.",
                "Samples are prototypes and require Phase 9 human review before any training use.",
                "Debug RGB-D and BEV images are kept in the ignored run directory and are not committed.",
            ],
        })
        exit_code = 0 if pass_ok else 2
    except Exception as exc:
        summary["exception"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
        exit_code = 1
    finally:
        summary["elapsed_sec"] = round(time.time() - started, 3)
        summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        write_report(report, summary)
        write_report(Path(args.top_report).expanduser().resolve(), summary)
        if app is not None:
            try:
                app.close()
            except Exception as exc:
                print(f"simulation_app.close failed: {exc!r}", file=sys.stderr)

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
