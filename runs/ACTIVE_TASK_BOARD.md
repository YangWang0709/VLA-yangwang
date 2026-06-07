# Active Task Board

current_phase: Phase 4 A1 primary-scene mapping smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
phase6_status: paused
next_phase: Phase 5 A1 candidate viewpoint + information gain smoke

## Phase 4 A1 Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase4_a1_mapping_smoke_20260607_194403
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
sensor_method: geometry_proxy_pointcloud_from_a1_base_pose
existing_sensor_reused: false
geometry_proxy_sensor_used: true
map_type: BEV occupancy grid
mapping_method: raycast_bev_proxy_mapping
map_resolution_m: 0.1
step_count: 10
successful_steps: 10
valid_observation_steps: 10
initial_known_ratio: 0.052969
final_known_ratio: 0.087188
final_occupied_cells: 308
final_known_free_cells: 250
final_unknown_cells: 5842
total_new_known_cells: 558
known_ratio_monotonic_non_decreasing: true
map_update_behavior: pass
collision_count: 0
stuck_count: 0
falling_count: 0
core_dump_found: false
safe_to_continue_phase5: true

## Platform Correction Summary

- USD real robot is `/World/A1`.
- The project must not claim that the USD contains a verified Go2 robot.
- Previous temporary Go2 proxy results remain proxy-only smoke and are superseded for formal A1 pipeline data.
- Phase 3 and Phase 4 now have formal A1 smoke results based on existing USD A1 prim.

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- primary_rollout: false
- candidate_generation: false
- Phase_5_executed: false
- Phase_6: false

## Next Phase

Phase 5 A1 candidate viewpoint + information gain smoke. Do not enter Phase 5 until explicitly requested.
