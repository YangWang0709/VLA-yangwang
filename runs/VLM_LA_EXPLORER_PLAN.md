# VLM-LA Explorer Plan

## Method Name

A1-VLM-LA Explorer

Full route name:

A1-VLM-LA Explorer for 3D Active Exploration

## Output Contract

`Go to candidate <id>.`

## Current New Scene

```yaml
current_phase: New Scene Phase A scene open and robot inspection
current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd_not_started
open_stage_result: true
safe_to_real_sensor_smoke: true
training_ready: false
```

The original user USD was localized into an ignored repaired bundle, matching the earlier complete-bundle approach used for the previous USD scene.

## New Scene Route

1. Phase A: scene open and robot inspection. Status: passed.
2. Phase B: real Isaac/Omniverse sensor suite smoke. Status: next.
3. Phase C: real-sensor mapping smoke.
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
