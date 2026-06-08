# WEBGPT Brief

## Current Phase

New Scene Phase H dataset quality audit / human review packet

## Context

current_scene_id: building_scene_1_scene_20260608_171052
current_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
current_scene_phase: New Scene Phase H dataset quality audit / human review packet
source_dataset: New Scene Phase G rollout
source_run_dir: /home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
camera_pointcloud_source: depth_backprojection
vlm_output_mode: pseudo_from_classical_selector
output_contract: Go to candidate <id>.
training_ready: false
requires_human_review: true
next_phase: Manual review result required before SFT preparation

negative_scope:
- training: false
- RL: false
- SFT: false
- GDPO: false
- map_predict: false
- real_VLM_inference: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- checkpoint_created: false


## Completed

- Audited New Scene Phase G real-sensor rollout samples.
- Split samples into accepted, warning, and rejected sets.
- Generated dataset quality summary, start quality summary, failure reason summary, plots, and a human review checklist.
- Kept `training_ready: false` and `requires_human_review: true`.

## Metrics

total_samples: 200
accepted_sample_count: 199
warning_sample_count: 1
rejected_sample_count: 0
acceptance_rate: 0.995
warning_rate: 0.005
rejection_rate: 0.0
parse_success_rate: 1.0
validation_success_rate: 1.0
movement_success_rate: 1.0
real_sensor_sample_rate: 1.0
average_final_known_ratio: 0.408687


## Next Action

Manual review result required before SFT preparation.
