#!/usr/bin/env python3
"""Isaac headless USD stage open smoke probe."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from collections import Counter
from pathlib import Path


def _empty_counts() -> dict[str, int]:
    return {
        "Xform": 0,
        "Mesh": 0,
        "Cube": 0,
        "Material": 0,
        "Camera": 0,
        "Light": 0,
        "PhysicsJoint": 0,
        "ArticulationRoot": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--usd", required=True, help="USD file to open")
    parser.add_argument("--out", required=True, help="JSON output path")
    parser.add_argument("--timeout", type=float, default=180.0, help="Stage load timeout in seconds")
    args = parser.parse_args()

    usd_path = Path(args.usd).expanduser().resolve()
    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    result: dict[str, object] = {
        "phase": "Phase 2",
        "probe": "isaac_headless_open_stage",
        "usd_path": str(usd_path),
        "usd_exists": usd_path.exists(),
        "open_stage_result": False,
        "open_stage_raw_result": None,
        "stage_available": False,
        "prim_count": 0,
        "prim_type_counts": _empty_counts(),
        "all_prim_type_counts": {},
        "stage_loading_status": None,
        "elapsed_sec": None,
        "exception": None,
        "traceback": None,
        "training": False,
        "rl": False,
        "map_predict": False,
        "rollout": False,
    }

    simulation_app = None
    started = time.time()
    exit_code = 1
    try:
        if not usd_path.exists():
            raise FileNotFoundError(str(usd_path))

        from isaacsim import SimulationApp

        simulation_app = SimulationApp({"headless": True})

        import omni.usd
        from pxr import UsdPhysics

        context = omni.usd.get_context()
        raw = context.open_stage(str(usd_path))
        result["open_stage_raw_result"] = repr(raw)

        stage = None
        deadline = time.time() + args.timeout
        while time.time() < deadline:
            if simulation_app is not None:
                simulation_app.update()
            stage = context.get_stage()
            if stage is not None:
                prims = list(stage.Traverse())
                if prims:
                    break
            time.sleep(0.1)

        if stage is None:
            stage = context.get_stage()

        if stage is not None:
            prims = list(stage.Traverse())
            type_counts: Counter[str] = Counter()
            summary_counts = _empty_counts()
            articulation_count = 0
            for prim in prims:
                type_name = prim.GetTypeName() or "UNDEFINED"
                type_counts[type_name] += 1
                if type_name in summary_counts:
                    summary_counts[type_name] += 1
                if "Light" in type_name:
                    summary_counts["Light"] += 1
                if "Joint" in type_name:
                    summary_counts["PhysicsJoint"] += 1
                try:
                    if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
                        articulation_count += 1
                except Exception:
                    pass
            summary_counts["ArticulationRoot"] = articulation_count
            result["stage_available"] = True
            result["prim_count"] = len(prims)
            result["prim_type_counts"] = dict(summary_counts)
            result["all_prim_type_counts"] = dict(sorted(type_counts.items()))
            result["open_stage_result"] = len(prims) > 0
        try:
            result["stage_loading_status"] = repr(context.get_stage_loading_status())
        except Exception:
            result["stage_loading_status"] = None
        exit_code = 0 if result["open_stage_result"] and result["stage_available"] else 2
    except Exception as exc:
        result["exception"] = repr(exc)
        result["traceback"] = traceback.format_exc()
        exit_code = 1
    finally:
        result["elapsed_sec"] = round(time.time() - started, 3)
        try:
            out_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as exc:
            print(f"failed to write JSON output: {exc!r}", file=sys.stderr)
        if simulation_app is not None:
            try:
                simulation_app.close()
            except Exception as exc:
                print(f"simulation_app.close failed: {exc!r}", file=sys.stderr)

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
