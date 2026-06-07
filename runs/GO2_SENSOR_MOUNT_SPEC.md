# Go2 Sensor Mount Spec

## Status

Phase 0 planning spec. Actual USD prim paths and sensor availability must be verified in Phase 2 and Phase 3.

## Frame Convention

```yaml
robot_platform: unitree_go2
robot_source: existing_usd_prim
working_premise_usd_contains_go2: true
go2_root_prim: TBD_by_phase_2_stage_inspection
go2_base_frame: TBD_by_phase_2_stage_inspection_or_base_link
sensor_frame: go2_front_camera
map_frame: map
odom_frame: odom
```

## Planned Sensor Mount

- Reuse existing camera/sensor prims if the USD already contains them.
- If no usable sensor exists, logically bind a front RGB-D/depth/pointcloud proxy to the existing Go2 base frame.
- The front sensor should face forward and sit slightly above the body center.
- Save camera extrinsics relative to the discovered base frame.
- If RTX sensors are too complex for the first smoke test, a geometry proxy observation is allowed with a clear caveat.

## Required Report Items

1. Go2 root prim path: TBD by Phase 2.
2. Go2 base frame: TBD by Phase 2.
3. Sensor frame: `go2_front_camera`.
4. Camera pose relative to base: planned front-facing, slightly above body center; exact transform TBD.
5. Depth / pointcloud proxy method: TBD in Phase 3.
6. Real rendered sensor used: false in Phase 0, TBD in Phase 3.
7. Geometry proxy observation used: false in Phase 0, TBD in Phase 3.
8. Locomotion mode: existing controller if available, otherwise first-version kinematic base movement.
9. USD already contains Go2: working premise true, pending Phase 2 verification.
10. Temporary Go2 proxy: not created in Phase 0; only allowed if Phase 2 finds no Go2.

## Negative Scope

Do not train Go2 locomotion. Do not let the VLM output velocities, coordinates, or joint actions.
