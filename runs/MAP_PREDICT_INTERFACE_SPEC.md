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
