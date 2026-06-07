# Scene Bundle Placement Report

phase: Phase 1
workspace: /home/ubuntu22/VLA
main_goal: Go2-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
scene_exists: true
copied_from_pi: true
source_bundle_path: /home/ubuntu22/pi/scenes/primary_building_scene_repaired/
bundle_size: 490M
dependencies_present: true
git_ignore_scene_bundle: true
files_over_50MB_tracked_by_git: none
safe_to_continue_phase2: true
training: false
RL: false
map_predict: false
PI_finetuning: false
Go2_locomotion_training: false

## Summary

The full primary scene bundle was copied from the old workspace into the new VLA workspace because the target USD did not previously exist. The copy used the complete source directory, including `dependencies/`, rather than copying only the USD file.

## Bundle Checks

- Target USD exists: true
- Target USD type: USD ASCII, version 1.0
- Target USD size: 358K
- Bundle directory: `/home/ubuntu22/VLA/scenes/primary_building_scene_repaired`
- Bundle size: 490M
- Dependencies directory exists: true

## Git Ignore Checks

The following paths are ignored by `.gitignore`:

```text
scenes/primary_building_scene_repaired/home_like_scene_v1.usd
scenes/primary_building_scene_repaired/dependencies
```

Evidence:

```text
.gitignore:2:scenes/primary_building_scene_repaired/ scenes/primary_building_scene_repaired/home_like_scene_v1.usd
.gitignore:2:scenes/primary_building_scene_repaired/ scenes/primary_building_scene_repaired/dependencies
```

## Large File Safety

- Files larger than 50MB tracked by Git: none
- Scene bundle committed to Git: false
- Meshes/textures/dependencies committed to Git: false
- Checkpoints/core dumps committed to Git: false

## Phase Gate

`safe_to_continue_phase2: true`

Phase 2 may run Isaac headless scene open and Go2 stage inspection smoke against:

```text
/home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
```

Do not proceed to Phase 3 or rollout until Phase 2 verifies scene loading and Go2 stage inspection.
