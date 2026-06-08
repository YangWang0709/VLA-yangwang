"""Dataset contracts for SceneSense-style occupancy completion.

The map_predict package is a feature provider. It consumes partial 3D
occupancy observations and returns predicted occupancy plus uncertainty. It is
not a planner, VLA model, rollout collector, or training launcher.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


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
) -> dict[str, Any]:
    """Build the canonical manifest for a local voxel crop dataset."""

    return {
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
