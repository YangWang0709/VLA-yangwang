# Active Task Board

current_phase: New Scene Phase A scene open and robot inspection
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd_not_started
training_ready: false
requires_human_review: true
next_phase: New Scene Phase B real Isaac/Omniverse sensor suite smoke

negative_scope:
- training: false
- SFT: false
- GDPO: false
- RL: false
- map_predict: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- real_vlm_inference: false
- rollout: false

## New Scene Phase A Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/new_scene_sampling_building_scene_1_scene_20260608_171052
script: /home/ubuntu22/VLA/scripts/new_scene_phaseA_open_and_robot_inspect.py
report: /home/ubuntu22/VLA/runs/new_scene_sampling_building_scene_1_scene_20260608_171052/NEW_SCENE_OPEN_AND_ROBOT_INSPECTION_REPORT.md
summary_json: /home/ubuntu22/VLA/runs/new_scene_sampling_building_scene_1_scene_20260608_171052/summary/open_and_robot_inspection_summary.json
bundle_localization_summary: /home/ubuntu22/VLA/runs/new_scene_sampling_building_scene_1_scene_20260608_171052/summary/new_scene_bundle_localization_summary.json
open_stage_result: true
stage_available: true
stage_open_method: pxr.Usd.Stage.Open after Isaac headless startup
stage_open_elapsed_sec: 2.59
prim_count: 1230
mesh_count: 170
cube_count: 149
material_count: 167
camera_count: 0
light_count: 1
articulation_root_count: 1
physics_joint_count: 54
core_dump_found: false
safe_to_real_sensor_smoke: true
formal_sampling_started: false

## Bundle Handling

The original user USD was not modified. A localized repaired bundle was created under `/home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/`, replacing the remote Unitree A1 reference with a local ignored dependency copy. The scene bundle remains excluded from Git by `.gitignore`.
