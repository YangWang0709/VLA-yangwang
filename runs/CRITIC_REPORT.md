# Critic Report

## Current Phase

Phase 7 A1 VLM-LA closed-loop smoke

## Corrected Fact

The USD scene's real robot is `/World/A1`, not Go2. Formal data uses:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

## Phase 7 Review

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429
script: /home/ubuntu22/VLA/scripts/phase7_a1_vlm_la_closed_loop_smoke.py
report: /home/ubuntu22/VLA/runs/A1_VLM_LA_CLOSED_LOOP_SMOKE_REPORT.md
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
geometry_proxy_used: false
mounted_geometry_proxy_used: false
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
real_vlm_inference: false
vlm_output_mode: pseudo_from_classical_selector
candidate_data_source: online_real_sensor_candidate_generation
output_contract: Go to candidate <id>.
action_count: 5
successful_action_count: 5
parse_success_rate: 1.0
validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
movement_success_rate: 1.0
fallback_count: 0
initial_known_ratio: 0.0
final_known_ratio: 0.322222
total_known_ratio_gain: 0.322222
known_ratio_monotonic_non_decreasing: true
average_candidate_count: 24.0
average_valid_candidate_count: 21.4
collision_count: 0
stuck_count: 0
falling_count: 0
failure_count: 0
safe_to_continue_phase8: true

## Findings

- No blocking issues found for the requested short closed-loop smoke scope.
- The loop used real RGB-D depth backprojection for mapping and online candidate generation.
- Pseudo VLM commands stayed within `Go to candidate <id>.`
- Parser, validator, target pose lookup, movement wrapper, and post-move map update all passed.
- No system collision, stuck, falling, checkpoint, training, long rollout, or real VLM inference was recorded.

## Residual Risks And Caveats

- Movement is kinematic root movement, not a trained or deployed A1 locomotion controller.
- This is a short smoke, not Phase 8 long rollout data collection.
- Runtime sensors and light are in-memory; the primary USD scene was not saved.

## Prohibited Work Check

- VLM training performed: false
- real VLM inference performed: false
- Phase 8 performed: false
- long rollout performed: false
- RL training performed: false
- map_predict training performed: false
- PI/openpi fine-tuning performed: false
- A1 locomotion training performed: false
- original USD saved or overwritten: false
- geometry proxy used: false
- mounted geometry proxy used: false
- A1 called Go2: false
- large files committed: false

## Decision

safe_to_continue_phase8: true
next_phase: Phase 8 A1 primary-scene VLM-LA long rollout data collection
