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

Only `selected_candidate_id` may drive downstream motion. Explanation text must be logged but ignored for motion decisions.

## Sensor, Map, And Candidate Gate

```yaml
sensor_method: real_isaac_omniverse_rgbd
map_update_source: depth_backprojection_pointcloud
camera_pointcloud_source: depth_backprojection
candidate_sampling_method: radial_24_candidates_3_radii_8_angles_around_a1_base
path_cost_method: astar_bev_grid_unknown_penalty
information_gain_method: real_sensor_bev_unknown_visibility
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
geometry_proxy_used: false
mounted_geometry_proxy_used: false
safe_to_continue_phase6: true
```

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

## Phase 6 Scope

Phase 6 may test only the constrained VLM-LA interface smoke when explicitly requested. It must not perform VLM training, RL, map_predict training, PI/openpi fine-tuning, rollout, or free-form coordinate control.
