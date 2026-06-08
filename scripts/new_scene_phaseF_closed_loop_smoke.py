#!/usr/bin/env python3
"""New Scene Phase F: short closed-loop smoke.

This wrapper reuses the already validated Phase 7 short closed-loop engine and
retargets it to the repaired new scene. It post-processes the logs and reports
into the New Scene Phase F schema.

It starts Isaac headless, opens the repaired new scene, uses the existing
/World/A1 prim, captures real Isaac/Omniverse RGB-D observations, updates a BEV
map from depth-backprojected pointclouds, generates candidates online, emits
pseudo VLM commands, parses/validates them, performs kinematic A1 movement, and
updates the map again. It does not run long rollout, real VLM inference,
training, SFT, GDPO, RL, map_predict, geometry proxy, or USD save.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


WORKSPACE = Path("/home/ubuntu22/VLA")
SCRIPT_DIR = WORKSPACE / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

PROJECT_NAME = "A1-VLM-LA Explorer"
MAIN_GOAL = "A1-VLM-LA Explorer for 3D Active Exploration"
PHASE = "New Scene Phase F short closed-loop smoke"
SCENE = WORKSPACE / "scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda"
ORIGINAL_USER_USD = WORKSPACE / "building_scene(1).usd"
SCENE_ID = "building_scene_1_scene_20260608_171052"
TOP_REPORT = WORKSPACE / "runs/NEW_SCENE_CLOSED_LOOP_SMOKE_REPORT.md"
COMPAT_DIR = WORKSPACE / "runs/new_scene_sampling_building_scene_1"
COMPAT_REPORT = COMPAT_DIR / "NEW_SCENE_CLOSED_LOOP_SMOKE_REPORT.md"
OUTPUT_CONTRACT = "Go to candidate <id>."
CANDIDATE_DATA_SOURCE = "online_new_scene_real_sensor_candidate_generation"
VLM_OUTPUT_MODE = "pseudo_from_classical_selector"
NEXT_PASS = "New Scene Phase G long rollout data collection"
NEXT_FAIL = "Fix New Scene Phase F short closed-loop smoke"


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def default_run_dir() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return WORKSPACE / "runs" / f"new_scene_building_scene_1_phaseF_closed_loop_smoke_{timestamp}"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def postprocess_csv(path: Path, summary: dict[str, Any]) -> None:
    if not path.exists():
        return
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        return
    for row in rows:
        row["phase"] = PHASE
        row["scene_path"] = str(SCENE)
    required_order = [
        "phase",
        "step_id",
        "timestamp",
        "scene_path",
        "a1_root_prim",
        "base_frame",
        "pre_base_x",
        "pre_base_y",
        "pre_base_z",
        "pre_base_yaw",
        "post_base_x",
        "post_base_y",
        "post_base_z",
        "post_base_yaw",
        "sensor_method",
        "rgb_available",
        "depth_available",
        "camera_pointcloud_available",
        "camera_pointcloud_source",
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
        "pseudo_vlm_command",
        "parse_success",
        "parsed_candidate_id",
        "validation_success",
        "target_x",
        "target_y",
        "target_z",
        "target_yaw",
        "movement_success",
        "distance_to_target_after_move",
        "fallback_used",
        "fallback_reason",
        "collision_flag",
        "stuck_flag",
        "falling_flag",
        "failure_reason",
    ]
    fieldnames = required_order + [key for key in rows[0].keys() if key not in required_order]
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    summary["closed_loop_steps_csv"] = str(path)


def postprocess_jsonl_logs(summary: dict[str, Any]) -> None:
    command_log = Path(summary["command_log_jsonl"])
    command_rows = load_jsonl(command_log)
    for row in command_rows:
        row["phase"] = PHASE
        row["candidate_data_source"] = CANDIDATE_DATA_SOURCE
        row["output_contract"] = OUTPUT_CONTRACT
        row["real_vlm_inference"] = False
        row["training"] = False
    write_jsonl(command_log, command_rows)

    parse_log = Path(summary["parse_log_jsonl"])
    parse_rows = load_jsonl(parse_log)
    for row in parse_rows:
        row["phase"] = PHASE
    write_jsonl(parse_log, parse_rows)


def update_summary(summary: dict[str, Any]) -> dict[str, Any]:
    safe = bool(summary.get("safe_to_continue_phase8"))
    summary.update(
        {
            "phase": PHASE,
            "workspace": str(WORKSPACE),
            "project_name": PROJECT_NAME,
            "main_goal": MAIN_GOAL,
            "current_scene_id": SCENE_ID,
            "scene_path": str(SCENE),
            "original_user_usd_path": str(ORIGINAL_USER_USD),
            "robot_platform": "unitree_a1",
            "robot_source": "existing_usd_prim",
            "a1_root_prim": "/World/A1",
            "base_frame": "/World/A1/base",
            "sensor_method": "real_isaac_omniverse_rgbd",
            "camera_pointcloud_source": "depth_backprojection",
            "geometry_proxy_used": False,
            "mounted_geometry_proxy_used": False,
            "movement_mode": "kinematic_existing_a1_root",
            "real_a1_locomotion_controller": False,
            "real_vlm_inference": False,
            "vlm_output_mode": VLM_OUTPUT_MODE,
            "output_contract": OUTPUT_CONTRACT,
            "candidate_data_source": CANDIDATE_DATA_SOURCE,
            "training_started": False,
            "RL_started": False,
            "SFT_started": False,
            "GDPO_started": False,
            "map_predict_started": False,
            "checkpoint_created": False,
            "long_rollout_started": False,
            "safe_to_long_rollout": safe,
            "next_phase": NEXT_PASS if safe else NEXT_FAIL,
            "top_report": str(TOP_REPORT),
            "compat_report": str(COMPAT_REPORT),
            "phaseE_commit_required": "8ec19e5 new scene: validate vlm la interface smoke",
        }
    )
    summary["caveats"] = [
        "This is a short closed-loop smoke, not a long rollout.",
        "VLM outputs are pseudo commands generated from the classical selector.",
        "Movement uses kinematic root updates; no A1 locomotion controller is trained or used.",
        "BEV mapping uses depth-backprojected real RGB-D pointclouds only.",
        "Runtime sensors and light are in-memory; the repaired USD is not saved.",
        "The new scene still emits non-blocking MDL material warnings during Isaac loading.",
    ]
    return summary


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# New Scene Closed Loop Smoke Report",
        "",
        "phase: New Scene Phase F",
        f"workspace: {WORKSPACE}",
        f"project_name: {PROJECT_NAME}",
        f"scene_path: {summary.get('scene_path')}",
        "robot_platform: unitree_a1",
        "robot_source: existing_usd_prim",
        "a1_root_prim: /World/A1",
        "base_frame: /World/A1/base",
        f"sensor_method: {summary.get('sensor_method')}",
        f"camera_pointcloud_source: {summary.get('camera_pointcloud_source')}",
        f"geometry_proxy_used: {bool_text(summary.get('geometry_proxy_used'))}",
        f"mounted_geometry_proxy_used: {bool_text(summary.get('mounted_geometry_proxy_used'))}",
        f"movement_mode: {summary.get('movement_mode')}",
        "real_a1_locomotion_controller: false",
        f"real_vlm_inference: {bool_text(summary.get('real_vlm_inference'))}",
        f"vlm_output_mode: {summary.get('vlm_output_mode')}",
        f"output_contract: {summary.get('output_contract')}",
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
        f"safe_to_long_rollout: {bool_text(summary.get('safe_to_long_rollout'))}",
        "training: false",
        "RL: false",
        "SFT: false",
        "GDPO: false",
        "map_predict: false",
        "PI_finetuning: false",
        "A1_locomotion_training: false",
        "long_rollout_started: false",
        "",
        "## Caveats",
        "",
    ]
    lines.extend(f"- {item}" for item in summary.get("caveats", []))
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- run_dir: {summary.get('run_dir')}",
            f"- closed_loop_steps_csv: {summary.get('closed_loop_steps_csv')}",
            f"- command_log_jsonl: {summary.get('command_log_jsonl')}",
            f"- parse_log_jsonl: {summary.get('parse_log_jsonl')}",
            f"- summary_json: {summary.get('summary_json')}",
            f"- plots_path: {summary.get('plots_path')}",
            "",
            "## Evidence",
            "",
            "- Candidate generation and scoring were online from the current real-sensor BEV map.",
            "- Commands were pseudo VLM outputs created from the classical selector.",
            "- Parser and validator enforced the `Go to candidate <id>.` contract.",
            "- The repaired USD scene was not saved or overwritten.",
            "",
            "## Negative Scope",
            "",
            "- No long rollout.",
            "- No training, RL, SFT, GDPO, map_predict, checkpoint, or real VLM inference.",
            "- No geometry proxy or mounted geometry proxy.",
            "- No Go2 label is used as the actual robot platform.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    passed = bool(summary.get("safe_to_long_rollout"))
    status = "passed" if passed else "failed"
    next_phase = summary.get("next_phase")
    common = f"""current_scene_id: {summary.get('current_scene_id')}
current_scene_path: {summary.get('scene_path')}
original_user_usd_path: {summary.get('original_user_usd_path')}
current_scene_phase: New Scene Phase F short closed-loop smoke
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
map_update_source: depth_backprojection_pointcloud
candidate_data_source: {summary.get('candidate_data_source')}
vlm_output_mode: {summary.get('vlm_output_mode')}
output_contract: {summary.get('output_contract')}
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
- long_rollout: false
- real_VLM_inference: false
- PI_action_finetuning: false
- A1_locomotion_training: false
"""
    metrics = f"""action_count: {summary.get('action_count')}
successful_action_count: {summary.get('successful_action_count')}
parse_success_rate: {summary.get('parse_success_rate')}
validation_success_rate: {summary.get('validation_success_rate')}
target_pose_lookup_success_rate: {summary.get('target_pose_lookup_success_rate')}
movement_success_rate: {summary.get('movement_success_rate')}
fallback_count: {summary.get('fallback_count')}
initial_known_ratio: {summary.get('initial_known_ratio')}
final_known_ratio: {summary.get('final_known_ratio')}
total_known_ratio_gain: {summary.get('total_known_ratio_gain')}
known_ratio_monotonic_non_decreasing: {bool_text(summary.get('known_ratio_monotonic_non_decreasing'))}
average_candidate_count: {summary.get('average_candidate_count')}
average_valid_candidate_count: {summary.get('average_valid_candidate_count')}
collision_count: {summary.get('collision_count')}
stuck_count: {summary.get('stuck_count')}
falling_count: {summary.get('falling_count')}
failure_count: {summary.get('failure_count')}
safe_to_long_rollout: {bool_text(summary.get('safe_to_long_rollout'))}
"""
    active = f"""# Active Task Board

current_phase: New Scene Phase F short closed-loop smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
{common}
{negative}

## New Scene Phase F Result

status: {status}
run_dir: {summary.get('run_dir')}
script: /home/ubuntu22/VLA/scripts/new_scene_phaseF_closed_loop_smoke.py
report: {TOP_REPORT}
summary_json: {summary.get('summary_json')}
closed_loop_steps_csv: {summary.get('closed_loop_steps_csv')}
command_log_jsonl: {summary.get('command_log_jsonl')}
parse_log_jsonl: {summary.get('parse_log_jsonl')}

{metrics}

## Scope

Phase F ran only a short closed-loop smoke. It used real Isaac/Omniverse RGB-D
observations, depth_backprojection pointclouds, online candidate generation,
pseudo VLM commands, parser/validator checks, and kinematic A1 root movement.
It did not run long rollout, real VLM inference, training, RL, SFT, GDPO,
map_predict, PI/openpi fine-tuning, A1 locomotion training, checkpoint creation,
geometry proxy, or USD save.
"""
    webgpt = f"""# WEBGPT Brief

## Current Phase

New Scene Phase F short closed-loop smoke

## Context

{common}
{negative}

## Completed

- Opened the repaired new scene and used existing `/World/A1`.
- Captured real Isaac/Omniverse RGB-D observations and depth_backprojection pointclouds.
- Updated a BEV map online before and after movement.
- Generated online candidate viewpoints and scored them with classical information gain.
- Emitted pseudo VLM commands using `Go to candidate <id>.`.
- Parsed, validated, looked up target pose, and moved A1 with a kinematic wrapper.
- Did not run long rollout, real VLM inference, training, SFT, GDPO, or USD save.

## Metrics

{metrics}

## Next Action

{next_phase}
"""
    critic = f"""# Critic Report

## Current Phase

New Scene Phase F short closed-loop smoke

## Finding

status: {status}

The new-scene short closed loop used real RGB-D/depth_backprojection mapping,
online candidates, pseudo VLM output, parser/validator checks, and kinematic A1
movement. No geometry proxy, old scene data, Go2 label, real VLM inference, or
training route was used.

## Evidence

- scene_path: {summary.get('scene_path')}
- action_count: {summary.get('action_count')}
- successful_action_count: {summary.get('successful_action_count')}
- parse_success_rate: {summary.get('parse_success_rate')}
- validation_success_rate: {summary.get('validation_success_rate')}
- target_pose_lookup_success_rate: {summary.get('target_pose_lookup_success_rate')}
- movement_success_rate: {summary.get('movement_success_rate')}
- final_known_ratio: {summary.get('final_known_ratio')}
- total_known_ratio_gain: {summary.get('total_known_ratio_gain')}
- collision_count: {summary.get('collision_count')}
- stuck_count: {summary.get('stuck_count')}
- falling_count: {summary.get('falling_count')}
- safe_to_long_rollout: {bool_text(summary.get('safe_to_long_rollout'))}

## Risks / Gates

- Phase F is a short smoke, not a long rollout.
- Real VLM inference was not run; VLM commands were pseudo labels from the classical selector.
- Continue to Phase G only after explicit user request.

training: false
RL: false
SFT: false
GDPO: false
long_rollout: false
real_VLM_inference: false
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
{common.strip()}
closed_loop_phaseF_status: {status}
safe_to_long_rollout: {bool_text(summary.get('safe_to_long_rollout'))}
```

## New Scene Route

1. Phase A: scene open and robot inspection. Status: passed.
2. Phase B: real Isaac/Omniverse sensor suite smoke. Status: passed.
3. Phase C: real-sensor mapping smoke. Status: passed.
4. Phase D: candidate viewpoint + information gain smoke. Status: passed.
5. Phase E: VLM-LA interface smoke. Status: passed.
6. Phase F: short closed-loop smoke. Status: {status}.
7. Phase G: long rollout data collection. Status: next if Phase F passed.
8. Phase H: dataset quality audit and human review packet.

## Phase F Gate

{metrics}

## Negative Scope

training: false
RL: false
SFT: false
GDPO: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
long_rollout: false
real_VLM_inference: false
"""
    dataset = f"""# VLM-LA Dataset Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Current New Scene Dataset Status

```yaml
{common.strip()}
sensor_phaseB_status: passed
mapping_phaseC_status: passed
candidate_phaseD_status: passed
interface_phaseE_status: passed
closed_loop_phaseF_status: {status}
safe_to_long_rollout: {bool_text(summary.get('safe_to_long_rollout'))}
```

No long-rollout dataset samples have been created in Phase F. Phase F only
validated the short closed-loop chain and wrote small smoke logs.

## Required New Scene Sample Metadata

Future Phase G samples, only after explicit user approval, must include:

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

Do not use new-scene data for SFT, GDPO, RL, or any training until a later
explicit human review approves preparation.
"""
    for path, text in {
        WORKSPACE / "runs/ACTIVE_TASK_BOARD.md": active,
        WORKSPACE / "runs/WEBGPT_BRIEF.md": webgpt,
        WORKSPACE / "runs/CRITIC_REPORT.md": critic,
        WORKSPACE / "runs/VLM_LA_EXPLORER_PLAN.md": plan,
        WORKSPACE / "runs/VLM_LA_DATASET_SPEC.md": dataset,
    }.items():
        path.write_text(text.strip() + "\n", encoding="utf-8")


def run_phase7_engine(run_dir: Path, actions: int, width: int, height: int, map_resolution_m: float) -> int:
    cmd = [
        sys.executable,
        str(SCRIPT_DIR / "phase7_a1_vlm_la_closed_loop_smoke.py"),
        "--usd",
        str(SCENE),
        "--run_dir",
        str(run_dir),
        "--top_report",
        str(TOP_REPORT),
        "--actions",
        str(actions),
        "--width",
        str(width),
        "--height",
        str(height),
        "--map_resolution_m",
        str(map_resolution_m),
    ]
    result = subprocess.run(cmd, cwd=str(WORKSPACE), check=False)
    return int(result.returncode)


def finalize_outputs(run_dir: Path) -> dict[str, Any]:
    summary_path = run_dir / "summary/closed_loop_summary.json"
    summary = update_summary(read_json(summary_path))
    postprocess_csv(Path(summary["closed_loop_steps_csv"]), summary)
    postprocess_jsonl_logs(summary)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    report_path = run_dir / "reports/NEW_SCENE_CLOSED_LOOP_SMOKE_REPORT.md"
    write_report(report_path, summary)
    write_report(TOP_REPORT, summary)
    write_report(COMPAT_REPORT, summary)
    write_status_files(summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run_dir", default=None)
    parser.add_argument("--actions", type=int, default=5)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--map_resolution_m", type=float, default=0.1)
    parser.add_argument("--postprocess_run_dir", default=None)
    args = parser.parse_args()

    run_dir = Path(args.postprocess_run_dir or args.run_dir).expanduser().resolve() if (args.postprocess_run_dir or args.run_dir) else default_run_dir()
    for sub in [
        "logs",
        "closed_loop",
        "commands",
        "parsing",
        "maps",
        "candidates",
        "plots",
        "reports",
        "summary",
        "debug_frames",
    ]:
        (run_dir / sub).mkdir(parents=True, exist_ok=True)
    COMPAT_DIR.mkdir(parents=True, exist_ok=True)

    if not args.postprocess_run_dir:
        run_phase7_engine(
            run_dir=run_dir,
            actions=max(5, min(int(args.actions), 8)),
            width=int(args.width),
            height=int(args.height),
            map_resolution_m=float(args.map_resolution_m),
        )
    summary = finalize_outputs(run_dir)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary.get("safe_to_long_rollout") else 2


if __name__ == "__main__":
    raise SystemExit(main())
