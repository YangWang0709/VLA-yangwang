# Active Task Board

current_phase: Phase 5 A1 candidate viewpoint + information gain smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
next_phase: Phase 6 VLM-LA interface smoke

## Phase 5 A1 Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase5_a1_candidate_gain_smoke_20260607_195140
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
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
safe_to_continue_phase6: true

## Caveats

- Phase 5 is proxy-mapping based candidate smoke, not final real-sensor data.
- Information gain uses BEV unknown visibility proxy, not real RGB-D SLAM or VLM inference.
- Path cost uses Euclidean distance plus BEV obstacle/unknown penalties, not a full planner.
- No Phase 6 work was executed in this step.

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- primary_rollout: false
- VLM_inference: false
- Phase_6_executed: false

## Next Phase

Phase 6 VLM-LA interface smoke, only when explicitly requested.
