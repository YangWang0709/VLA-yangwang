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
phaseH_status: completed
```

## New Scene Route

1. Phase A: scene open and robot inspection. Status: passed.
2. Phase B: real Isaac/Omniverse sensor suite smoke. Status: passed.
3. Phase C: real-sensor mapping smoke. Status: passed.
4. Phase D: candidate viewpoint + information gain smoke. Status: passed.
5. Phase E: VLM-LA interface smoke. Status: passed.
6. Phase F: short closed-loop smoke. Status: passed.
7. Phase G: long rollout data collection. Status: passed.
8. Phase H: dataset quality audit and human review packet. Status: completed.
9. SFT preparation: blocked until manual review approval.

## Phase H Gate

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


## Negative Scope

training: false
RL: false
SFT: false
GDPO: false
map_predict: false
PI_finetuning: false
A1_locomotion_training: false
real_VLM_inference: false
training_ready: false
