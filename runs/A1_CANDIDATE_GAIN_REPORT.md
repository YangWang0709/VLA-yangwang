# A1 Candidate Gain Report

phase: Phase 5
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
previous_proxy_results_status: superseded_for_formal_a1_pipeline
sensor_method: geometry_proxy_pointcloud_from_a1_base_pose
map_type: BEV occupancy grid
mapping_method: raycast_bev_proxy_mapping
candidate_sampling_method: radial_24_candidates_3_radii_8_angles_around_a1_base
path_cost_method: euclidean_plus_obstacle_penalty
information_gain_method: bev_unknown_visibility_proxy
score_formula: score = information_gain - 0.35 * path_cost - collision_penalty - invalid_penalty
step_count: 6
candidate_count_per_step: 24
total_candidate_rows: 144
valid_candidate_ratio: 0.3958
positive_gain_candidate_ratio: 0.8056
selected_candidate_valid_rate: 1.0
selected_is_top_score_rate: 1.0
path_cost_constant: false
min_path_cost: 0.9
max_path_cost: 6.98
min_information_gain: 0.0
max_information_gain: 406.0
failure_count: 0
BEV_candidate_render_path: /home/ubuntu22/VLA/runs/phase5_a1_candidate_gain_smoke_20260607_195140/bev_renders
candidate_summary_path: /home/ubuntu22/VLA/runs/phase5_a1_candidate_gain_smoke_20260607_195140/summary/candidate_summary.csv
candidate_steps_path: /home/ubuntu22/VLA/runs/phase5_a1_candidate_gain_smoke_20260607_195140/summary/candidate_steps.jsonl
safe_to_continue_phase6: true
training: false
RL: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout_started: false

## Caveats

- This is proxy-mapping based candidate smoke from existing USD A1, not final real-sensor data.
- Information gain uses BEV unknown visibility proxy, not real RGB-D SLAM or VLM inference.
- Path cost uses Euclidean distance plus BEV obstacle/unknown penalties, not a full planner.
- No A1-bound USD camera/sensor prim was found; candidates use proxy BEV observations only.

## Negative Scope

- No VLM training or inference.
- No VLM-LA interface smoke.
- No RL training.
- No map_predict training or mainline implementation.
- No PI/openpi action-head fine-tuning.
- No A1 locomotion policy training.
- No long rollout.
- No temporary Go2 proxy was created or used as formal data.
- Original USD scene was opened and edited only in memory; it was not saved or overwritten.
