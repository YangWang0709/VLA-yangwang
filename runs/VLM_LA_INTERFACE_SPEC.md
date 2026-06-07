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

## Primary Output

```text
Go to candidate <id>.
```

## Phase 8 Interface Gate

```yaml
candidate_data_source: online_real_sensor_candidate_generation
vlm_output_mode: pseudo_from_classical_selector
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
geometry_proxy_used: false
mounted_geometry_proxy_used: false
parse_success_rate: 1.0
validation_success_rate: 1.0
movement_success_rate: 1.0
safe_to_continue_phase9: true
```

## Parser And Validator Contract

The parser extracts the integer candidate ID from `Go to candidate <id>.` commands. The validator checks candidate existence, valid/reachable flags, and collision risk before target pose lookup.

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
v, omega
```

```text
robot joint actions
```

The main interface must remain candidate-ID based. Free coordinates, velocities, and joint commands are not accepted as VLM-LA outputs.
