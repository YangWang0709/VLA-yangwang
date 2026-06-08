# New Scene VLM-LA Interface Report

phase: New Scene Phase E
workspace: /home/ubuntu22/VLA
project_name: A1-VLM-LA Explorer
scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
candidate_data_source: new_scene_phaseD_real_sensor
output_contract: Go to candidate <id>.
phaseD_candidate_data_used: true
legal_command_count: 24
legal_parse_success_rate: 1.0
legal_validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
illegal_test_count: 59
illegal_reject_or_fallback_rate: 1.0
fallback_behavior: pass
free_coordinate_output_allowed: false
velocity_output_allowed: false
joint_action_output_allowed: false
malformed_output_rejected: true
final_interface_output_contract_ok: true
safe_to_closed_loop: true
training: false
RL: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout_started: false

## Caveats

- This is pseudo VLM output interface validation, not real VLM inference.
- Candidate data is read from New Scene Phase D real-sensor artifacts; no new candidates are generated.
- Fallback uses the Phase D classical selected candidate for the same step.
- No A1 movement, mapping, rollout, training, or USD save is performed.

## Artifacts

- run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseE_vlm_la_interface_20260608_183222
- phaseD_run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseD_candidate_gain_20260608_182127
- vlm_la_interface_smoke_jsonl: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseE_vlm_la_interface_20260608_183222/summary/vlm_la_interface_smoke.jsonl
- parse_summary_json: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseE_vlm_la_interface_20260608_183222/summary/parse_summary.json
- test_cases_csv: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseE_vlm_la_interface_20260608_183222/test_cases/interface_test_cases.csv

## Negative Scope

- No real VLM inference or fine-tuning.
- No closed-loop, rollout, A1 movement, mapping, or candidate generation.
- No training, RL, SFT, GDPO, map_predict, checkpoint, or USD modification.
- No geometry proxy and no old-scene candidate data.
