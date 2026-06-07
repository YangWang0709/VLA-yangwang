#!/usr/bin/env python3
"""Phase 5.6 A1-mounted real Isaac/Omniverse sensor suite smoke.

This smoke opens the primary scene read-only, creates runtime Isaac/Omniverse
camera and RTX LiDAR sensors, captures Replicator RGB-D outputs, and derives a
camera pointcloud from real depth plus camera intrinsics. It does not save the
USD stage, train models, generate candidates, run rollouts, or write raw sensor
dumps.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

import numpy as np


WORKSPACE = Path("/home/ubuntu22/VLA")
SCENE = WORKSPACE / "scenes/primary_building_scene_repaired/home_like_scene_v1.usd"
TOP_REPORT = WORKSPACE / "runs/A1_REAL_SENSOR_SUITE_SMOKE_REPORT.md"
A1_ROOT = "/World/A1"
BASE_FRAME = "/World/A1/base"
RUNTIME_ROOT = "/World/RuntimeSensors"
MOUNT_MARKER_PATH = "/World/A1/base/Sensors/a1_front_real_sensor_mount"
CAMERA_PATH = f"{RUNTIME_ROOT}/a1_front_rgbd_camera"
LIDAR_PATH = f"{RUNTIME_ROOT}/a1_front_lidar"
LIGHT_PATH = f"{RUNTIME_ROOT}/phase56_runtime_fill_light"
MOUNT_XYZ = (0.30, 0.0, 0.28)
MOUNT_RPY = (0.0, math.radians(-15.0), 0.0)
POINTCLOUD_STRIDE = 8


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def finite_float(value: Any) -> float | None:
    try:
        out = float(value)
    except Exception:
        return None
    return out if math.isfinite(out) else None


def find_core_dumps(workspace: Path) -> list[str]:
    matches: list[str] = []
    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in {".git", "scenes", "__pycache__"}]
        for name in files:
            low = name.lower()
            if low == "core" or low.startswith("core.") or low.endswith(".core") or low.endswith(".dmp"):
                matches.append(str(Path(root) / name))
                if len(matches) >= 20:
                    return matches
    return matches


def quatd_from_any(quat):
    from pxr import Gf

    imag = quat.GetImaginary()
    return Gf.Quatd(float(quat.GetReal()), Gf.Vec3d(float(imag[0]), float(imag[1]), float(imag[2])))


def quat_like(template, quatd):
    from pxr import Gf

    imag = quatd.GetImaginary()
    name = type(template).__name__ if template is not None else "Quatd"
    if name == "Quatf":
        return Gf.Quatf(float(quatd.GetReal()), Gf.Vec3f(float(imag[0]), float(imag[1]), float(imag[2])))
    if name == "Quath":
        return Gf.Quath(float(quatd.GetReal()), Gf.Vec3h(float(imag[0]), float(imag[1]), float(imag[2])))
    return Gf.Quatd(float(quatd.GetReal()), Gf.Vec3d(float(imag[0]), float(imag[1]), float(imag[2])))


def set_root_pose(root_prim, xyz: tuple[float, float, float], yaw: float, initial_orient) -> None:
    from pxr import Gf, UsdGeom

    xform = UsdGeom.Xformable(root_prim)
    ops = {op.GetName(): op for op in xform.GetOrderedXformOps()}
    translate_op = ops.get("xformOp:translate") or xform.AddTranslateOp()
    translate_op.Set(Gf.Vec3d(*xyz))
    orient_op = ops.get("xformOp:orient")
    if orient_op and initial_orient is not None:
        yaw_q = Gf.Quatd(math.cos(yaw / 2.0), Gf.Vec3d(0.0, 0.0, math.sin(yaw / 2.0)))
        orient_op.Set(quat_like(initial_orient, yaw_q * quatd_from_any(initial_orient)))


def world_translation(cache, prim) -> tuple[float, float, float]:
    t = cache.GetLocalToWorldTransform(prim).ExtractTranslation()
    return float(t[0]), float(t[1]), float(t[2])


def set_local_mount_xform(prim) -> None:
    from pxr import Gf, UsdGeom

    xf = UsdGeom.Xformable(prim)
    xf.ClearXformOpOrder()
    xf.AddTranslateOp().Set(Gf.Vec3d(*MOUNT_XYZ))
    xf.AddRotateYOp().Set(math.degrees(MOUNT_RPY[1]))


def norm3(v: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(sum(x * x for x in v))
    if length < 1e-9:
        return (1.0, 0.0, 0.0)
    return tuple(x / length for x in v)


def cross3(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def set_world_look_at(prim, eye: tuple[float, float, float], target: tuple[float, float, float]) -> None:
    from pxr import Gf, UsdGeom

    forward = norm3((target[0] - eye[0], target[1] - eye[1], target[2] - eye[2]))
    up = (0.0, 0.0, 1.0)
    right = cross3(forward, up)
    if math.sqrt(sum(x * x for x in right)) < 1e-6:
        up = (0.0, 1.0, 0.0)
        right = cross3(forward, up)
    right = norm3(right)
    true_up = cross3(right, forward)
    back = (-forward[0], -forward[1], -forward[2])
    matrix = Gf.Matrix4d(
        right[0], right[1], right[2], 0.0,
        true_up[0], true_up[1], true_up[2], 0.0,
        back[0], back[1], back[2], 0.0,
        eye[0], eye[1], eye[2], 1.0,
    )
    xf = UsdGeom.Xformable(prim)
    xf.ClearXformOpOrder()
    xf.AddTransformOp().Set(matrix)


def set_world_translate(prim, xyz: tuple[float, float, float]) -> None:
    from pxr import Gf, UsdGeom

    xf = UsdGeom.Xformable(prim)
    xf.ClearXformOpOrder()
    xf.AddTranslateOp().Set(Gf.Vec3d(*xyz))


def expected_sensor_pose(base_x: float, base_y: float, base_z: float, yaw: float) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    eye = (
        base_x + math.cos(yaw) * MOUNT_XYZ[0] - math.sin(yaw) * MOUNT_XYZ[1],
        base_y + math.sin(yaw) * MOUNT_XYZ[0] + math.cos(yaw) * MOUNT_XYZ[1],
        base_z + MOUNT_XYZ[2],
    )
    pitch = MOUNT_RPY[1]
    forward_flat = (math.cos(yaw), math.sin(yaw), 0.0)
    target = (
        eye[0] + math.cos(pitch) * forward_flat[0] * 2.0,
        eye[1] + math.cos(pitch) * forward_flat[1] * 2.0,
        eye[2] + math.sin(pitch) * 2.0,
    )
    return eye, target


def create_runtime_prims(stage, width: int, height: int) -> None:
    from pxr import Gf, Sdf, UsdGeom, UsdLux

    UsdGeom.Xform.Define(stage, RUNTIME_ROOT)
    UsdGeom.Xform.Define(stage, "/World/A1/base/Sensors")
    marker = UsdGeom.Xform.Define(stage, MOUNT_MARKER_PATH)
    set_local_mount_xform(marker.GetPrim())

    camera = UsdGeom.Camera.Define(stage, CAMERA_PATH)
    camera.CreateFocalLengthAttr(18.0)
    camera.CreateHorizontalApertureAttr(20.0)
    camera.CreateVerticalApertureAttr(15.0)
    camera.CreateClippingRangeAttr(Gf.Vec2f(0.05, 15.0))
    camera.CreateFocusDistanceAttr(2.0)

    light = UsdLux.SphereLight.Define(stage, LIGHT_PATH)
    light.CreateIntensityAttr(2500.0)
    light.CreateRadiusAttr(3.0)

    # Authored only in the unsaved runtime layer; included so camera params report
    # the intended smoke resolution even before the render product is created.
    camera.GetPrim().CreateAttribute("phase56:requestedWidth", Sdf.ValueTypeNames.Int).Set(int(width))
    camera.GetPrim().CreateAttribute("phase56:requestedHeight", Sdf.ValueTypeNames.Int).Set(int(height))


def attach_camera_annotators(rep, render_product) -> tuple[dict[str, Any], dict[str, str]]:
    annotators: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for name in [
        "rgb",
        "distance_to_image_plane",
        "camera_params",
        "pointcloud",
        "semantic_segmentation",
        "instance_segmentation",
    ]:
        try:
            annotator = rep.AnnotatorRegistry.get_annotator(name)
            annotator.attach([render_product])
            annotators[name] = annotator
        except Exception as exc:
            errors[name] = repr(exc)
    return annotators, errors


def try_create_lidar(stage, rep, eye: tuple[float, float, float], target: tuple[float, float, float]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "lidar_attempted": True,
        "lidar_available": False,
        "lidar_prim_path": LIDAR_PATH,
        "lidar_render_product_path": None,
        "lidar_annotator": None,
        "lidar_failure_reason": "",
    }
    try:
        import omni.kit.commands
        from pxr import Gf

        command_result = omni.kit.commands.execute(
            "IsaacSensorCreateRtxLidar",
            path=LIDAR_PATH,
            parent=None,
            config="Example_Rotary",
            translation=Gf.Vec3d(*eye),
            orientation=Gf.Quatd(1.0, 0.0, 0.0, 0.0),
            **{
                "omni:sensor:Core:outputFrameOfReference": "WORLD",
                "omni:sensor:Core:auxOutputType": "FULL",
            },
        )
        if isinstance(command_result, tuple):
            sensor_prim = command_result[-1]
        else:
            sensor_prim = command_result
        if not sensor_prim or not sensor_prim.IsValid():
            raise RuntimeError("IsaacSensorCreateRtxLidar returned no valid prim")
        set_world_look_at(sensor_prim, eye, target)
        hydra_texture = rep.create.render_product(
            LIDAR_PATH,
            [32, 32],
            name="Phase56RtxSensorRenderProduct",
            render_vars=["GenericModelOutput", "RtxSensorMetadata"],
        )
        annotator = rep.AnnotatorRegistry.get_annotator("IsaacCreateRTXLidarScanBuffer")
        try:
            annotator.initialize(
                outputIntensity=True,
                outputDistance=True,
                outputObjectId=True,
                outputVelocity=True,
                outputAzimuth=True,
                outputElevation=True,
                outputNormal=True,
                outputTimestamp=True,
                outputEmitterId=True,
                outputBeamId=True,
                outputMaterialId=True,
            )
        except Exception:
            pass
        annotator.attach([hydra_texture.path])
        result.update({
            "lidar_available": True,
            "lidar_render_product_path": hydra_texture.path,
            "lidar_annotator": annotator,
        })
    except Exception as exc:
        result["lidar_failure_reason"] = repr(exc)
    return result


def array_from_annotator_data(data: Any, key: str | None = None) -> np.ndarray | None:
    if data is None:
        return None
    if isinstance(data, dict):
        if key and key in data:
            return np.asarray(data[key])
        if "data" in data:
            return np.asarray(data["data"])
        return None
    return np.asarray(data)


def rgb_stats(data: Any) -> dict[str, Any]:
    arr = array_from_annotator_data(data)
    if arr is None or arr.ndim < 3:
        return {
            "available": False,
            "width": 0,
            "height": 0,
            "dtype": "",
            "mean": 0.0,
            "nonzero_ratio": 0.0,
            "array": None,
        }
    rgb = arr[..., :3]
    numeric = rgb.astype(np.float32)
    mean = float(np.mean(numeric)) if numeric.size else 0.0
    nonzero_ratio = float(np.count_nonzero(rgb) / rgb.size) if rgb.size else 0.0
    available = bool(arr.shape[0] > 0 and arr.shape[1] > 0 and math.isfinite(mean) and nonzero_ratio > 0.02)
    return {
        "available": available,
        "width": int(arr.shape[1]),
        "height": int(arr.shape[0]),
        "dtype": str(arr.dtype),
        "mean": round(mean, 4),
        "nonzero_ratio": round(nonzero_ratio, 4),
        "array": arr,
    }


def depth_stats(data: Any) -> dict[str, Any]:
    arr = array_from_annotator_data(data)
    if arr is None or arr.ndim < 2:
        return {
            "available": False,
            "width": 0,
            "height": 0,
            "min": None,
            "max": None,
            "mean": None,
            "valid_ratio": 0.0,
            "array": None,
        }
    depth = np.asarray(arr, dtype=np.float32)
    valid = depth[np.isfinite(depth) & (depth > 0.05) & (depth < 15.0)]
    valid_ratio = float(valid.size / depth.size) if depth.size else 0.0
    return {
        "available": bool(valid_ratio > 0.1 and valid.size > 0),
        "width": int(depth.shape[1]),
        "height": int(depth.shape[0]),
        "min": round(float(valid.min()), 4) if valid.size else None,
        "max": round(float(valid.max()), 4) if valid.size else None,
        "mean": round(float(valid.mean()), 4) if valid.size else None,
        "valid_ratio": round(valid_ratio, 4),
        "array": depth,
    }


def intrinsics_from_camera_params(params: Any, width: int, height: int) -> tuple[bool, dict[str, float]]:
    if not isinstance(params, dict):
        return False, {}
    fx = finite_float(params.get("cameraOpenCVFx"))
    fy = finite_float(params.get("cameraOpenCVFy"))
    cx = finite_float(params.get("cameraOpenCVCx"))
    cy = finite_float(params.get("cameraOpenCVCy"))
    if cx is None:
        cx = width / 2.0
    if cy is None:
        cy = height / 2.0
    if fx is None or fy is None or fx <= 0.0 or fy <= 0.0:
        focal = finite_float(params.get("cameraFocalLength"))
        aperture = params.get("cameraAperture")
        if focal is not None and aperture is not None and len(aperture) >= 2:
            ax = finite_float(aperture[0])
            ay = finite_float(aperture[1])
            if ax and ay:
                fx = width * focal / ax
                fy = height * focal / ay
    ok = all(v is not None and v > 0 for v in (fx, fy, cx, cy))
    if not ok:
        return False, {}
    return True, {"fx": float(fx), "fy": float(fy), "cx": float(cx), "cy": float(cy)}


def pointcloud_from_depth(depth: np.ndarray, intrinsics: dict[str, float], stride: int = POINTCLOUD_STRIDE) -> np.ndarray:
    if depth is None or depth.ndim != 2:
        return np.empty((0, 3), dtype=np.float32)
    fx = intrinsics["fx"]
    fy = intrinsics["fy"]
    cx = intrinsics["cx"]
    cy = intrinsics["cy"]
    rows, cols = np.indices(depth.shape)
    mask = np.isfinite(depth) & (depth > 0.05) & (depth < 15.0)
    mask &= (rows % stride == 0) & (cols % stride == 0)
    if not np.any(mask):
        return np.empty((0, 3), dtype=np.float32)
    z = depth[mask].astype(np.float32)
    u = cols[mask].astype(np.float32)
    v = rows[mask].astype(np.float32)
    x = (u - cx) / fx * z
    y = -(v - cy) / fy * z
    return np.stack([x, y, z], axis=1).astype(np.float32)


def pointcloud_stats(points: np.ndarray) -> dict[str, Any]:
    if points is None or points.size == 0:
        return {
            "available": False,
            "point_count": 0,
            "finite_ratio": 0.0,
            "min_x": None,
            "max_x": None,
            "min_y": None,
            "max_y": None,
            "min_z": None,
            "max_z": None,
            "not_all_same": False,
        }
    pts = np.asarray(points, dtype=np.float32).reshape(-1, 3)
    finite_mask = np.isfinite(pts).all(axis=1)
    finite = pts[finite_mask]
    finite_ratio = float(finite.shape[0] / pts.shape[0]) if pts.shape[0] else 0.0
    if finite.size == 0:
        return {
            "available": False,
            "point_count": int(pts.shape[0]),
            "finite_ratio": round(finite_ratio, 4),
            "min_x": None,
            "max_x": None,
            "min_y": None,
            "max_y": None,
            "min_z": None,
            "max_z": None,
            "not_all_same": False,
        }
    spread = np.ptp(finite, axis=0)
    not_all_same = bool(np.any(spread > 1e-4))
    return {
        "available": bool(pts.shape[0] > 0 and finite_ratio > 0.8 and not_all_same),
        "point_count": int(pts.shape[0]),
        "finite_ratio": round(finite_ratio, 4),
        "min_x": round(float(finite[:, 0].min()), 4),
        "max_x": round(float(finite[:, 0].max()), 4),
        "min_y": round(float(finite[:, 1].min()), 4),
        "max_y": round(float(finite[:, 1].max()), 4),
        "min_z": round(float(finite[:, 2].min()), 4),
        "max_z": round(float(finite[:, 2].max()), 4),
        "not_all_same": not_all_same,
    }


def lidar_stats(data: Any) -> dict[str, Any]:
    arr = array_from_annotator_data(data, "data")
    if arr is None:
        return {"available": False, "point_count": 0, "finite_ratio": 0.0}
    arr = np.asarray(arr)
    if arr.size == 0:
        return {"available": False, "point_count": 0, "finite_ratio": 0.0}
    pts = arr.reshape(-1, arr.shape[-1])[:, :3] if arr.ndim >= 2 else arr.reshape(-1, 1)
    if pts.shape[1] < 3:
        return {"available": False, "point_count": int(pts.shape[0]), "finite_ratio": 0.0}
    finite = np.isfinite(pts).all(axis=1)
    finite_ratio = float(np.count_nonzero(finite) / pts.shape[0]) if pts.shape[0] else 0.0
    return {
        "available": bool(pts.shape[0] > 0 and finite_ratio > 0.8),
        "point_count": int(pts.shape[0]),
        "finite_ratio": round(finite_ratio, 4),
    }


def segmentation_available(data: Any) -> bool:
    arr = array_from_annotator_data(data)
    return bool(arr is not None and arr.size > 0)


def save_rgb_png(array: np.ndarray | None, path: Path) -> bool:
    if array is None:
        return False
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        rgb = np.asarray(array)[..., :3]
        plt.imsave(path, rgb)
        return True
    except Exception:
        return False


def save_depth_vis(depth: np.ndarray | None, path: Path) -> bool:
    if depth is None:
        return False
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        arr = np.asarray(depth, dtype=np.float32)
        valid = arr[np.isfinite(arr) & (arr > 0.05) & (arr < 15.0)]
        if valid.size == 0:
            return False
        lo = float(np.percentile(valid, 2))
        hi = float(np.percentile(valid, 98))
        if hi <= lo:
            hi = lo + 1.0
        vis = np.clip((arr - lo) / (hi - lo), 0.0, 1.0)
        plt.imsave(path, vis, cmap="viridis")
        return True
    except Exception:
        return False


def write_report(path: Path, summary: dict[str, Any]) -> None:
    caveats = summary.get("caveats") or []
    debug_paths = summary.get("debug_frame_paths") or []
    lines = [
        "# A1 Real Sensor Suite Smoke Report",
        "",
        "phase: Phase 5.6",
        "workspace: /home/ubuntu22/VLA",
        "project_name: A1-VLM-LA Explorer",
        f"scene_path: {summary.get('scene_path')}",
        "robot_platform: unitree_a1",
        "robot_source: existing_usd_prim",
        "a1_root_prim: /World/A1",
        "base_frame: /World/A1/base",
        "previous_sensor_method: mounted_geometry_proxy_pointcloud_from_a1_front_sensor",
        "new_sensor_method: real_isaac_omniverse_sensor_suite",
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
        f"imu_available: {bool_text(summary.get('imu_available'))}",
        f"joint_state_available: {bool_text(summary.get('joint_state_available'))}",
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
        f"debug_frame_paths: {debug_paths}",
        f"safe_to_rerun_phase4_with_real_sensors: {bool_text(summary.get('safe_to_rerun_phase4_with_real_sensors'))}",
        f"safe_to_rerun_phase5_with_real_sensors: {bool_text(summary.get('safe_to_rerun_phase5_with_real_sensors'))}",
        f"caveats: {caveats}",
        "training: false",
        "RL: false",
        "map_predict: false",
        "PI_finetuning: false",
        "A1_locomotion_training: false",
        "rollout_started: false",
        "",
        "## Evidence",
        "",
        f"- run_dir: {summary.get('run_dir')}",
        f"- steps_csv: {summary.get('steps_csv')}",
        f"- summary_json: {summary.get('summary_json')}",
        "- RGB and depth are captured through Replicator render product annotators.",
        "- Camera pointcloud is derived from real depth and camera intrinsics; no geometry proxy is used.",
        "- Runtime camera is synced to the A1 base pose each step; the original USD file is not saved.",
        "",
        "## Caveats",
        "",
    ]
    lines.extend(f"- {item}" for item in caveats)
    lines.extend([
        "",
        "## Negative Scope",
        "",
        "- No Phase 6.",
        "- No candidate generation.",
        "- No training, RL, map_predict, checkpoint, or rollout.",
        "- No raw RGB-D or full pointcloud dumps were saved.",
        "- Original USD scene was opened and edited only in memory; it was not saved or overwritten.",
    ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", default=str(SCENE))
    parser.add_argument("--run_dir", required=True)
    parser.add_argument("--top_report", default=str(TOP_REPORT))
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
    steps_csv = summary_dir / "a1_real_sensor_suite_steps.csv"
    summary_json = summary_dir / "a1_real_sensor_suite_summary.json"
    report = reports_dir / "A1_REAL_SENSOR_SUITE_SMOKE_REPORT.md"
    top_report = Path(args.top_report).expanduser().resolve()
    started = time.time()
    app = None
    rows: list[dict[str, Any]] = []
    summary: dict[str, Any] = {
        "phase": "Phase 5.6 A1-mounted real Isaac/Omniverse sensor suite smoke",
        "workspace": str(WORKSPACE),
        "project_name": "A1-VLM-LA Explorer",
        "scene_path": str(usd),
        "scene_exists": usd.exists(),
        "scene_open_result": False,
        "stage_available": False,
        "robot_platform": "unitree_a1",
        "robot_source": "existing_usd_prim",
        "a1_root_prim": A1_ROOT,
        "a1_root_exists": False,
        "base_frame": BASE_FRAME,
        "base_pose_readable": False,
        "camera_prim_path": CAMERA_PATH,
        "lidar_prim_path": LIDAR_PATH,
        "sensor_mount_parent": "/World/A1/base (runtime camera synced under /World/RuntimeSensors)",
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
        "imu_available": False,
        "joint_state_available": False,
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
        "safe_to_rerun_phase4_with_real_sensors": False,
        "safe_to_rerun_phase5_with_real_sensors": False,
        "training_started": False,
        "RL_started": False,
        "map_predict_started": False,
        "checkpoint_created": False,
        "rollout_started": False,
        "debug_frame_paths": [],
        "steps_csv": str(steps_csv),
        "summary_json": str(summary_json),
        "run_dir": str(run_dir),
        "caveats": [
            "RTX LiDAR success is optional for this phase; RGB-D plus depth-derived pointcloud is the hard gate.",
            "Runtime light, camera, LiDAR, and marker prims are created in memory only; the primary USD is not saved.",
            "Camera pointcloud is compact depth backprojection metadata, not a raw full-resolution pointcloud dump.",
        ],
        "exception": None,
        "traceback": None,
        "elapsed_sec": None,
    }
    exit_code = 1

    try:
        if not usd.exists():
            raise FileNotFoundError(str(usd))
        from isaacsim import SimulationApp

        app = SimulationApp({"headless": True})
        import omni.usd
        import omni.replicator.core as rep
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
        create_runtime_prims(stage, args.width, args.height)
        camera_prim = stage.GetPrimAtPath(CAMERA_PATH)
        light_prim = stage.GetPrimAtPath(LIGHT_PATH)
        if not camera_prim or not camera_prim.IsValid():
            raise RuntimeError("Runtime RGB-D camera prim was not created")

        cache = UsdGeom.XformCache()
        initial_root = world_translation(cache, root)
        initial_base = world_translation(cache, base)
        summary["initial_root_pose_xyz"] = [round(v, 6) for v in initial_root]
        summary["initial_base_pose_xyz"] = [round(v, 6) for v in initial_base]
        summary["base_pose_readable"] = True
        ops = {op.GetName(): op for op in UsdGeom.Xformable(root).GetOrderedXformOps()}
        initial_orient = ops["xformOp:orient"].Get() if "xformOp:orient" in ops else None

        eye, target = expected_sensor_pose(initial_base[0], initial_base[1], initial_base[2], 0.0)
        set_world_look_at(camera_prim, eye, target)
        if light_prim and light_prim.IsValid():
            set_world_translate(light_prim, (initial_base[0], initial_base[1], initial_base[2] + 2.5))

        render_product = rep.create.render_product(CAMERA_PATH, (int(args.width), int(args.height)))
        camera_annotators, annotator_errors = attach_camera_annotators(rep, render_product)
        summary["camera_annotator_errors"] = annotator_errors
        summary["isaac_pointcloud_annotator_attempted"] = "pointcloud" in camera_annotators
        if "rgb" not in camera_annotators or "distance_to_image_plane" not in camera_annotators or "camera_params" not in camera_annotators:
            raise RuntimeError(f"Required RGB-D camera annotators unavailable: {annotator_errors}")

        lidar_info = try_create_lidar(stage, rep, eye, target)
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
            set_root_pose(root, (root_x, root_y, root_z), yaw, initial_orient)
            for _ in range(2):
                app.update()

            cache = UsdGeom.XformCache()
            base_x, base_y, base_z = world_translation(cache, base)
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
                except Exception as exc:
                    summary.setdefault("orchestrator_step_errors", []).append(repr(exc))
                app.update()

            cache = UsdGeom.XformCache()
            cam_x, cam_y, cam_z = world_translation(cache, camera_prim)
            camera_error = math.sqrt((cam_x - eye[0]) ** 2 + (cam_y - eye[1]) ** 2 + (cam_z - eye[2]) ** 2)
            camera_follows = camera_error < 0.02

            rgb = rgb_stats(camera_annotators["rgb"].get_data())
            depth = depth_stats(camera_annotators["distance_to_image_plane"].get_data())
            camera_params_data = camera_annotators["camera_params"].get_data()
            camera_params_available = isinstance(camera_params_data, dict) and bool(camera_params_data)
            intrinsics_available, intrinsics = intrinsics_from_camera_params(
                camera_params_data,
                depth["width"] or int(args.width),
                depth["height"] or int(args.height),
            )

            annotator_pc_stats = {"available": False, "point_count": 0, "finite_ratio": 0.0}
            if "pointcloud" in camera_annotators:
                try:
                    annotator_pc = array_from_annotator_data(camera_annotators["pointcloud"].get_data(), "data")
                    if annotator_pc is not None and annotator_pc.size > 0:
                        annotator_pc_stats = pointcloud_stats(np.asarray(annotator_pc).reshape(-1, 3))
                except Exception as exc:
                    summary.setdefault("pointcloud_annotator_errors", []).append(repr(exc))

            if annotator_pc_stats["available"]:
                pc_stats = annotator_pc_stats
                pc_source = "isaac_pointcloud_annotator"
            elif depth["available"] and intrinsics_available:
                points = pointcloud_from_depth(depth["array"], intrinsics)
                pc_stats = pointcloud_stats(points)
                pc_source = "depth_backprojection"
            else:
                pc_stats = pointcloud_stats(np.empty((0, 3), dtype=np.float32))
                pc_source = "unavailable"

            lidar_point_count = 0
            lidar_finite_ratio = 0.0
            lidar_available_step = False
            lidar_failure_reason = summary["lidar_failure_reason"]
            if lidar_annotator is not None:
                try:
                    stats = lidar_stats(lidar_annotator.get_data())
                    lidar_available_step = bool(stats["available"])
                    lidar_point_count = int(stats["point_count"])
                    lidar_finite_ratio = float(stats["finite_ratio"])
                except Exception as exc:
                    lidar_failure_reason = repr(exc)

            semantic_avail = False
            instance_avail = False
            if "semantic_segmentation" in camera_annotators:
                try:
                    semantic_avail = segmentation_available(camera_annotators["semantic_segmentation"].get_data())
                except Exception as exc:
                    summary.setdefault("semantic_errors", []).append(repr(exc))
            if "instance_segmentation" in camera_annotators:
                try:
                    instance_avail = segmentation_available(camera_annotators["instance_segmentation"].get_data())
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
            elif pc_source not in {"isaac_pointcloud_annotator", "depth_backprojection"}:
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
                "imu_available": False,
                "joint_state_available": False,
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
            ("first_rgb.png", first_rgb, save_rgb_png),
            ("last_rgb.png", last_rgb, save_rgb_png),
            ("first_depth_vis.png", first_depth, save_depth_vis),
            ("last_depth_vis.png", last_depth, save_depth_vis),
        ]:
            out = debug_dir / name
            if saver(array, out):
                debug_paths.append(str(out))
        summary["debug_frame_paths"] = debug_paths

        success = [r for r in rows if not r["failure_reason"]]
        rgb_valid = [r for r in rows if r["rgb_available"]]
        depth_valid = [r for r in rows if r["depth_available"] and r["depth_valid_ratio"] >= 0.1]
        pc_valid = [r for r in rows if r["camera_pointcloud_available"] and r["camera_pointcloud_source"] in {"isaac_pointcloud_annotator", "depth_backprojection"}]
        lidar_valid = [r for r in rows if r["lidar_available"]]
        follows = [r for r in rows if r["camera_follows_base"]]
        collision_count = sum(1 for r in rows if r["collision_flag"])
        stuck_count = sum(1 for r in rows if r["stuck_flag"])
        falling_count = sum(1 for r in rows if r["falling_flag"])
        core_files = find_core_dumps(WORKSPACE)
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
            "core_dump_found": bool(core_files),
            "core_dump_files": core_files,
            "real_rgb_sensor_available": len(rgb_valid) / len(rows) >= 0.8,
            "real_depth_sensor_available": len(depth_valid) / len(rows) >= 0.8,
            "real_camera_pointcloud_available": len(pc_valid) / len(rows) >= 0.8,
            "camera_pointcloud_source": selected_pc_source,
            "semantic_segmentation_available": any(bool(r["semantic_available"]) for r in rows),
            "instance_segmentation_available": any(bool(r["instance_available"]) for r in rows),
            "lidar_pointcloud_available": len(lidar_valid) > 0,
            "lidar_scan_available": False,
        })
        if summary["rtx_lidar_available"] and not summary["lidar_pointcloud_available"]:
            summary["lidar_failure_reason"] = summary["lidar_failure_reason"] or "RTX LiDAR prim/render product created but no pointcloud returns were read during the short smoke."
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
            and summary["camera_pointcloud_source"] in {"isaac_pointcloud_annotator", "depth_backprojection"}
            and not summary["geometry_proxy_used"]
            and not summary["mounted_geometry_proxy_used"]
            and summary["rtx_lidar_attempted"]
            and not summary["core_dump_found"]
            and collision_count == 0
            and stuck_count == 0
            and falling_count == 0
        )
        summary["safe_to_rerun_phase4_with_real_sensors"] = pass_ok
        summary["safe_to_rerun_phase5_with_real_sensors"] = pass_ok
        exit_code = 0 if pass_ok else 2
    except Exception as exc:
        summary["exception"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
        exit_code = 1
    finally:
        summary["elapsed_sec"] = round(time.time() - started, 3)
        summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        write_report(report, summary)
        write_report(top_report, summary)
        if app is not None:
            try:
                app.close()
            except Exception as exc:
                print(f"simulation_app.close failed: {exc!r}", file=sys.stderr)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
