# Go2 Stage Inspection Report

## Status

Phase 0 placeholder. Stage inspection has not run yet.

## Working Premise

The primary USD scene is expected to already contain a Unitree Go2 robot. Phase 2 must verify this by opening the stage and traversing prims.

## Required Phase 2 Output Fields

```yaml
go2_in_usd_found: TBD
go2_root_prim: TBD
go2_base_frame_candidate: TBD
existing_sensors_found: TBD
camera_prims: []
lidar_prims: []
temporary_go2_proxy_used: false
robot_source: existing_usd_prim_or_temporary_proxy
```

## Rules

- Prefer the existing USD Go2 prim.
- Do not create a second main robot if a Go2-like hierarchy exists.
- Create a temporary Go2-shaped proxy only if no Go2-like hierarchy is found.
- If a proxy is created, report:

```yaml
go2_in_usd_found: false
temporary_go2_proxy_used: true
not_final_robot_asset: true
```

## Next Phase

Phase 2 must implement and run `scripts/inspect_usd_go2_stage.py` after Phase 1 confirms the scene bundle is present.
