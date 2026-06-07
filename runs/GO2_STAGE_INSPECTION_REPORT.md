# Go2 Stage Inspection Report

phase: Phase 2
workspace: /home/ubuntu22/VLA
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
go2_in_usd_found: false
go2_root_prim: null
go2_base_frame_candidate: null
go2_candidate_prims:
  - score: 116
    type: Xform
    path: /World/A1
    matched_keywords: ['a1', 'articulation_root']
  - score: 44
    type: Xform
    path: /World/A1/trunk
    matched_keywords: ['trunk', 'a1']
  - score: 39
    type: Xform
    path: /World/A1/base
    matched_keywords: ['base', 'a1']
  - score: 29
    type: Xform
    path: /World/A1/FL_hip
    matched_keywords: ['a1']
  - score: 29
    type: Xform
    path: /World/A1/FR_hip
    matched_keywords: ['a1']
  - score: 29
    type: Xform
    path: /World/A1/RL_hip
    matched_keywords: ['a1']
  - score: 29
    type: Xform
    path: /World/A1/RR_hip
    matched_keywords: ['a1']
  - score: 28
    type: Xform
    path: /World/A1/FL_calf
    matched_keywords: ['a1']
  - score: 28
    type: Xform
    path: /World/A1/FL_thigh
    matched_keywords: ['a1']
  - score: 28
    type: Xform
    path: /World/A1/FR_calf
    matched_keywords: ['a1']
  - score: 28
    type: Xform
    path: /World/A1/FR_thigh
    matched_keywords: ['a1']
  - score: 28
    type: Xform
    path: /World/A1/RL_calf
    matched_keywords: ['a1']
  - score: 28
    type: Xform
    path: /World/A1/RL_thigh
    matched_keywords: ['a1']
  - score: 28
    type: Xform
    path: /World/A1/RR_calf
    matched_keywords: ['a1']
  - score: 28
    type: Xform
    path: /World/A1/RR_thigh
    matched_keywords: ['a1']
  - score: 28
    type: PhysicsFixedJoint
    path: /World/A1/base/floating_base
    matched_keywords: ['base', 'a1']
  - score: 28
    type: Cube
    path: /World/A1/base/visuals
    matched_keywords: ['base', 'a1']
  - score: 28
    type: PhysicsRevoluteJoint
    path: /World/A1/trunk/FL_hip_joint
    matched_keywords: ['trunk', 'a1']
  - score: 28
    type: PhysicsRevoluteJoint
    path: /World/A1/trunk/FR_hip_joint
    matched_keywords: ['trunk', 'a1']
  - score: 28
    type: PhysicsRevoluteJoint
    path: /World/A1/trunk/RL_hip_joint
    matched_keywords: ['trunk', 'a1']
  - score: 28
    type: PhysicsRevoluteJoint
    path: /World/A1/trunk/RR_hip_joint
    matched_keywords: ['trunk', 'a1']
  - score: 28
    type: Cube
    path: /World/A1/trunk/collisions
    matched_keywords: ['trunk', 'a1']
  - score: 28
    type: PhysicsFixedJoint
    path: /World/A1/trunk/imu_joint
    matched_keywords: ['trunk', 'a1']
  - score: 28
    type: Mesh
    path: /World/A1/trunk/visuals
    matched_keywords: ['trunk', 'a1']
  - score: 27
    type: Xform
    path: /World/A1/FL_foot
    matched_keywords: ['a1']
  - score: 27
    type: Xform
    path: /World/A1/FR_foot
    matched_keywords: ['a1']
  - score: 27
    type: Xform
    path: /World/A1/RL_foot
    matched_keywords: ['a1']
  - score: 27
    type: Xform
    path: /World/A1/RR_foot
    matched_keywords: ['a1']
  - score: 27
    type: Xform
    path: /World/A1/imu_link
    matched_keywords: ['a1']
  - score: 26
    type: Xform
    path: /World/A1/FL_thigh_shoulder
    matched_keywords: ['a1']
existing_camera_prims:
  - none
existing_lidar_prims:
  - none
existing_sensor_prims:
  - /World/A1/imu_link
  - /World/A1/imu_link/collisions
  - /World/A1/imu_link/visuals
  - /World/A1/trunk/imu_joint
prim_type_counts:
```json
{
  "Xform": 470,
  "Mesh": 127,
  "Cube": 279,
  "ArticulationRoot": 1,
  "PhysicsJoint": 66,
  "Camera": 0,
  "Lidar": 0,
  "Light": 1
}
```
inspection_json_path: /home/ubuntu22/VLA/runs/phase2_scene_open_go2_inspection_20260607_181505/probes/go2_stage_inspection.json
temporary_go2_proxy_required: true
safe_to_continue_phase3: true
caveats:
  - Only base/trunk-like prims were found; no explicit Go2/Unitree/robot keyword appeared in top candidates.
  - No Go2-like robot hierarchy was found by keyword inspection; Phase 3 must use a temporary Go2-shaped proxy and report it as non-final.
  - An articulated /World/A1 robot hierarchy was found, but no explicit Go2 or Unitree naming was found; do not report it as a verified Go2 prim.
  - No camera or lidar prim was found by type/name keyword inspection; Phase 3 may need a sensor proxy.

## Interpretation

The stage contains an articulated `/World/A1` robot hierarchy, including trunk/base/joint prims, but no explicit `Go2`, `Unitree`, `dog`, `quadruped`, or `robot` naming was found by this Phase 2 keyword inspection. Therefore this report does not claim that a verified Unitree Go2 prim exists in the USD.

Per the Phase 2 rule, Phase 3 may continue, but it must take the temporary Go2-shaped proxy route unless the user supplies or identifies a verified Go2 prim. It must not report `/World/A1` as an existing Go2 prim.

## Negative Scope

- training: false
- RL: false
- map_predict: false
- PI_finetuning: false
- Go2_locomotion_training: false
- primary_rollout: false
- USD stage modified: false
