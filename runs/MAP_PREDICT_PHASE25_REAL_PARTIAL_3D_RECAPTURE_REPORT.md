# MapPredict Phase 2.5 Real Partial 3D Recapture Report

phase: MapPredict Phase 2.5
purpose: rebuild real partial 3D occupancy samples
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
map_predict_role: feature_provider
planner: false
VLA: false
training_started: false
map_predict_training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false

## Old Phase 2 Limitation Summary

* Phase 2 proved dataset schema, crop, manifest, split, and visualization plumbing.
* Phase 2 used reconstructed_from_saved_rollout_metadata_limited because raw per-step 3D depth endpoints were not retained.
* Phase 2 main warning_count was 277 / 277, with observed_occupied_count_zero on every sample.
* Phase 2 safe_to_train_3d_unet_baseline was false.

## Recapture Method

route used: recapture
sensor_method: real_isaac_omniverse_rgbd
partial_3d_source: real_depth_backprojection_raycast
gt_type: dense_scan_pseudo_gt
frontier_connectivity: 6-neighborhood
start_count_per_scene: 5
max_steps_per_start: 10
full_occupancy_used_as_input: false
full_occupancy_label_only: true
dense_scan_pseudo_gt_is_perfect_ground_truth: false

## Scenes Processed

### old_home_like_scene_v1

scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
status: success
route_used: recapture
capture_step_count: 50
valid_rgb_capture_count: 50
valid_depth_capture_count: 50
world_point_count_total: 39122
failure_reason: None

### new_building_scene_1

scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
status: success
route_used: recapture
capture_step_count: 50
valid_rgb_capture_count: 50
valid_depth_capture_count: 50
world_point_count_total: 40513
failure_reason: None

## Main Dataset Summary

dataset_version: local_voxel_v1_real_partial_3d
dataset path: /home/ubuntu22/VLA/data/map_predict/local_voxel_dataset/local_voxel_v1_real_partial_3d
sample_count: 100
pass_count: 7
warning_count: 3
reject_count: 90
observed_occupied_zero_rate: 0.02
frontier_empty_rate: 0.0
gt_conflict stats: {'count': 100, 'max': 0.7987804878048781, 'mean': 0.39794723817101413, 'min': 0.0, 'p50': 0.4088288312170294, 'p90': 0.5324908974084389}
observed_free_count: {'count': 100, 'max': 4344.0, 'mean': 1625.29, 'min': 46.0, 'p50': 1460.0, 'p90': 2612.4}
observed_occupied_count: {'count': 100, 'max': 456.0, 'mean': 254.02, 'min': 0.0, 'p50': 269.0, 'p90': 360.3000000000001}
unknown_count: {'count': 100, 'max': 98258.0, 'mean': 96424.69, 'min': 93517.0, 'p50': 96579.5, 'p90': 97315.4}
frontier_count: {'count': 100, 'max': 2193.0, 'mean': 876.73, 'min': 46.0, 'p50': 720.5, 'p90': 1491.800000000001}
full_occupancy_occupied_count: {'count': 100, 'max': 2635.0, 'mean': 2249.11, 'min': 1811.0, 'p50': 2222.0, 'p90': 2588.0}
quality_flag_counts: {'low_observed_free_count': 2, 'observed_occupied_count_zero': 2, 'severe_gt_observed_conflict_ratio': 90}

## Split Summary

split summary: {'group_overlap': False, 'split_method': 'deterministic_scene_id_start_id_group_modulo', 'test_count': 10, 'test_group_count': 1, 'train_count': 70, 'train_group_count': 7, 'val_count': 20, 'val_group_count': 2}

## Visualization Paths

* /home/ubuntu22/VLA/runs/map_predict_phase25_real_partial_3d_recapture_20260608_235553/plots/old_home_like_scene_v1/sample_bev_observed_free.png
* /home/ubuntu22/VLA/runs/map_predict_phase25_real_partial_3d_recapture_20260608_235553/plots/old_home_like_scene_v1/sample_bev_observed_occupied.png
* /home/ubuntu22/VLA/runs/map_predict_phase25_real_partial_3d_recapture_20260608_235553/plots/old_home_like_scene_v1/sample_bev_unknown.png
* /home/ubuntu22/VLA/runs/map_predict_phase25_real_partial_3d_recapture_20260608_235553/plots/old_home_like_scene_v1/sample_bev_frontier.png
* /home/ubuntu22/VLA/runs/map_predict_phase25_real_partial_3d_recapture_20260608_235553/plots/old_home_like_scene_v1/sample_bev_full_occupancy.png
* /home/ubuntu22/VLA/runs/map_predict_phase25_real_partial_3d_recapture_20260608_235553/plots/old_home_like_scene_v1/sample_z_slices.png
* /home/ubuntu22/VLA/runs/map_predict_phase25_real_partial_3d_recapture_20260608_235553/plots/new_building_scene_1/sample_bev_observed_free.png
* /home/ubuntu22/VLA/runs/map_predict_phase25_real_partial_3d_recapture_20260608_235553/plots/new_building_scene_1/sample_bev_observed_occupied.png
* /home/ubuntu22/VLA/runs/map_predict_phase25_real_partial_3d_recapture_20260608_235553/plots/new_building_scene_1/sample_bev_unknown.png
* /home/ubuntu22/VLA/runs/map_predict_phase25_real_partial_3d_recapture_20260608_235553/plots/new_building_scene_1/sample_bev_frontier.png
* /home/ubuntu22/VLA/runs/map_predict_phase25_real_partial_3d_recapture_20260608_235553/plots/new_building_scene_1/sample_bev_full_occupancy.png
* /home/ubuntu22/VLA/runs/map_predict_phase25_real_partial_3d_recapture_20260608_235553/plots/new_building_scene_1/sample_z_slices.png

## Smoke Dataset Summary

dataset_version: local_voxel_smoke_v1_real_partial_3d
dataset path: /home/ubuntu22/VLA/data/map_predict/local_voxel_dataset/local_voxel_smoke_v1_real_partial_3d
sample_count: 100
pass_count: 1
warning_count: 3
reject_count: 96
observed_occupied_zero_rate: 0.02

## Decision

recapture_completed: true
main_reject_rate: 0.9
safe_to_rebuild_phase2_dataset: false
safe_to_train_3d_unet_baseline: false
next_phase: MapPredict Phase 2.6 finalize local voxel dataset with real partial 3D and resolve pseudo-GT alignment conflicts

## Constraints Honored

* map_predict training: false
* 3D U-Net training: false
* diffusion training: false
* VLA training: false
* SFT: false
* GDPO: false
* RL: false
* source USD modified: false
* raw RGB-D saved: false
* raw pointcloud dumps saved: false
* large `.npz` committed: false
