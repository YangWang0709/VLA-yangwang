#!/usr/bin/env python3
"""Phase 7 A1 VLM-LA closed-loop smoke.

This short smoke opens the primary USD, uses the existing /World/A1 prim,
captures real Isaac/Omniverse RGB-D observations, updates a BEV map from
depth-backprojected pointclouds, generates online candidate viewpoints, emits
pseudo VLM commands, parses/validates them, performs a kinematic A1 root move,
and updates the map again. It does not run real VLM inference, train, run a
long rollout, use geometry proxies, or save/overwrite the USD scene.
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

from phase4r_a1_real_sensor_mapping_smoke import (  # noqa: E402
    RealSensorBevMap,
    camera_points_to_world,
)
from phase5r_a1_real_sensor_candidate_gain_smoke import (  # noqa: E402
    CANDIDATE_SAMPLING_METHOD,
    INFORMATION_GAIN_METHOD,
    MAP_TYPE,
    MAPPING_METHOD,
    MAP_UPDATE_SOURCE,
    PATH_COST_METHOD,
    SCORE_FORMULA,
    angle_wrap,
    render_candidate_overlay,
    score_candidates,
)
from phase6_vlm_la_interface_smoke import (  # noqa: E402
    candidate_key,
    parse_language_command,
    target_pose,
    validate_candidate_id,
)
from phase56_a1_real_sensor_suite_smoke import (  # noqa: E402
    A1_ROOT,
    BASE_FRAME,
    CAMERA_PATH,
    LIDAR_PATH,
    MOUNT_RPY,
    SCENE,
    attach_camera_annotators,
    bool_text,
    create_runtime_prims,
    depth_stats,
    expected_sensor_pose,
    find_core_dumps,
    intrinsics_from_camera_params,
    lidar_stats,
    pointcloud_from_depth,
    pointcloud_stats,
    rgb_stats,
    save_depth_vis,
    save_rgb_png,
    segmentation_available,
    set_root_pose,
    set_world_look_at,
    set_world_translate,
    try_create_lidar,
    world_translation,
)


PHASE = "Phase 7 A1 VLM-LA closed-loop smoke"
TOP_REPORT = WORKSPACE / "runs/A1_VLM_LA_CLOSED_LOOP_SMOKE_REPORT.md"
PROJECT_NAME = "A1-VLM-LA Explorer"
MAIN_GOAL = "A1-VLM-LA Explorer for 3D Active Exploration"
SENSOR_METHOD = "real_isaac_omniverse_rgbd"
CAMERA_POINTCLOUD_SOURCE = "depth_backprojection"
OUTPUT_CONTRACT = "Go to candidate <id>."
MOVEMENT_MODE = "kinematic_existing_a1_root"
VLM_OUTPUT_MODE = "pseudo_from_classical_selector"
CANDIDATE_DATA_SOURCE = "online_real_sensor_candidate_generation"


def rate(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def candidate_index_for_step(step_id: int, rows: list[dict[str, Any]]) -> dict[tuple[int, int], dict[str, Any]]:
    indexed = {}
    for row in rows:
        indexed[candidate_key(step_id, int(row["candidate_id"]))] = row
    return indexed


def selected_candidate(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    selected = [r for r in rows if bool(r.get("selected_by_classical"))]
    return selected[0] if selected else None


def observation_failure(
    rgb: dict[str, Any],
    depth: dict[str, Any],
    camera_params_available: bool,
    intrinsics_available: bool,
    pc: dict[str, Any],
    pc_source: str,
    camera_follows: bool,
) -> str:
    if not camera_follows:
        return "camera_not_synced_to_a1_base"
    if not rgb["available"]:
        return "rgb_invalid"
    if not depth["available"]:
        return "depth_invalid"
    if not camera_params_available:
        return "camera_params_unavailable"
    if not intrinsics_available:
        return "camera_intrinsics_unavailable"
    if not pc["available"]:
        return "depth_backprojection_pointcloud_invalid"
    if pc_source != CAMERA_POINTCLOUD_SOURCE:
        return "camera_pointcloud_source_invalid"
    return ""


def capture_observation(
    app,
    rep,
    stage,
    camera_prim,
    light_prim,
    camera_annotators: dict[str, Any],
    lidar_annotator,
    base_pose: tuple[float, float, float, float],
    bev: RealSensorBevMap,
) -> dict[str, Any]:
    from pxr import UsdGeom

    base_x, base_y, base_z, yaw = base_pose
    eye, target = expected_sensor_pose(base_x, base_y, base_z, yaw)
    set_world_look_at(camera_prim, eye, target)
    if light_prim and light_prim.IsValid():
        set_world_translate(light_prim, (base_x, base_y, base_z + 2.5))
    lidar_prim = stage.GetPrimAtPath(LIDAR_PATH)
    if lidar_prim and lidar_prim.IsValid():
        set_world_look_at(lidar_prim, eye, target)

    for _ in range(3):
        app.update()
        try:
            rep.orchestrator.step()
        except Exception:
            pass
        app.update()

    cache = UsdGeom.XformCache()
    camera_x, camera_y, camera_z = world_translation(cache, camera_prim)
    camera_error = math.sqrt((camera_x - eye[0]) ** 2 + (camera_y - eye[1]) ** 2 + (camera_z - eye[2]) ** 2)
    camera_follows = camera_error < 0.02

    rgb = rgb_stats(camera_annotators["rgb"].get_data())
    depth = depth_stats(camera_annotators["distance_to_image_plane"].get_data())
    camera_params_data = camera_annotators["camera_params"].get_data()
    camera_params_available = isinstance(camera_params_data, dict) and bool(camera_params_data)
    intrinsics_available, intrinsics = intrinsics_from_camera_params(
        camera_params_data,
        depth["width"] or 320,
        depth["height"] or 240,
    )
    if depth["available"] and intrinsics_available:
        camera_points = pointcloud_from_depth(depth["array"], intrinsics)
        world_points = camera_points_to_world(camera_points, eye, target)
        pc = pointcloud_stats(camera_points)
        pc_source = CAMERA_POINTCLOUD_SOURCE
    else:
        camera_points = np.empty((0, 3), dtype=np.float32)
        world_points = np.empty((0, 3), dtype=np.float32)
        pc = pointcloud_stats(camera_points)
        pc_source = "unavailable"

    semantic_available = False
    instance_available = False
    if "semantic_segmentation" in camera_annotators:
        try:
            semantic_available = segmentation_available(camera_annotators["semantic_segmentation"].get_data())
        except Exception:
            semantic_available = False
    if "instance_segmentation" in camera_annotators:
        try:
            instance_available = segmentation_available(camera_annotators["instance_segmentation"].get_data())
        except Exception:
            instance_available = False

    lidar_available = False
    lidar_point_count = 0
    if lidar_annotator is not None:
        try:
            stats = lidar_stats(lidar_annotator.get_data())
            lidar_available = bool(stats["available"])
            lidar_point_count = int(stats["point_count"])
        except Exception:
            lidar_available = False

    map_stats = bev.update(base_x, base_y, yaw, camera_x, camera_y, camera_z, world_points)
    failure = observation_failure(rgb, depth, camera_params_available, intrinsics_available, pc, pc_source, camera_follows)
    return {
        "base_pose": {"x": base_x, "y": base_y, "z": base_z, "yaw": yaw},
        "sensor_pose": {"x": camera_x, "y": camera_y, "z": camera_z, "yaw": yaw, "pitch": MOUNT_RPY[1]},
        "rgb": rgb,
        "depth": depth,
        "camera_params_available": camera_params_available,
        "camera_intrinsics_available": intrinsics_available,
        "camera_pointcloud": pc,
        "camera_pointcloud_source": pc_source,
        "semantic_available": semantic_available,
        "instance_available": instance_available,
        "lidar_available": lidar_available,
        "lidar_point_count": lidar_point_count,
        "camera_follows_base": camera_follows,
        "map_stats": map_stats,
        "failure_reason": failure,
    }


def move_a1_kinematic(
    root_prim,
    initial_orient,
    current_root: tuple[float, float, float],
    current_base: tuple[float, float, float],
    target: dict[str, float],
) -> tuple[tuple[float, float, float], float]:
    dx = float(target["x"]) - current_base[0]
    dy = float(target["y"]) - current_base[1]
    new_root = (current_root[0] + dx, current_root[1] + dy, current_root[2])
    target_yaw = float(target["yaw"])
    set_root_pose(root_prim, new_root, target_yaw, initial_orient)
    return new_root, target_yaw


def save_plots(run_dir: Path, bev: RealSensorBevMap, rows: list[dict[str, Any]], selected_scores: list[float]) -> bool:
    plots_dir = run_dir / "plots"
    maps_dir = run_dir / "maps"
    plots_dir.mkdir(parents=True, exist_ok=True)
    maps_dir.mkdir(parents=True, exist_ok=True)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        with (plots_dir / "known_ratio_curve.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["step_id", "known_ratio_after"])
            writer.writeheader()
            writer.writerows({"step_id": r["step_id"], "known_ratio_after": r["known_ratio_after"]} for r in rows)
        with (plots_dir / "robot_xy_trace.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["step_id", "post_base_x", "post_base_y"])
            writer.writeheader()
            writer.writerows({"step_id": r["step_id"], "post_base_x": r["post_base_x"], "post_base_y": r["post_base_y"]} for r in rows)
        bev.save_ascii(maps_dir / "final_bev_ascii.txt")
        return False

    steps = [int(r["step_id"]) for r in rows]
    plt.figure(figsize=(6, 4))
    plt.plot(steps, [float(r["known_ratio_after"]) for r in rows], marker="o")
    plt.xlabel("step")
    plt.ylabel("known ratio")
    plt.title("Phase 7 known ratio")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / "known_ratio_curve.png", dpi=120)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.plot(steps, selected_scores, marker="o")
    plt.xlabel("step")
    plt.ylabel("selected score")
    plt.title("Selected candidate score")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / "selected_candidate_scores.png", dpi=120)
    plt.close()

    plt.figure(figsize=(5, 5))
    plt.plot([float(r["post_base_x"]) for r in rows], [float(r["post_base_y"]) for r in rows], marker="o", label="A1")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("A1 XY trace")
    plt.axis("equal")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_dir / "robot_xy_trace.png", dpi=120)
    plt.close()

    cmap = matplotlib.colors.ListedColormap(["#222222", "#d7f0d0", "#c23b22"])
    plt.figure(figsize=(6, 6))
    plt.imshow(bev.grid, origin="lower", cmap=cmap, interpolation="nearest")
    plt.title("Final BEV map")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(plots_dir / "final_bev_map.png", dpi=120)
    plt.close()
    bev.save_ascii(maps_dir / "final_bev_ascii.txt")
    return True


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# A1 VLM-LA Closed Loop Smoke Report",
        "",
        "phase: Phase 7",
        "workspace: /home/ubuntu22/VLA",
        f"project_name: {PROJECT_NAME}",
        f"scene_path: {summary.get('scene_path')}",
        "robot_platform: unitree_a1",
        "robot_source: existing_usd_prim",
        "a1_root_prim: /World/A1",
        "base_frame: /World/A1/base",
        f"sensor_method: {SENSOR_METHOD}",
        f"camera_pointcloud_source: {summary.get('camera_pointcloud_source')}",
        f"geometry_proxy_used: {bool_text(summary.get('geometry_proxy_used'))}",
        f"mounted_geometry_proxy_used: {bool_text(summary.get('mounted_geometry_proxy_used'))}",
        f"movement_mode: {MOVEMENT_MODE}",
        "real_a1_locomotion_controller: false",
        f"real_vlm_inference: {bool_text(summary.get('real_vlm_inference'))}",
        f"vlm_output_mode: {VLM_OUTPUT_MODE}",
        f"output_contract: {OUTPUT_CONTRACT}",
        f"action_count: {summary.get('action_count')}",
        f"successful_action_count: {summary.get('successful_action_count')}",
        f"parse_success_rate: {summary.get('parse_success_rate')}",
        f"validation_success_rate: {summary.get('validation_success_rate')}",
        f"target_pose_lookup_success_rate: {summary.get('target_pose_lookup_success_rate')}",
        f"movement_success_rate: {summary.get('movement_success_rate')}",
        f"fallback_count: {summary.get('fallback_count')}",
        f"initial_known_ratio: {summary.get('initial_known_ratio')}",
        f"final_known_ratio: {summary.get('final_known_ratio')}",
        f"total_known_ratio_gain: {summary.get('total_known_ratio_gain')}",
        f"known_ratio_monotonic_non_decreasing: {bool_text(summary.get('known_ratio_monotonic_non_decreasing'))}",
        f"average_candidate_count: {summary.get('average_candidate_count')}",
        f"average_valid_candidate_count: {summary.get('average_valid_candidate_count')}",
        f"collision_count: {summary.get('collision_count')}",
        f"stuck_count: {summary.get('stuck_count')}",
        f"falling_count: {summary.get('falling_count')}",
        f"failure_count: {summary.get('failure_count')}",
        f"plots path: {summary.get('plots_path')}",
        f"summary path: {summary.get('summary_json')}",
        f"safe_to_continue_phase8: {bool_text(summary.get('safe_to_continue_phase8'))}",
        f"caveats: {summary.get('caveats')}",
        "training: false",
        "RL: false",
        "map_predict: false",
        "PI_finetuning: false",
        "A1_locomotion_training: false",
        "long_rollout_started: false",
        "",
        "## Evidence",
        "",
        f"- run_dir: {summary.get('run_dir')}",
        f"- closed_loop_steps_csv: {summary.get('closed_loop_steps_csv')}",
        f"- command_log_jsonl: {summary.get('command_log_jsonl')}",
        f"- parse_log_jsonl: {summary.get('parse_log_jsonl')}",
        "- Candidate generation and scoring were online from the current real-sensor BEV map.",
        "- Commands were pseudo VLM outputs created from the classical selector.",
        "- The original USD scene was not saved or overwritten.",
        "",
        "## Negative Scope",
        "",
        "- No Phase 8.",
        "- No long rollout.",
        "- No training, RL, map_predict, checkpoint, or real VLM inference.",
        "- No geometry proxy or mounted geometry proxy.",
        "- No Go2 label is used as the actual robot platform.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_summary(usd: Path, run_dir: Path) -> dict[str, Any]:
    return {
        "phase": PHASE,
        "workspace": str(WORKSPACE),
        "project_name": PROJECT_NAME,
        "main_goal": MAIN_GOAL,
        "scene_path": str(usd),
        "scene_exists": usd.exists(),
        "robot_platform": "unitree_a1",
        "robot_source": "existing_usd_prim",
        "a1_root_prim": A1_ROOT,
        "base_frame": BASE_FRAME,
        "sensor_method": SENSOR_METHOD,
        "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE,
        "geometry_proxy_used": False,
        "mounted_geometry_proxy_used": False,
        "movement_mode": MOVEMENT_MODE,
        "real_a1_locomotion_controller": False,
        "real_vlm_inference": False,
        "vlm_output_mode": VLM_OUTPUT_MODE,
        "output_contract": OUTPUT_CONTRACT,
        "map_type": MAP_TYPE,
        "mapping_method": MAPPING_METHOD,
        "map_update_source": MAP_UPDATE_SOURCE,
        "candidate_data_source": CANDIDATE_DATA_SOURCE,
        "candidate_sampling_method": CANDIDATE_SAMPLING_METHOD,
        "path_cost_method": PATH_COST_METHOD,
        "information_gain_method": INFORMATION_GAIN_METHOD,
        "score_formula": SCORE_FORMULA,
        "training_started": False,
        "RL_started": False,
        "map_predict_started": False,
        "checkpoint_created": False,
        "long_rollout_started": False,
        "run_dir": str(run_dir),
        "safe_to_continue_phase8": False,
        "exception": None,
        "traceback": None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", default=str(SCENE))
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--top_report", default=str(TOP_REPORT))
    parser.add_argument("--actions", type=int, default=5)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--map_resolution_m", type=float, default=0.1)
    args = parser.parse_args()

    usd = Path(args.usd).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser().resolve()
    dirs = {
        "logs": run_dir / "logs",
        "closed_loop": run_dir / "closed_loop",
        "commands": run_dir / "commands",
        "parsing": run_dir / "parsing",
        "maps": run_dir / "maps",
        "candidates": run_dir / "candidates",
        "plots": run_dir / "plots",
        "reports": run_dir / "reports",
        "summary": run_dir / "summary",
        "debug_frames": run_dir / "debug_frames",
    }
    for directory in dirs.values():
        directory.mkdir(parents=True, exist_ok=True)

    summary = build_summary(usd, run_dir)
    steps_csv = dirs["summary"] / "closed_loop_steps.csv"
    summary_json = dirs["summary"] / "closed_loop_summary.json"
    command_log = dirs["commands"] / "command_log.jsonl"
    parse_log = dirs["parsing"] / "parse_log.jsonl"
    report = dirs["reports"] / "A1_VLM_LA_CLOSED_LOOP_SMOKE_REPORT.md"
    app = None
    rows: list[dict[str, Any]] = []
    command_rows: list[dict[str, Any]] = []
    parse_rows: list[dict[str, Any]] = []
    selected_scores: list[float] = []
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
        root_xyz = world_translation(cache, root)
        base_xyz = world_translation(cache, base)
        summary["initial_root_pose_xyz"] = [round(v, 6) for v in root_xyz]
        summary["initial_base_pose_xyz"] = [round(v, 6) for v in base_xyz]
        summary["base_pose_readable"] = True
        ops = {op.GetName(): op for op in UsdGeom.Xformable(root).GetOrderedXformOps()}
        initial_orient = ops["xformOp:orient"].Get() if "xformOp:orient" in ops else None
        yaw = 0.0

        eye, target = expected_sensor_pose(base_xyz[0], base_xyz[1], base_xyz[2], yaw)
        set_world_look_at(camera_prim, eye, target)
        if light_prim and light_prim.IsValid():
            set_world_translate(light_prim, (base_xyz[0], base_xyz[1], base_xyz[2] + 2.5))
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

        bev = RealSensorBevMap(base_xyz[0], base_xyz[1], resolution_m=float(args.map_resolution_m))
        initial_known_ratio = 0.0
        last_known_ratio = initial_known_ratio
        action_count = max(5, min(int(args.actions), 8))
        first_rgb = last_rgb = first_depth = last_depth = None

        for step_id in range(action_count):
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
            if step_id == 0:
                first_rgb = pre_obs["rgb"]["array"]
                first_depth = pre_obs["depth"]["array"]
            last_rgb = pre_obs["rgb"]["array"]
            last_depth = pre_obs["depth"]["array"]
            known_ratio_before = float(pre_obs["map_stats"]["known_ratio"])

            base_pose = {"x": pre_base[0], "y": pre_base[1], "z": pre_base[2], "yaw": pre_yaw}
            candidate_rows = score_candidates(bev, base_pose)
            for candidate in candidate_rows:
                candidate["step_id"] = step_id
            chosen = selected_candidate(candidate_rows)
            fallback_used = False
            fallback_reason = None
            if chosen is None:
                fallback_used = True
                fallback_reason = "no_valid_positive_gain_candidate"
                candidate_rows = sorted(candidate_rows, key=lambda r: float(r["score"]), reverse=True)
                chosen = candidate_rows[0] if candidate_rows else None
            if chosen is None:
                raise RuntimeError(f"no candidates generated at step {step_id}")
            selected_id = int(chosen["candidate_id"])
            pseudo_command = f"Go to candidate {selected_id}."

            indexed = candidate_index_for_step(step_id, candidate_rows)
            parsed = parse_language_command(pseudo_command)
            validation = validate_candidate_id(parsed["selected_candidate_id"], step_id, indexed)
            lookup = target_pose(indexed.get(candidate_key(step_id, int(parsed["selected_candidate_id"])))) if parsed["parse_success"] else None
            if not (parsed["parse_success"] and validation["valid"] and lookup):
                fallback_used = True
                fallback_reason = parsed["error"] or validation["reason"] or "target_pose_lookup_failed"
                lookup = target_pose(chosen)
                parsed["selected_candidate_id"] = selected_id

            render_candidate_overlay(
                bev,
                step_id,
                base_pose,
                (pre_obs["sensor_pose"]["x"], pre_obs["sensor_pose"]["y"], pre_obs["sensor_pose"]["z"]),
                candidate_rows,
                dirs["plots"] / f"candidate_overlay_step_{step_id:03d}.png",
            )
            with (dirs["candidates"] / f"candidate_step_{step_id:03d}.csv").open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(candidate_rows[0].keys()), extrasaction="ignore")
                writer.writeheader()
                writer.writerows(candidate_rows)

            pre_root = root_xyz
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
            last_rgb = post_obs["rgb"]["array"]
            last_depth = post_obs["depth"]["array"]

            known_ratio_after = float(post_obs["map_stats"]["known_ratio"])
            distance_to_target = math.hypot(post_base[0] - lookup["x"], post_base[1] - lookup["y"])
            moved_distance = math.hypot(post_base[0] - pre_base[0], post_base[1] - pre_base[1])
            movement_success = distance_to_target <= 0.35 and moved_distance > 0.02
            collision_flag = bool(chosen.get("collision_risk")) or not bool(chosen.get("is_valid"))
            stuck_flag = moved_distance < 0.02
            falling_flag = post_base[2] < 0.2 or post_base[2] > 1.5 or abs(post_base[2] - base_xyz[2]) > 0.6
            failure_reason = ""
            if pre_obs["failure_reason"]:
                failure_reason = f"pre_{pre_obs['failure_reason']}"
            elif post_obs["failure_reason"]:
                failure_reason = f"post_{post_obs['failure_reason']}"
            elif not parsed["parse_success"]:
                failure_reason = "parse_failed"
            elif not validation["valid"]:
                failure_reason = validation["reason"]
            elif lookup is None:
                failure_reason = "target_pose_lookup_failed"
            elif not movement_success:
                failure_reason = "movement_not_within_target_tolerance"
            elif collision_flag:
                failure_reason = "selected_candidate_collision_or_invalid"
            elif stuck_flag:
                failure_reason = "a1_base_pose_did_not_move"
            elif falling_flag:
                failure_reason = "a1_base_z_out_of_expected_range"

            selected_scores.append(float(chosen["score"]))
            row = {
                "step_id": step_id,
                "timestamp": round(time.time(), 3),
                "a1_root_prim": A1_ROOT,
                "base_frame": BASE_FRAME,
                "pre_base_x": round(pre_base[0], 4),
                "pre_base_y": round(pre_base[1], 4),
                "pre_base_z": round(pre_base[2], 4),
                "pre_base_yaw": round(pre_yaw, 4),
                "post_base_x": round(post_base[0], 4),
                "post_base_y": round(post_base[1], 4),
                "post_base_z": round(post_base[2], 4),
                "post_base_yaw": round(yaw, 4),
                "sensor_method": SENSOR_METHOD,
                "rgb_available": bool(pre_obs["rgb"]["available"] and post_obs["rgb"]["available"]),
                "depth_available": bool(pre_obs["depth"]["available"] and post_obs["depth"]["available"]),
                "camera_pointcloud_available": bool(pre_obs["camera_pointcloud"]["available"] and post_obs["camera_pointcloud"]["available"]),
                "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE,
                "known_ratio_before": round(known_ratio_before, 6),
                "known_ratio_after": round(known_ratio_after, 6),
                "known_ratio_delta": round(known_ratio_after - last_known_ratio, 6),
                "occupied_cells": int(post_obs["map_stats"]["occupied_cells"]),
                "known_free_cells": int(post_obs["map_stats"]["known_free_cells"]),
                "unknown_cells": int(post_obs["map_stats"]["unknown_cells"]),
                "candidate_count": len(candidate_rows),
                "valid_candidate_count": sum(1 for r in candidate_rows if bool(r.get("is_valid")) and bool(r.get("is_reachable"))),
                "positive_gain_candidate_count": sum(1 for r in candidate_rows if int(r.get("information_gain", 0)) > 0),
                "selected_candidate_id": selected_id,
                "selected_score": round(float(chosen["score"]), 4),
                "selected_information_gain": int(chosen["information_gain"]),
                "selected_path_cost": chosen["path_cost"],
                "pseudo_vlm_command": pseudo_command,
                "parse_success": bool(parsed["parse_success"]),
                "parsed_candidate_id": parsed["selected_candidate_id"],
                "validation_success": bool(validation["valid"]),
                "target_x": round(float(lookup["x"]), 4) if lookup else None,
                "target_y": round(float(lookup["y"]), 4) if lookup else None,
                "target_z": round(float(lookup["z"]), 4) if lookup else None,
                "target_yaw": round(float(lookup["yaw"]), 4) if lookup else None,
                "movement_success": bool(movement_success),
                "distance_to_target_after_move": round(distance_to_target, 4),
                "fallback_used": bool(fallback_used),
                "fallback_reason": fallback_reason,
                "collision_flag": bool(collision_flag),
                "stuck_flag": bool(stuck_flag),
                "falling_flag": bool(falling_flag),
                "failure_reason": failure_reason,
            }
            rows.append(row)
            command_rows.append({
                "step_id": step_id,
                "candidate_data_source": CANDIDATE_DATA_SOURCE,
                "selected_candidate_id": selected_id,
                "pseudo_vlm_command": pseudo_command,
                "output_contract": OUTPUT_CONTRACT,
                "real_vlm_inference": False,
                "training": False,
            })
            parse_rows.append({
                "step_id": step_id,
                "input_command": pseudo_command,
                "parse_success": bool(parsed["parse_success"]),
                "parsed_candidate_id": parsed["selected_candidate_id"],
                "candidate_exists": bool(validation["exists"]),
                "candidate_valid": bool(validation["is_valid_candidate"]),
                "candidate_reachable": bool(validation["is_reachable"]),
                "target_pose_lookup_success": lookup is not None,
                "fallback_used": bool(fallback_used),
                "fallback_reason": fallback_reason,
            })
            last_known_ratio = known_ratio_after

        with steps_csv.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        write_jsonl(command_log, command_rows)
        write_jsonl(parse_log, parse_rows)

        for name, array, saver in [
            ("first_rgb.png", first_rgb, save_rgb_png),
            ("last_rgb.png", last_rgb, save_rgb_png),
            ("first_depth_vis.png", first_depth, save_depth_vis),
            ("last_depth_vis.png", last_depth, save_depth_vis),
        ]:
            saver(array, dirs["debug_frames"] / name)
        plots_saved = save_plots(run_dir, bev, rows, selected_scores)
        core_files = find_core_dumps(WORKSPACE)

        success_rows = [r for r in rows if not r["failure_reason"]]
        parse_success = [r for r in rows if r["parse_success"]]
        validation_success = [r for r in rows if r["validation_success"]]
        lookup_success = [r for r in rows if r["target_x"] is not None]
        movement_success = [r for r in rows if r["movement_success"]]
        collision_count = sum(1 for r in rows if r["collision_flag"])
        stuck_count = sum(1 for r in rows if r["stuck_flag"])
        falling_count = sum(1 for r in rows if r["falling_flag"])
        known_after = [float(r["known_ratio_after"]) for r in rows]
        monotonic = all(known_after[i] + 1e-6 >= known_after[i - 1] for i in range(1, len(known_after)))
        final_known_ratio = known_after[-1] if known_after else initial_known_ratio
        pass_ok = bool(
            summary["scene_open_result"]
            and summary["a1_root_exists"]
            and len(rows) >= 5
            and len(success_rows) >= 5
            and min(int(r["candidate_count"]) for r in rows) >= 16
            and len(parse_success) == len(rows)
            and len(validation_success) == len(rows)
            and len(lookup_success) == len(rows)
            and rate(len(movement_success), len(rows)) >= 0.8
            and final_known_ratio > initial_known_ratio
            and collision_count == 0
            and stuck_count == 0
            and falling_count == 0
            and not core_files
            and summary["geometry_proxy_used"] is False
            and summary["mounted_geometry_proxy_used"] is False
            and all(r["pseudo_vlm_command"].startswith("Go to candidate ") for r in rows)
        )
        summary.update({
            "action_count": len(rows),
            "successful_action_count": len(success_rows),
            "parse_success_rate": rate(len(parse_success), len(rows)),
            "validation_success_rate": rate(len(validation_success), len(rows)),
            "target_pose_lookup_success_rate": rate(len(lookup_success), len(rows)),
            "movement_success_rate": rate(len(movement_success), len(rows)),
            "fallback_count": sum(1 for r in rows if r["fallback_used"]),
            "initial_known_ratio": round(initial_known_ratio, 6),
            "final_known_ratio": round(final_known_ratio, 6),
            "total_known_ratio_gain": round(final_known_ratio - initial_known_ratio, 6),
            "known_ratio_monotonic_non_decreasing": monotonic,
            "average_candidate_count": round(sum(int(r["candidate_count"]) for r in rows) / len(rows), 4),
            "average_valid_candidate_count": round(sum(int(r["valid_candidate_count"]) for r in rows) / len(rows), 4),
            "collision_count": collision_count,
            "stuck_count": stuck_count,
            "falling_count": falling_count,
            "failure_count": len(rows) - len(success_rows),
            "real_rgb_sensor_available": all(bool(r["rgb_available"]) for r in rows),
            "real_depth_sensor_available": all(bool(r["depth_available"]) for r in rows),
            "real_camera_pointcloud_available": all(bool(r["camera_pointcloud_available"]) for r in rows),
            "plots_saved": bool(plots_saved),
            "plots_path": str(dirs["plots"]),
            "summary_json": str(summary_json),
            "closed_loop_steps_csv": str(steps_csv),
            "command_log_jsonl": str(command_log),
            "parse_log_jsonl": str(parse_log),
            "core_dump_found": bool(core_files),
            "core_dump_files": core_files,
            "safe_to_continue_phase8": pass_ok,
            "caveats": [
                "This is a short closed-loop smoke, not a long rollout.",
                "VLM outputs are pseudo commands generated from the classical selector.",
                "Movement uses kinematic root updates; no A1 locomotion controller is trained or used.",
                "BEV mapping uses depth-backprojected real RGB-D pointclouds only.",
                "Runtime sensors and light are in-memory; the primary USD is not saved.",
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
