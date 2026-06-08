#!/usr/bin/env python3
"""New Scene Phase G: real-sensor VLM-LA long rollout data collection.

This wrapper retargets the validated Phase 8 rollout engine to the repaired new
scene. The engine performs the Isaac/Omniverse RGB-D closed-loop collection; the
parent process then rewrites summaries, samples, reports, and status files into
the New Scene Phase G schema.

No training, real VLM inference, geometry proxy, mounted proxy, USD save, or
checkpoint path is used.
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
ENGINE = SCRIPT_DIR / "phase8_a1_vlm_la_long_rollout.py"

PROJECT_NAME = "A1-VLM-LA Explorer"
MAIN_GOAL = "A1-VLM-LA Explorer for 3D Active Exploration"
PHASE = "New Scene Phase G long rollout data collection"
SCENE_ID = "building_scene_1_scene_20260608_171052"
SCENE = WORKSPACE / "scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda"
ORIGINAL_USER_USD = WORKSPACE / "building_scene(1).usd"
TOP_REPORT = WORKSPACE / "runs/NEW_SCENE_VLM_LA_LONG_ROLLOUT_REPORT.md"
COMPAT_DIR = WORKSPACE / "runs/new_scene_sampling_building_scene_1"
COMPAT_REPORT = COMPAT_DIR / "NEW_SCENE_VLM_LA_LONG_ROLLOUT_REPORT.md"

OUTPUT_CONTRACT = "Go to candidate <id>."
ROBOT_PLATFORM = "unitree_a1"
ROBOT_SOURCE = "existing_usd_prim"
SENSOR_METHOD = "real_isaac_omniverse_rgbd"
CAMERA_POINTCLOUD_SOURCE = "depth_backprojection"
VLM_OUTPUT_MODE = "pseudo_from_classical_selector"
LABEL_SOURCE = "classical_argmax_information_gain_minus_path_cost"
DATASET_NAME = "new_scene_building_scene_1_a1_vlm_la_real_sensor_rollout_v0"
NEXT_PASS = "New Scene Phase H dataset quality audit / human review packet"
NEXT_FAIL = "Fix New Scene Phase G long rollout data collection"
PHASE_F_REQUIRED_COMMIT = "daf915f new scene: validate short closed loop smoke"


def bool_text(value: Any) -> str:
    return "true" if bool(value) else "false"


def rate(num: int, den: int) -> float:
    return round(num / den, 4) if den else 0.0


def default_run_dir(smoke: bool) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "_smoke" if smoke else ""
    return WORKSPACE / "runs" / f"new_scene_building_scene_1_phaseG_long_rollout_{timestamp}{suffix}"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def rewrite_sample_id(sample_id: str) -> str:
    marker = "_a1_"
    if marker in sample_id:
        return f"new_scene_building_scene_1_a1_{sample_id.split(marker, 1)[1]}"
    return sample_id.replace("home_like_scene_v1", "new_scene_building_scene_1")


def update_csv(path: Path, extra: dict[str, Any]) -> None:
    if not path.exists():
        return
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
    if not rows:
        return
    for row in rows:
        for key, value in extra.items():
            row[key] = value
    fieldnames = list(rows[0].keys())
    for key in extra:
        if key not in fieldnames:
            fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def run_engine(args: argparse.Namespace, run_dir: Path) -> int:
    logs = run_dir / "logs"
    reports = run_dir / "reports"
    for name in [
        "logs",
        "rollout",
        "samples",
        "bev_renders",
        "debug_frames",
        "commands",
        "parsing",
        "candidates",
        "maps",
        "plots",
        "reports",
        "summary",
    ]:
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    for start_id in range(int(args.start_count)):
        (run_dir / f"start_{start_id:03d}").mkdir(parents=True, exist_ok=True)

    engine_report = reports / "A1_ENGINE_LONG_ROLLOUT_REPORT.md"
    cmd = [
        sys.executable,
        str(ENGINE),
        "--usd",
        str(SCENE),
        "--run_dir",
        str(run_dir),
        "--top_report",
        str(engine_report),
        "--start_count",
        str(args.start_count),
        "--max_actions_per_start",
        str(args.max_actions_per_start),
        "--width",
        str(args.width),
        "--height",
        str(args.height),
        "--map_resolution_m",
        str(args.map_resolution_m),
        "--map_width_m",
        str(args.map_width_m),
        "--map_height_m",
        str(args.map_height_m),
        "--save_debug_every",
        str(args.save_debug_every),
    ]
    (logs / "phaseG_engine_command.txt").write_text(" ".join(cmd) + "\n", encoding="utf-8")
    with (logs / "phaseG_engine_stdout.log").open("w", encoding="utf-8") as stdout, (
        logs / "phaseG_engine_stderr.log"
    ).open("w", encoding="utf-8") as stderr:
        completed = subprocess.run(cmd, cwd=str(WORKSPACE), stdout=stdout, stderr=stderr, check=False)
    return int(completed.returncode)


def compute_safe(summary: dict[str, Any], smoke: bool) -> bool:
    if smoke:
        return False
    total_actions = int(summary.get("total_action_count") or 0)
    candidate_rows = int(summary.get("candidate_rows") or 0)
    return bool(
        summary.get("scene_open_result")
        and summary.get("a1_root_exists")
        and summary.get("real_rgb_sensor_available")
        and summary.get("real_depth_sensor_available")
        and summary.get("real_camera_pointcloud_available")
        and summary.get("geometry_proxy_used") is False
        and summary.get("mounted_geometry_proxy_used") is False
        and int(summary.get("start_count") or 0) >= 10
        and int(summary.get("completed_start_count") or 0) >= 10
        and total_actions >= 20
        and candidate_rows >= max(total_actions * 16, 1)
        and float(summary.get("parse_success_rate") or 0.0) >= 0.99
        and float(summary.get("validation_success_rate") or 0.0) >= 0.95
        and float(summary.get("movement_success_rate") or 0.0) >= 0.8
        and float(summary.get("real_rgb_sensor_valid_rate") or 0.0) >= 0.95
        and float(summary.get("real_depth_sensor_valid_rate") or 0.0) >= 0.99
        and float(summary.get("real_camera_pointcloud_valid_rate") or 0.0) >= 0.99
        and int(summary.get("collision_count") or 0) == 0
        and int(summary.get("stuck_count") or 0) == 0
        and int(summary.get("falling_count") or 0) == 0
        and not summary.get("core_dump_found")
    )


def postprocess_samples(run_dir: Path, summary: dict[str, Any]) -> None:
    samples_path = run_dir / "samples/vlm_la_samples.jsonl"
    samples = load_jsonl(samples_path)
    for sample in samples:
        sample["sample_id"] = rewrite_sample_id(str(sample.get("sample_id", "")))
        sample["phase"] = PHASE
        sample["workspace"] = str(WORKSPACE)
        sample["scene_id"] = SCENE_ID
        sample["scene_path"] = str(SCENE)
        sample["robot_platform"] = ROBOT_PLATFORM
        sample["robot_source"] = ROBOT_SOURCE
        sample["sensor_method"] = SENSOR_METHOD
        sample["camera_pointcloud_source"] = CAMERA_POINTCLOUD_SOURCE
        sample["geometry_proxy_used"] = False
        sample["mounted_geometry_proxy_used"] = False
        sample["label_source"] = LABEL_SOURCE
        sample["output_contract"] = OUTPUT_CONTRACT
        sample["real_vlm_inference"] = False
        sample["training"] = False
    write_jsonl(samples_path, samples)
    summary["vlm_la_sample_count"] = len(samples)

    for rel_path in ["commands/command_log.jsonl", "parsing/parse_log.jsonl"]:
        path = run_dir / rel_path
        rows = load_jsonl(path)
        for row in rows:
            if "sample_id" in row:
                row["sample_id"] = rewrite_sample_id(str(row["sample_id"]))
            row["phase"] = PHASE
            row["scene_id"] = SCENE_ID
            row["scene_path"] = str(SCENE)
            row["output_contract"] = OUTPUT_CONTRACT
            row["real_vlm_inference"] = False
            row["training"] = False
        write_jsonl(path, rows)


def postprocess_manifest(run_dir: Path, summary: dict[str, Any]) -> None:
    manifest_path = run_dir / "samples/dataset_manifest.json"
    manifest = {
        "dataset_name": DATASET_NAME,
        "sample_format": "vlm_la_jsonl",
        "sample_file": "samples/vlm_la_samples.jsonl",
        "robot_platform": ROBOT_PLATFORM,
        "robot_source": ROBOT_SOURCE,
        "scene_id": SCENE_ID,
        "scene_path": str(SCENE),
        "sensor_method": SENSOR_METHOD,
        "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE,
        "label_source": LABEL_SOURCE,
        "output_contract": OUTPUT_CONTRACT,
        "training_ready": False,
        "requires_human_review": True,
        "sample_count": int(summary.get("vlm_la_sample_count") or 0),
    }
    write_json(manifest_path, manifest)
    summary["dataset_manifest_path"] = str(manifest_path)


def postprocess_csvs(run_dir: Path) -> None:
    extra = {
        "phase": PHASE,
        "scene_id": SCENE_ID,
        "scene_path": str(SCENE),
        "robot_platform": ROBOT_PLATFORM,
        "robot_source": ROBOT_SOURCE,
        "sensor_method": SENSOR_METHOD,
        "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE,
        "geometry_proxy_used": "false",
        "mounted_geometry_proxy_used": "false",
    }
    update_csv(run_dir / "summary/rollout_steps.csv", extra)
    update_csv(run_dir / "summary/candidate_summary.csv", extra)


def postprocess_summary(
    run_dir: Path,
    args: argparse.Namespace,
    engine_returncode: int,
) -> dict[str, Any]:
    summary_path = run_dir / "summary/rollout_summary.json"
    summary = read_json(summary_path)
    postprocess_samples(run_dir, summary)
    postprocess_manifest(run_dir, summary)
    postprocess_csvs(run_dir)

    safe = compute_safe(summary, bool(args.smoke))
    summary.update(
        {
            "phase": PHASE,
            "workspace": str(WORKSPACE),
            "project_name": PROJECT_NAME,
            "main_goal": MAIN_GOAL,
            "current_scene_id": SCENE_ID,
            "scene_path": str(SCENE),
            "original_user_usd_path": str(ORIGINAL_USER_USD),
            "robot_platform": ROBOT_PLATFORM,
            "robot_source": ROBOT_SOURCE,
            "a1_root_prim": "/World/A1",
            "base_frame": "/World/A1/base",
            "sensor_method": SENSOR_METHOD,
            "camera_pointcloud_source": CAMERA_POINTCLOUD_SOURCE,
            "geometry_proxy_used": False,
            "mounted_geometry_proxy_used": False,
            "vlm_output_mode": VLM_OUTPUT_MODE,
            "real_vlm_inference": False,
            "output_contract": OUTPUT_CONTRACT,
            "label_source": LABEL_SOURCE,
            "dataset_name": DATASET_NAME,
            "start_count": int(args.start_count),
            "max_actions_per_start": int(args.max_actions_per_start),
            "training_started": False,
            "RL_started": False,
            "SFT_started": False,
            "GDPO_started": False,
            "map_predict_started": False,
            "checkpoint_created": False,
            "PI_finetuning": False,
            "A1_locomotion_training": False,
            "training_ready": False,
            "requires_human_review": True,
            "safe_to_human_review": safe,
            "safe_to_continue_phase9": safe,
            "smoke_only": bool(args.smoke),
            "engine_returncode": engine_returncode,
            "phaseF_commit_required": PHASE_F_REQUIRED_COMMIT,
            "next_phase": NEXT_PASS if safe else NEXT_FAIL,
            "top_report": str(TOP_REPORT),
            "compat_report": str(COMPAT_REPORT),
            "vlm_la_samples_path": str(run_dir / "samples/vlm_la_samples.jsonl"),
            "rollout_summary_path": str(summary_path),
            "candidate_summary_path": str(run_dir / "summary/candidate_summary.csv"),
            "rollout_steps_csv": str(run_dir / "summary/rollout_steps.csv"),
            "start_summary_csv": str(run_dir / "summary/start_summary.csv"),
            "command_log_jsonl": str(run_dir / "commands/command_log.jsonl"),
            "parse_log_jsonl": str(run_dir / "parsing/parse_log.jsonl"),
            "plots_path": str(run_dir / "plots"),
            "caveats": [
                "Pseudo VLM commands are generated by the classical selector; no real VLM inference was run.",
                "A1 movement uses kinematic root updates; no A1 locomotion controller was trained or used.",
                "Samples are prototypes and require Phase H human review before any training use.",
                "Debug RGB-D and BEV images are kept in the ignored run directory and are not committed.",
                "The repaired USD scene is opened read-only and is not saved or overwritten.",
                "The new scene can emit non-blocking MDL material warnings during Isaac loading.",
            ],
        }
    )
    write_json(summary_path, summary)
    return summary


def write_report(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# New Scene VLM-LA Long Rollout Report",
        "",
        "phase: New Scene Phase G",
        f"workspace: {summary.get('workspace')}",
        f"project_name: {summary.get('project_name')}",
        f"current_scene_id: {summary.get('current_scene_id')}",
        f"scene_path: {summary.get('scene_path')}",
        f"robot_platform: {summary.get('robot_platform')}",
        f"robot_source: {summary.get('robot_source')}",
        f"a1_root_prim: {summary.get('a1_root_prim')}",
        f"base_frame: {summary.get('base_frame')}",
        f"sensor_method: {summary.get('sensor_method')}",
        f"camera_pointcloud_source: {summary.get('camera_pointcloud_source')}",
        f"geometry_proxy_used: {bool_text(summary.get('geometry_proxy_used'))}",
        f"mounted_geometry_proxy_used: {bool_text(summary.get('mounted_geometry_proxy_used'))}",
        f"vlm_output_mode: {summary.get('vlm_output_mode')}",
        f"real_vlm_inference: {bool_text(summary.get('real_vlm_inference'))}",
        f"output_contract: {summary.get('output_contract')}",
        f"start_count: {summary.get('start_count')}",
        f"completed_start_count: {summary.get('completed_start_count')}",
        f"max_actions_per_start: {summary.get('max_actions_per_start')}",
        f"total_action_count: {summary.get('total_action_count')}",
        f"total_step_rows: {summary.get('total_step_rows')}",
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
        f"real_rgb_sensor_available: {bool_text(summary.get('real_rgb_sensor_available'))}",
        f"real_depth_sensor_available: {bool_text(summary.get('real_depth_sensor_available'))}",
        f"real_camera_pointcloud_available: {bool_text(summary.get('real_camera_pointcloud_available'))}",
        f"real_rgb_sensor_valid_rate: {summary.get('real_rgb_sensor_valid_rate')}",
        f"real_depth_sensor_valid_rate: {summary.get('real_depth_sensor_valid_rate')}",
        f"real_camera_pointcloud_valid_rate: {summary.get('real_camera_pointcloud_valid_rate')}",
        f"dataset_manifest path: {summary.get('dataset_manifest_path')}",
        f"vlm_la_samples path: {summary.get('vlm_la_samples_path')}",
        f"rollout_summary path: {summary.get('rollout_summary_path')}",
        f"candidate_summary path: {summary.get('candidate_summary_path')}",
        f"rollout_steps path: {summary.get('rollout_steps_csv')}",
        f"plots path: {summary.get('plots_path')}",
        f"safe_to_human_review: {bool_text(summary.get('safe_to_human_review'))}",
        f"training_ready: {bool_text(summary.get('training_ready'))}",
        "training: false",
        "RL: false",
        "SFT: false",
        "GDPO: false",
        "map_predict: false",
        "PI_finetuning: false",
        "A1_locomotion_training: false",
        "checkpoint_created: false",
        "",
        "## Caveats",
        "",
    ]
    for caveat in summary.get("caveats", []):
        lines.append(f"- {caveat}")
    lines.extend(
        [
            "",
            "## Artifacts",
            "",
            f"- run_dir: {summary.get('run_dir')}",
            f"- dataset_manifest: {summary.get('dataset_manifest_path')}",
            f"- vlm_la_samples: {summary.get('vlm_la_samples_path')}",
            f"- rollout_summary: {summary.get('rollout_summary_path')}",
            f"- rollout_steps_csv: {summary.get('rollout_steps_csv')}",
            f"- candidate_summary_csv: {summary.get('candidate_summary_path')}",
            f"- command_log_jsonl: {summary.get('command_log_jsonl')}",
            f"- parse_log_jsonl: {summary.get('parse_log_jsonl')}",
            f"- plots_path: {summary.get('plots_path')}",
            "",
            "## Evidence",
            "",
            "- The repaired new scene was opened read-only and was not saved or overwritten.",
            "- RGB-D observations came from Isaac/Omniverse Replicator annotators.",
            "- Pointclouds came from depth backprojection using camera intrinsics.",
            "- Candidate labels use the final command contract: `Go to candidate <id>.`",
            "- Dataset manifest keeps `training_ready: false` and `requires_human_review: true`.",
            "",
            "## Negative Scope",
            "",
            "- No VLM training, SFT, GDPO, RL, map_predict, PI/openpi fine-tuning, or A1 locomotion training.",
            "- No real VLM inference.",
            "- No geometry proxy or mounted geometry proxy.",
            "- No checkpoint, core dump, USD bundle, mesh, texture, or dependency is included.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_status_files(summary: dict[str, Any]) -> None:
    current_phase = PHASE
    status = "passed" if summary.get("safe_to_human_review") else "needs_fix"
    next_phase = summary.get("next_phase")
    common = f"""current_scene_id: {SCENE_ID}
current_scene_path: {SCENE}
original_user_usd_path: {ORIGINAL_USER_USD}
current_scene_phase: {current_phase}
robot_platform: {ROBOT_PLATFORM}
robot_source: {ROBOT_SOURCE}
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: {SENSOR_METHOD}
camera_pointcloud_source: {CAMERA_POINTCLOUD_SOURCE}
map_update_source: depth_backprojection_pointcloud
candidate_data_source: online_new_scene_real_sensor_candidate_generation
vlm_output_mode: {VLM_OUTPUT_MODE}
output_contract: {OUTPUT_CONTRACT}
training_ready: false
requires_human_review: true
safe_to_human_review: {bool_text(summary.get('safe_to_human_review'))}
next_phase: {next_phase}
"""
    negative = """negative_scope:
- training: false
- RL: false
- SFT: false
- GDPO: false
- map_predict: false
- real_VLM_inference: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- checkpoint_created: false
"""
    metrics = f"""start_count: {summary.get('start_count')}
completed_start_count: {summary.get('completed_start_count')}
max_actions_per_start: {summary.get('max_actions_per_start')}
total_action_count: {summary.get('total_action_count')}
candidate_rows: {summary.get('candidate_rows')}
vlm_la_sample_count: {summary.get('vlm_la_sample_count')}
average_final_known_ratio: {summary.get('average_final_known_ratio')}
average_known_ratio_gain: {summary.get('average_known_ratio_gain')}
parse_success_rate: {summary.get('parse_success_rate')}
validation_success_rate: {summary.get('validation_success_rate')}
movement_success_rate: {summary.get('movement_success_rate')}
starts_with_failures: {summary.get('starts_with_failures')}
collision_count: {summary.get('collision_count')}
stuck_count: {summary.get('stuck_count')}
falling_count: {summary.get('falling_count')}
real_rgb_sensor_valid_rate: {summary.get('real_rgb_sensor_valid_rate')}
real_depth_sensor_valid_rate: {summary.get('real_depth_sensor_valid_rate')}
real_camera_pointcloud_valid_rate: {summary.get('real_camera_pointcloud_valid_rate')}
"""

    (WORKSPACE / "runs/ACTIVE_TASK_BOARD.md").write_text(
        f"""# Active Task Board

current_phase: {current_phase}
workspace: {WORKSPACE}
main_goal: {MAIN_GOAL}
{common}
{negative}

## New Scene Phase G Result

status: {status}
run_dir: {summary.get('run_dir')}
script: {WORKSPACE / 'scripts/new_scene_phaseG_long_rollout.py'}
report: {TOP_REPORT}
summary_json: {summary.get('rollout_summary_path')}
rollout_steps_csv: {summary.get('rollout_steps_csv')}
candidate_summary_csv: {summary.get('candidate_summary_path')}
vlm_la_samples_jsonl: {summary.get('vlm_la_samples_path')}
dataset_manifest: {summary.get('dataset_manifest_path')}

{metrics}

## Scope

Phase G collected new-scene real-sensor VLM-LA rollout prototype data. Labels
are pseudo VLM commands from the classical selector using `{OUTPUT_CONTRACT}`.
No real VLM inference, training, RL, SFT, GDPO, map_predict, checkpoint,
geometry proxy, mounted geometry proxy, or USD save was used.
""",
        encoding="utf-8",
    )

    (WORKSPACE / "runs/WEBGPT_BRIEF.md").write_text(
        f"""# WEBGPT Brief

## Current Phase

{current_phase}

## Context

{common}
{negative}

## Completed

- Collected new-scene real Isaac/Omniverse RGB-D rollout samples.
- Used `/World/A1` and `/World/A1/base` as the existing USD robot prims.
- Updated BEV maps from depth-backprojected pointclouds.
- Generated online candidate viewpoints and pseudo VLM labels.
- Enforced the output contract `{OUTPUT_CONTRACT}`.
- Kept `training_ready: false` and `requires_human_review: true`.

## Metrics

{metrics}

## Next Action

{next_phase}
""",
        encoding="utf-8",
    )

    (WORKSPACE / "runs/CRITIC_REPORT.md").write_text(
        f"""# Critic Report

## Current Phase

{current_phase}

## Finding

status: {status}

New Scene Phase G used the repaired new scene, existing `/World/A1`, real
Isaac/Omniverse RGB-D observations, depth_backprojection pointclouds, online
candidate generation, pseudo VLM command labels, parser/validator checks, and
kinematic A1 root movement. It did not use geometry proxy, mounted proxy, old
scene data, Go2 labels, real VLM inference, or any training route.

## Evidence

- scene_path: {SCENE}
- run_dir: {summary.get('run_dir')}
- dataset_manifest: {summary.get('dataset_manifest_path')}
- vlm_la_samples: {summary.get('vlm_la_samples_path')}
- safe_to_human_review: {bool_text(summary.get('safe_to_human_review'))}
- {metrics.replace(chr(10), chr(10) + '- ').rstrip('- ')}

## Risks / Gates

- Samples are not training-ready and require Phase H human review.
- VLM commands are pseudo labels from a classical selector; no real VLM inference was run.
- Movement uses a kinematic root wrapper, not an A1 locomotion controller.

training: false
RL: false
SFT: false
GDPO: false
map_predict: false
real_VLM_inference: false
USD_modified_or_saved: false
""",
        encoding="utf-8",
    )

    (WORKSPACE / "runs/VLM_LA_EXPLORER_PLAN.md").write_text(
        f"""# VLM-LA Explorer Plan

## Method Name

{PROJECT_NAME}

Full route name:

{MAIN_GOAL}

## Output Contract

`{OUTPUT_CONTRACT}`

## Current New Scene

```yaml
{common}phaseG_status: {status}
```

## New Scene Route

1. Phase A: scene open and robot inspection. Status: passed.
2. Phase B: real Isaac/Omniverse sensor suite smoke. Status: passed.
3. Phase C: real-sensor mapping smoke. Status: passed.
4. Phase D: candidate viewpoint + information gain smoke. Status: passed.
5. Phase E: VLM-LA interface smoke. Status: passed.
6. Phase F: short closed-loop smoke. Status: passed.
7. Phase G: long rollout data collection. Status: {status}.
8. Phase H: dataset quality audit and human review packet.

## Phase G Gate

{metrics}

## Negative Scope

training: false
RL: false
SFT: false
GDPO: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
real_VLM_inference: false
training_ready: false
""",
        encoding="utf-8",
    )

    (WORKSPACE / "runs/VLM_LA_DATASET_SPEC.md").write_text(
        f"""# VLM-LA Dataset Spec

## Project Route

{MAIN_GOAL}

## Current New Scene Dataset Status

```yaml
{common}dataset_name: {DATASET_NAME}
sample_format: vlm_la_jsonl
sample_file: {summary.get('vlm_la_samples_path')}
dataset_manifest: {summary.get('dataset_manifest_path')}
phaseG_status: {status}
```

## Phase G Sample Metadata

Each sample records real RGB-D metadata, depth_backprojection pointcloud stats,
BEV map and candidate image references, candidate table data, selected candidate
ID, target language, parser and validator results, target pose lookup, movement
result, map statistics, and failure reason if present.

## Training Gate

training_ready: false
requires_human_review: true

Do not use new-scene data for SFT, GDPO, RL, or any training until a later
explicit human review approves preparation.
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run_dir", default="")
    parser.add_argument("--start_count", type=int, default=10)
    parser.add_argument("--max_actions_per_start", type=int, default=20)
    parser.add_argument("--width", type=int, default=320)
    parser.add_argument("--height", type=int, default=240)
    parser.add_argument("--map_resolution_m", type=float, default=0.2)
    parser.add_argument("--map_width_m", type=float, default=16.0)
    parser.add_argument("--map_height_m", type=float, default=16.0)
    parser.add_argument("--save_debug_every", type=int, default=1)
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--skip_engine", action="store_true", help="Post-process an existing run_dir only.")
    parser.add_argument("--no_status", action="store_true")
    parser.add_argument("--no_top_report", action="store_true")
    args = parser.parse_args()

    if args.smoke:
        args.start_count = min(args.start_count, 2)
        args.max_actions_per_start = min(args.max_actions_per_start, 5)

    run_dir = Path(args.run_dir).expanduser().resolve() if args.run_dir else default_run_dir(args.smoke)
    run_dir.mkdir(parents=True, exist_ok=True)

    if not SCENE.exists():
        raise FileNotFoundError(str(SCENE))
    if not ENGINE.exists():
        raise FileNotFoundError(str(ENGINE))

    engine_returncode = 0
    if not args.skip_engine:
        engine_returncode = run_engine(args, run_dir)

    summary = postprocess_summary(run_dir, args, engine_returncode)
    run_report = run_dir / "reports/NEW_SCENE_VLM_LA_LONG_ROLLOUT_REPORT.md"
    write_report(run_report, summary)
    if not args.no_top_report:
        write_report(TOP_REPORT, summary)
        COMPAT_DIR.mkdir(parents=True, exist_ok=True)
        write_report(COMPAT_REPORT, summary)
    if not args.no_status and not args.smoke:
        write_status_files(summary)

    print(json.dumps(summary, indent=2, ensure_ascii=False))

    if args.smoke:
        min_smoke_ok = bool(
            summary.get("scene_open_result")
            and summary.get("a1_root_exists")
            and int(summary.get("total_action_count") or 0) >= 2
            and float(summary.get("parse_success_rate") or 0.0) >= 0.99
            and float(summary.get("validation_success_rate") or 0.0) >= 0.95
            and float(summary.get("movement_success_rate") or 0.0) >= 0.8
            and not summary.get("geometry_proxy_used")
            and not summary.get("mounted_geometry_proxy_used")
        )
        return 0 if min_smoke_ok else 2
    return 0 if summary.get("safe_to_human_review") else 2


if __name__ == "__main__":
    raise SystemExit(main())
