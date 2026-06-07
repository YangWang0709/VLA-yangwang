# Critic Report

## Current Phase

Phase 6 VLM-LA interface smoke

## Corrected Fact

The USD scene's real robot is `/World/A1`, not Go2. Formal data uses:

```yaml
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
```

## Phase 6 Review

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase6_vlm_la_interface_smoke_20260607_205612
script: /home/ubuntu22/VLA/scripts/phase6_vlm_la_interface_smoke.py
report: /home/ubuntu22/VLA/runs/VLM_LA_INTERFACE_SMOKE_REPORT.md
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
sensor_method: real_isaac_omniverse_rgbd
candidate_data_source: phase5r_real_sensor
output_contract: Go to candidate <id>.
phase5r_candidate_data_used: true
phase5r_run_dir: /home/ubuntu22/VLA/runs/phase5r_a1_real_sensor_candidate_gain_smoke_20260607_204631
legal_command_count: 24
legal_parse_success_rate: 1.0
legal_validation_success_rate: 1.0
target_pose_lookup_success_rate: 1.0
illegal_test_count: 47
illegal_reject_or_fallback_rate: 1.0
fallback_test_passed: true
invalid_candidate_fallback_tested: true
unreachable_candidate_fallback_tested: true
free_coordinate_output_allowed: false
velocity_output_allowed: false
joint_action_output_allowed: false
malformed_output_rejected: true
A1_moved: false
mapping_started: false
candidate_generation_started: false
real_vlm_inference_started: false
safe_to_continue_phase7: true

## Findings

- No blocking issues found for the requested interface smoke scope.
- Legal pseudo VLM commands parse and validate at 1.0 success rate.
- Illegal commands reject or fallback at 1.0 rate.
- Free coordinate, velocity, joint action, and malformed outputs are rejected.
- Invalid and unreachable candidate IDs trigger fallback to the Phase 5R classical selected candidate.

## Residual Risks And Caveats

- This validates the VLM-LA command interface with pseudo outputs, not real VLM inference.
- Phase 7 closed-loop smoke is now allowed by the gate, but was not run here.
- Downstream motion execution remains outside this Phase 6 smoke.

## Prohibited Work Check

- VLM training performed: false
- real VLM inference performed: false
- Phase 7 performed: false
- A1 movement performed: false
- mapping performed: false
- candidate generation performed: false
- RL training performed: false
- map_predict training performed: false
- PI/openpi fine-tuning performed: false
- A1 locomotion training performed: false
- rollout performed: false
- original USD saved or overwritten: false
- old proxy candidate data used: false
- large files committed: false

## Decision

safe_to_continue_phase7: true
next_phase: Phase 7 A1 VLM-LA closed-loop smoke
