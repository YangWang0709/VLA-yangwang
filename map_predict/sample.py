"""Inference interface for MapPredict occupancy predictions and BEV features."""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader

from map_predict.bev_project import project_prediction_to_bev
from map_predict.dataset import MapPredictVoxelDataset
from map_predict.frontier_features import (
    frontier_feature_nan_count,
    frontier_feature_rows,
    frontier_mask_from_3d,
)
from map_predict.metrics import occupancy_completion_metrics, uncertainty_evaluation_metrics
from map_predict.model_3d_unet import OccupancyUNet3D
from map_predict.uncertainty import (
    has_dropout_module,
    preserve_observed_space,
    probability_entropy_uncertainty,
)


WORKSPACE = Path("/home/ubuntu22/VLA")
DEFAULT_DATASET_ROOT = WORKSPACE / "data/map_predict/local_voxel_dataset/local_voxel_v2_aligned_real_partial_3d"
PHASE3_REPORT = WORKSPACE / "runs/MAP_PREDICT_PHASE3_3D_UNET_BASELINE_REPORT.md"


@dataclass(frozen=True)
class MapPredictOutput:
    predicted_occupancy: Any
    occupancy_probability: Any
    uncertainty: Any
    bev_pred_occ: Any | None
    bev_uncertainty: Any | None
    frontier_features: list[dict[str, Any]]
    metadata: dict[str, Any]


def format_feature_provider_output(
    predicted_occupancy: Any,
    occupancy_probability: Any,
    uncertainty: Any,
    *,
    bev_pred_occ: Any | None = None,
    bev_uncertainty: Any | None = None,
    frontier_features: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> MapPredictOutput:
    return MapPredictOutput(
        predicted_occupancy=predicted_occupancy,
        occupancy_probability=occupancy_probability,
        uncertainty=uncertainty,
        bev_pred_occ=bev_pred_occ,
        bev_uncertainty=bev_uncertainty,
        frontier_features=frontier_features or [],
        metadata={
            "module": "map_predict",
            "role": "feature_provider",
            "planner": False,
            "vla": False,
            **(metadata or {}),
        },
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--checkpoint", type=Path, default=None)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--splits", nargs="+", default=["val", "test"])
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--bev-occ-projection", default="max", choices=["max", "probabilistic_union"])
    parser.add_argument("--bev-uncertainty-projection", default="max", choices=["max", "mean_unknown_z"])
    parser.add_argument("--save-sample-npz", action="store_true")
    parser.add_argument("--max-debug-samples", type=int, default=6)
    return parser.parse_args()


def resolve_device(device_arg: str) -> torch.device:
    if device_arg == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_arg)


def resolve_checkpoint(checkpoint: Path | None) -> Path:
    if checkpoint is not None:
        return checkpoint
    if PHASE3_REPORT.exists():
        text = PHASE3_REPORT.read_text(encoding="utf-8")
        match = re.search(r"checkpoint path:\s*(\S+)", text)
        if match:
            path = Path(match.group(1))
            if path.exists():
                return path
    candidates = sorted(WORKSPACE.glob("runs/map_predict_phase3_3d_unet_baseline_*/checkpoints/best_3d_unet.pt"))
    if not candidates:
        raise FileNotFoundError("could not resolve Phase 3 checkpoint")
    return candidates[-1]


def build_run_dir(run_dir: Path | None) -> Path:
    if run_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = WORKSPACE / f"runs/map_predict_phase4_uncertainty_bev_projection_{timestamp}"
    for name in (
        "logs",
        "inference",
        "uncertainty",
        "bev",
        "frontier_features",
        "plots",
        "reports",
        "summary",
        "debug_predictions",
    ):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    (run_dir / "logs/phase4.started").write_text(datetime.now().isoformat() + "\n", encoding="utf-8")
    return run_dir


def load_model(checkpoint_path: Path, device: torch.device) -> tuple[OccupancyUNet3D, dict[str, Any]]:
    checkpoint = torch.load(checkpoint_path, map_location=device)
    config = checkpoint.get("model_config", {"in_channels": 6, "out_channels": 1, "base_channels": 16, "levels": 3})
    model = OccupancyUNet3D(**config).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    return model, config


def collate_single(batch: list[dict[str, Any]]) -> dict[str, Any]:
    if len(batch) != 1:
        raise ValueError("Phase 4 inference uses batch_size=1 to keep per-sample outputs simple")
    return batch[0]


def mean_dict(rows: list[dict[str, float]]) -> dict[str, float]:
    if not rows:
        return {}
    keys = sorted(rows[0].keys())
    out: dict[str, float] = {}
    for key in keys:
        out[key] = float(np.mean([row[key] for row in rows]))
    return out


def finite_nan_count(rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in rows:
        for value in row.values():
            if isinstance(value, float) and not np.isfinite(value):
                count += 1
    return count


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def save_debug_images(run_dir: Path, debug_records: list[dict[str, Any]]) -> None:
    if not debug_records:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    count = min(4, len(debug_records))
    plt.figure(figsize=(4 * count, 4))
    for idx, record in enumerate(debug_records[:count], start=1):
        ax = plt.subplot(1, count, idx)
        ax.imshow(record["bev_pred_occ"], cmap="magma", origin="lower", vmin=0.0, vmax=1.0)
        ax.set_title(record["sample_id"][:18])
        ax.axis("off")
    plt.tight_layout()
    plt.savefig(run_dir / "plots/bev_pred_occ_examples.png", dpi=140)
    plt.close()

    plt.figure(figsize=(4 * count, 4))
    for idx, record in enumerate(debug_records[:count], start=1):
        ax = plt.subplot(1, count, idx)
        ax.imshow(record["bev_uncertainty"], cmap="viridis", origin="lower", vmin=0.0, vmax=1.0)
        ax.set_title(record["sample_id"][:18])
        ax.axis("off")
    plt.tight_layout()
    plt.savefig(run_dir / "plots/bev_uncertainty_examples.png", dpi=140)
    plt.close()

    all_unc = np.concatenate([record["uncertainty"].reshape(-1) for record in debug_records])
    plt.figure(figsize=(6, 4))
    plt.hist(all_unc, bins=50)
    plt.xlabel("normalized entropy uncertainty")
    plt.ylabel("voxel count")
    plt.tight_layout()
    plt.savefig(run_dir / "plots/uncertainty_histogram.png", dpi=140)
    plt.close()

    for idx, record in enumerate(debug_records):
        sample_id = record["sample_id"].replace("/", "_")
        plt.figure(figsize=(5, 5))
        plt.imshow(record["bev_pred_occ"], cmap="magma", origin="lower", vmin=0.0, vmax=1.0)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(run_dir / f"debug_predictions/sample_{idx:03d}_{sample_id}_bev_pred_occ.png", dpi=140)
        plt.close()

        plt.figure(figsize=(5, 5))
        plt.imshow(record["bev_uncertainty"], cmap="viridis", origin="lower", vmin=0.0, vmax=1.0)
        plt.axis("off")
        plt.tight_layout()
        plt.savefig(run_dir / f"debug_predictions/sample_{idx:03d}_{sample_id}_bev_uncertainty.png", dpi=140)
        plt.close()


def save_frontier_distribution(run_dir: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    metrics = ["frontier_voxel_count", "mean_uncertainty", "predicted_occupied_risk", "expected_information_gain_proxy"]
    plt.figure(figsize=(10, 7))
    for idx, metric in enumerate(metrics, start=1):
        ax = plt.subplot(2, 2, idx)
        ax.hist([float(row[metric]) for row in rows], bins=30)
        ax.set_title(metric)
    plt.tight_layout()
    plt.savefig(run_dir / "plots/frontier_feature_distributions.png", dpi=140)
    plt.close()


@torch.no_grad()
def run_inference(
    *,
    model: OccupancyUNet3D,
    dataset: MapPredictVoxelDataset,
    split_name: str,
    run_dir: Path,
    device: torch.device,
    bev_occ_projection: str,
    bev_uncertainty_projection: str,
    save_sample_npz: bool,
    max_debug_samples: int,
) -> tuple[list[dict[str, float]], list[dict[str, float]], list[dict[str, Any]], list[dict[str, Any]]]:
    loader = DataLoader(dataset, batch_size=1, shuffle=False, collate_fn=collate_single)
    inference_rows: list[dict[str, float]] = []
    uncertainty_rows: list[dict[str, float]] = []
    frontier_rows: list[dict[str, Any]] = []
    debug_records: list[dict[str, Any]] = []

    for item in loader:
        inputs = item["input"].unsqueeze(0).to(device=device, dtype=torch.float32)
        logits = model(inputs).squeeze(0).squeeze(0).detach().cpu().numpy()
        pred_occ_prob = 1.0 / (1.0 + np.exp(-logits.astype(np.float32)))
        uncertainty = probability_entropy_uncertainty(pred_occ_prob)

        observed_free = item["observed_free"].numpy()
        observed_occupied = item["observed_occupied"].numpy()
        unknown_mask = item["unknown_mask"].numpy()
        frontier_mask = item["frontier_mask"].numpy()
        if int(frontier_mask.sum()) == 0:
            frontier_mask = frontier_mask_from_3d(observed_free, unknown_mask).astype(np.uint8)
        full_occupancy = item["full_occupancy"].numpy()
        pred_occ_prob, uncertainty = preserve_observed_space(
            pred_occ_prob,
            uncertainty,
            observed_free,
            observed_occupied,
        )
        bev = project_prediction_to_bev(
            pred_occ_prob,
            uncertainty,
            observed_free,
            observed_occupied,
            unknown_mask,
            occ_projection=bev_occ_projection,
            uncertainty_projection=bev_uncertainty_projection,
        )

        sample_id = str(item["sample_id"])
        completion = occupancy_completion_metrics(
            pred_occ_prob,
            full_occupancy,
            unknown_mask,
            observed_free,
            observed_occupied,
        )
        uncertainty_metrics = uncertainty_evaluation_metrics(
            uncertainty,
            unknown_mask,
            observed_free,
            observed_occupied,
            pred_occ_prob,
            full_occupancy,
        )
        inference_rows.append({"split": split_name, **completion})
        uncertainty_rows.append({"split": split_name, **uncertainty_metrics})
        rows = frontier_feature_rows(
            sample_id=sample_id,
            frontier_mask=frontier_mask,
            unknown_mask=unknown_mask,
            pred_occ_prob=pred_occ_prob,
            uncertainty=uncertainty,
            bev_pred_occ=bev["bev_pred_occ"],
            bev_uncertainty=bev["bev_uncertainty"],
        )
        for row in rows:
            row["split"] = split_name
        frontier_rows.extend(rows)

        if save_sample_npz:
            np.savez_compressed(
                run_dir / "inference" / f"{sample_id}.npz",
                pred_occ_prob=pred_occ_prob.astype(np.float32),
                voxel_uncertainty=uncertainty.astype(np.float32),
                bev_pred_occ=bev["bev_pred_occ"].astype(np.float32),
                bev_uncertainty=bev["bev_uncertainty"].astype(np.float32),
                sample_id=sample_id,
                split=split_name,
            )

        if len(debug_records) < max_debug_samples:
            debug_records.append(
                {
                    "sample_id": sample_id,
                    "bev_pred_occ": bev["bev_pred_occ"],
                    "bev_uncertainty": bev["bev_uncertainty"],
                    "uncertainty": uncertainty,
                }
            )

    return inference_rows, uncertainty_rows, frontier_rows, debug_records


def main() -> None:
    args = parse_args()
    run_dir = build_run_dir(args.run_dir)
    checkpoint_path = resolve_checkpoint(args.checkpoint)
    device = resolve_device(args.device)
    model, model_config = load_model(checkpoint_path, device)
    dropout_available = has_dropout_module(model)

    all_inference_rows: list[dict[str, float]] = []
    all_uncertainty_rows: list[dict[str, float]] = []
    all_frontier_rows: list[dict[str, Any]] = []
    all_debug_records: list[dict[str, Any]] = []
    split_counts: dict[str, int] = {}

    for split in args.splits:
        dataset = MapPredictVoxelDataset(args.dataset_root / "splits" / f"{split}.txt")
        split_counts[split] = len(dataset)
        inference_rows, uncertainty_rows, frontier_rows, debug_records = run_inference(
            model=model,
            dataset=dataset,
            split_name=split,
            run_dir=run_dir,
            device=device,
            bev_occ_projection=args.bev_occ_projection,
            bev_uncertainty_projection=args.bev_uncertainty_projection,
            save_sample_npz=args.save_sample_npz,
            max_debug_samples=max(0, args.max_debug_samples - len(all_debug_records)),
        )
        all_inference_rows.extend(inference_rows)
        all_uncertainty_rows.extend(uncertainty_rows)
        all_frontier_rows.extend(frontier_rows)
        all_debug_records.extend(debug_records)

    inference_summary = mean_dict([{k: v for k, v in row.items() if k != "split"} for row in all_inference_rows])
    uncertainty_summary = mean_dict([{k: v for k, v in row.items() if k != "split"} for row in all_uncertainty_rows])
    frontier_nan_count = frontier_feature_nan_count(all_frontier_rows)
    frontier_summary = {
        "frontier_row_count": len(all_frontier_rows),
        "frontier_feature_nan_count": int(frontier_nan_count),
        "frontier_rows_per_sample_mean": float(len(all_frontier_rows) / max(len(all_inference_rows), 1)),
    }
    if all_frontier_rows:
        for key in (
            "frontier_voxel_count",
            "frontier_bev_cell_count",
            "predicted_free_volume",
            "predicted_occupied_risk",
            "mean_uncertainty",
            "max_uncertainty",
            "uncertainty_volume",
            "expected_information_gain_proxy",
        ):
            frontier_summary[f"{key}_mean"] = float(np.mean([float(row[key]) for row in all_frontier_rows]))

    observed_space_preserved = bool(inference_summary.get("observed_consistency_error", 1.0) <= 1e-8)
    uncertainty_gap_pass = bool(
        uncertainty_summary.get("uncertainty_mean_unknown", 0.0)
        > uncertainty_summary.get("uncertainty_mean_observed", 0.0)
    )
    safe_to_build_frontier_scoring = bool(
        observed_space_preserved and uncertainty_gap_pass and frontier_summary["frontier_row_count"] > 0 and frontier_nan_count == 0
    )

    write_json(run_dir / "summary/inference_metrics.json", inference_summary)
    write_json(run_dir / "summary/uncertainty_metrics.json", uncertainty_summary)
    write_json(run_dir / "summary/frontier_feature_summary.json", frontier_summary)
    write_csv(run_dir / "frontier_features/frontier_feature_table.csv", all_frontier_rows)
    save_debug_images(run_dir, all_debug_records)
    save_frontier_distribution(run_dir, all_frontier_rows)

    summary = {
        "phase": "MapPredict Phase 4",
        "source_model": "3D U-Net baseline",
        "checkpoint_path": str(checkpoint_path),
        "dataset": args.dataset_root.name,
        "dataset_root": str(args.dataset_root),
        "samples_evaluated": int(sum(split_counts.values())),
        "split_counts": split_counts,
        "uncertainty_methods": {
            "probability_entropy": True,
            "mc_dropout_available": bool(dropout_available),
            "mc_dropout_used": False,
        },
        "observed_space_preserved": observed_space_preserved,
        "observed_consistency_error_after_projection": inference_summary.get("observed_consistency_error", None),
        "BEV_projection_method": {
            "bev_occ_projection": args.bev_occ_projection,
            "bev_uncertainty_projection": args.bev_uncertainty_projection,
        },
        "inference_metrics": inference_summary,
        "uncertainty_metrics": uncertainty_summary,
        "frontier_feature_summary": frontier_summary,
        "frontier_feature_table_path": str(run_dir / "frontier_features/frontier_feature_table.csv"),
        "visualization_paths": [
            str(run_dir / "plots/bev_pred_occ_examples.png"),
            str(run_dir / "plots/bev_uncertainty_examples.png"),
            str(run_dir / "plots/uncertainty_histogram.png"),
            str(run_dir / "plots/frontier_feature_distributions.png"),
        ],
        "model_config": model_config,
        "map_predict_training_started": False,
        "diffusion_training_started": False,
        "VLA_training_started": False,
        "SFT_started": False,
        "GDPO_started": False,
        "RL_started": False,
        "rollout_started": False,
        "safe_to_build_frontier_scoring_baseline": safe_to_build_frontier_scoring,
        "next_phase": (
            "MapPredict Phase 5 frontier feature extraction and scoring baseline"
            if safe_to_build_frontier_scoring
            else "Fix MapPredict Phase 4 uncertainty / BEV projection"
        ),
    }
    write_json(run_dir / "summary/phase4_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
