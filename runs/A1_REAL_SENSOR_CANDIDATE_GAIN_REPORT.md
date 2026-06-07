# A1 Real Sensor Candidate Gain Smoke Report

phase: Phase 5R-real
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
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
BEV candidate render path: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631/bev_renders
candidate_summary path: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631/summary/candidate_summary.csv
candidate_steps path: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631/summary/candidate_steps.jsonl
safe_to_continue_phase6: true
caveats: ['Candidate gain is classical scoring, not VLM inference.', 'BEV map and candidate gains use depth-backprojected real RGB-D pointclouds.', 'RTX LiDAR and segmentation are optional telemetry and not required for pass/fail.', 'Runtime sensors and light are in-memory; the primary USD is not saved.']
training: false
RL: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout_started: false

## Evidence

- run_dir: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631
- candidate_summary_json: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631/summary/candidate_summary.json
- candidate_summary_csv: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631/summary/candidate_summary.csv
- candidate_steps_jsonl: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631/summary/candidate_steps.jsonl
- bev_renders_dir: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631/bev_renders
- Candidate scoring used the BEV map updated from depth-backprojected real RGB-D pointclouds.
- RTX LiDAR and segmentation were recorded only as optional telemetry.
- The original USD scene was not saved or overwritten.

## Negative Scope

- No Phase 6 was run automatically.
- No VLM inference or fine-tuning.
- No training, RL, map_predict, checkpoint, or rollout.
- No geometry proxy or mounted geometry proxy candidate-gain source.
- No Go2 label is used as the actual robot platform.
