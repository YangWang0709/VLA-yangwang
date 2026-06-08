#!/usr/bin/env python3
"""MapPredict Phase 1 Route B: USD bounds voxelization prototype.

This script intentionally implements a conservative prototype. It voxelizes
world-space bounds for Mesh/Cube prims inside the same grid produced by Route A.
The result is not exact mesh GT; it is a bbox occupancy prototype for auditing
USD-based GT feasibility.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

import numpy as np


WORKSPACE = Path("/home/ubuntu22/VLA")
RUNS_DIR = WORKSPACE / "runs"
DATA_ROOT = WORKSPACE / "data/map_predict/full_occupancy_gt"
TOP_REPORT = RUNS_DIR / "MAP_PREDICT_PHASE1_FULL_OCCUPANCY_GT_REPORT.md"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def latest_run_dir() -> Path:
    matches = sorted(RUNS_DIR.glob("map_predict_phase1_full_occupancy_gt_*"))
    if not matches:
        raise FileNotFoundError("No map_predict_phase1_full_occupancy_gt_* run directory found")
    return matches[-1]


def grid_meta(scene: dict[str, Any]) -> tuple[np.ndarray, float, tuple[int, int, int]]:
    origin = np.asarray(scene["origin_xyz"], dtype=np.float32)
    voxel_size = float(scene["voxel_size"])
    shape = tuple(int(v) for v in scene["grid_shape"])
    return origin, voxel_size, shape


def bbox_indices(min_pt, max_pt, origin: np.ndarray, voxel_size: float, shape: tuple[int, int, int]) -> tuple[slice, slice, slice] | None:
    mn = np.floor((np.asarray(min_pt, dtype=np.float32) - origin) / voxel_size).astype(np.int32)
    mx = np.ceil((np.asarray(max_pt, dtype=np.float32) - origin) / voxel_size).astype(np.int32)
    d, h, w = shape
    ix0, iy0, iz0 = int(mn[0]), int(mn[1]), int(mn[2])
    ix1, iy1, iz1 = int(mx[0]), int(mx[1]), int(mx[2])
    ix0, iy0, iz0 = max(0, ix0), max(0, iy0), max(0, iz0)
    ix1, iy1, iz1 = min(w, ix1), min(h, iy1), min(d, iz1)
    if ix1 <= ix0 or iy1 <= iy0 or iz1 <= iz0:
        return None
    return slice(iz0, iz1), slice(iy0, iy1), slice(ix0, ix1)


def voxelize_scene_bounds(scene: dict[str, Any], max_prims: int) -> dict[str, Any]:
    from pxr import Gf, Usd, UsdGeom

    origin, voxel_size, shape = grid_meta(scene)
    occupancy = np.zeros(shape, dtype=np.uint8)
    stage = Usd.Stage.Open(scene["scene_path"])
    if stage is None:
        raise RuntimeError("Usd.Stage.Open returned None")
    bbox_cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), [UsdGeom.Tokens.default_, UsdGeom.Tokens.render, UsdGeom.Tokens.proxy])
    supported_types = {"Mesh", "Cube"}
    unsupported: list[str] = []
    prim_count = 0
    filled_count = 0
    for prim in stage.Traverse():
        type_name = prim.GetTypeName()
        if type_name not in supported_types:
            if type_name and len(unsupported) < 50:
                unsupported.append(f"{prim.GetPath()}:{type_name}")
            continue
        if prim_count >= max_prims:
            break
        prim_count += 1
        try:
            bound = bbox_cache.ComputeWorldBound(prim)
            box = bound.ComputeAlignedBox()
            if box.IsEmpty():
                continue
            mn = box.GetMin()
            mx = box.GetMax()
            slices = bbox_indices((mn[0], mn[1], mn[2]), (mx[0], mx[1], mx[2]), origin, voxel_size, shape)
            if slices is None:
                continue
            occupancy[slices] = 1
            filled_count += 1
        except Exception as exc:
            if len(unsupported) < 50:
                unsupported.append(f"{prim.GetPath()}:bbox_error:{repr(exc)}")
    occupied_count = int(np.count_nonzero(occupancy))
    status = "partial_success" if occupied_count > 0 else "failed"
    output_dir = DATA_ROOT / scene["scene_id"]
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "full_occupancy_usd_voxel.npz"
    np.savez_compressed(
        output_path,
        occupancy=occupancy,
        voxel_size=np.asarray(voxel_size, dtype=np.float32),
        origin_xyz=origin.astype(np.float32),
        grid_shape=np.asarray(shape, dtype=np.int32),
        scene_id=np.asarray(scene["scene_id"]),
        scene_path=np.asarray(scene["scene_path"]),
        gt_type=np.asarray("usd_bbox_voxelization_prototype"),
    )
    return {
        "usd_voxelization_status": status,
        "usd_voxel_gt_path": str(output_path),
        "usd_voxel_occupied_count": occupied_count,
        "usd_voxel_supported_prim_count": prim_count,
        "usd_voxel_filled_prim_count": filled_count,
        "usd_voxelization_method": "mesh_cube_world_bbox_fill_prototype",
        "unsupported_prim_examples": unsupported,
        "usd_voxel_failure_reason": None if occupied_count > 0 else "no_supported_geometry_intersected_grid",
    }


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# MapPredict Phase 1 Full Occupancy GT Report",
        "",
        "phase: MapPredict Phase 1",
        "purpose: generate full occupancy GT prototype for SceneSense-style map_predict",
        f"workspace: {summary.get('workspace')}",
        f"project_name: {summary.get('project_name')}",
        f"main_goal: {summary.get('main_goal')}",
        "map_predict_role: feature_provider",
        "planner: false",
        "VLA: false",
        "training_started: false",
        "map_predict_training_started: false",
        "SFT_started: false",
        "GDPO_started: false",
        "RL_started: false",
        "rollout_started: false",
        "",
        "## Route Status",
        "",
        f"route_a_dense_scan_status: {summary.get('route_a_dense_scan_status')}",
        f"route_b_usd_voxelization_status: {summary.get('route_b_usd_voxelization_status')}",
        f"full_occupancy_gt_type: {summary.get('full_occupancy_gt_type')}",
        f"safe_to_build_local_voxel_dataset: {bool_text(summary.get('safe_to_build_local_voxel_dataset'))}",
        "next_phase: MapPredict Phase 2 local voxel crop dataset generation",
        "",
        "## Scenes Processed",
        "",
    ]
    for scene in summary.get("scenes", []):
        lines.extend(
            [
                f"### {scene.get('scene_id')}",
                "",
                f"scene_path: {scene.get('scene_path')}",
                f"dense_scan_status: {scene.get('dense_scan_status')}",
                f"usd_voxelization_status: {scene.get('usd_voxelization_status')}",
                f"gt_path: {scene.get('gt_path')}",
                f"usd_voxel_gt_path: {scene.get('usd_voxel_gt_path')}",
                f"voxel_size: {scene.get('voxel_size')}",
                f"grid_shape: {scene.get('grid_shape')}",
                f"occupied_count: {scene.get('occupied_count')}",
                f"free_count: {scene.get('free_count')}",
                f"observed_count: {scene.get('observed_count')}",
                f"unknown_count: {scene.get('unknown_count')}",
                f"occupied_ratio: {scene.get('occupied_ratio')}",
                f"free_ratio: {scene.get('free_ratio')}",
                f"observed_ratio: {scene.get('observed_ratio')}",
                f"quality_pass: {bool_text(scene.get('quality_pass'))}",
                f"failure_reason: {scene.get('failure_reason')}",
                f"usd_voxel_occupied_count: {scene.get('usd_voxel_occupied_count')}",
                f"usd_voxel_supported_prim_count: {scene.get('usd_voxel_supported_prim_count')}",
                f"usd_voxel_filled_prim_count: {scene.get('usd_voxel_filled_prim_count')}",
                "",
            ]
        )
    lines.extend(
        [
            "## SceneSense GitHub Alignment",
            "",
            "* Reviewed repository: https://github.com/arpg/SceneSense",
            "* Reviewed project page: https://arpg.github.io/scenesense/",
            "* This prototype follows the SceneSense boundary of occupancy completion from partial observation.",
            "* Observed-space preservation remains mandatory for later inference: predictions may fill unknown regions but must not overwrite observed free/occupied voxels.",
            "* Frontier/candidate usage is feature enrichment only; this module does not output robot actions.",
            "",
            "## Limitations",
            "",
            "* Dense scan GT is `dense_scan_pseudo_gt`, not final perfect mesh GT.",
            "* USD voxelization here is a bounds-fill prototype and is stricter only as an audit aid, not final training GT.",
            "* Generated `.npz` files are excluded from Git by default.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", default="")
    parser.add_argument("--max-prims", type=int, default=5000)
    args = parser.parse_args()
    run_dir = Path(args.run_dir) if args.run_dir else latest_run_dir()
    summary_path = run_dir / "summary/full_occupancy_gt_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    app = None
    try:
        from isaacsim import SimulationApp

        app = SimulationApp({"headless": True})
        statuses = []
        for scene in summary.get("scenes", []):
            if scene.get("dense_scan_status") != "success":
                scene["usd_voxelization_status"] = "skipped"
                continue
            try:
                update = voxelize_scene_bounds(scene, int(args.max_prims))
                scene.update(update)
                statuses.append(scene.get("usd_voxelization_status"))
            except Exception as exc:
                scene["usd_voxelization_status"] = "failed"
                scene["usd_voxel_failure_reason"] = repr(exc)
                statuses.append("failed")
        if statuses and all(s in {"success", "partial_success"} for s in statuses):
            summary["route_b_usd_voxelization_status"] = "partial_success"
        elif any(s in {"success", "partial_success"} for s in statuses):
            summary["route_b_usd_voxelization_status"] = "partial_success"
        else:
            summary["route_b_usd_voxelization_status"] = "failed" if statuses else "skipped"
        write_json(summary_path, summary)
        write_report(TOP_REPORT, summary)
        write_report(run_dir / "reports/MAP_PREDICT_PHASE1_FULL_OCCUPANCY_GT_REPORT.md", summary)
    finally:
        if app is not None:
            app.close()
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
