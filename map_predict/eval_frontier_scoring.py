"""Evaluate the Phase 5 handcrafted frontier scoring baseline."""

from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from map_predict.frontier_features import frontier_feature_rows, frontier_mask_from_3d
from map_predict.frontier_scoring import load_scoring_config, score_formula, score_frontiers, to_float


WORKSPACE = Path("/home/ubuntu22/VLA")
DEFAULT_DATASET_ROOT = WORKSPACE / "data/map_predict/local_voxel_dataset/local_voxel_v2_aligned_real_partial_3d"
DEFAULT_CONFIG = WORKSPACE / "configs/map_predict/frontier_scoring_baseline.yaml"
PHASE4_REPORT = WORKSPACE / "runs/MAP_PREDICT_PHASE4_UNCERTAINTY_BEV_REPORT.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--phase4-run-dir", type=Path, default=None)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--run-dir", type=Path, default=None)
    return parser.parse_args()


def resolve_phase4_run_dir(run_dir: Path | None) -> Path:
    if run_dir is not None:
        return run_dir
    if PHASE4_REPORT.exists():
        match = re.search(r"run_dir:\s*(\S+)", PHASE4_REPORT.read_text(encoding="utf-8"))
        if match:
            candidate = Path(match.group(1))
            if candidate.exists():
                return candidate
    candidates = sorted(WORKSPACE.glob("runs/map_predict_phase4_uncertainty_bev_projection_*"))
    candidates = [path for path in candidates if path.is_dir() and not path.name.endswith("_smoke")]
    if not candidates:
        raise FileNotFoundError("could not resolve Phase 4 run directory")
    return candidates[-1]


def build_run_dir(run_dir: Path | None) -> Path:
    if run_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = WORKSPACE / f"runs/map_predict_phase5_frontier_scoring_baseline_{timestamp}"
    for name in ("logs", "frontier_features", "scoring", "plots", "reports", "summary", "debug"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    (run_dir / "logs/phase5.started").write_text(datetime.now().isoformat() + "\n", encoding="utf-8")
    return run_dir


def scalar_to_python(value: Any) -> Any:
    if isinstance(value, np.ndarray) and value.shape == ():
        return value.item()
    if isinstance(value, np.generic):
        return value.item()
    return value


def as_text(value: Any) -> str:
    value = scalar_to_python(value)
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def build_dataset_index(dataset_root: Path) -> dict[str, Path]:
    index: dict[str, Path] = {}
    for sample_path in sorted(dataset_root.glob("*/*.npz")):
        with np.load(sample_path, allow_pickle=True) as data:
            sample_id = as_text(data["sample_id"]) if "sample_id" in data.files else sample_path.stem
        index[sample_id] = sample_path
    return index


def load_phase4_frontier_table(phase4_run_dir: Path) -> list[dict[str, str]]:
    table = phase4_run_dir / "frontier_features/frontier_feature_table.csv"
    if not table.exists():
        return []
    with table.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def extract_frontier_features(
    *,
    phase4_run_dir: Path,
    dataset_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    dataset_index = build_dataset_index(dataset_root)
    phase4_rows = load_phase4_frontier_table(phase4_run_dir)
    split_by_sample = {row["sample_id"]: row.get("split", "") for row in phase4_rows}
    rows: list[dict[str, Any]] = []
    missing_dataset_samples: list[str] = []
    inference_paths = sorted((phase4_run_dir / "inference").glob("*.npz"))
    for inference_path in inference_paths:
        with np.load(inference_path, allow_pickle=True) as pred_data:
            sample_id = as_text(pred_data["sample_id"])
            pred_occ_prob = pred_data["pred_occ_prob"].astype(np.float32)
            uncertainty = pred_data["voxel_uncertainty"].astype(np.float32)
            bev_pred_occ = pred_data["bev_pred_occ"].astype(np.float32)
            bev_uncertainty = pred_data["bev_uncertainty"].astype(np.float32)
            split = as_text(pred_data["split"]) if "split" in pred_data.files else split_by_sample.get(sample_id, "")
        sample_path = dataset_index.get(sample_id)
        if sample_path is None:
            missing_dataset_samples.append(sample_id)
            continue
        with np.load(sample_path, allow_pickle=True) as data:
            observed_free = data["observed_free"].astype(np.uint8)
            unknown_mask = data["unknown_mask"].astype(np.uint8)
            frontier_mask = data["frontier_mask"].astype(np.uint8)
            if int(frontier_mask.sum()) == 0:
                frontier_mask = frontier_mask_from_3d(observed_free, unknown_mask).astype(np.uint8)
            scene_id = as_text(data["scene_id"]) if "scene_id" in data.files else sample_path.parent.name
            robot_pose = data["robot_pose"].astype(np.float32) if "robot_pose" in data.files else None
            crop_origin = data["crop_origin_xyz"].astype(np.float32) if "crop_origin_xyz" in data.files else None
            voxel_size = float(scalar_to_python(data["voxel_size"])) if "voxel_size" in data.files else None
        sample_rows = frontier_feature_rows(
            sample_id=sample_id,
            scene_id=scene_id,
            frontier_mask=frontier_mask,
            unknown_mask=unknown_mask,
            pred_occ_prob=pred_occ_prob,
            uncertainty=uncertainty,
            bev_pred_occ=bev_pred_occ,
            bev_uncertainty=bev_uncertainty,
            robot_pose=robot_pose,
            crop_origin_xyz=crop_origin,
            voxel_size=voxel_size,
        )
        for row in sample_rows:
            row["split"] = split
            row["source_phase4_inference"] = str(inference_path)
        rows.extend(sample_rows)
    metadata = {
        "phase4_frontier_row_count": len(phase4_rows),
        "phase5_extracted_frontier_row_count": len(rows),
        "phase4_inference_file_count": len(inference_paths),
        "missing_dataset_sample_count": len(missing_dataset_samples),
        "missing_dataset_samples": missing_dataset_samples[:20],
    }
    return rows, metadata


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def nan_count(rows: list[dict[str, Any]], keys: list[str] | None = None) -> int:
    total = 0
    for row in rows:
        items = row.items() if keys is None else ((key, row.get(key)) for key in keys)
        for _, value in items:
            if isinstance(value, str) and value == "":
                continue
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(parsed):
                total += 1
    return total


def summarize_scoring(
    *,
    scored_rows: list[dict[str, Any]],
    config,
    extraction_metadata: dict[str, Any],
) -> dict[str, Any]:
    sample_ids = sorted({str(row.get("sample_id", "")) for row in scored_rows})
    selected_rows = [row for row in scored_rows if bool(row.get("selected_by_map_predict_score"))]
    reachable_rows = [row for row in scored_rows if bool(row.get("reachability_proxy"))]
    selected_valid = [row for row in selected_rows if bool(row.get("reachability_proxy")) and not bool(row.get("invalid_flag"))]
    top_score_checks = []
    for sample_id in sample_ids:
        sample_rows = [
            row
            for row in scored_rows
            if str(row.get("sample_id", "")) == sample_id and bool(row.get("reachability_proxy"))
        ]
        selected = [row for row in sample_rows if bool(row.get("selected_by_map_predict_score"))]
        if not sample_rows or not selected:
            top_score_checks.append(False)
            continue
        best_score = max(to_float(row.get("score"), default=-np.inf) for row in sample_rows)
        top_score_checks.append(abs(to_float(selected[0].get("score"), default=-np.inf) - best_score) <= 1e-6)

    score_values = [to_float(row.get("score"), default=np.nan) for row in scored_rows]
    finite_scores = [value for value in score_values if np.isfinite(value)]
    selected_scores = [to_float(row.get("score"), default=np.nan) for row in selected_rows]
    safe_to_integrate = bool(
        len(scored_rows) > 0
        and len(selected_rows) == len(sample_ids)
        and nan_count(scored_rows, ["score"]) == 0
        and all(top_score_checks)
        and (len(selected_valid) / max(len(selected_rows), 1)) >= 0.999
    )
    summary = {
        "phase": "MapPredict Phase 5 frontier feature extraction + scoring baseline",
        "source_phase": "MapPredict Phase 4 uncertainty + BEV projection",
        "frontier_row_count": len(scored_rows),
        "sample_count": len(sample_ids),
        "scored_frontier_count": len(scored_rows),
        "selected_frontier_count": len(selected_rows),
        "reachable_frontier_count": len(reachable_rows),
        "nan_feature_count": nan_count(scored_rows),
        "nan_score_count": nan_count(scored_rows, ["score"]),
        "selected_frontier_valid_rate": float(len(selected_valid) / max(len(selected_rows), 1)),
        "selected_is_top_score_rate": float(sum(top_score_checks) / max(len(top_score_checks), 1)),
        "sample_selection_rate": float(len(selected_rows) / max(len(sample_ids), 1)),
        "score_min": float(np.min(finite_scores)) if finite_scores else None,
        "score_max": float(np.max(finite_scores)) if finite_scores else None,
        "score_mean": float(np.mean(finite_scores)) if finite_scores else None,
        "selected_score_mean": float(np.mean(selected_scores)) if selected_scores else None,
        "score_formula": score_formula(),
        "alpha": config.alpha,
        "beta": config.beta,
        "gamma": config.gamma,
        "delta": config.delta,
        "path_cost_method": config.path_cost_method,
        "reachability_method": config.reachability_method,
        "risk_method": config.risk_method,
        "agreement_with_classical_selector": None,
        "score_regret_proxy": None,
        "safe_to_integrate_with_exploration_selector": safe_to_integrate,
        "safe_to_prepare_vla_features": safe_to_integrate,
        "training_started": False,
        "map_predict_training_started": False,
        "VLA_training_started": False,
        "diffusion_training_started": False,
        "SFT_started": False,
        "GDPO_started": False,
        "RL_started": False,
        "rollout_started": False,
        "data_volume_warning": "current dataset is sufficient for pipeline validation but not final training or paper-level results",
        **extraction_metadata,
    }
    return summary


def save_plots(run_dir: Path, scored_rows: list[dict[str, Any]]) -> None:
    if not scored_rows:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def col(name: str) -> list[float]:
        return [to_float(row.get(name), default=np.nan) for row in scored_rows]

    selected = [row for row in scored_rows if bool(row.get("selected_by_map_predict_score"))]
    plt.figure(figsize=(6, 4))
    plt.hist(col("score"), bins=30)
    plt.xlabel("score")
    plt.tight_layout()
    plt.savefig(run_dir / "plots/score_distribution.png", dpi=140)
    plt.close()

    plt.figure(figsize=(6, 4))
    plt.hist([to_float(row.get("score"), default=np.nan) for row in selected], bins=20)
    plt.xlabel("selected frontier score")
    plt.tight_layout()
    plt.savefig(run_dir / "plots/selected_frontier_score_distribution.png", dpi=140)
    plt.close()

    scatter_specs = [
        ("predicted_free_volume", "predicted_free_volume_vs_score.png"),
        ("uncertainty_volume", "uncertainty_volume_vs_score.png"),
        ("predicted_occupied_risk", "occupied_risk_vs_score.png"),
        ("path_cost_proxy", "path_cost_vs_score.png"),
    ]
    for key, filename in scatter_specs:
        plt.figure(figsize=(6, 4))
        plt.scatter(col(key), col("score"), s=14, alpha=0.75)
        plt.xlabel(key)
        plt.ylabel("score")
        plt.tight_layout()
        plt.savefig(run_dir / "plots" / filename, dpi=140)
        plt.close()

    # Lightweight overlay-style sanity plot: selected frontier centroids per sample.
    examples = selected[:6]
    if examples:
        plt.figure(figsize=(8, 5))
        for row in examples:
            plt.scatter(
                to_float(row.get("frontier_centroid_x")),
                to_float(row.get("frontier_centroid_y")),
                s=max(20.0, min(250.0, to_float(row.get("frontier_bev_cell_count")))),
                label=str(row.get("sample_id", ""))[-18:],
                alpha=0.7,
            )
        plt.xlabel("BEV x")
        plt.ylabel("BEV y")
        plt.legend(fontsize=6)
        plt.tight_layout()
        plt.savefig(run_dir / "plots/selected_frontier_overlay_examples.png", dpi=140)
        plt.close()


def main() -> None:
    args = parse_args()
    phase4_run_dir = resolve_phase4_run_dir(args.phase4_run_dir)
    run_dir = build_run_dir(args.run_dir)
    config = load_scoring_config(args.config)
    extracted_rows, extraction_metadata = extract_frontier_features(
        phase4_run_dir=phase4_run_dir,
        dataset_root=args.dataset_root,
    )
    scored_rows = score_frontiers(extracted_rows, config)
    summary = summarize_scoring(scored_rows=scored_rows, config=config, extraction_metadata=extraction_metadata)
    summary.update(
        {
            "phase4_run_dir": str(phase4_run_dir),
            "dataset_root": str(args.dataset_root),
            "scoring_config_path": str(args.config),
            "frontier_feature_scored_table_path": str(
                run_dir / "frontier_features/frontier_feature_scored_table.csv"
            ),
        }
    )
    write_csv(run_dir / "frontier_features/frontier_feature_scored_table.csv", scored_rows)
    write_json(run_dir / "summary/frontier_scoring_summary.json", summary)
    save_plots(run_dir, scored_rows)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
