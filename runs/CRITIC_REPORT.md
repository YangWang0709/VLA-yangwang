# Critic Report

## Current Phase

Phase 5R-real A1 candidate viewpoint + information gain smoke with real sensors

## Corrected Fact

The USD scene's real robot is `/World/A1`, not Go2. Formal data uses:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

## Phase 5R-real Review

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

## Findings

- No blocking issues found for the requested smoke scope.
- Candidate gain uses real RGB-D depth backprojection and BEV map updates, not old proxy data.
- `selected_by_classical` matched the top-scoring valid positive-gain candidate for every decision step.
- `path_cost_constant` is false and information gain varies across candidates.

## Residual Risks And Caveats

- This is a smoke validation of the classical candidate interface, not final autonomous exploration.
- RTX LiDAR and segmentation are optional telemetry and are not required for pass/fail.
- Phase 6 VLM-LA interface smoke is now allowed by the gate, but was not run here.

## Prohibited Work Check

- VLM training performed: false
- VLM inference performed: false
- Phase 6 performed: false
- RL training performed: false
- map_predict training performed: false
- PI/openpi fine-tuning performed: false
- A1 locomotion training performed: false
- rollout performed: false
- original USD saved or overwritten: false
- geometry proxy used: false
- mounted geometry proxy used: false
- large files committed: false

## Decision

safe_to_continue_phase6: true
next_phase: Phase 6 VLM-LA interface smoke
