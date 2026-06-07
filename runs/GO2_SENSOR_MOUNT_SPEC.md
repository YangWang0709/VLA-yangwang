# Go2 Sensor Mount Spec

current_phase: Phase 3 Unitree Go2 sensor smoke
workspace: /home/ubuntu22/VLA
main_goal: Go2-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.

## Robot Source

robot_platform_target: Unitree Go2
go2_in_usd_found: false
robot_source: temporary_go2_proxy
temporary_go2_proxy_used: true
not_final_robot_asset: true
go2_root_prim: /World/TemporaryGo2Proxy
base_frame: temporary_go2_base_link
sensor_frame: go2_front_camera
map_frame: map
odom_frame: odom

## Sensor Method

sensor_method: geometry/depth/pointcloud proxy
real_rendered_sensor_used: false
geometry_proxy_observation_used: true
raw_sensor_dump_saved: false
large_image_saved: false

The temporary sensor frame is attached logically in front of the temporary proxy body. Phase 3 generated lightweight finite pointcloud/depth proxy statistics only; it did not render RGB/depth images or save raw sensor arrays.

## Camera Pose Relative To Base

- x: 0.36 m forward
- y: 0.00 m lateral
- z: 0.18 m above temporary base center
- yaw/pitch/roll: aligned forward with the temporary base frame

## Locomotion Mode

movement_mode: kinematic_proxy
real_go2_locomotion_controller: false
Go2_locomotion_training: false
joint_actions_used: false
base_velocity_commands_from_VLM: false

## Phase 3 Smoke Metrics

- step_count: 8
- successful_steps: 8
- sensor_valid_rate: 1.0
- min_pointcloud_count: 161
- max_pointcloud_count: 161
- collision_count: 0
- stuck_count: 0
- falling_count: 0
- safe_to_continue_phase4: true

## Caveats

- Phase 2 did not verify an existing Go2 prim inside the USD.
- `/World/A1` is not treated as Go2.
- The temporary proxy is a smoke-test sensor carrier and not a final robot asset.
- The sensor method is a proxy observation, not real RTX sensor rendering.

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- Go2_locomotion_training: false
- primary_rollout: false
