# WEBGPT Brief

## Current Phase

New Scene Phase A scene open and robot inspection

## Context

current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd_not_started
training_ready: false
requires_human_review: true

## Completed

- Searched requested roots and selected the newest user USD.
- Observed that direct `omni.usd` open on the single USDC was unsafe/unstable.
- Followed the previous bundle approach: created a localized repaired bundle and kept the original USD unchanged.
- Replaced the remote Unitree A1 reference with a local dependency copy inside the ignored bundle.
- Validated the localized scene with Isaac headless plus `pxr.Usd.Stage.Open`.
- Confirmed `/World/A1` and `/World/A1/base`.

## Metrics

open_stage_result: true
stage_available: true
stage_open_elapsed_sec: 2.59
prim_count: 1230
mesh_count: 170
cube_count: 149
material_count: 167
articulation_root_count: 1
physics_joint_count: 54
core_dump_found: false
safe_to_real_sensor_smoke: true

## Next Action

Continue only to New Scene Phase B real Isaac/Omniverse sensor suite smoke. Do not start rollout, training, SFT, GDPO, RL, or map_predict.
