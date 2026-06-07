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

## Real Sensor Candidate Metadata

```yaml
sensor_route: real_isaac_omniverse_sensor_suite
sensor_method: real_isaac_omniverse_rgbd
candidate_data_source: phase5r_real_sensor
phase5r_run_dir: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631
geometry_proxy_used: false
mounted_geometry_proxy_used: false
```

## Interface Smoke Metadata

```yaml
vlm_la_interface_smoke_jsonl: /home/ubuntu22/VLA/runs/phase6_vlm_la_interface_smoke_20260607_205612/summary/vlm_la_interface_smoke.jsonl
parse_summary_json: /home/ubuntu22/VLA/runs/phase6_vlm_la_interface_smoke_20260607_205612/summary/parse_summary.json
test_cases_csv: /home/ubuntu22/VLA/runs/phase6_vlm_la_interface_smoke_20260607_205612/test_cases/interface_test_cases.csv
output_contract: Go to candidate <id>.
legal_command_count: 24
legal_parse_success_rate: 1.0
legal_validation_success_rate: 1.0
illegal_test_count: 47
illegal_reject_or_fallback_rate: 1.0
target_pose_lookup_success_rate: 1.0
fallback_test_passed: true
safe_to_continue_phase7: true
```

## Status

Phase 6 VLM-LA interface smoke passed. No training is allowed at this stage.

## Sample Purpose

Each sample tests that an interface can choose a candidate viewpoint through constrained language, not free-form coordinates or low-level robot commands.

## Label Contract

`target_language` must contain a parseable candidate ID:

```text
Go to candidate <id>.
```

## Large Artifact Safety

Raw sensor data, large RGB-D/depth/BEV images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
