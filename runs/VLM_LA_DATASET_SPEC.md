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

## Real Sensor Metadata

```yaml
sensor_route: real_isaac_omniverse_sensor_suite
run_dir: /home/ubuntu22/VLA/runs/phase56_a1_real_sensor_suite_smoke_20260607_202405
camera_prim_path: /World/RuntimeSensors/a1_front_rgbd_camera
sensor_mount_parent: /World/A1/base (runtime camera synced under /World/RuntimeSensors)
sensor_mount_xyz: [0.3, 0.0, 0.28]
sensor_mount_rpy: [0.0, -0.261799, 0.0]
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
camera_pointcloud_source: depth_backprojection
rtx_lidar_attempted: true
rtx_lidar_available: true
semantic_segmentation_available: true
instance_segmentation_available: true
geometry_proxy_used: false
mounted_geometry_proxy_used: false
```

## Status

Phase 5.6 A1 real sensor suite smoke passed. No training is allowed at this stage.

## Phase 5.6 Provenance

```yaml
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
step_count: 6
successful_steps: 6
rgb_valid_steps: 6
depth_valid_steps: 6
camera_pointcloud_valid_steps: 6
camera_follows_base_rate: 1.0
safe_to_rerun_phase4_with_real_sensors: true
safe_to_rerun_phase5_with_real_sensors: true
```

## Sample Purpose

Each sample teaches a model to choose a candidate viewpoint through constrained language, not free-form coordinates or low-level robot commands.

## Label Contract

`target_language` must contain a parseable candidate ID:

```text
Go to candidate <id>.
```

## Current Gate

Rerun Phase 4 and Phase 5 with real Isaac/Omniverse sensor observations before Phase 6 VLM-LA interface smoke. Do not prepare training, rollout, or final evaluation yet.

## Large Artifact Safety

Raw sensor data, large RGB-D/depth/BEV images, `.npz`, `.hdf5`, checkpoints, meshes, textures, and USD scene bundles must not be committed to Git.
