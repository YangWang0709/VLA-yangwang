# Active Task Board

current_phase: Phase 8 A1 primary-scene VLM-LA long rollout data collection
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
vlm_output_mode: pseudo_from_classical_selector
next_phase: Phase 9 human review packet
negative_scope:
- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- real_vlm_inference: false
- geometry_proxy: false
- mounted_geometry_proxy: false
- USD_scene_modification: false
- checkpoint_created: false
- long_rollout_data_collection: true

## Phase 8 Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536
script: /home/ubuntu22/VLA/scripts/phase8_a1_vlm_la_long_rollout.py
report: /home/ubuntu22/VLA/runs/A1_VLM_LA_LONG_ROLLOUT_REPORT.md
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
real_rgb_sensor_available: true
real_depth_sensor_available: true
real_camera_pointcloud_available: true
real_rgb_sensor_valid_rate: 0.987
real_depth_sensor_valid_rate: 1.0
real_camera_pointcloud_valid_rate: 1.0
geometry_proxy_used: false
mounted_geometry_proxy_used: false
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
real_vlm_inference: false
vlm_output_mode: pseudo_from_classical_selector
output_contract: Go to candidate <id>.
start_count: 10
completed_start_count: 10
max_actions_per_start: 8
total_action_count: 77
candidate_rows: 1848
vlm_la_sample_count: 77
average_final_known_ratio: 0.305375
average_known_ratio_gain: 0.305375
parse_success_rate: 1.0
validation_success_rate: 1.0
movement_success_rate: 1.0
starts_with_failures: 1
rgb_invalid_step_count: 1
collision_count: 0
stuck_count: 0
falling_count: 0
safe_to_continue_phase9: true

## Evidence Paths

- rollout_steps_csv: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/summary/rollout_steps.csv
- candidate_summary_csv: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/summary/candidate_summary.csv
- vlm_la_samples_jsonl: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/samples/vlm_la_samples.jsonl
- dataset_manifest_json: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/samples/dataset_manifest.json
- rollout_summary_json: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/summary/rollout_summary.json
- plots_path: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/plots

## Decision

Phase 8 passed as A1 real-sensor VLM-LA rollout data collection in the primary scene. It used existing USD A1 at `/World/A1`, Isaac/Omniverse RGB-D sensing, depth-backprojected pointclouds, online BEV mapping, candidate scoring, pseudo VLM commands, parser/validator checks, target pose lookup, and kinematic A1 root movement.

The collected samples are not training-ready. They require Phase 9 human review before any training or fine-tuning use.
