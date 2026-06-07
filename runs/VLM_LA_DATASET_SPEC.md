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
map_update_source: depth_backprojection_pointcloud
camera_pointcloud_source: depth_backprojection
candidate_summary_csv: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631/summary/candidate_summary.csv
candidate_steps_jsonl: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631/summary/candidate_steps.jsonl
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
semantic_segmentation_available: true
instance_segmentation_available: true
rtx_lidar_available: true
lidar_used_for_candidate_gain: false
geometry_proxy_used: false
mounted_geometry_proxy_used: false
```

## Status

Phase 5R-real A1 real-sensor candidate gain smoke passed. No training is allowed at this stage.

## Phase 5R-real Provenance

```yaml
step_count: 6
successful_steps: 6
candidate_count_per_step: 24
total_candidate_rows: 144
valid_candidate_ratio: 0.8958
positive_gain_candidate_ratio: 0.8819
selected_candidate_valid_rate: 1.0
selected_is_top_score_rate: 1.0
path_cost_constant: false
min_path_cost: 1.0243
max_path_cost: 6.4742
min_information_gain: 0
max_information_gain: 749
failure_count: 0
safe_to_continue_phase6: true
```

## Sample Purpose

Each sample teaches a model or interface smoke test to choose a candidate viewpoint through constrained language, not free-form coordinates or low-level robot commands.

## Label Contract

`target_language` must contain a parseable candidate ID:

```text
Go to candidate <id>.
```

## Large Artifact Safety

Raw sensor data, large RGB-D/depth/BEV images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
