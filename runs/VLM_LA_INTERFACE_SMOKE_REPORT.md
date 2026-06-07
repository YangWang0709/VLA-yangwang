# VLM-LA Interface Smoke Report

phase: Phase 6
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
sensor_method: real_isaac_omniverse_rgbd
candidate_data_source: phase5r_real_sensor
output_contract: Go to candidate <id>.
phase5r_candidate_data_used: true
legal_command_count: 24
legal_parse_success_rate: 1.0
legal_validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
illegal_test_count: 47
illegal_reject_or_fallback_rate: 1.0
fallback_behavior: pass
free_coordinate_output_allowed: false
velocity_output_allowed: false
joint_action_output_allowed: false
safe_to_continue_phase7: true
caveats: ['This is pseudo VLM output interface validation, not real VLM inference.', 'Candidate data is read from Phase 5R real-sensor artifacts; no new candidates are generated.', 'Fallback uses the Phase 5R classical selected candidate for the same step.']
training: false
RL: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout_started: false

## Evidence

- phase5r_run_dir: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631
- run_dir: /home/ubuntu22/VLA/runs/phase6_vlm_la_interface_smoke_20260607_205612
- vlm_la_interface_smoke_jsonl: /home/ubuntu22/VLA/runs/phase6_vlm_la_interface_smoke_20260607_205612/summary/vlm_la_interface_smoke.jsonl
- parse_summary_json: /home/ubuntu22/VLA/runs/phase6_vlm_la_interface_smoke_20260607_205612/summary/parse_summary.json
- test_cases_csv: /home/ubuntu22/VLA/runs/phase6_vlm_la_interface_smoke_20260607_205612/test_cases/interface_test_cases.csv

## Negative Scope

- No real VLM inference or fine-tuning.
- No Phase 7.
- No A1 movement, rollout, mapping, or candidate generation.
- No training, RL, map_predict, checkpoint, or USD modification.
- No old proxy candidate data.
