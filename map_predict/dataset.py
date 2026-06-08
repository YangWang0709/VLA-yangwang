"""Dataset contracts for SceneSense-style occupancy completion.

The map_predict package is a feature provider. It consumes partial 3D
occupancy observations and returns predicted occupancy plus uncertainty. It is
not a planner, VLA model, rollout collector, or training launcher.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np

try:
    import torch
    from torch.utils.data import Dataset
except Exception:  # pragma: no cover - torch may be unavailable in lint contexts.
    torch = None
    Dataset = object


REQUIRED_SAMPLE_KEYS = (
    "observed_free",
    "observed_occupied",
    "unknown_mask",
    "frontier_mask",
    "robot_pose",
    "full_occupancy",
    "voxel_size",
    "crop_origin",
    "scene_id",
    "episode_id",
    "step_id",
)


@dataclass(frozen=True)
class RolloutSource:
    """Pointer to an existing real-sensor rollout or quality audit output."""

    scene_id: str
    scene_path: str
    rollout_dir: Path
    quality_dir: Path | None = None


@dataclass
class MapPredictSample:
    """Canonical sample metadata for occupancy completion."""

    sample_id: str
    scene_id: str
    episode_id: int
    step_id: int
    voxel_size: float
    crop_origin: tuple[float, float, float]
    robot_pose: tuple[float, float, float, float]
    observed_free: Any
    observed_occupied: Any
    unknown_mask: Any
    frontier_mask: Any
    full_occupancy: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_record(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "scene_id": self.scene_id,
            "episode_id": self.episode_id,
            "step_id": self.step_id,
            "voxel_size": self.voxel_size,
            "crop_origin": list(self.crop_origin),
            "robot_pose": list(self.robot_pose),
            "observed_free": self.observed_free,
            "observed_occupied": self.observed_occupied,
            "unknown_mask": self.unknown_mask,
            "frontier_mask": self.frontier_mask,
            "full_occupancy": self.full_occupancy,
            "metadata": self.metadata,
        }


def validate_sample_record(record: dict[str, Any], require_gt: bool = True) -> list[str]:
    """Return validation errors for a map_predict sample record."""

    errors: list[str] = []
    for key in REQUIRED_SAMPLE_KEYS:
        if key not in record:
            errors.append(f"missing key: {key}")
    if require_gt and record.get("full_occupancy") is None:
        errors.append("missing full_occupancy ground truth")
    for key in ("observed_free", "observed_occupied", "unknown_mask", "frontier_mask"):
        value = record.get(key)
        if value is None:
            continue
        shape = getattr(value, "shape", None)
        if shape is not None and len(shape) != 3:
            errors.append(f"{key} must be [D, H, W], got {tuple(shape)}")
    pose = record.get("robot_pose")
    if pose is not None and len(pose) != 4:
        errors.append("robot_pose must be [x, y, z, yaw]")
    origin = record.get("crop_origin")
    if origin is not None and len(origin) != 3:
        errors.append("crop_origin must be [x, y, z]")
    return errors


def iter_rollout_sources(workspace: Path) -> Iterable[RolloutSource]:
    """Yield the two current real-sensor rollout sources known in Phase 0."""

    runs = workspace / "runs"
    yield RolloutSource(
        scene_id="old_home_like_scene_v1",
        scene_path=str(workspace / "scenes/primary_building_scene_repaired/home_like_scene_v1.usd"),
        rollout_dir=runs / "phase8_a1_vlm_la_long_rollout_20260607_212536",
        quality_dir=runs / "phase9_human_review_packet_20260607_213732",
    )
    yield RolloutSource(
        scene_id="new_building_scene_1",
        scene_path=str(workspace / "scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda"),
        rollout_dir=runs / "new_scene_building_scene_1_phaseG_long_rollout_20260608_185904",
        quality_dir=runs / "new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002",
    )


def local_voxel_dataset_manifest(
    *,
    dataset_name: str,
    gt_type: str,
    scenes: list[str],
    voxel_shape: tuple[int, int, int],
    voxel_size: float,
    sample_count: int,
    pass_count: int,
    warning_count: int,
    reject_count: int,
    partial_3d_source: str,
    observed_occupied_zero_rate: float | None = None,
) -> dict[str, Any]:
    """Build the canonical manifest for a local voxel crop dataset."""

    manifest = {
        "dataset_name": dataset_name,
        "gt_type": gt_type,
        "scenes": scenes,
        "voxel_shape": list(voxel_shape),
        "voxel_layout": ["D", "H", "W"],
        "voxel_axis_order": "D=z, H=y, W=x",
        "voxel_size": float(voxel_size),
        "sample_count": int(sample_count),
        "pass_count": int(pass_count),
        "warning_count": int(warning_count),
        "reject_count": int(reject_count),
        "partial_3d_source": partial_3d_source,
        "training_ready": False,
        "requires_review": True,
    }
    if observed_occupied_zero_rate is not None:
        manifest["observed_occupied_zero_rate"] = float(observed_occupied_zero_rate)
    return manifest


def _scalar_to_python(value: Any) -> Any:
    if isinstance(value, np.ndarray) and value.shape == ():
        return value.item()
    if isinstance(value, np.generic):
        return value.item()
    return value


def _as_text(value: Any) -> str:
    value = _scalar_to_python(value)
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return str(value)


def _load_split_paths(split_file: Path, dataset_root: Path | None = None) -> tuple[Path, list[Path]]:
    split_file = Path(split_file)
    if dataset_root is None:
        dataset_root = split_file.parent.parent if split_file.parent.name == "splits" else split_file.parent
    paths: list[Path] = []
    for raw in split_file.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        sample_path = Path(line)
        if not sample_path.is_absolute():
            sample_path = dataset_root / sample_path
        paths.append(sample_path)
    return dataset_root, paths


def _generate_height_channel(shape: Sequence[int]) -> np.ndarray:
    depth = int(shape[0])
    z_values = (np.arange(depth, dtype=np.float32) + 0.5) / max(float(depth), 1.0)
    return np.broadcast_to(z_values[:, None, None], tuple(shape)).astype(np.float32)


def _generate_robot_position_gaussian(
    shape: Sequence[int],
    robot_pose: np.ndarray,
    crop_origin_xyz: np.ndarray,
    voxel_size: float,
    sigma_vox: float = 2.0,
) -> np.ndarray:
    """Generate a robot-position prior in D=Z,H=Y,W=X voxel layout."""

    d, h, w = (int(v) for v in shape)
    pose = np.asarray(robot_pose, dtype=np.float32).reshape(-1)
    origin = np.asarray(crop_origin_xyz, dtype=np.float32).reshape(-1)
    if pose.size < 3 or origin.size < 3 or voxel_size <= 0:
        return np.zeros((d, h, w), dtype=np.float32)
    center_w = (float(pose[0]) - float(origin[0])) / float(voxel_size)
    center_h = (float(pose[1]) - float(origin[1])) / float(voxel_size)
    center_d = (float(pose[2]) - float(origin[2])) / float(voxel_size)
    zz, yy, xx = np.meshgrid(
        np.arange(d, dtype=np.float32),
        np.arange(h, dtype=np.float32),
        np.arange(w, dtype=np.float32),
        indexing="ij",
    )
    dist2 = (zz - center_d) ** 2 + (yy - center_h) ** 2 + (xx - center_w) ** 2
    return np.exp(-0.5 * dist2 / max(float(sigma_vox) ** 2, 1e-6)).astype(np.float32)


class MapPredictVoxelDataset(Dataset):
    """PyTorch dataset for local voxel occupancy-completion crops.

    The split file stores paths relative to the dataset root, such as
    ``old_home_like_scene_v1/sample_000000.npz``. Only ``quality_status=pass``
    samples are used by default for Phase 3 baseline training.
    """

    input_channel_names = (
        "observed_free",
        "observed_occupied",
        "unknown_mask",
        "frontier_mask",
        "robot_position_gaussian",
        "height_channel",
    )

    def __init__(
        self,
        split_file: str | Path,
        *,
        dataset_root: str | Path | None = None,
        require_quality_status: str | None = "pass",
        return_torch: bool = True,
    ) -> None:
        self.split_file = Path(split_file)
        root_arg = Path(dataset_root) if dataset_root is not None else None
        self.dataset_root, candidate_paths = _load_split_paths(self.split_file, root_arg)
        self.require_quality_status = require_quality_status
        self.return_torch = bool(return_torch)
        self.sample_paths: list[Path] = []
        self.skipped_paths: list[tuple[Path, str]] = []
        for sample_path in candidate_paths:
            if require_quality_status is None:
                self.sample_paths.append(sample_path)
                continue
            with np.load(sample_path, allow_pickle=True) as data:
                status = _as_text(data["quality_status"]) if "quality_status" in data.files else ""
            if status == require_quality_status:
                self.sample_paths.append(sample_path)
            else:
                self.skipped_paths.append((sample_path, status))
        manifest_path = self.dataset_root / "dataset_manifest.json"
        self.manifest: dict[str, Any] = {}
        if manifest_path.exists():
            self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    def __len__(self) -> int:
        return len(self.sample_paths)

    def _load_arrays(self, sample_path: Path) -> dict[str, Any]:
        with np.load(sample_path, allow_pickle=True) as data:
            return {key: data[key].copy() for key in data.files}

    def __getitem__(self, index: int) -> dict[str, Any]:
        sample_path = self.sample_paths[index]
        arrays = self._load_arrays(sample_path)

        observed_free = arrays["observed_free"].astype(np.uint8)
        observed_occupied = arrays["observed_occupied"].astype(np.uint8)
        unknown_mask = arrays["unknown_mask"].astype(np.uint8)
        frontier_mask = arrays["frontier_mask"].astype(np.uint8)
        full_occupancy = arrays["full_occupancy"].astype(np.float32)
        shape = observed_free.shape
        voxel_size = float(_scalar_to_python(arrays.get("voxel_size", np.array(1.0, dtype=np.float32))))
        crop_origin = arrays.get("crop_origin_xyz", arrays.get("crop_origin", np.zeros(3, dtype=np.float32)))
        robot_pose = arrays.get("robot_pose", np.zeros(4, dtype=np.float32))

        robot_position_gaussian = arrays.get("robot_position_gaussian")
        if robot_position_gaussian is None:
            robot_position_gaussian = _generate_robot_position_gaussian(shape, robot_pose, crop_origin, voxel_size)
        height_channel = arrays.get("height_channel")
        if height_channel is None:
            height_channel = _generate_height_channel(shape)

        input_array = np.stack(
            [
                observed_free.astype(np.float32),
                observed_occupied.astype(np.float32),
                unknown_mask.astype(np.float32),
                frontier_mask.astype(np.float32),
                robot_position_gaussian.astype(np.float32),
                height_channel.astype(np.float32),
            ],
            axis=0,
        )

        metadata = {
            "sample_path": str(sample_path),
            "relative_sample_path": str(sample_path.relative_to(self.dataset_root)),
            "sample_id": _as_text(arrays.get("sample_id", sample_path.stem)),
            "scene_id": _as_text(arrays.get("scene_id", sample_path.parent.name)),
            "episode_id": int(_scalar_to_python(arrays.get("episode_id", np.array(0)))),
            "start_id": int(_scalar_to_python(arrays.get("start_id", np.array(-1)))),
            "step_id": int(_scalar_to_python(arrays.get("step_id", np.array(0)))),
            "quality_status": _as_text(arrays.get("quality_status", "")),
            "quality_flags": arrays.get("quality_flags", np.array([], dtype=object)).tolist(),
            "gt_type": _as_text(arrays.get("gt_type", "")),
            "partial_3d_source": _as_text(arrays.get("partial_3d_source", "")),
            "axis_order_convention": _as_text(arrays.get("axis_order_convention", "D=Z,H=Y,W=X")),
            "voxel_size": voxel_size,
            "crop_origin": np.asarray(crop_origin, dtype=np.float32).reshape(-1).tolist(),
            "robot_pose": np.asarray(robot_pose, dtype=np.float32).reshape(-1).tolist(),
        }

        if torch is not None and self.return_torch:
            return {
                "input": torch.from_numpy(input_array.astype(np.float32)),
                "observed_free": torch.from_numpy(observed_free),
                "observed_occupied": torch.from_numpy(observed_occupied),
                "unknown_mask": torch.from_numpy(unknown_mask),
                "frontier_mask": torch.from_numpy(frontier_mask),
                "full_occupancy": torch.from_numpy(full_occupancy),
                "sample_id": metadata["sample_id"],
                "metadata": metadata,
            }
        return {
            "input": input_array.astype(np.float32),
            "observed_free": observed_free,
            "observed_occupied": observed_occupied,
            "unknown_mask": unknown_mask,
            "frontier_mask": frontier_mask,
            "full_occupancy": full_occupancy,
            "sample_id": metadata["sample_id"],
            "metadata": metadata,
        }
