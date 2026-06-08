# VLA Phase Status Audit

phase: status audit only
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
audit_scope: old primary USD and new building_scene_1 USD phase completion check
training: false
rollout_started: false
data_modified: false

## Summary

1. old_usd_scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
2. old_usd_long_rollout_completed: true
3. old_usd_dataset_quality_audit_human_review_packet_completed: true
4. old_usd_sft_dataset_preparation_completed: false
5. new_usd_scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
6. new_usd_long_rollout_completed: true
7. new_usd_dataset_quality_audit_human_review_packet_completed: true
8. current_recommended_next_step: manual review result required before any SFT dataset preparation; do not train or start SFT/GDPO until explicit approval.

## Old USD / Primary Scene

scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
long_rollout_report: /home/ubuntu22/VLA/runs/A1_VLM_LA_LONG_ROLLOUT_REPORT.md (present)
dataset_quality_report: /home/ubuntu22/VLA/runs/DATASET_QUALITY_REPORT.md (present)
human_review_checklist: /home/ubuntu22/VLA/runs/HUMAN_REVIEW_A1_VLM_LA_DATASET_CHECKLIST.md (present)
sft_dataset_preparation_report: /home/ubuntu22/VLA/runs/VLM_SFT_DATASET_PREPARATION_REPORT.md (missing)
completion_status: long rollout=true, quality/human review packet=true, SFT preparation=false

### Old Long Rollout Evidence

- phase: Phase 8
- scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
- start_count: 10
- completed_start_count: 10
- total_action_count: 77
- safe_to_continue_phase9: true
- training: false

### Old Quality Audit Evidence

- phase: Phase 9
- source phase: Phase 8
- total_samples: 77
- accepted_sample_count: 74
- warning_sample_count: 3
- rejected_sample_count: 0
- training_ready: false
- requires_human_review: true
- recommended_next_phase: manual_review_before_sft_preparation

## New USD / building_scene_1

scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
long_rollout_report: /home/ubuntu22/VLA/runs/NEW_SCENE_VLM_LA_LONG_ROLLOUT_REPORT.md (present)
dataset_quality_report: /home/ubuntu22/VLA/runs/NEW_SCENE_DATASET_QUALITY_REPORT.md (present)
human_review_checklist: /home/ubuntu22/VLA/runs/HUMAN_REVIEW_NEW_SCENE_DATASET_CHECKLIST.md (present)
completion_status: long rollout=true, quality/human review packet=true

### New Long Rollout Evidence

- phase: New Scene Phase G
- scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
- start_count: 10
- completed_start_count: 10
- total_action_count: 200
- safe_to_human_review: true
- training_ready: false
- training: false

### New Quality Audit Evidence

- phase: New Scene Phase H
- source phase: New Scene Phase G
- total_samples: 200
- accepted_sample_count: 199
- warning_sample_count: 1
- rejected_sample_count: 0
- training_ready: false
- requires_human_review: true
- recommended_next_phase: manual_review_before_sft_preparation

## Run Directory Search

Command:

```bash
find /home/ubuntu22/VLA/runs -maxdepth 2 -type d | sort | grep -E "phase8|phase9|phase10|phaseG|phaseH|sft"
```

Result:

```text
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/bev_renders
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/candidates
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/commands
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/debug_frames
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/logs
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/maps
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/parsing
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/plots
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/reports
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/rollout
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/samples
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/start_000
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/start_001
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185826_smoke/summary
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/bev_renders
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/candidates
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/commands
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/debug_frames
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/logs
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/maps
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/parsing
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/plots
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/reports
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/rollout
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/samples
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/start_000
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/start_001
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/start_002
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/start_003
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/start_004
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/start_005
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/start_006
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/start_007
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/start_008
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/start_009
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseG_long_rollout_20260608_185904/summary
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/accepted
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/logs
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/plots
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/quality
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/rejected
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/reports
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/summary
/home/ubuntu22/VLA/runs/new_scene_building_scene_1_phaseH_dataset_quality_audit_20260608_191002/warning
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/bev_renders
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/candidates
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/commands
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/debug_frames
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/logs
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/maps
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/parsing
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/plots
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/reports
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/rollout
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/samples
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/start_000
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/start_001
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212417_smoke/summary
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/bev_renders
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/candidates
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/commands
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/debug_frames
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/logs
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/maps
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/parsing
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/plots
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/reports
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/rollout
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/samples
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/start_000
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/start_001
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/start_002
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/start_003
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/start_004
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/start_005
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/start_006
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/start_007
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/start_008
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/start_009
/home/ubuntu22/VLA/runs/phase8_a1_vlm_la_long_rollout_20260607_212536/summary
/home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732
/home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/accepted
/home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/logs
/home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/plots
/home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/quality
/home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/rejected
/home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/reports
/home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/summary
/home/ubuntu22/VLA/runs/phase9_human_review_packet_20260607_213732/warning
```

Interpretation:

- Old primary scene has Phase 8 rollout run directories and a Phase 9 human review packet directory.
- No phase10 or sft run directory was found by this search.
- New building_scene_1 has Phase G long rollout directories and a Phase H dataset quality audit directory.

## Git Check

git_status_before_report_write:

```text
位于分支 main
您的分支与上游分支 'origin/main' 一致。

无文件要提交，干净的工作区
```

git_log_oneline_last_20:

```text
c89b92d new scene: prepare dataset quality review packet
cad2f08 new scene: collect vlm la rollout data
daf915f new scene: validate short closed loop smoke
8ec19e5 new scene: validate vlm la interface smoke
dc1fabc new scene: validate candidate viewpoint gain smoke
bf6b508 new scene: validate real sensor mapping smoke
c9fac10 new scene: validate real isaac sensor suite
6ca99bc new scene: validate scene open and robot inspection
5eceefd phase 9: prepare a1 vlm la dataset human review packet
a1fefa8 phase 8: collect a1 vlm la real sensor rollout data
f877e57 phase 7: validate a1 vlm la closed loop smoke
1d391ee phase 6: validate vlm la candidate command interface
61aace3 phase 5r: validate a1 real sensor candidate gain smoke
af99567 phase 4r: validate a1 real sensor mapping smoke
9c90495 phase 5.6: validate a1 real isaac sensor suite smoke
da45b4e phase 5.5: validate a1 mounted sensor smoke
37dd38a phase 5: validate a1 candidate viewpoint gain smoke
74aaf89 phase 4: validate a1 mapping smoke
ffb0703 phase 3: validate existing usd a1 sensor smoke
438cf51 phase correction: audit robot platform and switch from go2 label to a1
```

## Recommendation

- Do not start training, SFT, GDPO, RL, map_predict, real VLM inference, or additional rollout from this audit.
- Both old and new USD routes have reached dataset quality audit / human review packet stage.
- Old USD has not completed SFT dataset preparation because `runs/VLM_SFT_DATASET_PREPARATION_REPORT.md` is missing and no phase10/sft run directory was found.
- New USD has not entered SFT dataset preparation; it is at Phase H with `training_ready: false` and `requires_human_review: true`.
- The correct next step is manual review decision for one or both datasets before any SFT preparation phase.
