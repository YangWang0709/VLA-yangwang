# MapPredict Dataset Spec

phase: MapPredict Phase 0
dataset_role: partial 3D occupancy to full occupancy completion
training_started: false
source_data_mutated: false

## Canonical Sample

```python
sample = {
    "observed_free": [D, H, W],
    "observed_occupied": [D, H, W],
    "unknown_mask": [D, H, W],
    "frontier_mask": [D, H, W],
    "robot_pose": [x, y, z, yaw],
    "full_occupancy": [D, H, W],
    "voxel_size": float,
    "crop_origin": [x, y, z],
    "scene_id": str,
    "episode_id": int,
    "step_id": int,
}
```

## Required Input Channels

* `observed_free`: voxels observed free by fused depth rays.
* `observed_occupied`: voxels observed occupied by depth endpoints or USD GT.
* `unknown_mask`: voxels not yet observed.
* `frontier_mask`: voxels or BEV cells adjacent to known free and unknown space.

## Required Target

* `full_occupancy`: dense occupancy GT for the crop. Current rollout data does
  not contain this field. It must be generated in a later phase by dense scan or
  USD voxelization before supervised training.

## Current Rollout Compatibility

* RGB-D route: available through real Isaac/Omniverse RGB-D outputs.
* Pointcloud route: available as `depth_backprojection`.
* A1 pose: available per sample and per rollout step.
* BEV explored map: available as candidate render images and final ASCII BEV maps.
* Candidate/frontier data: candidate tables are available; explicit frontier masks
  are not yet materialized and should be derived from occupancy grids.
* Full occupancy GT: not available.

## Storage Guidance

First dataset shards should use compressed numpy or zarr-style arrays in a later
phase. Phase 0 only defines schema and code interfaces; it does not create large
array datasets.
