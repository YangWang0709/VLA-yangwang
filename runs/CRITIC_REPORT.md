# Critic Report

## Current Phase

Phase 4 A1 primary-scene mapping smoke

## Corrected Fact

The USD scene's real robot is `/World/A1`, not Go2.

## Phase 4 A1 Mapping Review

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase4_a1_mapping_smoke_20260607_194403
script: /home/ubuntu22/VLA/scripts/phase4_a1_mapping_smoke.py
report: /home/ubuntu22/VLA/runs/A1_MAPPING_SMOKE_REPORT.md

## Evidence

- primary scene opened successfully.
- `/World/A1` exists.
- base_frame: `/World/A1/base`.
- movement_mode: `kinematic_existing_a1_root`.
- sensor_method: `geometry_proxy_pointcloud_from_a1_base_pose`.
- mapping_method: `raycast_bev_proxy_mapping`.
- step_count: 10.
- successful_steps: 10.
- valid_observation_steps: 10.
- initial_known_ratio: 0.052969.
- final_known_ratio: 0.087188.
- final_occupied_cells: 308.
- final_known_free_cells: 250.
- final_unknown_cells: 5842.
- total_new_known_cells: 558.
- known_ratio_monotonic_non_decreasing: true.
- map_update_behavior: pass.
- collision_count: 0.
- stuck_count: 0.
- falling_count: 0.
- core_dump_found: false.
- safe_to_continue_phase5: true.

## Residual Risks And Caveats

- Existing USD cameras are only Omniverse default cameras, not A1-mounted sensors.
- This is BEV mapping smoke from geometry proxy observations, not real RGB-D SLAM.
- The A1 movement is an in-memory kinematic root update, not a trained or existing A1 locomotion controller.
- This phase does not validate candidate generation, information gain ranking, VLM parsing, or Phase 6 behavior.

## Prohibited Work Check

- VLM training performed: false
- VLM inference performed: false
- RL training performed: false
- map_predict training performed: false
- PI/openpi fine-tuning performed: false
- A1 locomotion training performed: false
- Phase 5 candidate generation performed: false
- Phase 6 performed: false
- rollout performed: false
- original USD saved or overwritten: false
- temporary Go2 proxy created: false
- large files committed: false

## Decision

Phase 4 A1 mapping smoke is sufficient to proceed to Phase 5 A1 candidate viewpoint + information gain smoke when requested. Do not enter Phase 5 or Phase 6 in this step.
