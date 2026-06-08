<!-- map_predict_phase25_status:start -->
## MapPredict Phase 2.5 Real Partial 3D Interface Status

current_phase: MapPredict Phase 2.5 real partial 3D occupancy recapture
feature_provider_role: true
planner: false
VLA: false
output_actions: false
input_partial_3d_source: real_depth_backprojection_raycast
input_channels: observed_free, observed_occupied, unknown_mask, frontier_mask, robot_position_gaussian, height_channel
metadata_channels: robot_pose, camera_pose, camera_intrinsics, crop_origin_xyz, crop_center_xyz, voxel_size
target_label: full_occupancy
target_label_type: dense_scan_pseudo_gt
target_label_is_perfect_ground_truth: false
full_occupancy_used_as_input: false
observed_occupied_zero_rate: 0.02
safe_to_train_3d_unet_baseline: false
training_started: false
map_predict_training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
VLM_output_contract_unchanged: Go to candidate <id>.
next_phase: MapPredict Phase 2.6 finalize local voxel dataset with real partial 3D and resolve pseudo-GT alignment conflicts
<!-- map_predict_phase25_status:end -->

<!-- map_predict_phase2_status:start -->
## MapPredict Phase 2 Local Voxel Dataset Status

current_phase: MapPredict Phase 2 local voxel crop dataset generation
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
map_predict_goal: SceneSense-style partial occupancy completion and uncertainty feature provider
dataset_version: local_voxel_v0_dense_scan_pseudo_gt
dataset_path: /home/ubuntu22/VLA/data/map_predict/local_voxel_dataset/local_voxel_v0_dense_scan_pseudo_gt
source_GT: dense_scan_pseudo_gt
dense_scan_pseudo_gt_is_perfect_ground_truth: false
partial_3d_source: reconstructed_from_saved_rollout_metadata_limited
voxel_shape: [24, 64, 64]
voxel_size: 0.2
sample_count: 277
pass_count: 0
warning_count: 277
reject_count: 0
training_started: false
map_predict_training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false
requires_review: true
training_ready: false
safe_to_train_3d_unet_baseline: false
run_dir: /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621
report: /home/ubuntu22/VLA/runs/MAP_PREDICT_PHASE2_LOCAL_VOXEL_DATASET_REPORT.md
next_phase: MapPredict Phase 3 3D U-Net occupancy completion baseline, only if Phase 2 quality passes
<!-- map_predict_phase2_status:end -->



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

# MapPredict Interface Spec

phase: MapPredict Phase 0
module: map_predict
role: feature_provider
planner: false
VLA: false
training_started: false

## Input

The feature provider receives a voxel crop with channels:

* observed_free: [D, H, W]
* observed_occupied: [D, H, W]
* unknown_mask: [D, H, W]
* frontier_mask: [D, H, W]
* robot_pose: [x, y, z, yaw]
* crop_origin: [x, y, z]
* voxel_size: float

## Output

The feature provider returns:

* predicted_occupancy: [D, H, W]
* occupancy_probability: [D, H, W]
* uncertainty: [D, H, W]
* bev_uncertainty: [H, W]
* optional candidate_features with local uncertainty statistics

## Downstream Contract

map_predict must not emit navigation commands. It only enriches map and candidate
features. The VLM-LA output contract remains:

`Go to candidate <id>.`

## Candidate Feature Enrichment

For each candidate, later phases may attach:

* map_predict_uncertainty_mean
* map_predict_uncertainty_max
* predicted_occupied_ratio_near_candidate
* predicted_free_ratio_near_candidate
* unknown_to_predicted_free_gain

These fields are advisory features. They do not replace command validation.
