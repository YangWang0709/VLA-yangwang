# Active Task Board

current_phase: Phase 7 A1 VLM-LA closed-loop smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
candidate_data_source: online_real_sensor_candidate_generation
vlm_output_mode: pseudo_from_classical_selector
negative_scope:
- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- real_vlm_inference: false
- long_rollout: false
next_phase: Phase 8 A1 primary-scene VLM-LA long rollout data collection

## Phase 7 Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429
script: /home/ubuntu22/VLA/scripts/phase7_a1_vlm_la_closed_loop_smoke.py
report: /home/ubuntu22/VLA/runs/A1_VLM_LA_CLOSED_LOOP_SMOKE_REPORT.md
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
geometry_proxy_used: false
mounted_geometry_proxy_used: false
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
real_vlm_inference: false
vlm_output_mode: pseudo_from_classical_selector
candidate_data_source: online_real_sensor_candidate_generation
output_contract: Go to candidate <id>.
action_count: 5
successful_action_count: 5
parse_success_rate: 1.0
validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
movement_success_rate: 1.0
fallback_count: 0
initial_known_ratio: 0.0
final_known_ratio: 0.322222
total_known_ratio_gain: 0.322222
known_ratio_monotonic_non_decreasing: true
average_candidate_count: 24.0
average_valid_candidate_count: 21.4
collision_count: 0
stuck_count: 0
falling_count: 0
failure_count: 0
safe_to_continue_phase8: true

## Evidence Paths

- closed_loop_steps_csv: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/summary/closed_loop_steps.csv
- command_log_jsonl: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/commands/command_log.jsonl
- parse_log_jsonl: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/parsing/parse_log.jsonl
- summary_json: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/summary/closed_loop_summary.json
- plots_path: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/plots

## Decision

Phase 7 passed as a short closed-loop smoke using existing USD A1, real Isaac/Omniverse RGB-D sensing, online candidate generation, pseudo VLM commands, parser/validator, and kinematic movement. It is safe to continue to Phase 8 A1 primary-scene VLM-LA long rollout data collection when explicitly requested. Phase 8 was not run in this task.
