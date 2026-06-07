# VLM-LA Interface Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Robot Platform

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

## Purpose

Define a constrained language-action interface for candidate viewpoint selection. The interface does not expose coordinates, velocities, or joint actions to the VLM.

## Primary Output

```text
Go to candidate <id>.
```

## Parser Contract

The parser extracts the integer candidate ID from a valid command. It must validate that:

- The command contains a candidate ID.
- The ID exists in the current candidate table.
- The candidate is valid.
- The candidate is reachable.

Only `selected_candidate_id` may drive control. Explanation text must be logged but ignored for motion decisions.

## Sensor And Map Route Gate

Phase 4R-real validates BEV mapping from real Isaac/Omniverse RGB-D observations.

```yaml
sensor_method: real_isaac_omniverse_rgbd
map_update_source: depth_backprojection_pointcloud
camera_pointcloud_source: depth_backprojection
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
geometry_proxy_used: false
mounted_geometry_proxy_used: false
```

Phase 5 should be rerun with real sensor mapping before Phase 6 interface smoke.

## Invalid Main Outputs

```text
Go to the left room.
```

```json
{
  "x": 1.2,
  "y": 3.4,
  "yaw": 1.57
}
```

```text
forward, turn left, forward
```

```text
v, omega
```

```text
robot joint actions
```

## Fallback Policy

If parsing or candidate validation fails, the system must fall back to the classical candidate selector for that step and log the reason code.

## Current Gate

Do not enter Phase 6 yet. Next phase is `Rerun Phase 5 A1 candidate viewpoint + information gain smoke with real sensors`.
