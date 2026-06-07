# WEBGPT Brief

## Current Phase

Phase 6 VLM-LA interface smoke

## Context

current_phase: Phase 6 VLM-LA interface smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
candidate_data_source: phase5r_real_sensor
primary_input_channels:
- RGB
- depth
- depth_backprojected_pointcloud
- camera intrinsics/extrinsics
- BEV explored_map
- candidate viewpoints
negative_scope:
- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- primary_rollout: false
next_phase: Phase 7 A1 VLM-LA closed-loop smoke

## Completed

- Created `scripts/phase6_vlm_la_interface_smoke.py`.
- Read Phase 5R real-sensor candidate artifacts.
- Generated pseudo VLM commands in the required contract: `Go to candidate <id>.`
- Parsed legal text, lowercase, explanation-bearing text, and JSON command forms.
- Rejected coordinate, velocity, joint action, malformed JSON, missing ID, out-of-range ID, invalid candidate ID, and unreachable candidate ID cases.
- Validated candidate existence, valid/reachable flags, collision risk, and target pose lookup.
- Verified fallback to the Phase 5R classical selected candidate for invalid outputs.
- Wrote `runs/VLM_LA_INTERFACE_SMOKE_REPORT.md`.

## Metrics

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase6_vlm_la_interface_smoke_20260607_205612
script: /home/ubuntu22/VLA/scripts/phase6_vlm_la_interface_smoke.py
report: /home/ubuntu22/VLA/runs/VLM_LA_INTERFACE_SMOKE_REPORT.md
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
candidate_data_source: phase5r_real_sensor
output_contract: Go to candidate <id>.
phase5r_candidate_data_used: true
phase5r_run_dir: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631
legal_command_count: 24
legal_parse_success_rate: 1.0
legal_validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
illegal_test_count: 47
illegal_reject_or_fallback_rate: 1.0
fallback_test_passed: true
invalid_candidate_fallback_tested: true
unreachable_candidate_fallback_tested: true
free_coordinate_output_allowed: false
velocity_output_allowed: false
joint_action_output_allowed: false
malformed_output_rejected: true
A1_moved: false
mapping_started: false
candidate_generation_started: false
real_vlm_inference_started: false
safe_to_continue_phase7: true

## Negative Scope

- No real VLM inference or fine-tuning.
- No Phase 7 execution.
- No A1 movement, mapping, candidate generation, rollout, training, RL, map_predict, checkpoint, or USD modification.
- No old proxy candidate data.
