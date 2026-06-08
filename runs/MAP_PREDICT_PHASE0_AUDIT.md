# MapPredict Phase 0 Audit

phase: MapPredict Phase 0
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
module_name: map_predict
module_role: SceneSense-style feature provider
planner: false
VLA: false
training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false
source_vla_data_modified: false

## Existing Data Sources

old_scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
old_rollout_dir: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536
old_quality_dir: /home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732
old_accepted_samples: 74
old_warning_samples: 3
old_rejected_samples: 0

new_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
new_rollout_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904
new_quality_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002
new_accepted_samples: 199
new_warning_samples: 1
new_rejected_samples: 0

## Data Availability Audit

RGB-D available: true

Evidence:

* old scene `rgb_valid_rate: 0.987`, `depth_valid_rate: 1.0`
* new scene `rgb_valid_rate: 1.0`, `depth_valid_rate: 1.0`
* sample media paths exist under both rollout dirs for BEV, RGB, and depth visualization.

depth_backprojection pointcloud available: true

Evidence:

* old scene `camera_pointcloud_valid_rate: 1.0`
* new scene `camera_pointcloud_valid_rate: 1.0`
* sample field `camera_pointcloud_source: depth_backprojection`
* rollout step fields include `camera_pointcloud_available`, `depth_valid_ratio`, and `pointcloud_point_count`.

A1 pose available: true

Evidence:

* sample field `robot_pose` is present with `[x, y, z, yaw]` values.
* rollout step CSV includes pre and post base pose fields.

BEV explored_map available: partially

Evidence:

* per-step BEV candidate render images exist.
* final BEV ASCII maps exist per start in `maps/start_*_final_bev_ascii.txt`.
* per-step numeric 3D occupancy tensors are not currently materialized.

candidate/frontier data available: partially

Evidence:

* candidate tables are present per sample with id, pose, validity, path cost,
  information gain, and score.
* explicit frontier masks are not stored yet. They should be derived from
  `observed_free` and `unknown_mask` after voxelization.

full occupancy GT available: false

Evidence:

* accepted VLM-LA samples have no `full_occupancy`, GT, or dense occupancy keys.
* current rollout artifacts are partial exploration outputs, not complete scene
  occupancy labels.

## Can Current Rollouts Produce MapPredict Samples?

can_generate_partial_observation_inputs: true
can_generate_frontier_masks_after_voxelization: true
can_generate_supervised_full_occupancy_targets_now: false
ready_to_train_map_predict: false

Current data can seed partial-observation inputs and candidate-feature alignment,
but supervised map_predict training requires full occupancy GT generation first.

## Required Sample Format

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

## Full Occupancy GT Generation Options

Option A: USD voxelization

* Open repaired USD scenes read-only.
* Traverse collision/renderable meshes and voxelize occupied space into a
  scene-level grid.
* Produce crop-level `full_occupancy` by slicing around each robot pose.
* Advantage: deterministic and does not require rollout.
* Risk: needs careful treatment of thin geometry, non-collidable visuals, and
  semantic filtering.

Option B: dense scan

* Run a separate approved data-generation phase with fixed dense camera/A1 poses.
* Fuse multiview depth into a dense scene occupancy or TSDF grid.
* Produce crop-level `full_occupancy` from the dense fused grid.
* Advantage: sensor-consistent labels.
* Risk: requires explicit approval because it is new simulation data collection.

Recommended next phase: MapPredict Phase 1 USD voxelization and dense-scan GT
prototype, without model training.

## Files Created

* map_predict/dataset.py
* map_predict/voxelize.py
* map_predict/crop.py
* map_predict/model_3d_unet.py
* map_predict/diffusion.py
* map_predict/train.py
* map_predict/sample.py
* map_predict/uncertainty.py
* map_predict/bev_project.py
* map_predict/metrics.py
* map_predict/frontier_features.py
* configs/map_predict/voxel_32x32x16.yaml
* configs/map_predict/voxel_64x64x24.yaml
* configs/map_predict/diffusion_small.yaml
* runs/MAP_PREDICT_PLAN.md
* runs/MAP_PREDICT_DATASET_SPEC.md
* runs/MAP_PREDICT_INTERFACE_SPEC.md
* runs/MAP_PREDICT_PHASE0_AUDIT.md

## Safety Conclusion

safe_to_continue_map_predict_phase1: true
safe_to_train_map_predict: false
requires_full_occupancy_gt_before_training: true
requires_user_approval_before_training: true
