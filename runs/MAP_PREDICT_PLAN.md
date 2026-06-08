<!-- map_predict_phase25_status:start -->
## MapPredict Phase 2.5 Real Partial 3D Recapture Status

current_phase: MapPredict Phase 2.5 real partial 3D occupancy recapture
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
module_role: SceneSense-style feature provider
dataset_version: local_voxel_v1_real_partial_3d
partial_3d_source: real_depth_backprojection_raycast
gt_type: dense_scan_pseudo_gt
recapture_completed: true
sample_count: 100
observed_occupied_zero_rate: 0.02
main_reject_rate: 0.9
safe_to_rebuild_phase2_dataset: false
safe_to_train_3d_unet_baseline: false
training_started: false
map_predict_training_started: false
VLA_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
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

# MapPredict Plan

phase: MapPredict Phase 0
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
module_name: map_predict
module_role: SceneSense-style feature provider
planner: false
VLA: false
training_started: false
rollout_started: false
GDPO_started: false

## Objective

Implement a map_predict module that consumes partial 3D occupancy and returns
predicted occupancy plus uncertainty. The output is intended to enrich frontier
and candidate features for later planners or VLM-LA interfaces. It does not
select actions by itself.

## Phase 0 Scope

* Audit whether current real-sensor rollout data can produce map_predict samples.
* Define the canonical sample schema.
* Create engineering skeleton files under `map_predict/`.
* Create draft configs under `configs/map_predict/`.
* Document the interface between occupancy completion and downstream frontier features.

## Planned Phases

1. Phase 0: data audit and format design.
2. Phase 1: generate full occupancy GT by dense scan or USD voxelization.
3. Phase 2: build offline map_predict dataset shards.
4. Phase 3: train a small 3D occupancy completion baseline only after approval.
5. Phase 4: expose uncertainty BEV and candidate-level feature enrichment.
6. Phase 5: evaluate closed-loop impact without changing the VLM output contract.

## Non-Goals

* No VLM training.
* No SFT or GDPO.
* No rollout.
* No planner implementation.
* No mutation of Phase 8, Phase G, Phase 9, Phase H, or Phase 10 source data.
