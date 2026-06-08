# Critic Report

## Current Phase

New Scene Phase B real sensor suite smoke

## Finding

status: passed

The repaired new scene was rendered through the real Isaac/Omniverse RGB-D sensor route. Geometry proxy and mounted geometry proxy were not used as formal sensor data.

## Evidence

- scene_path: /home/ubuntu22/VLA/scenes/new_scene_building_scene_1_repaired/building_scene_1_repaired.usda
- a1_root_prim: /World/A1
- base_frame: /World/A1/base
- camera_prim_path: /World/RuntimeSensors/a1_front_rgbd_camera
- pointcloud_source: depth_backprojection
- rgb_valid_steps: 6
- depth_valid_steps: 6
- camera_pointcloud_valid_steps: 6
- camera_follows_base_rate: 1.0
- rtx_lidar_attempted: true
- rtx_lidar_available: true
- core_dump_found: false
- safe_to_mapping: true

## Risks / Gates

- RTX LiDAR is optional for this gate; failures are recorded but do not block RGB-D if the main route passes.
- Some referenced props may emit MDL material warnings; the RGB-D/depth pointcloud gate is based on rendered sensor validity, not material completeness.
- Do not start Phase C unless `safe_to_mapping` is true.

training: false
RL: false
SFT: false
GDPO: false
rollout: false
USD_modified_or_saved: false
