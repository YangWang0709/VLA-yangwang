# A1 VLM-LA Closed Loop Smoke Report

phase: Phase 7
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
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
plots path: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/plots
summary path: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/summary/closed_loop_summary.json
safe_to_continue_phase8: true
caveats: ['This is a short closed-loop smoke, not a long rollout.', 'VLM outputs are pseudo commands generated from the classical selector.', 'Movement uses kinematic root updates; no A1 locomotion controller is trained or used.', 'BEV mapping uses depth-backprojected real RGB-D pointclouds only.', 'Runtime sensors and light are in-memory; the primary USD is not saved.']
training: false
RL: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
long_rollout_started: false

## Evidence

- run_dir: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429
- closed_loop_steps_csv: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/summary/closed_loop_steps.csv
- command_log_jsonl: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/commands/command_log.jsonl
- parse_log_jsonl: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/parsing/parse_log.jsonl
- Candidate generation and scoring were online from the current real-sensor BEV map.
- Commands were pseudo VLM outputs created from the classical selector.
- The original USD scene was not saved or overwritten.

## Negative Scope

- No Phase 8.
- No long rollout.
- No training, RL, map_predict, checkpoint, or real VLM inference.
- No geometry proxy or mounted geometry proxy.
- No Go2 label is used as the actual robot platform.
