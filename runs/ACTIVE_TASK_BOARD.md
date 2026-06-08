# Active Task Board

current_phase: New Scene Phase B real sensor suite smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
current_scene_phase: New Scene Phase B real sensor suite smoke
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_sensor_suite
output_contract: Go to candidate <id>.
training_ready: false
requires_human_review: true
next_phase: New Scene Phase C real-sensor mapping smoke

negative_scope:
- training: false
- RL: false
- SFT: false
- GDPO: false
- map_predict: false
- rollout: false
- PI_action_finetuning: false
- A1_locomotion_training: false

## New Scene Phase B Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseB_real_sensor_smoke_20260608_180523
script: /home/ubuntu22/VLA/scripts/new_scene_phaseB_real_sensor_smoke.py
report: /home/ubuntu22/VLA/runs/NEW_SCENE_REAL_SENSOR_SMOKE_REPORT.md
summary_json: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseB_real_sensor_smoke_20260608_180523/summary/new_scene_real_sensor_summary.json
steps_csv: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseB_real_sensor_smoke_20260608_180523/summary/new_scene_real_sensor_steps.csv

step_count: 6
successful_steps: 6
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
camera_pointcloud_source: depth_backprojection
rtx_lidar_attempted: true
rtx_lidar_available: true
camera_follows_base_rate: 1.0
geometry_proxy_used: false
mounted_geometry_proxy_used: false
core_dump_found: false
safe_to_mapping: true

## Scope

No mapping, candidate generation, VLM-LA interface, rollout, training, RL, SFT, GDPO, map_predict, PI/openpi fine-tuning, A1 locomotion training, checkpoint creation, or USD save was run.
