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

## Phase 8 Rollout Dataset Metadata

```yaml
dataset_name: a1_vlm_la_real_sensor_rollout_v0
sample_format: vlm_la_jsonl
sample_file: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/samples/vlm_la_samples.jsonl
dataset_manifest: /home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/samples/dataset_manifest.json
training_ready: false
requires_human_review: true
label_source: classical_argmax_information_gain_minus_path_cost
target_language_contract: Go to candidate <id>.
sensor_route: real_isaac_omniverse_sensor_suite
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
geometry_proxy_used: false
mounted_geometry_proxy_used: false
real_vlm_inference: false
```

## Phase 8 Provenance

```yaml
start_count: 10
completed_start_count: 10
total_action_count: 77
candidate_rows: 1848
vlm_la_sample_count: 77
average_final_known_ratio: 0.305375
average_known_ratio_gain: 0.305375
parse_success_rate: 1.0
validation_success_rate: 1.0
movement_success_rate: 1.0
rgb_valid_rate: 0.987
depth_valid_rate: 1.0
camera_pointcloud_valid_rate: 1.0
safe_to_continue_phase9: true
```

## Status

Phase 8 passed. The data is review-only and must not be used for training until Phase 9 human review.

## Label Contract

`target_language` must contain a parseable candidate ID:

```text
Go to candidate <id>.
```

## Large Artifact Safety

Raw sensor data, large RGB-D/depth/BEV images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
