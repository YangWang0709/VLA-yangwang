# MapPredict Phase 2 Local Voxel Dataset Report

phase: MapPredict Phase 2
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
source_GT: dense_scan_pseudo_gt
source GT: dense_scan_pseudo_gt
dense_scan_pseudo_gt_is_perfect_ground_truth: false
training_ready: false
requires_review: true
training_started: false
map_predict_training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false

## Source Scenes

- old_home_like_scene_v1: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
- new_building_scene_1: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda

## Source Rollout Dirs

- old_home_like_scene_v1: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536
- new_building_scene_1: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904

## Dataset Outputs

dataset_version: local_voxel_v0_dense_scan_pseudo_gt
dataset_path: /home/ubuntu22/VLA/data/map_predict/local_voxel_dataset/local_voxel_v0_dense_scan_pseudo_gt
smoke_dataset_version: local_voxel_smoke_v0_dense_scan_pseudo_gt
smoke_dataset_path: /home/ubuntu22/VLA/data/map_predict/local_voxel_dataset/local_voxel_smoke_v0_dense_scan_pseudo_gt
voxel_shape: [24, 64, 64]
smoke_voxel_shape: [16, 32, 32]
voxel_size: 0.2
crop_type: robot_centered
partial_3d_source: reconstructed_from_saved_rollout_metadata_limited
frontier_mask_generation_method: observed_free voxel adjacent to unknown voxel
frontier_connectivity: 6

## Main Dataset Quality

sample_count: 277
pass_count: 0
warning_count: 277
reject_count: 0
observed_free_count_distribution: {"count": 277, "max": 14754.0, "mean": 4718.209386281588, "min": 366.0, "p50": 4500.0, "p90": 8436.0}
observed_occupied_count_distribution: {"count": 277, "max": 0.0, "mean": 0.0, "min": 0.0, "p50": 0.0, "p90": 0.0}
unknown_count_distribution: {"count": 277, "max": 97938.0, "mean": 93585.79061371842, "min": 83550.0, "p50": 93804.0, "p90": 97227.6}
frontier_count_distribution: {"count": 277, "max": 5992.0, "mean": 2184.967509025271, "min": 270.0, "p50": 2208.0, "p90": 3750.8}
full_occupancy_occupied_count_distribution: {"count": 277, "max": 2940.0, "mean": 1948.0830324909748, "min": 1065.0, "p50": 1947.0, "p90": 2532.2}
gt_observed_conflict_ratio_distribution: {"count": 277, "max": 0.0, "mean": 0.0, "min": 0.0, "p50": 0.0, "p90": 0.0}
empty_crop_count: 0
frontier_empty_count: 0
unknown_empty_count: 0
quality_flag_counts: {"observed_occupied_count_zero": 277, "partial_3d_source_limited": 277}

## Smoke Dataset Quality

sample_count: 16
pass_count: 0
warning_count: 16
reject_count: 0

## Split Summary

split_method: deterministic_scene_id_start_id_group_modulo
train_count: 232
val_count: 21
test_count: 24
train_group_count: 14
val_group_count: 3
test_group_count: 3
group_overlap: false

## Visualization Paths

- /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621/plots/old_home_like_scene_v1/sample_bev_observed_free.png
- /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621/plots/old_home_like_scene_v1/sample_bev_observed_occupied.png
- /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621/plots/old_home_like_scene_v1/sample_bev_unknown.png
- /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621/plots/old_home_like_scene_v1/sample_bev_frontier.png
- /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621/plots/old_home_like_scene_v1/sample_bev_full_occupancy.png
- /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621/plots/old_home_like_scene_v1/sample_z_slices.png
- /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621/plots/new_building_scene_1/sample_bev_observed_free.png
- /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621/plots/new_building_scene_1/sample_bev_observed_occupied.png
- /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621/plots/new_building_scene_1/sample_bev_unknown.png
- /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621/plots/new_building_scene_1/sample_bev_frontier.png
- /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621/plots/new_building_scene_1/sample_bev_full_occupancy.png
- /home/ubuntu22/VLA/runs/map_predict_phase2_local_voxel_dataset_20260608_213621/plots/new_building_scene_1/sample_z_slices.png

## Limitations

- dense_scan_pseudo_gt is pseudo GT generated from multi-view Isaac depth; it is not perfect ground truth.
- Raw per-step 3D pointcloud arrays were not saved in the rollout directories.
- observed_free/observed_occupied are limited metadata reconstructions from rollout poses and map stats.
- The local voxel crop dataset is for engineering validation and human review before any training.

## Safety Decision

safe_to_train_3d_unet_baseline: false
safe_to_continue_phase3_engineering: true
next_phase: MapPredict Phase 3 3D U-Net occupancy completion baseline, only if Phase 2 quality passes and user explicitly approves training.
