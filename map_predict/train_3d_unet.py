"""Train the MapPredict Phase 3 3D U-Net occupancy baseline."""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

import torch
from torch.utils.data import DataLoader

from map_predict.dataset import MapPredictVoxelDataset
from map_predict.losses import enforce_observed_consistency, occupancy_completion_loss
from map_predict.metrics import occupancy_completion_metrics
from map_predict.model_3d_unet import OccupancyUNet3D, count_parameters


WORKSPACE = Path("/home/ubuntu22/VLA")
DEFAULT_DATASET_ROOT = WORKSPACE / "data/map_predict/local_voxel_dataset/local_voxel_v2_aligned_real_partial_3d"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--run-dir", type=Path, default=None)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--lambda-obs", type=float, default=0.1)
    parser.add_argument("--base-channels", type=int, default=16)
    parser.add_argument("--num-workers", type=int, default=0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--unknown-pos-weight", default="auto", help="'auto', 'none', or a numeric value")
    parser.add_argument("--max-train-batches", type=int, default=None)
    parser.add_argument("--tag", default="baseline")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def build_run_dir(run_dir: Path | None, tag: str) -> Path:
    if run_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_dir = WORKSPACE / f"runs/map_predict_phase3_3d_unet_baseline_{timestamp}"
    for name in ("logs", "checkpoints", "metrics", "plots", "reports", "summary", "debug_predictions"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    (run_dir / "logs" / f"{tag}.started").write_text(datetime.now().isoformat() + "\n", encoding="utf-8")
    return run_dir


def collate_map_predict(batch: list[dict[str, Any]]) -> dict[str, Any]:
    tensor_keys = (
        "input",
        "observed_free",
        "observed_occupied",
        "unknown_mask",
        "frontier_mask",
        "full_occupancy",
    )
    out = {key: torch.stack([item[key] for item in batch], dim=0) for key in tensor_keys}
    out["sample_id"] = [item["sample_id"] for item in batch]
    out["metadata"] = [item["metadata"] for item in batch]
    return out


def make_loader(dataset: MapPredictVoxelDataset, batch_size: int, shuffle: bool, num_workers: int) -> DataLoader:
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        pin_memory=torch.cuda.is_available(),
        collate_fn=collate_map_predict,
    )


def resolve_device(device_arg: str) -> torch.device:
    if device_arg == "auto":
        return torch.device("cuda" if torch.cuda.is_available() else "cpu")
    return torch.device(device_arg)


def compute_unknown_pos_weight(dataset: MapPredictVoxelDataset, mode: str) -> float | None:
    if mode == "none":
        return None
    if mode != "auto":
        return float(mode)
    positive = 0.0
    negative = 0.0
    for item in dataset:
        unknown = item["unknown_mask"].bool()
        target = item["full_occupancy"].float()
        positive += float(target[unknown].sum().item())
        negative += float(unknown.sum().item() - target[unknown].sum().item())
    if positive <= 0:
        return 1.0
    return float(min(max(negative / positive, 1.0), 50.0))


def mean_dict(rows: list[dict[str, float]]) -> dict[str, float]:
    if not rows:
        return {}
    keys = sorted(rows[0].keys())
    return {key: float(np.mean([row[key] for row in rows])) for key in keys}


@torch.no_grad()
def evaluate(model: OccupancyUNet3D, loader: DataLoader, device: torch.device) -> dict[str, float]:
    model.eval()
    rows: list[dict[str, float]] = []
    for batch in loader:
        inputs = batch["input"].to(device=device, dtype=torch.float32)
        logits = model(inputs).squeeze(1)
        prob = torch.sigmoid(logits)
        prob = enforce_observed_consistency(
            prob,
            batch["observed_free"].to(device=device),
            batch["observed_occupied"].to(device=device),
        )
        prob_np = prob.detach().cpu().numpy()
        full_np = batch["full_occupancy"].detach().cpu().numpy()
        unknown_np = batch["unknown_mask"].detach().cpu().numpy()
        free_np = batch["observed_free"].detach().cpu().numpy()
        occ_np = batch["observed_occupied"].detach().cpu().numpy()
        for idx in range(prob_np.shape[0]):
            rows.append(occupancy_completion_metrics(prob_np[idx], full_np[idx], unknown_np[idx], free_np[idx], occ_np[idx]))
    return mean_dict(rows)


def train_epoch(
    model: OccupancyUNet3D,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    *,
    lambda_obs: float,
    unknown_pos_weight: float | None,
    gradient_clip: float = 1.0,
    max_batches: int | None = None,
) -> dict[str, float]:
    model.train()
    losses: list[dict[str, float]] = []
    for batch_idx, batch in enumerate(loader):
        if max_batches is not None and batch_idx >= max_batches:
            break
        inputs = batch["input"].to(device=device, dtype=torch.float32)
        batch_on_device = {
            "full_occupancy": batch["full_occupancy"].to(device=device),
            "unknown_mask": batch["unknown_mask"].to(device=device),
            "observed_free": batch["observed_free"].to(device=device),
            "observed_occupied": batch["observed_occupied"].to(device=device),
        }
        optimizer.zero_grad(set_to_none=True)
        logits = model(inputs)
        loss_parts = occupancy_completion_loss(
            logits,
            batch_on_device,
            lambda_obs=lambda_obs,
            unknown_pos_weight=unknown_pos_weight,
        )
        loss = loss_parts["loss"]
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), gradient_clip)
        optimizer.step()
        losses.append(
            {
                "loss": float(loss.detach().cpu().item()),
                "loss_unknown": float(loss_parts["loss_unknown"].detach().cpu().item()),
                "loss_observed": float(loss_parts["loss_observed"].detach().cpu().item()),
            }
        )
    return mean_dict(losses)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def make_plots(run_dir: Path, train_rows: list[dict[str, Any]], val_rows: list[dict[str, Any]]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    epochs = [row["epoch"] for row in train_rows]
    plt.figure(figsize=(7, 4))
    plt.plot(epochs, [row["loss"] for row in train_rows], label="train loss")
    plt.plot([row["epoch"] for row in val_rows], [row["unknown_region_bce"] for row in val_rows], label="val unknown BCE")
    plt.xlabel("epoch")
    plt.legend()
    plt.tight_layout()
    plt.savefig(run_dir / "plots/loss_curve.png", dpi=140)
    plt.close()

    plt.figure(figsize=(7, 4))
    plt.plot([row["epoch"] for row in val_rows], [row["unknown_region_iou"] for row in val_rows], label="val unknown IoU")
    plt.plot([row["epoch"] for row in val_rows], [row["naive_all_free_iou"] for row in val_rows], "--", label="all-free")
    plt.plot([row["epoch"] for row in val_rows], [row["naive_all_occupied_iou"] for row in val_rows], "--", label="all-occupied")
    plt.xlabel("epoch")
    plt.legend()
    plt.tight_layout()
    plt.savefig(run_dir / "plots/val_unknown_iou_curve.png", dpi=140)
    plt.close()


@torch.no_grad()
def write_debug_predictions(
    model: OccupancyUNet3D,
    dataset: MapPredictVoxelDataset,
    run_dir: Path,
    device: torch.device,
    count: int = 3,
) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    model.eval()
    for idx in range(min(count, len(dataset))):
        item = dataset[idx]
        sample_id = str(item["sample_id"]).replace("/", "_")
        inputs = item["input"].unsqueeze(0).to(device=device, dtype=torch.float32)
        prob = torch.sigmoid(model(inputs).squeeze(1))
        prob = enforce_observed_consistency(
            prob,
            item["observed_free"].unsqueeze(0).to(device=device),
            item["observed_occupied"].unsqueeze(0).to(device=device),
        )[0].detach().cpu().numpy()
        gt = item["full_occupancy"].numpy()
        free = item["observed_free"].numpy()
        occ = item["observed_occupied"].numpy()
        unknown = item["unknown_mask"].numpy()

        panels = [
            ("pred BEV", prob.max(axis=0)),
            ("gt BEV", gt.max(axis=0)),
            ("observed occ BEV", occ.max(axis=0)),
            ("unknown BEV", unknown.max(axis=0)),
        ]
        plt.figure(figsize=(10, 3))
        for panel_idx, (title, image) in enumerate(panels, start=1):
            ax = plt.subplot(1, 4, panel_idx)
            ax.imshow(image, cmap="viridis", origin="lower")
            ax.set_title(title)
            ax.axis("off")
        plt.tight_layout()
        plt.savefig(run_dir / f"debug_predictions/sample_{idx:03d}_{sample_id}_bev_pred.png", dpi=140)
        plt.close()

        z_indices = [prob.shape[0] // 4, prob.shape[0] // 2, (3 * prob.shape[0]) // 4]
        plt.figure(figsize=(8, 7))
        for row, z in enumerate(z_indices):
            for col, (title, vol, cmap) in enumerate((("pred", prob, "magma"), ("gt", gt, "gray"), ("free", free, "Blues"))):
                ax = plt.subplot(len(z_indices), 3, row * 3 + col + 1)
                ax.imshow(vol[z], cmap=cmap, origin="lower")
                ax.set_title(f"z={z} {title}")
                ax.axis("off")
        plt.tight_layout()
        plt.savefig(run_dir / f"debug_predictions/sample_{idx:03d}_{sample_id}_z_slices.png", dpi=140)
        plt.close()


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    run_dir = build_run_dir(args.run_dir, args.tag)
    device = resolve_device(args.device)

    train_dataset = MapPredictVoxelDataset(args.dataset_root / "splits/train.txt")
    val_dataset = MapPredictVoxelDataset(args.dataset_root / "splits/val.txt")
    test_dataset = MapPredictVoxelDataset(args.dataset_root / "splits/test.txt")
    if len(train_dataset) == 0 or len(val_dataset) == 0 or len(test_dataset) == 0:
        raise RuntimeError("train/val/test splits must all contain quality_status=pass samples")

    train_loader = make_loader(train_dataset, args.batch_size, shuffle=True, num_workers=args.num_workers)
    val_loader = make_loader(val_dataset, args.batch_size, shuffle=False, num_workers=args.num_workers)
    test_loader = make_loader(test_dataset, args.batch_size, shuffle=False, num_workers=args.num_workers)

    model = OccupancyUNet3D(in_channels=6, out_channels=1, base_channels=args.base_channels, levels=3).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    unknown_pos_weight = compute_unknown_pos_weight(train_dataset, args.unknown_pos_weight)

    first_batch = next(iter(train_loader))
    with torch.no_grad():
        forward_shape = list(model(first_batch["input"].to(device=device, dtype=torch.float32)).shape)
    train_rows: list[dict[str, Any]] = []
    val_rows: list[dict[str, Any]] = []
    best_epoch = -1
    best_val_unknown_iou = -math.inf
    best_val_unknown_bce = math.inf
    best_checkpoint = run_dir / "checkpoints/best_3d_unet.pt"

    for epoch in range(1, args.epochs + 1):
        train_metrics = train_epoch(
            model,
            train_loader,
            optimizer,
            device,
            lambda_obs=args.lambda_obs,
            unknown_pos_weight=unknown_pos_weight,
            max_batches=args.max_train_batches,
        )
        val_metrics = evaluate(model, val_loader, device)
        train_row = {"epoch": epoch, **train_metrics}
        val_row = {"epoch": epoch, **val_metrics}
        train_rows.append(train_row)
        val_rows.append(val_row)
        better_iou = val_metrics["unknown_region_iou"] > best_val_unknown_iou + 1e-8
        same_iou_better_bce = (
            abs(val_metrics["unknown_region_iou"] - best_val_unknown_iou) <= 1e-8
            and val_metrics["unknown_region_bce"] < best_val_unknown_bce
        )
        if better_iou or same_iou_better_bce:
            best_epoch = epoch
            best_val_unknown_iou = float(val_metrics["unknown_region_iou"])
            best_val_unknown_bce = float(val_metrics["unknown_region_bce"])
            torch.save(
                {
                    "model_state_dict": model.state_dict(),
                    "model_config": {
                        "in_channels": 6,
                        "out_channels": 1,
                        "base_channels": args.base_channels,
                        "levels": 3,
                    },
                    "epoch": epoch,
                    "val_metrics": val_metrics,
                    "args": vars(args) | {"run_dir": str(run_dir), "dataset_root": str(args.dataset_root)},
                },
                best_checkpoint,
            )
        print(
            f"epoch={epoch:03d} loss={train_metrics['loss']:.5f} "
            f"val_bce={val_metrics['unknown_region_bce']:.5f} "
            f"val_iou={val_metrics['unknown_region_iou']:.5f}",
            flush=True,
        )

    checkpoint = torch.load(best_checkpoint, map_location=device)
    model.load_state_dict(checkpoint["model_state_dict"])
    test_metrics = evaluate(model, test_loader, device)
    train_loss_decreased = bool(len(train_rows) > 1 and train_rows[-1]["loss"] < train_rows[0]["loss"])
    best_val_metrics = checkpoint["val_metrics"]
    safe_to_build_uncertainty = bool(
        train_loss_decreased
        and best_val_metrics["unknown_region_bce"] < best_val_metrics["naive_all_free_bce"]
        and best_val_metrics["unknown_region_iou"] > best_val_metrics["naive_all_free_iou"]
        and best_val_metrics["observed_consistency_error"] <= 1e-6
        and test_metrics["observed_consistency_error"] <= 1e-6
    )

    write_csv(run_dir / "summary/train_metrics.csv", train_rows)
    write_csv(run_dir / "summary/val_metrics.csv", val_rows)
    write_json(run_dir / "summary/test_metrics.json", test_metrics)
    model_summary = {
        "phase": "MapPredict Phase 3",
        "model": "3D U-Net occupancy completion baseline",
        "dataset": args.dataset_root.name,
        "dataset_root": str(args.dataset_root),
        "sample_count": len(train_dataset) + len(val_dataset) + len(test_dataset),
        "split": {"train": len(train_dataset), "val": len(val_dataset), "test": len(test_dataset)},
        "skipped_non_pass": {
            "train": len(train_dataset.skipped_paths),
            "val": len(val_dataset.skipped_paths),
            "test": len(test_dataset.skipped_paths),
        },
        "input_channels": list(MapPredictVoxelDataset.input_channel_names),
        "output": "occupancy_logits [B,1,D,H,W]",
        "forward_shape": forward_shape,
        "loss_formula": "BCEWithLogits(unknown_mask, dense_scan_pseudo_gt) + lambda_obs * BCEWithLogits(observed_free|observed_occupied)",
        "lambda_obs": args.lambda_obs,
        "unknown_pos_weight": unknown_pos_weight,
        "epochs": args.epochs,
        "batch_size": args.batch_size,
        "optimizer": "AdamW",
        "lr": args.lr,
        "weight_decay": args.weight_decay,
        "base_channels": args.base_channels,
        "parameter_count": count_parameters(model),
        "best_epoch": best_epoch,
        "best_val_unknown_iou": best_val_unknown_iou,
        "best_val_unknown_bce": best_val_unknown_bce,
        "best_val_metrics": best_val_metrics,
        "test_metrics": test_metrics,
        "train_loss_start": train_rows[0]["loss"],
        "train_loss_end": train_rows[-1]["loss"],
        "train_loss_decreased": train_loss_decreased,
        "checkpoint_path": str(best_checkpoint),
        "training_started": True,
        "diffusion_training_started": False,
        "VLA_training_started": False,
        "SFT_started": False,
        "GDPO_started": False,
        "gt_type": "dense_scan_pseudo_gt",
        "dense_scan_pseudo_gt_is_perfect_ground_truth": False,
        "safe_to_build_uncertainty_baseline": safe_to_build_uncertainty,
        "next_phase": (
            "MapPredict Phase 4 uncertainty baseline via MC dropout / ensemble or lightweight diffusion sampling"
            if safe_to_build_uncertainty
            else "Fix MapPredict Phase 3 3D U-Net baseline"
        ),
    }
    write_json(run_dir / "summary/model_summary.json", model_summary)
    make_plots(run_dir, train_rows, val_rows)
    write_debug_predictions(model, test_dataset, run_dir, device)
    write_json(run_dir / "summary/run_complete.json", {"completed_at": datetime.now().isoformat(), **model_summary})
    print(json.dumps(model_summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
