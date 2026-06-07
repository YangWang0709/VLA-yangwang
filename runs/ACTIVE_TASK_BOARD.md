# Active Task Board

current_phase: Phase 3 Unitree A1 sensor smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
phase6_status: paused
next_phase: Phase 4 A1 primary-scene mapping smoke

## Phase 3 A1 Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase3_a1_sensor_smoke_20260607_193054
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
base_frame: /World/A1/base
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
existing_sensor_reused: false
geometry_proxy_sensor_used: true
sensor_method: geometry_proxy_pointcloud_from_a1_base_pose
step_count: 8
successful_steps: 8
sensor_valid_steps: 8
sensor_valid_rate: 1.0
min_pointcloud_count: 161
max_pointcloud_count: 161
collision_count: 0
stuck_count: 0
falling_count: 0
core_dump_found: false
safe_to_continue_phase4: true

## Platform Correction Summary

- USD real robot is `/World/A1`.
- The project must not claim that the USD contains a verified Go2 robot.
- Previous Phase 3 and Phase 4 results used `temporary_go2_proxy`, so they remain valid only as proxy pipeline smoke.
- The new formal Phase 3 smoke uses the existing USD A1 prim.
- Current repository still has no formal Phase 5 candidate gain artifact.

## Formal A1 Fields

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
```

## Legacy Proxy Fields

```yaml
robot_platform: temporary_quadruped_proxy
robot_source: temporary_go2_proxy
not_final_robot_asset: true
```

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- primary_rollout: false
- candidate_generation: false
- Phase_6: false

## Next Phase

Proceed to Phase 4 A1 primary-scene mapping smoke only when requested. Do not enter Phase 6 yet.
