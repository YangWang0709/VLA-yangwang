# WEBGPT Brief

## Current Phase

Phase 4 A1 primary-scene mapping smoke

## Workspace

/home/ubuntu22/VLA

## Main Goal

A1-VLM-LA Explorer for 3D Active Exploration

## Output Contract

Go to candidate <id>.

## Robot Platform

robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base

## Completed

- Created `scripts/phase4_a1_mapping_smoke.py`.
- Opened the primary USD scene without saving or overwriting it.
- Used the existing `/World/A1` prim and `/World/A1/base` frame.
- Ran 10 short in-memory kinematic A1 root mapping steps.
- Built a BEV occupancy grid from geometry proxy pointcloud/depth observations.
- Wrote `runs/A1_MAPPING_SMOKE_REPORT.md`.

## Phase 4 Metrics

run_dir: /home/ubuntu22/VLA/runs/phase4_a1_mapping_smoke_20260607_194403
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
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

## Key Caveats

- No A1-bound USD camera/sensor prim was found; only Omniverse default cameras exist.
- Sensor data is geometry proxy pointcloud/depth, not real RGB-D SLAM.
- Movement is `kinematic_existing_a1_root`, not real A1 locomotion control.
- Phase 5 candidate generation was not run.

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- candidate_generation: false
- primary_rollout: false
- Phase_5_executed: false
- Phase_6: false

## Next Step

Phase 5 A1 candidate viewpoint + information gain smoke, only when explicitly requested.
