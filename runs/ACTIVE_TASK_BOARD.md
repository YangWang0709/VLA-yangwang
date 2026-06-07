# Active Task Board

current_phase: Phase 5.5 A1 mounted sensor smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
next_phase: Rerun Phase 4 A1 mapping smoke with mounted sensor

## Reason

Phase 3 through Phase 5 passed with `geometry_proxy_pointcloud_from_a1_base_pose`, but final VLM-LA data should use an A1-mounted sensor or at least an A1-mounted proxy sensor. Phase 5.5 validates a runtime sensor frame mounted under `/World/A1/base` before rerunning mapping and candidate gain.

## Phase 5.5 Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase55_a1_mounted_sensor_smoke_20260607_200210
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
sensor_mount_parent: /World/A1/base
sensor_frame: a1_front_sensor
sensor_frame_path: /World/A1/base/Sensors/a1_front_sensor
sensor_mount_xyz: [0.3, 0.0, 0.28]
sensor_mount_rpy: [0.0, -0.261799, 0.0]
real_rgb_sensor_available: false
real_depth_sensor_available: false
real_pointcloud_available: false
mounted_geometry_proxy_used: true
step_count: 6
successful_steps: 6
rgb_valid_steps: 0
depth_valid_steps: 6
pointcloud_valid_steps: 6
sensor_follows_base_rate: 1.0
average_depth_valid_ratio: 1.0
average_pointcloud_count: 432.0
collision_count: 0
stuck_count: 0
falling_count: 0
core_dump_found: false
safe_to_rerun_phase4_with_mounted_sensor: true
safe_to_rerun_phase5_with_mounted_sensor: true

## Caveats

- Real Isaac RGB-D capture was not used; runtime camera prims are mounted frame markers.
- Depth and pointcloud are A1-mounted geometry proxy observations from the mounted sensor frame.
- This is not final real-sensor RGB-D data.
- Do not enter Phase 6 until Phase 4 and Phase 5 are rerun with the mounted sensor route.

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- candidate_generation: false
- primary_rollout: false
- Phase_6_executed: false

## Next Phase

Rerun Phase 4 A1 mapping smoke with mounted sensor.
