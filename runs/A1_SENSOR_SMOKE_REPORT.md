# A1 Sensor Smoke Report

phase: Phase 3
workspace: /home/ubuntu22/VLA
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
project_name: A1-VLM-LA Explorer
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
a1_root_exists: true
a1_has_articulation_root_api: true
base_frame: /World/A1/base
previous_proxy_results_status: superseded_for_formal_a1_pipeline
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
existing_sensor_reused: false
geometry_proxy_sensor_used: true
sensor_method: geometry_proxy_pointcloud_from_a1_base_pose
sensor_frame: /World/A1/base/front_geometry_proxy
sensor_pose_relative_to_a1_base: {'x': 0.36, 'y': 0.0, 'z': 0.18, 'yaw_rad': 0.0}
step_count: 8
successful_steps: 8
sensor_valid_steps: 8
sensor_valid_rate: 1.0
min_pointcloud_count: 161
max_pointcloud_count: 161
average_pointcloud_count: 161
collision_count: 0
stuck_count: 0
falling_count: 0
core_dump_found: false
safe_to_continue_phase4: true
training: false
RL: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout_started: false

## Artifacts

- run_dir: `/home/ubuntu22/VLA/runs/phase3_a1_sensor_smoke_20260607_193054`
- steps_csv: `/home/ubuntu22/VLA/runs/phase3_a1_sensor_smoke_20260607_193054/sensor_smoke/a1_sensor_smoke_steps.csv`
- summary_json: `/home/ubuntu22/VLA/runs/phase3_a1_sensor_smoke_20260607_193054/summary/a1_sensor_smoke_summary.json`
- run_report: `/home/ubuntu22/VLA/runs/phase3_a1_sensor_smoke_20260607_193054/reports/A1_SENSOR_SMOKE_REPORT.md`
- top_report: `/home/ubuntu22/VLA/runs/A1_SENSOR_SMOKE_REPORT.md`

## Existing USD Sensors

- available_camera_count: 4
- a1_bound_sensor_prims: []

## Caveats

- This is formal A1 pipeline smoke based on the existing USD prim /World/A1, not the old temporary Go2 proxy.
- Sensor data is a lightweight geometry/depth/pointcloud proxy bound to A1 base/front pose, not RTX rendering or a raw sensor dump.
- Movement is a short in-memory kinematic root pose update, not real A1 locomotion control or a rollout.
- No A1-bound USD camera/sensor prim was found; only geometry proxy observations were used.

## Core Dump Files

- none

## Negative Scope

- No VLM training.
- No RL training.
- No map_predict training or mainline implementation.
- No PI/openpi action-head fine-tuning.
- No A1 locomotion policy training.
- No Phase 4 mapping, candidate generation, Phase 6 interface smoke, or long rollout.
- No temporary Go2 proxy was created.
- Original USD scene was opened and edited only in memory; it was not saved or overwritten.
