#!/usr/bin/env python3
"""Inspect a USD stage for existing Unitree Go2-like robot prims."""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

ROBOT_KEYWORDS = ("go2", "unitree", "dog", "quadruped", "robot", "base", "base_link", "trunk", "a1")
SENSOR_KEYWORDS = ("camera", "lidar", "depth", "rgb", "sensor", "laser", "imu")
BASE_KEYWORDS = ("base_link", "base", "trunk")


def _as_list(items, limit=None):
    if limit is None:
        return list(items)
    return list(items)[:limit]


def _score_candidate(path: str, type_name: str, child_count: int, has_articulation: bool) -> int:
    text = path.lower()
    score = 0
    if "go2" in text:
        score += 100
    if "unitree" in text:
        score += 60
    if "quadruped" in text or "dog" in text:
        score += 45
    if "robot" in text:
        score += 35
    if "a1" in text:
        score += 20
    if "base_link" in text:
        score += 18
    elif "base" in text or "trunk" in text:
        score += 12
    if type_name == "Xform":
        score += 8
    if child_count > 0:
        score += min(child_count, 10)
    if has_articulation:
        score += 80
    # Prefer hierarchy roots over individual meshes/base links when scores are close.
    score -= min(path.count("/"), 12)
    return score


def _ancestor_prefix(path: str, max_depth: int = 5) -> str:
    parts = [p for p in path.split("/") if p]
    if len(parts) <= max_depth:
        return path
    return "/" + "/".join(parts[:max_depth])


def _write_markdown(path: Path, data: dict) -> None:
    lines = []
    lines.append("# Go2 Stage Inspection Report")
    lines.append("")
    lines.append("phase: Phase 2")
    lines.append("workspace: /home/ubuntu22/VLA")
    lines.append(f"scene_path: {data['scene_path']}")
    lines.append(f"go2_in_usd_found: {str(data['go2_in_usd_found']).lower()}")
    lines.append(f"go2_root_prim: {data['go2_root_prim'] if data['go2_root_prim'] else 'null'}")
    lines.append(f"go2_base_frame_candidate: {data['go2_base_frame_candidate'] if data['go2_base_frame_candidate'] else 'null'}")
    lines.append(f"temporary_go2_proxy_required: {str(data['temporary_go2_proxy_required']).lower()}")
    lines.append(f"safe_to_continue_phase3: {str(data['safe_to_continue_phase3']).lower()}")
    lines.append(f"inspection_json_path: {data['inspection_json_path']}")
    lines.append("")
    lines.append("## Candidate Prims")
    lines.append("")
    if data["go2_candidate_prims"]:
        for item in data["go2_candidate_prims"][:30]:
            lines.append(f"- score={item['score']} type={item['type']} path={item['path']}")
    else:
        lines.append("- none")
    lines.append("")
    lines.append("## Existing Camera Prims")
    lines.append("")
    for p in data["existing_camera_prims"] or ["none"]:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("## Existing Lidar Prims")
    lines.append("")
    for p in data["existing_lidar_prims"] or ["none"]:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("## Existing Sensor Prims")
    lines.append("")
    for p in data["existing_sensor_prims"][:40] or ["none"]:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("## Prim Type Counts")
    lines.append("")
    for key, value in data["prim_type_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Caveats")
    lines.append("")
    for c in data["caveats"] or ["none"]:
        lines.append(f"- {c}")
    lines.append("")
    lines.append("## Negative Scope")
    lines.append("")
    lines.append("- training: false")
    lines.append("- RL: false")
    lines.append("- map_predict: false")
    lines.append("- PI_finetuning: false")
    lines.append("- Go2_locomotion_training: false")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", required=True)
    parser.add_argument("--out_json", required=True)
    parser.add_argument("--out_md", required=True)
    parser.add_argument("--timeout", type=float, default=180.0)
    args = parser.parse_args()

    usd_path = Path(args.usd).expanduser().resolve()
    out_json = Path(args.out_json).expanduser().resolve()
    out_md = Path(args.out_md).expanduser().resolve()
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    result = {
        "phase": "Phase 2",
        "workspace": "/home/ubuntu22/VLA",
        "scene_path": str(usd_path),
        "scene_exists": usd_path.exists(),
        "go2_in_usd_found": False,
        "go2_root_prim": None,
        "go2_base_frame_candidate": None,
        "go2_candidate_prims": [],
        "existing_camera_prims": [],
        "existing_lidar_prims": [],
        "existing_sensor_prims": [],
        "prim_type_counts": {
            "Xform": 0,
            "Mesh": 0,
            "Cube": 0,
            "ArticulationRoot": 0,
            "PhysicsJoint": 0,
            "Camera": 0,
            "Lidar": 0,
            "Light": 0,
        },
        "all_prim_type_counts": {},
        "inspection_json_path": str(out_json),
        "temporary_go2_proxy_required": True,
        "safe_to_continue_phase3": False,
        "caveats": [],
        "exception": None,
        "traceback": None,
        "training": False,
        "rl": False,
        "map_predict": False,
        "rollout": False,
    }

    simulation_app = None
    try:
        if not usd_path.exists():
            raise FileNotFoundError(str(usd_path))

        from isaacsim import SimulationApp

        simulation_app = SimulationApp({"headless": True})

        from pxr import Usd, UsdPhysics

        stage = Usd.Stage.Open(str(usd_path))
        if stage is None:
            raise RuntimeError("Usd.Stage.Open returned None")

        prims = list(stage.Traverse())
        type_counts = Counter()
        candidates = []
        base_candidates = []
        camera_prims = []
        lidar_prims = []
        sensor_prims = []
        root_scores = Counter()
        articulation_paths = set()

        for prim in prims:
            path = str(prim.GetPath())
            name = prim.GetName()
            type_name = prim.GetTypeName() or "UNDEFINED"
            low = f"{path} {name} {type_name}".lower()
            type_counts[type_name] += 1
            child_count = len(list(prim.GetChildren()))
            try:
                has_articulation = bool(prim.HasAPI(UsdPhysics.ArticulationRootAPI))
            except Exception:
                has_articulation = False
            if has_articulation:
                articulation_paths.add(path)

            if type_name == "Camera" or "camera" in low:
                camera_prims.append(path)
            if "lidar" in low or "laser" in low or type_name.lower() == "lidar":
                lidar_prims.append(path)
            if any(k in low for k in SENSOR_KEYWORDS):
                sensor_prims.append(path)

            matched = [k for k in ROBOT_KEYWORDS if k in low]
            if has_articulation and "articulation_root" not in matched:
                matched.append("articulation_root")
            if matched:
                score = _score_candidate(path, type_name, child_count, has_articulation)
                item = {
                    "path": path,
                    "name": name,
                    "type": type_name,
                    "matched_keywords": matched,
                    "score": score,
                    "child_count": child_count,
                    "has_articulation_root_api": has_articulation,
                }
                candidates.append(item)
                root_scores[_ancestor_prefix(path)] += max(score, 1)
                if any(k in low for k in BASE_KEYWORDS):
                    base_candidates.append(item)

        summary_counts = result["prim_type_counts"].copy()
        for type_name, count in type_counts.items():
            if type_name in summary_counts:
                summary_counts[type_name] += count
            if "Joint" in type_name:
                summary_counts["PhysicsJoint"] += count
            if "Light" in type_name:
                summary_counts["Light"] += count
            if "Lidar" in type_name or "lidar" in type_name.lower():
                summary_counts["Lidar"] += count
        summary_counts["ArticulationRoot"] = len(articulation_paths)

        candidates.sort(key=lambda item: (-item["score"], item["path"]))
        base_candidates.sort(key=lambda item: (-item["score"], item["path"]))
        root_ranked = root_scores.most_common(20)

        selected_root = None
        if candidates:
            # Prefer a high-scoring ancestor/root if many matching prims share it.
            selected_root = root_ranked[0][0] if root_ranked else candidates[0]["path"]
            # If the top individual candidate is a clear Go2/Unitree root, keep it.
            top = candidates[0]
            if any(k in top["path"].lower() for k in ("go2", "unitree", "quadruped", "robot")) and top["type"] == "Xform":
                selected_root = top["path"]

        selected_base = None
        if selected_root:
            in_root_base = [c for c in base_candidates if c["path"].startswith(selected_root)]
            if in_root_base:
                selected_base = in_root_base[0]["path"]
            elif base_candidates:
                selected_base = base_candidates[0]["path"]

        # A Go2-like hierarchy is considered present if a candidate contains Go2,
        # Unitree, quadruped, dog, robot, or an articulation/base hierarchy signal.
        go2_like = False
        if candidates:
            for item in candidates[:20]:
                text = item["path"].lower()
                if any(k in text for k in ("go2", "unitree", "quadruped", "dog", "robot")):
                    go2_like = True
                    break
            if not go2_like and selected_base:
                result["caveats"].append("Only base/trunk-like prims were found; no explicit Go2/Unitree/robot keyword appeared in top candidates.")

        result.update({
            "go2_in_usd_found": bool(go2_like),
            "go2_root_prim": selected_root if go2_like else None,
            "go2_base_frame_candidate": selected_base if go2_like else None,
            "go2_candidate_prims": candidates[:50],
            "root_candidate_prefixes": [{"path": p, "score": s} for p, s in root_ranked],
            "existing_camera_prims": sorted(set(camera_prims)),
            "existing_lidar_prims": sorted(set(lidar_prims)),
            "existing_sensor_prims": sorted(set(sensor_prims)),
            "prim_type_counts": summary_counts,
            "all_prim_type_counts": dict(sorted(type_counts.items())),
            "temporary_go2_proxy_required": not bool(go2_like),
            "safe_to_continue_phase3": True,
        })
        if not go2_like:
            result["caveats"].append("No Go2-like robot hierarchy was found by keyword inspection; Phase 3 must use a temporary Go2-shaped proxy and report it as non-final.")
        if go2_like and not selected_base:
            result["caveats"].append("Go2-like hierarchy found, but no explicit base/base_link/trunk frame candidate was identified.")
        if any("/A1" in item["path"] for item in candidates):
            result["caveats"].append("An articulated /World/A1 robot hierarchy was found, but no explicit Go2 or Unitree naming was found; do not report it as a verified Go2 prim.")
        if not result["existing_camera_prims"] and not result["existing_lidar_prims"]:
            result["caveats"].append("No camera or lidar prim was found by type/name keyword inspection; Phase 3 may need a sensor proxy.")
        exit_code = 0
    except Exception as exc:
        result["exception"] = repr(exc)
        result["traceback"] = traceback.format_exc()
        result["safe_to_continue_phase3"] = False
        exit_code = 1
    finally:
        out_json.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        _write_markdown(out_md, result)
        if simulation_app is not None:
            try:
                simulation_app.close()
            except Exception as exc:
                print(f"simulation_app.close failed: {exc!r}", file=sys.stderr)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
