# VLM-LA Explorer Plan

## Method Name

A1-VLM-LA Explorer

Full route name:

A1-VLM-LA Explorer for 3D Active Exploration

## Workspace

`/home/ubuntu22/VLA`

## Robot Platform

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

The USD scene's real robot is `/World/A1`. Do not claim the USD contains a verified Go2 robot unless a real Go2 asset is provided or substituted later.

## Current Progress

- Phase 1 placed the primary USD scene bundle and kept it ignored by Git.
- Phase 2 opened the scene and identified the articulated `/World/A1` hierarchy.
- Phase 3 A1 sensor smoke passed using base-pose geometry proxy observations.
- Phase 4 A1 mapping smoke passed using base-pose proxy observations.
- Phase 5 A1 candidate gain smoke passed using base-pose proxy BEV maps.
- Phase 5.5 A1 mounted sensor smoke passed using mounted geometry proxy observations.
- Phase 5.6 A1 real sensor suite smoke passed using real Replicator RGB-D and `depth_backprojection` pointcloud.

## Real Sensor Route

```yaml
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
geometry_proxy_used: false
mounted_geometry_proxy_used: false
safe_to_rerun_phase4_with_real_sensors: true
safe_to_rerun_phase5_with_real_sensors: true
```

## Core Pipeline

```text
USD scene with /World/A1
-> A1-synced real Isaac/Omniverse RGB-D sensor route
-> real depth-derived pointcloud and optional RTX LiDAR/segmentation
-> explored_map / partial map
-> candidate viewpoints
-> BEV render with candidate IDs
-> VLM output: Go to candidate <id>.
-> LA parser: selected_candidate_id = <id>
-> candidate table lookup: candidate id -> target viewpoint pose
-> planner / A1 movement wrapper
```

## Output Contract

```text
Go to candidate <id>.
```

Only the candidate ID may drive control. Explanation text may be logged but must not control motion.

## Current Gate

Phase 5.6 passed. The next formal route is `Rerun Phase 4 A1 mapping smoke with real Isaac/Omniverse sensors`. Do not enter Phase 6 yet.

## Negative Scope

Do not train VLM, RL, map_predict, PI/openpi action heads, or A1 locomotion policies in the current stage. Do not let the VLM output free coordinates, base velocities, or joint actions. Do not commit scene bundles, meshes, textures, raw sensor dumps, checkpoints, core dumps, tokens, keys, or private configs.
