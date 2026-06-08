# VLM-LA Dataset Spec

## Project Route

A1-VLM-LA Explorer for 3D Active Exploration

## Current New Scene Dataset Status

```yaml
current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
current_scene_phase: New Scene Phase E VLM-LA interface smoke
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
map_update_source: depth_backprojection_pointcloud
candidate_data_source: new_scene_phaseD_real_sensor
output_contract: Go to candidate <id>.
training_ready: false
requires_human_review: true
next_phase: New Scene Phase F short closed-loop smoke
sensor_phaseB_status: passed
mapping_phaseC_status: passed
candidate_phaseD_status: passed
interface_phaseE_status: passed
phaseD_candidate_data_used: true
safe_to_closed_loop: true
```

No new-scene rollout dataset samples have been created. Phase E only produced
small interface smoke records from the Phase D candidate table. It did not create
training data, rollout samples, or real VLM outputs.

## Required New Scene Sample Metadata

Future Phase G samples, only after Phase F passes and the user approves, must include:

- real RGB/depth metadata
- depth_backprojection pointcloud stats
- BEV map/candidate render reference
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

Do not use new-scene data for SFT, GDPO, RL, or any training until a later
explicit human review approves preparation.
