# VLM-LA Dataset Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Formal A1 Metadata

Formal A1 data must use:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

## Phase 7 Closed-Loop Metadata

```yaml
sensor_route: real_isaac_omniverse_sensor_suite
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
candidate_data_source: online_real_sensor_candidate_generation
vlm_output_mode: pseudo_from_classical_selector
movement_mode: kinematic_existing_a1_root
closed_loop_steps_csv: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/summary/closed_loop_steps.csv
command_log_jsonl: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/commands/command_log.jsonl
parse_log_jsonl: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/parsing/parse_log.jsonl
summary_json: /home/ubuntu22/VLA/runs/phase7_a1_vlm_la_closed_loop_smoke_20260607_210429/summary/closed_loop_summary.json
geometry_proxy_used: false
mounted_geometry_proxy_used: false
real_vlm_inference: false
long_rollout_started: false
```

## Phase 7 Provenance

```yaml
action_count: 5
successful_action_count: 5
parse_success_rate: 1.0
validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
movement_success_rate: 1.0
initial_known_ratio: 0.0
final_known_ratio: 0.322222
total_known_ratio_gain: 0.322222
collision_count: 0
stuck_count: 0
falling_count: 0
failure_count: 0
safe_to_continue_phase8: true
```

## Status

Phase 7 A1 VLM-LA closed-loop smoke passed. No training is allowed at this stage.

## Label Contract

`target_language` must contain a parseable candidate ID:

```text
Go to candidate <id>.
```

## Large Artifact Safety

Raw sensor data, large RGB-D/depth/BEV images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
