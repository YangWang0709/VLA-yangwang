# Scene Open Smoke Report

phase: Phase 2
workspace: /home/ubuntu22/VLA
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
scene_file_type: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd: USD ASCII, version 1.0
scene_bundle_size: 490M
dependencies_present: true
git_ignore_scene_bundle: true
isaac_headless_open_exit_code: 0
open_stage_result: true
stage_available: true
prim_count: 1324
mesh_count: 127
cube_count: 279
material_count: 124
camera_count: 4
core_dump_found: false
mdl_warnings_found: true
mdl_warnings_blocking: false
safe_to_continue_go2_sensor_smoke: true
training: false
RL: false
map_predict: false
PI_finetuning: false
Go2_locomotion_training: false

## Probe Artifacts

- JSON: `/home/ubuntu22/VLA/runs/phase2_scene_open_go2_inspection_20260607_181505/probes/isaac_open_scene.json`
- Log: `/home/ubuntu22/VLA/runs/phase2_scene_open_go2_inspection_20260607_181505/logs/isaac_open_scene.log`
- Run directory: `/home/ubuntu22/VLA/runs/phase2_scene_open_go2_inspection_20260607_181505`

## Notes

Isaac headless opened the stage successfully and traversed 1324 prims. MDL/material warnings were observed in the log, but they did not block stage opening and are therefore non-blocking for Phase 2.

## Prim Type Counts

```json
{
  "Xform": 470,
  "Mesh": 127,
  "Cube": 279,
  "Material": 124,
  "Camera": 4,
  "Light": 1,
  "PhysicsJoint": 66,
  "ArticulationRoot": 1
}
```
