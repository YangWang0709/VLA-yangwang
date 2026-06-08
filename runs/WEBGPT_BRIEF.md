<!-- map_predict_phase5_status:start -->
## MapPredict Phase 5 Frontier Scoring Status

current_phase: MapPredict Phase 5 frontier scoring baseline
project_name: A1-VLM-LA Explorer
module_role: SceneSense-style feature provider
source_model: Phase 3 3D U-Net baseline
source_uncertainty: Phase 4 probability_entropy
3d_unet_checkpoint_available: true
frontier_row_count: 92
sample_count: 29
selected_frontier_count: 29
selected_frontier_valid_rate: 1.0
selected_is_top_score_rate: 1.0
nan_feature_count: 0
nan_score_count: 0
path_cost_method: euclidean_proxy
reachability_method: bev_validity_proxy
map_predict_training_started: false
diffusion_training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false
safe_to_integrate_with_exploration_selector: true
safe_to_prepare_vla_features: true
data_volume_warning: current dataset is sufficient for pipeline validation but not final training or paper-level results
next_phase: MapPredict Phase 6 integrate map_predict features into frontier selector / VLA dataset builder
<!-- map_predict_phase5_status:end -->

<!-- map_predict_phase4_status:start -->
## MapPredict Phase 4 Uncertainty + BEV Projection Status

current_phase: MapPredict Phase 4 uncertainty baseline + BEV projection
project_name: A1-VLM-LA Explorer
module_role: SceneSense-style feature provider
source_model: 3D U-Net baseline
3d_unet_checkpoint_available: true
dataset: local_voxel_v2_aligned_real_partial_3d
samples_evaluated: 29
uncertainty_method: probability_entropy
mc_dropout_available: false
bev_occ_projection: max
bev_uncertainty_projection: max
observed_space_preserved: true
observed_consistency_error_after_projection: 0.0
unknown_region_iou: 0.24285150260276642
unknown_region_bce: 0.1688627752784241
uncertainty_mean_unknown: 0.11295758059312558
uncertainty_mean_observed: 0.0
frontier_feature_row_count: 92
frontier_feature_nan_count: 0
map_predict_training_started: false
diffusion_training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false
checkpoint_committed_to_git: false
safe_to_build_frontier_scoring_baseline: true
next_phase: MapPredict Phase 5 frontier feature extraction and scoring baseline
<!-- map_predict_phase4_status:end -->

<!-- map_predict_phase3_status:start -->
## MapPredict Phase 3 3D U-Net Baseline Status

current_phase: MapPredict Phase 3 3D U-Net occupancy completion baseline
project_name: A1-VLM-LA Explorer
module_role: SceneSense-style feature provider
dataset: local_voxel_v2_aligned_real_partial_3d
gt_type: dense_scan_pseudo_gt
dense_scan_pseudo_gt_is_perfect_ground_truth: false
partial_3d_source: real_depth_backprojection_raycast
sample_count: 97
train/val/test: 68 / 20 / 9
model: lightweight 3-level 3D U-Net
input_channels: observed_free, observed_occupied, unknown_mask, frontier_mask, robot_position_gaussian, height_channel
output: occupancy_logits [B,1,D,H,W]
training_started: true
map_predict_training_started: true
diffusion_training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false
best_val_unknown_iou: 0.24434269921427498
best_val_unknown_bce: 0.16702158148546034
test_unknown_iou: 0.2395377323549695
observed_consistency_error: 0.0
checkpoint_committed_to_git: false
safe_to_build_uncertainty_baseline: true
next_phase: MapPredict Phase 4 uncertainty baseline via MC dropout / ensemble or lightweight diffusion sampling
<!-- map_predict_phase3_status:end -->

<!-- map_predict_phase26_status:start -->
## MapPredict Phase 2.6 Alignment Debug Status

current_phase: MapPredict Phase 2.6 pseudo-GT alignment conflict resolution
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
source_dataset: local_voxel_v1_real_partial_3d
corrected_dataset_version: local_voxel_v2_aligned_real_partial_3d
corrected_dataset_path: /home/ubuntu22/VLA/data/map_predict/local_voxel_dataset/local_voxel_v2_aligned_real_partial_3d
axis_order_convention: D=Z,H=Y,W=X
partial_3d_source: real_depth_backprojection_raycast
gt_type: dense_scan_pseudo_gt
main_conflict_cause: Phase 2.5 counted dense_scan_pseudo_gt unknown voxels as conflicts.
fixes_applied: conflict_metric_excludes_gt_unknown; endpoint_margin_vox_1
sample_count: 100
pass_count: 97
warning_count: 3
reject_count: 0
observed_occupied_zero_rate: 0.02
gt_observed_conflict_ratio_mean: 0.024815626936946437
gt_observed_conflict_ratio_p95: 0.06417149773117023
round_trip_error_max: 0.0
voxel_size_check: pass
training_started: false
map_predict_training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
training_ready: false
requires_review: true
safe_to_train_3d_unet_baseline: true
next_phase: MapPredict Phase 3 3D U-Net occupancy completion baseline
<!-- map_predict_phase26_status:end -->

<!-- map_predict_phase25_status:start -->
## MapPredict Phase 2.5 Real Partial 3D Recapture Status

current_phase: MapPredict Phase 2.5 real partial 3D occupancy recapture
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
dataset_version: local_voxel_v1_real_partial_3d
dataset_path: /home/ubuntu22/VLA/data/map_predict/local_voxel_dataset/local_voxel_v1_real_partial_3d
source_GT: dense_scan_pseudo_gt
dense_scan_pseudo_gt_is_perfect_ground_truth: false
partial_3d_source: real_depth_backprojection_raycast
sensor_method: real_isaac_omniverse_rgbd
sample_count: 100
pass_count: 7
warning_count: 3
reject_count: 90
observed_occupied_zero_rate: 0.02
frontier_empty_rate: 0.0
main_reject_rate: 0.9
main_reject_reason: severe_gt_observed_conflict_ratio_against_dense_scan_pseudo_gt
recapture_completed: true
training_started: false
map_predict_training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
safe_to_rebuild_phase2_dataset: false
safe_to_train_3d_unet_baseline: false
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

# WEBGPT Brief

## Current Phase

Combined manual review decision before SFT preparation

## Context

current_phase: Combined manual review decision before SFT preparation
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
output_contract: Go to candidate <id>.
old_scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
new_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
old_quality_audit_completed: true
new_quality_audit_completed: true
total_samples_all: 277
accepted_samples_all: 273
warning_samples_all: 4
rejected_samples_all: 0
combined_acceptance_rate: 0.9856
whether_data_is_multi_scene: true
whether_all_data_real_sensor: true
whether_geometry_proxy_in_training_candidates: false
approve_for_sft_preparation: yes
approve_for_direct_training: no
approve_for_gdpo_preparation: no
training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false
next_phase: Phase 10 combined SFT dataset preparation, only if approved

negative_scope:
- training: false
- SFT: false
- GDPO: false
- RL: false
- rollout: false
- resampling: false
- real_VLM_inference: false
- raw_data_modified: false
- training_ready_changed: false


## Decision

The old primary scene dataset and the new building_scene_1 dataset have both
completed quality audit / human review packet stages. Combined rejected samples
are 0, real sensor rate is 1.0 for both, and parser/validator rates are 1.0.

Recommended next phase: Phase 10 combined SFT dataset preparation, only if approved.
No model training is approved by this decision.
