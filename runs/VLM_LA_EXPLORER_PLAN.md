# VLM-LA Explorer Plan

## Method Name

A1-VLM-LA Explorer

Full route name:

A1-VLM-LA Explorer for 3D Active Exploration

## Output Contract

`Go to candidate <id>.`

## Current New Scene

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
real_rgb_sensor_available: true
real_depth_sensor_available: true
real_camera_pointcloud_available: true
camera_pointcloud_source: depth_backprojection
safe_to_mapping: true
```

## New Scene Route

1. Phase A: scene open and robot inspection. Status: passed.
2. Phase B: real Isaac/Omniverse sensor suite smoke. Status: passed.
3. Phase C: real-sensor mapping smoke. Status: next.
4. Phase D: candidate viewpoint gain smoke.
5. Phase E: VLM-LA interface smoke.
6. Phase F: short closed-loop smoke.
7. Phase G: long rollout data collection.
8. Phase H: dataset quality audit and human review packet.

## Negative Scope

training: false
RL: false
SFT: false
GDPO: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
rollout: false
