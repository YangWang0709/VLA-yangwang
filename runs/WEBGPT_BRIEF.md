# WEBGPT Brief

## Current Phase

Phase 7 A1 VLM-LA closed-loop smoke

## Context

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

## Completed

- Created `scripts/phase7_a1_vlm_la_closed_loop_smoke.py`.
- Opened the primary USD scene without saving or overwriting it.
- Used existing `/World/A1` and `/World/A1/base`.
- Used the real Isaac/Omniverse RGB-D route with depth-backprojected pointclouds.
- Updated a BEV explored_map from real sensor data.
- Generated online candidate viewpoints and classical scores at each action step.
- Emitted pseudo VLM commands in the required contract: `Go to candidate <id>.`
- Parsed and validated commands, looked up target poses, and moved A1 with a kinematic wrapper.
- Updated the map after movement and wrote `runs/A1_VLM_LA_CLOSED_LOOP_SMOKE_REPORT.md`.

## Metrics

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

## Negative Scope

- No Phase 8 execution.
- No long rollout.
- No real VLM inference or fine-tuning.
- No training, RL, map_predict, checkpoint, or A1 locomotion training.
- No geometry proxy, mounted geometry proxy, old proxy candidate data, or Go2 relabeling.
