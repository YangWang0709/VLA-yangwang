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

## Mounted Sensor Metadata

```yaml
sensor_mount_parent: /World/A1/base
sensor_frame: a1_front_sensor
sensor_frame_path: /World/A1/base/Sensors/a1_front_sensor
sensor_mount_xyz: [0.3, 0.0, 0.28]
sensor_mount_rpy: [0.0, -0.261799, 0.0]
real_rgb_sensor_available: false
real_depth_sensor_available: false
real_pointcloud_available: false
mounted_geometry_proxy_used: true
```

## Status

Phase 5.5 A1 mounted sensor smoke passed. No training is allowed at this stage.

## Phase 5.5 Provenance

```yaml
run_dir: /home/ubuntu22/VLA/runs/phase55_a1_mounted_sensor_smoke_20260607_200210
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
depth_valid_steps: 6
pointcloud_valid_steps: 6
sensor_follows_base_rate: 1.0
safe_to_rerun_phase4_with_mounted_sensor: true
safe_to_rerun_phase5_with_mounted_sensor: true
```

## Sample Purpose

Each sample teaches a model to choose a candidate viewpoint through constrained language, not free-form coordinates or low-level robot commands.

## Label Contract

`target_language` must contain a parseable candidate ID:

```text
Go to candidate <id>.
```

## Current Gate

Rerun Phase 4 and Phase 5 with mounted sensor observations before Phase 6 VLM-LA interface smoke. Do not prepare training, rollout, or final evaluation yet.

## Large Artifact Safety

Raw sensor data, large BEV/RGB/depth images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
