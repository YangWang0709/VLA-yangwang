# Critic Report

## Current Phase

Phase 8 A1 primary-scene VLM-LA long rollout data collection

## Corrected Fact

The USD scene's real robot is `/World/A1`, not Go2. Formal data uses:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

## Phase 8 Review

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536
script: /home/ubuntu22/VLA/scripts/phase8_a1_vlm_la_long_rollout.py
report: /home/ubuntu22/VLA/runs/A1_VLM_LA_LONG_ROLLOUT_REPORT.md
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
real_rgb_sensor_available: true
real_depth_sensor_available: true
real_camera_pointcloud_available: true
real_rgb_sensor_valid_rate: 0.987
real_depth_sensor_valid_rate: 1.0
real_camera_pointcloud_valid_rate: 1.0
geometry_proxy_used: false
mounted_geometry_proxy_used: false
movement_mode: kinematic_existing_a1_root
real_a1_locomotion_controller: false
real_vlm_inference: false
vlm_output_mode: pseudo_from_classical_selector
output_contract: Go to candidate <id>.
start_count: 10
completed_start_count: 10
max_actions_per_start: 8
total_action_count: 77
candidate_rows: 1848
vlm_la_sample_count: 77
average_final_known_ratio: 0.305375
average_known_ratio_gain: 0.305375
parse_success_rate: 1.0
validation_success_rate: 1.0
movement_success_rate: 1.0
starts_with_failures: 1
rgb_invalid_step_count: 1
collision_count: 0
stuck_count: 0
falling_count: 0
safe_to_continue_phase9: true

## Findings

- No blocking issue found for Phase 8 pass criteria.
- Ten starts were attempted and completed with at least two action steps each.
- Candidate-ID output contract stayed constrained to `Go to candidate <id>.`
- Parser, validator, target pose lookup, and movement success rates were 1.0.
- Depth and depth-backprojected pointcloud validity rates were 1.0.
- One post-move RGB validity check failed at start 004 step 004 and is recorded as `post_rgb_invalid`; raw CSV/JSONL rows were not edited.
- No collision, stuck, falling, training, RL, checkpoint, real VLM inference, geometry proxy, or mounted geometry proxy was recorded.

## Residual Risks And Caveats

- Movement is kinematic root movement, not a trained or deployed A1 locomotion controller.
- VLM labels are pseudo labels from a classical selector, not real VLM inference.
- Samples are prototype data and require Phase 9 human review before any training use.
- RGB validity was 0.987 across rollout step rows because of the one recorded post-move RGB failure.

## Evidence

- rollout_steps_csv: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/summary/rollout_steps.csv
- candidate_summary_csv: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/summary/candidate_summary.csv
- vlm_la_samples_jsonl: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/samples/vlm_la_samples.jsonl
- dataset_manifest_json: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/samples/dataset_manifest.json
- rollout_summary_json: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/summary/rollout_summary.json
- plots_path: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/plots

## Prohibited Work Check

- VLM training performed: false
- real VLM inference performed: false
- RL training performed: false
- map_predict training performed: false
- PI/openpi fine-tuning performed: false
- A1 locomotion training performed: false
- checkpoint created: false
- geometry proxy used: false
- USD scene modified: false
