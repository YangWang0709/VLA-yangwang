#!/usr/bin/env python3
"""Prepare the combined A1 VLM-LA SFT dataset artifacts.

This script only prepares dataset files and protocol drafts. It does not train,
fine-tune, run rollout, run VLM inference, or create checkpoints.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


WORKSPACE = Path("/home/ubuntu22/VLA")
RUNS_DIR = WORKSPACE / "runs"
SCRIPT_PHASE = "Phase 10 combined SFT dataset preparation only"
OUTPUT_CONTRACT = "Go to candidate <id>."
PROJECT_NAME = "A1-VLM-LA Explorer"
MAIN_GOAL = "A1-VLM-LA Explorer for 3D Active Exploration"
OLD_SCENE_PATH = WORKSPACE / "scenes/primary_building_scene_repaired/home_like_scene_v1.usd"
NEW_SCENE_PATH = WORKSPACE / "scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda"
SOURCE_REVIEW_DECISION = RUNS_DIR / "COMBINED_DATASET_REVIEW_DECISION.md"

SYSTEM_PROMPT = (
    "You are an embodied exploration assistant for a Unitree A1 robot. "
    "Given a BEV explored map, robot pose, and candidate viewpoints, choose "
    "the best next viewpoint for active exploration. You must answer using "
    "exactly this format: Go to candidate <id>."
)

USER_PROMPT_PREFIX = """Task: Select the best next viewpoint for active exploration.

Inputs:
- BEV explored map with candidate IDs.
- Optional RGB observation.
- Candidate table.
- Robot pose and map statistics.

Rules:
- Choose exactly one valid candidate ID.
- Do not output coordinates.
- Do not output velocity.
- Do not output joint actions.
- Answer only: Go to candidate <id>.
"""

COMMAND_RE = re.compile(r"^Go to candidate (?P<id>\d+)\.$")


def latest_dir(pattern: str) -> Path:
    matches = sorted(RUNS_DIR.glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No run directory matched {pattern}")
    return matches[-1]


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def workspace_relative(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(WORKSPACE))
    except ValueError:
        return str(path)


def resolve_media_path(source_run_dir: Path, raw_path: str | None) -> Path | None:
    if not raw_path:
        return None
    p = Path(raw_path)
    if p.is_absolute():
        return p
    return source_run_dir / p


def candidate_table(candidates: list[dict[str, Any]]) -> str:
    lines = [
        "id | valid | reachable | x | y | yaw | information_gain | path_cost | score",
        "--- | --- | --- | --- | --- | --- | --- | --- | ---",
    ]
    for cand in candidates:
        lines.append(
            "{id} | {valid} | {reachable} | {x} | {y} | {yaw} | {gain} | {cost} | {score}".format(
                id=cand.get("id"),
                valid=cand.get("is_valid"),
                reachable=cand.get("is_reachable"),
                x=cand.get("x"),
                y=cand.get("y"),
                yaw=cand.get("yaw"),
                gain=cand.get("information_gain"),
                cost=cand.get("path_cost"),
                score=cand.get("score"),
            )
        )
    return "\n".join(lines)


def user_prompt(sample: dict[str, Any], candidates: list[dict[str, Any]]) -> str:
    robot_pose = json.dumps(sample.get("robot_pose", {}), sort_keys=True)
    map_stats = json.dumps(sample.get("map_stats", {}), sort_keys=True)
    return (
        USER_PROMPT_PREFIX
        + "\nRobot pose:\n"
        + robot_pose
        + "\n\nMap statistics:\n"
        + map_stats
        + "\n\nCandidate table:\n"
        + candidate_table(candidates)
    )


def source_bundle(name: str, scene_path: Path, run_pattern: str) -> dict[str, Any]:
    run_dir = latest_dir(run_pattern)
    summary_path = run_dir / "summary/dataset_quality_summary.json"
    summary = read_json(summary_path)
    quality_dir = run_dir / "quality"
    return {
        "name": name,
        "scene_path": str(scene_path),
        "run_dir": str(run_dir),
        "source_run_dir": summary.get("source_run_dir"),
        "summary_path": str(summary_path),
        "summary": summary,
        "accepted_path": str(quality_dir / "accepted_samples.jsonl"),
        "warning_path": str(quality_dir / "warning_samples.jsonl"),
        "rejected_path": str(quality_dir / "rejected_samples.jsonl"),
        "accepted": read_jsonl(quality_dir / "accepted_samples.jsonl"),
        "warning": read_jsonl(quality_dir / "warning_samples.jsonl"),
        "rejected": read_jsonl(quality_dir / "rejected_samples.jsonl"),
    }


def parse_candidate_command(text: str) -> int | None:
    m = COMMAND_RE.match(str(text or "").strip())
    if not m:
        return None
    return int(m.group("id"))


def normalize_scene_id(source_name: str, sample: dict[str, Any]) -> str:
    if sample.get("scene_id"):
        return str(sample["scene_id"])
    if source_name == "old_scene":
        return "old_home_like_scene_v1"
    return source_name


def validate_and_convert(record: dict[str, Any], source: dict[str, Any]) -> dict[str, Any]:
    sample = dict(record.get("sample") or {})
    sample_id = str(record.get("sample_id") or sample.get("sample_id"))
    if not sample_id:
        raise ValueError("Accepted record is missing sample_id")
    if record.get("quality_status") != "pass":
        raise ValueError(f"{sample_id}: non-pass sample entered SFT conversion")

    sensor_method = sample.get("sensor_method")
    if sensor_method != "real_isaac_omniverse_rgbd":
        raise ValueError(f"{sample_id}: unexpected sensor_method {sensor_method}")
    if bool(sample.get("geometry_proxy_used")):
        raise ValueError(f"{sample_id}: geometry_proxy_used is true")
    if bool(sample.get("mounted_geometry_proxy_used")):
        raise ValueError(f"{sample_id}: mounted_geometry_proxy_used is true")

    target_language = str(record.get("target_language") or sample.get("target_language") or "")
    target_candidate_id = parse_candidate_command(target_language)
    if target_candidate_id is None:
        raise ValueError(f"{sample_id}: target_language is not parseable: {target_language}")
    selected_candidate_id = int(record.get("selected_candidate_id", sample.get("selected_candidate_id")))
    if selected_candidate_id != target_candidate_id:
        raise ValueError(f"{sample_id}: selected_candidate_id does not match target_language")

    candidates = list(sample.get("candidates") or [])
    candidate_ids = {int(c.get("id")) for c in candidates if c.get("id") is not None}
    if selected_candidate_id not in candidate_ids:
        raise ValueError(f"{sample_id}: selected candidate id is absent from candidate table")

    source_run_dir = Path(str(source["source_run_dir"]))
    bev_path = resolve_media_path(source_run_dir, sample.get("bev_image"))
    rgb_path = resolve_media_path(source_run_dir, sample.get("rgb_image"))
    depth_path = resolve_media_path(source_run_dir, sample.get("depth_image"))
    if bev_path is None or not bev_path.exists():
        raise FileNotFoundError(f"{sample_id}: BEV candidate render missing: {bev_path}")

    images = [workspace_relative(bev_path)]
    if rgb_path is not None and rgb_path.exists():
        images.append(workspace_relative(rgb_path))

    scene_id = normalize_scene_id(source["name"], sample)
    start_id = int(record.get("start_id", -1))
    step_id = int(record.get("step_id", -1))

    converted = {
        "id": sample_id,
        "sample_id": sample_id,
        "scene_id": scene_id,
        "source_scene_key": source["name"],
        "source_quality_run_dir": source["run_dir"],
        "source_rollout_run_dir": source["source_run_dir"],
        "scene_path": sample.get("scene_path") or source["scene_path"],
        "images": images,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt(sample, candidates)},
            {"role": "assistant", "content": target_language},
        ],
        "robot_platform": sample.get("robot_platform"),
        "robot_source": sample.get("robot_source"),
        "sensor_method": sensor_method,
        "camera_pointcloud_source": sample.get("camera_pointcloud_source"),
        "geometry_proxy_used": bool(sample.get("geometry_proxy_used")),
        "mounted_geometry_proxy_used": bool(sample.get("mounted_geometry_proxy_used")),
        "bev_image": workspace_relative(bev_path),
        "rgb_image": workspace_relative(rgb_path) if rgb_path and rgb_path.exists() else None,
        "depth_image": workspace_relative(depth_path) if depth_path and depth_path.exists() else None,
        "robot_pose": sample.get("robot_pose"),
        "map_stats": sample.get("map_stats"),
        "candidates": candidates,
        "prompt": sample.get("prompt") or "Select the best next viewpoint for active exploration.",
        "target_language": target_language,
        "selected_candidate_id": selected_candidate_id,
        "label_source": sample.get("label_source"),
        "quality_status": record.get("quality_status"),
        "quality_flags": list(record.get("quality_flags") or []),
        "start_id": start_id,
        "step_id": step_id,
        "metadata": {
            "robot_platform": sample.get("robot_platform"),
            "robot_source": sample.get("robot_source"),
            "sensor_method": sensor_method,
            "camera_pointcloud_source": sample.get("camera_pointcloud_source"),
            "geometry_proxy_used": bool(sample.get("geometry_proxy_used")),
            "mounted_geometry_proxy_used": bool(sample.get("mounted_geometry_proxy_used")),
            "selected_candidate_id": selected_candidate_id,
            "label_source": sample.get("label_source"),
            "quality_status": record.get("quality_status"),
            "quality_flags": list(record.get("quality_flags") or []),
            "scene_id": scene_id,
            "scene_path": sample.get("scene_path") or source["scene_path"],
            "start_id": start_id,
            "step_id": step_id,
            "output_contract": OUTPUT_CONTRACT,
        },
    }
    return converted


def split_samples(samples: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    by_scene: dict[str, dict[int, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for sample in samples:
        by_scene[sample["scene_id"]][int(sample["start_id"])].append(sample)

    split_names = ["train", "val", "test"]
    splits: dict[str, list[dict[str, Any]]] = {name: [] for name in split_names}
    split_group_keys: dict[str, list[str]] = {name: [] for name in split_names}

    for scene_id in sorted(by_scene):
        starts = sorted(by_scene[scene_id])
        n = len(starts)
        if n >= 3:
            val_count = max(1, round(n * 0.15))
            test_count = max(1, round(n * 0.15))
            train_count = n - val_count - test_count
            if train_count < 1:
                train_count = 1
                if test_count > 1:
                    test_count -= 1
                else:
                    val_count -= 1
            train_starts = starts[:train_count]
            val_starts = starts[train_count : train_count + val_count]
            test_starts = starts[train_count + val_count :]
        elif n == 2:
            train_starts = starts[:1]
            val_starts = []
            test_starts = starts[1:]
        else:
            train_starts = starts
            val_starts = []
            test_starts = []

        assignment = {
            "train": train_starts,
            "val": val_starts,
            "test": test_starts,
        }
        for split_name, assigned_starts in assignment.items():
            for start_id in assigned_starts:
                rows = sorted(by_scene[scene_id][start_id], key=lambda row: int(row["step_id"]))
                splits[split_name].extend(rows)
                split_group_keys[split_name].append(f"{scene_id}:start{start_id:03d}")

    for split_name in split_names:
        splits[split_name].sort(key=lambda row: (row["scene_id"], int(row["start_id"]), int(row["step_id"])))

    summary = {
        "split_by": "scene_id_and_start_id",
        "target_ratio": {"train": 0.70, "val": 0.15, "test": 0.15},
        "train_sample_count": len(splits["train"]),
        "val_sample_count": len(splits["val"]),
        "test_sample_count": len(splits["test"]),
        "train_scene_ids": sorted({row["scene_id"] for row in splits["train"]}),
        "val_scene_ids": sorted({row["scene_id"] for row in splits["val"]}),
        "test_scene_ids": sorted({row["scene_id"] for row in splits["test"]}),
        "train_start_ids": split_group_keys["train"],
        "val_start_ids": split_group_keys["val"],
        "test_start_ids": split_group_keys["test"],
    }
    return splits, summary


def warning_pool(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for record in source["warning"]:
        sample = dict(record.get("sample") or {})
        rows.append(
            {
                "sample_id": record.get("sample_id") or sample.get("sample_id"),
                "source_scene_key": source["name"],
                "scene_path": sample.get("scene_path") or source["scene_path"],
                "quality_status": record.get("quality_status"),
                "quality_flags": record.get("quality_flags") or [],
                "warning_reason": record.get("warning_reason"),
                "target_language": record.get("target_language") or sample.get("target_language"),
                "excluded_from_sft": True,
                "reason": "warning samples require optional human review and are excluded from first SFT dataset",
            }
        )
    return rows


def rejected_pool(source: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for record in source["rejected"]:
        sample = dict(record.get("sample") or {})
        rows.append(
            {
                "sample_id": record.get("sample_id") or sample.get("sample_id"),
                "source_scene_key": source["name"],
                "scene_path": sample.get("scene_path") or source["scene_path"],
                "quality_status": record.get("quality_status"),
                "quality_flags": record.get("quality_flags") or [],
                "reject_reason": record.get("reject_reason"),
                "excluded_from_sft": True,
                "reason": "rejected samples are never included in SFT dataset",
            }
        )
    return rows


def make_prompt_template() -> str:
    return f"""# Combined VLM SFT Prompt Template

phase: Phase 10 combined SFT dataset preparation only
project_name: {PROJECT_NAME}
output_contract: {OUTPUT_CONTRACT}
training_started: false
SFT_started: false
GDPO_started: false

## System Prompt

{SYSTEM_PROMPT}

## User Prompt Template

Task: Select the best next viewpoint for active exploration.

Inputs:

* BEV explored map with candidate IDs.
* Optional RGB observation.
* Candidate table.
* Robot pose and map statistics.

Rules:

* Choose exactly one valid candidate ID.
* Do not output coordinates.
* Do not output velocity.
* Do not output joint actions.
* Answer only: Go to candidate <id>.

Candidate table:

id | valid | reachable | x | y | yaw | information_gain | path_cost | score
--- | --- | --- | --- | --- | --- | --- | --- | ---
...

## Assistant Output

Go to candidate <id>.
"""


def make_training_config_draft(run_dir: Path, summary: dict[str, Any]) -> str:
    return f"""# Combined VLM SFT Training Config Draft

phase: Phase 10 combined SFT dataset preparation only
draft_only: true
training_started: false
SFT_started: false
GDPO_started: false
checkpoint_created: false
requires_user_approval_before_training: true

## Model Candidates

* Qwen2.5-VL-7B-Instruct for debug
* Qwen2.5-VL-32B-Instruct as main model
* Qwen2.5-VL-72B-Instruct optional strong baseline

## Training Method

* LoRA / QLoRA
* no full fine-tune in first stage

## Input

* BEV candidate render
* optional RGB observation
* candidate table text

## Output

* {OUTPUT_CONTRACT}

## Dataset Paths

* sft_samples: {run_dir / 'dataset/sft_samples.jsonl'}
* train: {run_dir / 'splits/train.jsonl'}
* val: {run_dir / 'splits/val.jsonl'}
* test: {run_dir / 'splits/test.jsonl'}

## Metrics

* exact_candidate_id_accuracy
* parse_success_rate
* valid_output_rate
* invalid_output_rate
* candidate_id_exists_rate
* score_regret
* selected_candidate_valid_rate

## Dataset Counts

* sft_sample_count: {summary['sft_sample_count']}
* train_sample_count: {summary['train_sample_count']}
* val_sample_count: {summary['val_sample_count']}
* test_sample_count: {summary['test_sample_count']}
"""


def make_evaluation_protocol() -> str:
    return f"""# Combined VLM SFT Evaluation Protocol

phase: Phase 10 combined SFT dataset preparation only
project_name: {PROJECT_NAME}
output_contract: {OUTPUT_CONTRACT}
training_started: false
SFT_started: false
GDPO_started: false

## Offline Metrics

1. Parse success rate
2. Exact candidate id accuracy
3. Candidate id exists rate
4. Selected candidate validity rate
5. Score regret
6. Top-k agreement with classical selector
7. Invalid output rate
8. Coordinate / velocity / joint-action rejection rate
9. Per-scene accuracy
10. Old-scene vs new-scene generalization
11. Later closed-loop coverage evaluation

## Hard Rejection Rules

Any output that contains coordinates, velocity commands, joint actions, or any
format other than `Go to candidate <id>.` is invalid for this project contract.
"""


def make_report(run_dir: Path, summary: dict[str, Any], split_summary: dict[str, Any]) -> str:
    return f"""# Combined VLM SFT Dataset Preparation Report

phase: Phase 10
phase_detail: Phase 10 combined SFT dataset preparation only
project_name: {PROJECT_NAME}
main_goal: {MAIN_GOAL}
output_contract: {OUTPUT_CONTRACT}

## Source Scenes

* old_scene: {OLD_SCENE_PATH}
* new_scene: {NEW_SCENE_PATH}

## Source Review Decision

* source_review_decision: {SOURCE_REVIEW_DECISION}
* approve_for_sft_preparation: yes
* approve_for_direct_training: no
* approve_for_gdpo_preparation: no

## Samples Used

* old_scene_accepted_samples: {summary['old_scene_accepted_samples']}
* new_scene_accepted_samples: {summary['new_scene_accepted_samples']}
* accepted_samples_used: {summary['sft_sample_count']}
* warning_samples_excluded: {summary['source_warning_samples']}
* rejected_samples_excluded: {summary['source_rejected_samples']}
* geometry_proxy_used_in_sft: {str(summary['geometry_proxy_used_in_sft']).lower()}
* all_data_real_sensor: true

## Dataset Artifacts

* sft_samples path: {run_dir / 'dataset/sft_samples.jsonl'}
* optional_review_pool path: {run_dir / 'dataset/optional_review_pool.jsonl'}
* rejected_samples_excluded path: {run_dir / 'dataset/rejected_samples_excluded.jsonl'}
* train split path: {run_dir / 'splits/train.jsonl'}
* val split path: {run_dir / 'splits/val.jsonl'}
* test split path: {run_dir / 'splits/test.jsonl'}
* split_summary path: {run_dir / 'splits/split_summary.json'}
* prompt template path: {RUNS_DIR / 'COMBINED_VLM_SFT_PROMPT_TEMPLATE.md'}
* training config draft path: {RUNS_DIR / 'COMBINED_VLM_SFT_TRAINING_CONFIG_DRAFT.md'}
* evaluation protocol path: {RUNS_DIR / 'COMBINED_VLM_SFT_EVALUATION_PROTOCOL.md'}
* summary path: {run_dir / 'summary/combined_sft_dataset_summary.json'}

## Split Summary

* split_by: {split_summary['split_by']}
* train_sample_count: {split_summary['train_sample_count']}
* val_sample_count: {split_summary['val_sample_count']}
* test_sample_count: {split_summary['test_sample_count']}
* train_scene_ids: {', '.join(split_summary['train_scene_ids'])}
* val_scene_ids: {', '.join(split_summary['val_scene_ids'])}
* test_scene_ids: {', '.join(split_summary['test_scene_ids'])}

## Safety

* training_started: false
* SFT_started: false
* GDPO_started: false
* RL_started: false
* checkpoint_created: false
* requires_user_approval_before_training: true

## Recommended Next Phase

user approval for SFT training or collect more rollout data
"""


def phase_status_block(run_dir: Path, summary: dict[str, Any]) -> str:
    return f"""<!-- phase10_combined_sft_status:start -->
## Phase 10 Combined SFT Dataset Preparation Status

current_phase: Phase 10 combined SFT dataset preparation only
project_name: {PROJECT_NAME}
main_goal: {MAIN_GOAL}
output_contract: {OUTPUT_CONTRACT}
source_review_decision: {SOURCE_REVIEW_DECISION}
phase10_run_dir: {run_dir}
sft_sample_count: {summary['sft_sample_count']}
train_sample_count: {summary['train_sample_count']}
val_sample_count: {summary['val_sample_count']}
test_sample_count: {summary['test_sample_count']}
robot_platform: unitree_a1
sensor_method: real_isaac_omniverse_rgbd
geometry_proxy_used_in_sft: false
training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
checkpoint_created: false
requires_user_approval_before_training: true
next_phase: User approval required before SFT training
<!-- phase10_combined_sft_status:end -->
"""


def update_status_file(path: Path, block: str) -> None:
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        text = ""
    start = "<!-- phase10_combined_sft_status:start -->"
    end = "<!-- phase10_combined_sft_status:end -->"
    if start in text and end in text:
        before = text[: text.index(start)]
        after = text[text.index(end) + len(end) :]
        new_text = before.rstrip() + "\n\n" + block.rstrip() + "\n" + after.lstrip()
    else:
        new_text = block.rstrip() + "\n\n" + text.lstrip()
    write_text(path, new_text)


def main() -> None:
    if not SOURCE_REVIEW_DECISION.exists():
        raise FileNotFoundError(SOURCE_REVIEW_DECISION)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUNS_DIR / f"phase10_combined_sft_dataset_preparation_{timestamp}"
    for rel in ["dataset", "splits", "configs", "reports", "summary", "templates", "source_manifests"]:
        (run_dir / rel).mkdir(parents=True, exist_ok=True)

    old = source_bundle("old_scene", OLD_SCENE_PATH, "phase9_human_review_packet_*")
    new = source_bundle("new_scene", NEW_SCENE_PATH, "new_scene_building_scene_1_phaseH_dataset_quality_audit_*")
    sources = [old, new]

    converted: list[dict[str, Any]] = []
    for source in sources:
        for record in source["accepted"]:
            converted.append(validate_and_convert(record, source))
    converted.sort(key=lambda row: (row["scene_id"], int(row["start_id"]), int(row["step_id"])))

    splits, split_summary = split_samples(converted)

    warning_rows = [row for source in sources for row in warning_pool(source)]
    rejected_rows = [row for source in sources for row in rejected_pool(source)]

    write_jsonl(run_dir / "dataset/sft_samples.jsonl", converted)
    write_jsonl(run_dir / "dataset/optional_review_pool.jsonl", warning_rows)
    write_jsonl(run_dir / "dataset/rejected_samples_excluded.jsonl", rejected_rows)
    for split_name, rows in splits.items():
        write_jsonl(run_dir / f"splits/{split_name}.jsonl", rows)
    write_json(run_dir / "splits/split_summary.json", split_summary)

    source_manifest = {
        "phase": SCRIPT_PHASE,
        "source_review_decision": str(SOURCE_REVIEW_DECISION),
        "sources": [
            {
                "name": source["name"],
                "scene_path": source["scene_path"],
                "quality_run_dir": source["run_dir"],
                "source_rollout_run_dir": source["source_run_dir"],
                "accepted_path": source["accepted_path"],
                "warning_path": source["warning_path"],
                "rejected_path": source["rejected_path"],
                "accepted_sample_count": len(source["accepted"]),
                "warning_sample_count": len(source["warning"]),
                "rejected_sample_count": len(source["rejected"]),
            }
            for source in sources
        ],
    }
    write_json(run_dir / "source_manifests/source_manifest.json", source_manifest)

    old_count = len(old["accepted"])
    new_count = len(new["accepted"])
    source_warning_count = sum(len(source["warning"]) for source in sources)
    source_rejected_count = sum(len(source["rejected"]) for source in sources)
    scene_counts = Counter(row["source_scene_key"] for row in converted)
    summary = {
        "phase": SCRIPT_PHASE,
        "workspace": str(WORKSPACE),
        "project_name": PROJECT_NAME,
        "main_goal": MAIN_GOAL,
        "source_review_decision": str(SOURCE_REVIEW_DECISION),
        "old_scene_path": str(OLD_SCENE_PATH),
        "new_scene_path": str(NEW_SCENE_PATH),
        "old_scene_accepted_samples": old_count,
        "new_scene_accepted_samples": new_count,
        "source_warning_samples": source_warning_count,
        "source_rejected_samples": source_rejected_count,
        "sft_sample_count": len(converted),
        "train_sample_count": split_summary["train_sample_count"],
        "val_sample_count": split_summary["val_sample_count"],
        "test_sample_count": split_summary["test_sample_count"],
        "scene_counts": dict(scene_counts),
        "robot_platform": "unitree_a1",
        "robot_source": "existing_usd_prim",
        "a1_root_prim": "/World/A1",
        "sensor_method": "real_isaac_omniverse_rgbd",
        "camera_pointcloud_source": "depth_backprojection",
        "geometry_proxy_used_in_sft": False,
        "mounted_geometry_proxy_used_in_sft": False,
        "output_contract": OUTPUT_CONTRACT,
        "training_started": False,
        "SFT_started": False,
        "RL_started": False,
        "GDPO_started": False,
        "checkpoint_created": False,
        "ready_for_user_training_approval": True,
        "requires_user_approval_before_training": True,
        "run_dir": str(run_dir),
        "sft_samples_path": str(run_dir / "dataset/sft_samples.jsonl"),
        "train_path": str(run_dir / "splits/train.jsonl"),
        "val_path": str(run_dir / "splits/val.jsonl"),
        "test_path": str(run_dir / "splits/test.jsonl"),
        "split_summary_path": str(run_dir / "splits/split_summary.json"),
        "prompt_template_path": str(RUNS_DIR / "COMBINED_VLM_SFT_PROMPT_TEMPLATE.md"),
        "training_config_draft_path": str(RUNS_DIR / "COMBINED_VLM_SFT_TRAINING_CONFIG_DRAFT.md"),
        "evaluation_protocol_path": str(RUNS_DIR / "COMBINED_VLM_SFT_EVALUATION_PROTOCOL.md"),
    }
    expected_count = old_count + new_count
    if len(converted) != expected_count:
        raise RuntimeError(f"Converted sample count mismatch: {len(converted)} != {expected_count}")
    if len(converted) != 273:
        raise RuntimeError(f"Expected 273 first-stage SFT samples, got {len(converted)}")

    write_json(run_dir / "summary/combined_sft_dataset_summary.json", summary)
    write_json(run_dir / "configs/training_config_draft.json", {
        "draft_only": True,
        "model_candidates": [
            "Qwen2.5-VL-7B-Instruct",
            "Qwen2.5-VL-32B-Instruct",
            "Qwen2.5-VL-72B-Instruct",
        ],
        "training_method": "LoRA / QLoRA",
        "full_finetune": False,
        "output_contract": OUTPUT_CONTRACT,
        "training_started": False,
        "SFT_started": False,
        "GDPO_started": False,
    })
    write_text(run_dir / "templates/prompt_template.md", make_prompt_template())
    write_text(RUNS_DIR / "COMBINED_VLM_SFT_PROMPT_TEMPLATE.md", make_prompt_template())
    write_text(RUNS_DIR / "COMBINED_VLM_SFT_TRAINING_CONFIG_DRAFT.md", make_training_config_draft(run_dir, summary))
    write_text(RUNS_DIR / "COMBINED_VLM_SFT_EVALUATION_PROTOCOL.md", make_evaluation_protocol())
    report = make_report(run_dir, summary, split_summary)
    write_text(RUNS_DIR / "COMBINED_VLM_SFT_DATASET_PREPARATION_REPORT.md", report)
    write_text(run_dir / "reports/COMBINED_VLM_SFT_DATASET_PREPARATION_REPORT.md", report)

    block = phase_status_block(run_dir, summary)
    for rel_path in [
        "ACTIVE_TASK_BOARD.md",
        "WEBGPT_BRIEF.md",
        "CRITIC_REPORT.md",
        "VLM_LA_EXPLORER_PLAN.md",
        "VLM_LA_INTERFACE_SPEC.md",
        "VLM_LA_DATASET_SPEC.md",
    ]:
        update_status_file(RUNS_DIR / rel_path, block)

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
