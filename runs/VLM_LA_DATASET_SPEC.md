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

## Real Sensor Mapping Metadata

```yaml
sensor_route: real_isaac_omniverse_sensor_suite
sensor_method: real_isaac_omniverse_rgbd
map_update_source: depth_backprojection_pointcloud
camera_pointcloud_source: depth_backprojection
run_dir: /home/ubuntu22/VLA/runs/phase4r_a1_real_sensor_mapping_smoke_20260607_203607
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
semantic_segmentation_available: true
instance_segmentation_available: true
rtx_lidar_available: true
lidar_used_for_mapping: false
geometry_proxy_used: false
mounted_geometry_proxy_used: false
```

## Status

Phase 4R-real A1 real-sensor mapping smoke passed. No training is allowed at this stage.

## Phase 4R-real Provenance

```yaml
step_count: 10
successful_steps: 10
valid_rgb_steps: 10
valid_depth_steps: 10
valid_camera_pointcloud_steps: 10
initial_known_ratio: 0.055802
final_known_ratio: 0.069383
final_occupied_cells: 136
final_known_free_cells: 426
final_unknown_cells: 7538
safe_to_rerun_phase5_with_real_sensors: true
safe_to_continue_phase6: false
```

## Sample Purpose

Each sample teaches a model to choose a candidate viewpoint through constrained language, not free-form coordinates or low-level robot commands.

## Label Contract

`target_language` must contain a parseable candidate ID:

```text
Go to candidate <id>.
```

## Current Gate

Rerun Phase 5 with real Isaac/Omniverse sensor mapping before Phase 6 VLM-LA interface smoke. Do not prepare training, rollout, or final evaluation yet.

## Large Artifact Safety

Raw sensor data, large RGB-D/depth/BEV images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
