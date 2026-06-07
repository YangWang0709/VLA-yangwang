# Go2 Sensor Smoke Report

phase: Phase 3
workspace: /home/ubuntu22/VLA
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform_target: Unitree Go2
go2_in_usd_found: false
robot_source: temporary_go2_proxy
temporary_go2_proxy_used: true
not_final_robot_asset: true
movement_mode: kinematic_proxy
real_go2_locomotion_controller: false
go2_root_prim: /World/TemporaryGo2Proxy
base_frame: temporary_go2_base_link
sensor_method: geometry/depth/pointcloud proxy
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
Go2_locomotion_training: false
rollout_started: false

## Artifacts

- steps_csv: `/home/ubuntu22/VLA/runs/phase3_go2_sensor_smoke_20260607_190528/sensor_smoke/go2_sensor_smoke_steps.csv`
- summary_json: `/home/ubuntu22/VLA/runs/phase3_go2_sensor_smoke_20260607_190528/sensor_smoke/go2_sensor_smoke_summary.json`

## Caveats

- Phase 2 did not verify an existing Go2 prim; this run uses a temporary Go2-shaped proxy and must not be treated as a final robot asset.
- Sensor data is a lightweight geometry/depth/pointcloud proxy, not an RTX camera or raw sensor dump.
- Movement is kinematic proxy pose update, not real Go2 locomotion control.

## Negative Scope

- No VLM training.
- No RL training.
- No map_predict training or mainline implementation.
- No PI/openpi action-head fine-tuning.
- No Go2 locomotion policy training.
- No long rollout, mapping, candidate generation, or VLM inference.
- Original USD scene was opened and edited only in memory; it was not saved or overwritten.
