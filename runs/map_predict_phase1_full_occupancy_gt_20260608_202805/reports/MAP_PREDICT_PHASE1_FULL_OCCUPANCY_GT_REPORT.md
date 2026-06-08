# MapPredict Phase 1 Full Occupancy GT Report

phase: MapPredict Phase 1
purpose: generate full occupancy GT prototype for SceneSense-style map_predict
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
map_predict_role: feature_provider
planner: false
VLA: false
training_started: false
map_predict_training_started: false
SFT_started: false
GDPO_started: false
RL_started: false
rollout_started: false

## Route Status

route_a_dense_scan_status: success
route_b_usd_voxelization_status: partial_success
full_occupancy_gt_type: dense_scan_pseudo_gt
safe_to_build_local_voxel_dataset: true
next_phase: MapPredict Phase 2 local voxel crop dataset generation

## Scenes Processed

### old_home_like_scene_v1

scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
dense_scan_status: success
usd_voxelization_status: partial_success
gt_path: /home/ubuntu22/VLA/data/map_predict/full_occupancy_gt/old_home_like_scene_v1/full_occupancy_dense_scan.npz
usd_voxel_gt_path: /home/ubuntu22/VLA/data/map_predict/full_occupancy_gt/old_home_like_scene_v1/full_occupancy_usd_voxel.npz
voxel_size: 0.2
grid_shape: [13, 105, 106]
occupied_count: 5696
free_count: 45683
observed_count: 51379
unknown_count: 93311
occupied_ratio: 0.039367
free_ratio: 0.31573
observed_ratio: 0.355097
quality_pass: true
failure_reason: None
usd_voxel_occupied_count: 21187
usd_voxel_supported_prim_count: 406
usd_voxel_filled_prim_count: 100

### new_building_scene_1

scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
dense_scan_status: success
usd_voxelization_status: partial_success
gt_path: /home/ubuntu22/VLA/data/map_predict/full_occupancy_gt/new_building_scene_1/full_occupancy_dense_scan.npz
usd_voxel_gt_path: /home/ubuntu22/VLA/data/map_predict/full_occupancy_gt/new_building_scene_1/full_occupancy_usd_voxel.npz
voxel_size: 0.2
grid_shape: [13, 102, 111]
occupied_count: 4250
free_count: 34429
observed_count: 38679
unknown_count: 108507
occupied_ratio: 0.028875
free_ratio: 0.233915
observed_ratio: 0.26279
quality_pass: true
failure_reason: None
usd_voxel_occupied_count: 22894
usd_voxel_supported_prim_count: 319
usd_voxel_filled_prim_count: 88

## SceneSense GitHub Alignment

* Reviewed repository: https://github.com/arpg/SceneSense
* Reviewed project page: https://arpg.github.io/scenesense/
* This prototype follows the SceneSense boundary of occupancy completion from partial observation.
* Observed-space preservation remains mandatory for later inference: predictions may fill unknown regions but must not overwrite observed free/occupied voxels.
* Frontier/candidate usage is feature enrichment only; this module does not output robot actions.

## Limitations

* Dense scan GT is `dense_scan_pseudo_gt`, not final perfect mesh GT.
* USD voxelization here is a bounds-fill prototype and is stricter only as an audit aid, not final training GT.
* Generated `.npz` files are excluded from Git by default.
