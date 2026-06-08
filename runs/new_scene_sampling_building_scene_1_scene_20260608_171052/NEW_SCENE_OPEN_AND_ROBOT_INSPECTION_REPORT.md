# New Scene Open And Robot Inspection Report

phase: New Scene Phase A
workspace: /home/ubuntu22/VLA
current_scene_id: building_scene_1_scene_20260608_171052
NEW_SCENE_PATH: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
original_user_usd_path: /home/ubuntu22/VLA/building_scene(1).usd
scene_selection_reason: localized repaired bundle derived from newest user USD /home/ubuntu22/VLA/building_scene(1).usd; remote Unitree A1 reference replaced by local dependency copy
scene_exists: true
scene_size_bytes: 283059
scene_mtime: 2026-06-08 17:31:28
stage_open_method: pxr.Usd.Stage.Open after Isaac headless startup
stage_open_elapsed_sec: 2.59
open_stage_result: true
stage_available: true
prim_count: 1230
core_dump_found: false
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
a1_base_frame_candidate: /World/A1/base
safe_to_real_sensor_smoke: true
formal_sampling_started: false
next_action: continue_to_new_scene_phaseB_real_sensor_smoke

## Bundle Handling

- The original user USD was not modified or overwritten.
- The selected Phase A entry is a localized repaired bundle copy.
- The remote Unitree A1 reference was replaced by a local dependency copy inside the ignored bundle.

## Prim Counts

- Mesh: 170
- Cube: 149
- Material: 167
- Camera: 0
- Light: 1
- ArticulationRoot: 1
- PhysicsJoint: 54

## A1 / Robot Candidate Prims

- score=730 type=Xform articulation=true keywords=a1,articulation_root path=/World/A1
- score=214 type=Xform articulation=false keywords=a1,trunk path=/World/A1/trunk
- score=209 type=Xform articulation=false keywords=a1,base path=/World/A1/base
- score=194 type=PhysicsFixedJoint articulation=false keywords=a1,base path=/World/A1/base/floating_base
- score=194 type=Cube articulation=false keywords=a1,base path=/World/A1/base/visuals
- score=194 type=PhysicsRevoluteJoint articulation=false keywords=a1,trunk path=/World/A1/trunk/FL_hip_joint
- score=194 type=PhysicsRevoluteJoint articulation=false keywords=a1,trunk path=/World/A1/trunk/FR_hip_joint
- score=194 type=PhysicsRevoluteJoint articulation=false keywords=a1,trunk path=/World/A1/trunk/RL_hip_joint
- score=194 type=PhysicsRevoluteJoint articulation=false keywords=a1,trunk path=/World/A1/trunk/RR_hip_joint
- score=194 type=Cube articulation=false keywords=a1,trunk path=/World/A1/trunk/collisions
- score=194 type=PhysicsFixedJoint articulation=false keywords=a1,trunk path=/World/A1/trunk/imu_joint
- score=194 type=Mesh articulation=false keywords=a1,trunk path=/World/A1/trunk/visuals
- score=193 type=Xform articulation=false keywords=a1 path=/World/A1/FL_hip
- score=193 type=Xform articulation=false keywords=a1 path=/World/A1/FR_hip
- score=193 type=Xform articulation=false keywords=a1 path=/World/A1/RL_hip
- score=193 type=Xform articulation=false keywords=a1 path=/World/A1/RR_hip
- score=192 type=Xform articulation=false keywords=a1 path=/World/A1/FL_calf
- score=192 type=Xform articulation=false keywords=a1 path=/World/A1/FL_thigh
- score=192 type=Xform articulation=false keywords=a1 path=/World/A1/FR_calf
- score=192 type=Xform articulation=false keywords=a1 path=/World/A1/FR_thigh
- score=192 type=Xform articulation=false keywords=a1 path=/World/A1/RL_calf
- score=192 type=Xform articulation=false keywords=a1 path=/World/A1/RL_thigh
- score=192 type=Xform articulation=false keywords=a1 path=/World/A1/RR_calf
- score=192 type=Xform articulation=false keywords=a1 path=/World/A1/RR_thigh
- score=191 type=Xform articulation=false keywords=a1 path=/World/A1/FL_foot
- score=191 type=Xform articulation=false keywords=a1 path=/World/A1/FR_foot
- score=191 type=Xform articulation=false keywords=a1 path=/World/A1/RL_foot
- score=191 type=Xform articulation=false keywords=a1 path=/World/A1/RR_foot
- score=191 type=Xform articulation=false keywords=a1 path=/World/A1/imu_link
- score=190 type=Xform articulation=false keywords=a1 path=/World/A1/FL_thigh_shoulder
- score=190 type=Xform articulation=false keywords=a1 path=/World/A1/FR_thigh_shoulder
- score=190 type=Xform articulation=false keywords=a1 path=/World/A1/RL_thigh_shoulder
- score=190 type=Xform articulation=false keywords=a1 path=/World/A1/RR_thigh_shoulder
- score=186 type=UNDEFINED articulation=false keywords=a1 path=/World/A1/Looks
- score=177 type=Material articulation=false keywords=a1 path=/World/A1/Looks/material_black
- score=177 type=Material articulation=false keywords=a1 path=/World/A1/Looks/material_blue
- score=177 type=Material articulation=false keywords=a1 path=/World/A1/Looks/material_brown
- score=177 type=Material articulation=false keywords=a1 path=/World/A1/Looks/material_green
- score=177 type=Material articulation=false keywords=a1 path=/World/A1/Looks/material_grey
- score=177 type=Material articulation=false keywords=a1 path=/World/A1/Looks/material_orange

## Existing Camera Prims

- none

## Existing Lidar Prims

- none

## Existing Sensor-Like Prims

- /World/A1/trunk/imu_joint
- /World/A1/imu_link
- /World/A1/imu_link/visuals
- /World/A1/imu_link/collisions

## Negative Scope

- training: false
- RL: false
- SFT: false
- GDPO: false
- map_predict: false
- PI_finetuning: false
- A1_locomotion_training: false
- rollout: false
- real_sensor_smoke_started: false
- USD_modified_or_saved: false
