# VLM-LA Dataset Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Current New Scene Dataset Status

```yaml
current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
current_scene_phase: New Scene Phase B real sensor suite smoke
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_sensor_suite
output_contract: Go to candidate <id>.
training_ready: false
requires_human_review: true
next_phase: New Scene Phase C real-sensor mapping smoke
sensor_phaseB_status: passed
real_rgb_sensor_available: true
real_depth_sensor_available: true
real_camera_pointcloud_available: true
camera_pointcloud_source: depth_backprojection
```

No new-scene dataset samples have been created. Phase B only validated the real sensor route and did not create mapping, candidate, rollout, or training data.

## Required New Scene Sample Metadata

Future Phase G samples, only after Phase B-F pass, must include:

- real RGB/depth metadata
- depth_backprojection or Isaac pointcloud annotator stats
- BEV candidate render reference
- candidate table reference
- selected_candidate_id
- target_language: `Go to candidate <id>.`
- parser and validator result
- target pose
- movement result
- map stats
- failure reason if any

## Training Gate

training_ready: false
requires_human_review: true

Do not use new-scene data for SFT, GDPO, RL, or any training until a later explicit human review approves preparation.
