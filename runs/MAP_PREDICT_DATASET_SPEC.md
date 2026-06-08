<!-- map_predict_phase1_status:start -->
## MapPredict Phase 1 Full Occupancy GT Prototype Status

current_phase: MapPredict Phase 1 full occupancy GT prototype
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
map_predict_goal: SceneSense-style partial occupancy completion and uncertainty feature provider
map_predict_is_planner: false
map_predict_is_vla: false
map_predict_outputs_actions: false
SceneSense_GitHub_reviewed: true
SceneSense_repo: https://github.com/arpg/SceneSense
SceneSense_project_page: https://arpg.github.io/scenesense/
route_a_dense_scan_status: success
route_b_usd_voxelization_status: partial_success
full_occupancy_gt_type: dense_scan_pseudo_gt
pseudo_gt_not_final_mesh_gt: true
safe_to_build_local_voxel_dataset: true
training_started: false
map_predict_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false
source_vla_data_modified: false
next_phase: MapPredict Phase 2 local voxel crop dataset generation
run_dir: /home/ubuntu22/VLA/runs/map_predict_phase1_full_occupancy_gt_20260608_202805
summary_json: /home/ubuntu22/VLA/runs/map_predict_phase1_full_occupancy_gt_20260608_202805/summary/full_occupancy_gt_summary.json
report: /home/ubuntu22/VLA/runs/MAP_PREDICT_PHASE1_FULL_OCCUPANCY_GT_REPORT.md
<!-- map_predict_phase1_status:end -->

## Phase 1 Scene Results

old_home_like_scene_v1:
- dense_scan_status: success
- usd_voxelization_status: partial_success
- dense_scan_gt_path: /home/ubuntu22/VLA/data/map_predict/full_occupancy_gt/old_home_like_scene_v1/full_occupancy_dense_scan.npz
- usd_voxel_gt_path: /home/ubuntu22/VLA/data/map_predict/full_occupancy_gt/old_home_like_scene_v1/full_occupancy_usd_voxel.npz

new_building_scene_1:
- dense_scan_status: success
- usd_voxelization_status: partial_success
- dense_scan_gt_path: /home/ubuntu22/VLA/data/map_predict/full_occupancy_gt/new_building_scene_1/full_occupancy_dense_scan.npz
- usd_voxel_gt_path: /home/ubuntu22/VLA/data/map_predict/full_occupancy_gt/new_building_scene_1/full_occupancy_usd_voxel.npz

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
