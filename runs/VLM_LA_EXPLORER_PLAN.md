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
- Phase 5.5 A1 mounted sensor smoke passed using `/World/A1/base/Sensors/a1_front_sensor` mounted geometry proxy observations.

## Mounted Sensor Route

```yaml
run_dir: /home/ubuntu22/VLA/runs/phase55_a1_mounted_sensor_smoke_20260607_200210
sensor_mount_parent: /World/A1/base
sensor_frame: a1_front_sensor
sensor_mount_xyz: [0.3, 0.0, 0.28]
sensor_mount_rpy: [0.0, -0.261799, 0.0]
real_rgb_sensor_available: false
real_depth_sensor_available: false
real_pointcloud_available: false
mounted_geometry_proxy_used: true
safe_to_rerun_phase4_with_mounted_sensor: true
safe_to_rerun_phase5_with_mounted_sensor: true
```

## Core Pipeline

```text
USD scene with /World/A1
-> A1-mounted sensor frame
-> depth / pointcloud or RGB-D observation
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

Phase 5.5 passed. The next formal route is rerunning Phase 4 A1 mapping smoke with mounted sensor. Do not enter Phase 6 yet.

## Negative Scope

Do not train VLM, RL, map_predict, PI/openpi action heads, or A1 locomotion policies in the current stage. Do not let the VLM output free coordinates, base velocities, or joint actions. Do not commit scene bundles, meshes, textures, raw sensor dumps, checkpoints, core dumps, tokens, keys, or private configs.
