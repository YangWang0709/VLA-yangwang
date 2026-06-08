# Active Task Board

current_phase: New Scene Phase E VLM-LA interface smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration

current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
current_scene_phase: New Scene Phase E VLM-LA interface smoke
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
map_update_source: depth_backprojection_pointcloud
candidate_data_source: new_scene_phaseD_real_sensor
output_contract: Go to candidate <id>.
training_ready: false
requires_human_review: true
next_phase: New Scene Phase F short closed-loop smoke


negative_scope:
- training: false
- RL: false
- SFT: false
- GDPO: false
- map_predict: false
- rollout: false
- real_VLM_inference: false
- closed_loop: false
- A1_movement: false
- mapping: false
- candidate_generation: false
- PI_action_finetuning: false
- A1_locomotion_training: false


## New Scene Phase E Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseE_vlm_la_interface_20260608_183222
script: /home/ubuntu22/VLA/scripts/new_scene_phaseE_vlm_la_interface_smoke.py
report: /home/ubuntu22/VLA/runs/NEW_SCENE_VLM_LA_INTERFACE_REPORT.md
summary_json: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseE_vlm_la_interface_20260608_183222/summary/parse_summary.json
interface_jsonl: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseE_vlm_la_interface_20260608_183222/summary/vlm_la_interface_smoke.jsonl
test_cases_csv: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseE_vlm_la_interface_20260608_183222/test_cases/interface_test_cases.csv
phaseD_run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseD_candidate_gain_20260608_182127


phaseD_candidate_data_used: true
legal_command_count: 24
legal_parse_success_rate: 1.0
legal_validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
illegal_test_count: 59
illegal_reject_or_fallback_rate: 1.0
fallback_behavior: pass
invalid_candidate_fallback_passed: true
unreachable_candidate_fallback_passed: true
free_coordinate_output_allowed: false
velocity_output_allowed: false
joint_action_output_allowed: false
malformed_output_rejected: true
final_interface_output_contract_ok: true
safe_to_closed_loop: true


## Scope

Phase E only validated candidate-language parsing, candidate ID validation,
target pose lookup, and fallback behavior. It did not start Isaac, move A1,
run closed-loop, rollout, mapping, candidate generation, real VLM inference,
training, RL, SFT, GDPO, map_predict, checkpoint creation, geometry proxy, or USD save.
