# WEBGPT Brief

## Current Phase

Phase 5R-real A1 candidate viewpoint + information gain smoke with real sensors

## Context

current_phase: Phase 5R-real A1 candidate viewpoint + information gain smoke with real sensors
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
primary_input_channels:
- RGB
- depth
- depth_backprojected_pointcloud
- camera intrinsics/extrinsics
- BEV explored_map
- candidate viewpoints
optional_channels:
- semantic segmentation
- instance segmentation
- RTX LiDAR
negative_scope:
- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- primary_rollout: false
next_phase: Phase 6 VLM-LA interface smoke

## Completed

- Created `scripts/phase5r_a1_real_sensor_candidate_gain_smoke.py`.
- Opened the primary USD scene without saving or overwriting it.
- Used existing `/World/A1` and `/World/A1/base`.
- Reused the real Isaac/Omniverse RGB-D route from Phase 5.6/4R.
- Updated BEV explored_map from depth-backprojected real RGB-D pointclouds.
- Generated 24 candidate viewpoints per step for 6 smoke steps.
- Computed validity, A* grid path cost, unknown visibility information gain, classical score, and selected candidate sanity checks.
- Wrote `runs/A1_REAL_SENSOR_CANDIDATE_GAIN_REPORT.md`.

## Metrics

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631
script: /home/ubuntu22/VLA/scripts/phase5r_a1_real_sensor_candidate_gain_smoke.py
report: /home/ubuntu22/VLA/runs/A1_REAL_SENSOR_CANDIDATE_GAIN_REPORT.md
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
camera_pointcloud_source: depth_backprojection
semantic_segmentation_available: true
instance_segmentation_available: true
rtx_lidar_available: true
lidar_used_for_candidate_gain: false
lidar_is_required_for_pass: false
geometry_proxy_used: false
mounted_geometry_proxy_used: false
map_type: BEV occupancy grid
mapping_method: raycast_real_sensor_bev_mapping
map_update_source: depth_backprojection_pointcloud
candidate_sampling_method: radial_24_candidates_3_radii_8_angles_around_a1_base
path_cost_method: astar_bev_grid_unknown_penalty
information_gain_method: real_sensor_bev_unknown_visibility
score_formula: score = information_gain - 0.2 * path_cost - 1.0 * collision_penalty - 200.0 * invalid_penalty
step_count: 6
successful_steps: 6
candidate_count_per_step: 24
total_candidate_rows: 144
valid_candidate_ratio: 0.8958
positive_gain_candidate_ratio: 0.8819
selected_candidate_valid_rate: 1.0
selected_is_top_score_rate: 1.0
path_cost_constant: false
min_path_cost: 1.0243
max_path_cost: 6.4742
min_information_gain: 0
max_information_gain: 749
failure_count: 0
safe_to_continue_phase6: true

## Negative Scope

- No VLM inference or fine-tuning.
- No Phase 6 execution.
- No training, RL, map_predict, checkpoint, long rollout, or A1 locomotion training.
- No geometry proxy or mounted geometry proxy.
- No Go2 label is used as the actual robot platform.
