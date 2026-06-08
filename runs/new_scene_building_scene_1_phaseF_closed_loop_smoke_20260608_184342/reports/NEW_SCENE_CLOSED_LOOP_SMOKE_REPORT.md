# New Scene Closed Loop Smoke Report

phase: New Scene Phase F
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
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
final_known_ratio: 0.236667
total_known_ratio_gain: 0.236667
known_ratio_monotonic_non_decreasing: true
average_candidate_count: 24.0
average_valid_candidate_count: 21.4
collision_count: 0
stuck_count: 0
falling_count: 0
failure_count: 0
plots path: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342/plots
summary path: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342/summary/closed_loop_summary.json
safe_to_long_rollout: true
training: false
RL: false
SFT: false
GDPO: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
long_rollout_started: false

## Caveats

- This is a short closed-loop smoke, not a long rollout.
- VLM outputs are pseudo commands generated from the classical selector.
- Movement uses kinematic root updates; no A1 locomotion controller is trained or used.
- BEV mapping uses depth-backprojected real RGB-D pointclouds only.
- Runtime sensors and light are in-memory; the repaired USD is not saved.
- The new scene still emits non-blocking MDL material warnings during Isaac loading.

## Artifacts

- run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342
- closed_loop_steps_csv: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342/summary/closed_loop_steps.csv
- command_log_jsonl: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342/commands/command_log.jsonl
- parse_log_jsonl: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342/parsing/parse_log.jsonl
- summary_json: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342/summary/closed_loop_summary.json
- plots_path: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseF_closed_loop_smoke_20260608_184342/plots

## Evidence

- Candidate generation and scoring were online from the current real-sensor BEV map.
- Commands were pseudo VLM outputs created from the classical selector.
- Parser and validator enforced the `Go to candidate <id>.` contract.
- The repaired USD scene was not saved or overwritten.

## Negative Scope

- No long rollout.
- No training, RL, SFT, GDPO, map_predict, checkpoint, or real VLM inference.
- No geometry proxy or mounted geometry proxy.
- No Go2 label is used as the actual robot platform.
