# Active Task Board

current_phase: Phase 5.5 robot platform correction audit
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
phase6_status: paused

## Correction Summary

- USD real robot is `/World/A1`.
- The project must no longer claim that the USD contains a verified Go2 robot.
- Phase 3 and Phase 4 used `temporary_go2_proxy`, so they remain valid only as proxy pipeline smoke.
- Phase 5 artifacts were not found in the current repository.
- Old proxy data must be labeled:
  - robot_platform: temporary_quadruped_proxy
  - robot_source: temporary_go2_proxy
  - not_final_robot_asset: true

## Current Decision

phase3_phase4_validity: valid_as_proxy_pipeline_smoke
phase5_validity: not_available
not_valid_as_final_a1_data: true
rerun_needed_for_a1: true

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- Go2_locomotion_training: false
- primary_rollout: false
- Phase_6: false

## Next Phase

Rerun Phase 3 through Phase 5 using explicit `/World/A1` root prim, or explicitly continue as proxy only. Do not enter Phase 6 yet.
