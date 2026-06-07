# Failure Diagnosis

## Phase 0 Status

No blocking Phase 0 failure is recorded.

## Known Caveats

- The primary USD scene has not been placed or inspected in Phase 0.
- `omni` and `pxr` direct module discovery were not available through a simple Python import probe, even though `isaacsim` and `isaaclab` were discoverable. Phase 2 should use the correct Isaac headless launcher/probe path rather than treating this simple import probe as final USD capability evidence.
- Go2 root prim and base frame are not known until Phase 2 stage inspection.

## Recovery Plan

If Phase 1 cannot find the scene under `/home/ubuntu22/VLA/scenes`, copy the complete bundle from `/home/ubuntu22/pi/scenes/primary_building_scene_repaired/` without deleting or overwriting the old workspace. Keep the bundle ignored by Git.
