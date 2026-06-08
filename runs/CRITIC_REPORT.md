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

<!-- phase10_combined_sft_status:start -->
## Phase 10 Combined SFT Dataset Preparation Status

current_phase: Phase 10 combined SFT dataset preparation only
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
source_review_decision: /home/ubuntu22/VLA/runs/COMBINED_DATASET_REVIEW_DECISION.md
phase10_run_dir: /home/ubuntu22/VLA/runs/phase10_combined_sft_dataset_preparation_20260608_193108
sft_sample_count: 273
train_sample_count: 161
val_sample_count: 56
test_sample_count: 56
robot_platform: unitree_a1
sensor_method: real_isaac_omniverse_rgbd
geometry_proxy_used_in_sft: false
training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
checkpoint_created: false
requires_user_approval_before_training: true
next_phase: User approval required before SFT training
<!-- phase10_combined_sft_status:end -->

# Critic Report

## Current Phase

Combined manual review decision before SFT preparation

## Finding

status: completed

The combined review decision aggregates old and new scene quality audit reports
without modifying source data. It approves SFT dataset preparation only, not
direct training, not GDPO preparation, and not any model update.

## Evidence

- old_total_samples: 77
- old_accepted_samples: 74
- old_warning_samples: 3
- old_rejected_samples: 0
- new_total_samples: 200
- new_accepted_samples: 199
- new_warning_samples: 1
- new_rejected_samples: 0
- total_samples_all: 277
- accepted_samples_all: 273
- warning_samples_all: 4
- rejected_samples_all: 0
- whether_all_data_real_sensor: true
- whether_geometry_proxy_in_training_candidates: false
- approve_for_sft_preparation: yes

## Gate

Next phase may prepare a combined SFT dataset artifact. Training itself remains
blocked until a later explicit approval.

training: false
SFT: false
GDPO: false
RL: false
rollout: false
raw_data_modified: false
