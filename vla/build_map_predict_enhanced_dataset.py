"""Build a small MapPredict-enhanced VLA sample preview.

This script produces preview JSONL only. It does not construct a full training
dataset and does not start VLA, SFT, GDPO, RL, diffusion, or rollout jobs.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from exploration.frontier_feature_schema import validate_enhanced_vla_sample
from map_predict.export_frontier_features import export_frontier_features, resolve_phase5_table


WORKSPACE = Path("/home/ubuntu22/VLA")
TARGET_ACTION_RE = re.compile(r"^Go to candidate \d+\.$")


def build_run_dir(run_dir: Path | None) -> Path:
    if run_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = WORKSPACE / f"runs/map_predict_phase6_feature_integration_{timestamp}"
    for name in ("logs", "samples", "summary", "reports", "debug"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    (run_dir / "logs/phase6.started").write_text(datetime.now().isoformat() + "\n", encoding="utf-8")
    return run_dir


def _candidate_table_from_features(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    table = []
    for feature in features:
        frontier_id = int(feature["frontier_id"])
        table.append(
            {
                "candidate_id": frontier_id,
                "source": "map_predict_frontier",
                "frontier_id": frontier_id,
                "map_predict_score": feature.get("map_predict_score"),
                "reachability_proxy": feature.get("reachability_proxy"),
            }
        )
    return table


def build_enhanced_sample(
    *,
    sample_id: str,
    features: list[dict[str, Any]],
    selection: dict[str, Any],
) -> dict[str, Any]:
    selected_frontier_id = selection.get("selected_frontier_id")
    selected_candidate_id = int(selected_frontier_id) if selected_frontier_id is not None else None
    target_action = f"Go to candidate {selected_candidate_id}." if selected_candidate_id is not None else ""
    return {
        "sample_id": sample_id,
        "robot_platform": "unitree_a1",
        "sensor_method": "real_isaac_omniverse_rgbd",
        "images": {
            "bev_explored_map": None,
            "rgb": None,
            "map_predict_bev_occ": None,
            "map_predict_uncertainty": None,
            "frontier_overlay": None,
        },
        "candidate_table": _candidate_table_from_features(features),
        "map_predict_frontier_features": features,
        "map_predict_selector": {
            "selected_frontier_id": selected_frontier_id,
            "score": selection.get("score"),
            "reason": selection.get("reason", {}),
            "failure_reason": selection.get("failure_reason", ""),
        },
        "prompt": "Select the best next viewpoint for active exploration.",
        "action_type": "high_level_candidate_action",
        "target_action": target_action,
        "selected_candidate_id": selected_candidate_id,
        "training": False,
    }


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frontier-table", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--preview-count", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_dir = build_run_dir(args.run_dir)
    frontier_table = resolve_phase5_table(args.frontier_table)
    exported = export_frontier_features(frontier_table)
    features_by_sample = exported["features_by_sample"]
    selections = exported["selections_by_sample"]

    samples: list[dict[str, Any]] = []
    invalid_selected_count = 0
    nan_score_count = 0
    validation_error_count = 0
    for sample_id in sorted(features_by_sample)[: max(0, int(args.preview_count))]:
        selection = selections.get(sample_id, {"selected_frontier_id": None, "score": None, "failure_reason": "missing_selection"})
        if selection.get("selected_frontier_id") is None:
            invalid_selected_count += 1
        score = selection.get("score")
        if score is None or score != score:
            nan_score_count += 1
        sample = build_enhanced_sample(sample_id=sample_id, features=features_by_sample[sample_id], selection=selection)
        validation_errors = validate_enhanced_vla_sample(sample)
        if validation_errors:
            validation_error_count += 1
            sample["validation_errors"] = validation_errors
        samples.append(sample)

    preview_path = run_dir / "samples/enhanced_vla_samples_preview.jsonl"
    write_jsonl(preview_path, samples)

    reparsed_count = 0
    target_action_valid = 0
    map_predict_fields_present = 0
    with preview_path.open(encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            reparsed_count += 1
            if TARGET_ACTION_RE.match(str(row.get("target_action", ""))):
                target_action_valid += 1
            if row.get("map_predict_frontier_features"):
                map_predict_fields_present += 1

    sample_count = len(features_by_sample)
    selector_smoke_passed = bool(
        sample_count > 0
        and all(selection.get("selected_frontier_id") is not None for selection in selections.values())
        and all((selection.get("score") is not None and selection.get("score") == selection.get("score")) for selection in selections.values())
    )
    target_action_format_valid_rate = float(target_action_valid / max(reparsed_count, 1))
    summary = {
        "phase": "MapPredict Phase 6 feature integration",
        "source_phase": "MapPredict Phase 5 frontier scoring baseline",
        "source_frontier_table": str(frontier_table),
        "frontier_rows": len(exported["frontier_rows"]),
        "sample_count": sample_count,
        "selector_smoke_passed": selector_smoke_passed,
        "enhanced_vla_preview_count": len(samples),
        "preview_sample_path": str(preview_path),
        "json_parse_count": reparsed_count,
        "nan_score_count": nan_score_count,
        "invalid_selected_count": invalid_selected_count,
        "validation_error_count": validation_error_count,
        "target_action_format_valid_rate": target_action_format_valid_rate,
        "map_predict_feature_field_rate": float(map_predict_fields_present / max(reparsed_count, 1)),
        "safe_to_prepare_full_enhanced_vla_dataset": bool(
            selector_smoke_passed
            and len(samples) > 0
            and invalid_selected_count == 0
            and nan_score_count == 0
            and validation_error_count == 0
            and target_action_format_valid_rate == 1.0
        ),
        "safe_to_integrate_online_selector": bool(selector_smoke_passed and invalid_selected_count == 0 and nan_score_count == 0),
        "training_started": False,
        "map_predict_training_started": False,
        "VLA_training_started": False,
        "SFT_started": False,
        "GDPO_started": False,
        "RL_started": False,
        "diffusion_training_started": False,
        "rollout_started": False,
        "output_contract": "Go to candidate <id>.",
        "action_type": "high_level_candidate_action",
        "data_volume_warning": "current dataset is sufficient for pipeline validation but not enough for final diffusion or VLA training",
    }
    summary_path = run_dir / "summary/map_predict_feature_integration_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
