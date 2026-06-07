# Active Task Board

current_phase: Phase 5.6 A1-mounted real Isaac/Omniverse sensor suite smoke
workspace: /home/ubuntu22/VLA
main_goal: A1-VLM-LA Explorer for 3D Active Exploration
output_contract: Go to candidate <id>.
robot_platform: unitree_a1
robot_source: existing_usd_prim
a1_root_prim: /World/A1
base_frame: /World/A1/base
next_phase: Rerun Phase 4 A1 mapping smoke with real Isaac/Omniverse sensors

## Reason

Phase 5.5 proved an A1-mounted frame but still used `mounted_geometry_proxy_pointcloud_from_a1_front_sensor`. Phase 5.6 replaces that route with real Isaac/Omniverse Replicator RGB-D capture and a depth-derived pointcloud. Geometry proxy data must not be treated as final sensor data.

## Phase 5.6 Result

status: passed
run_dir: /home/ubuntu22/VLA/runs/phase56_a1_real_sensor_suite_smoke_20260607_202405
scene_path: /home/ubuntu22/VLA/scenes/primary_building_scene_repaired/home_like_scene_v1.usd
camera_prim_path: /World/RuntimeSensors/a1_front_rgbd_camera
sensor_mount_parent: /World/A1/base (runtime camera synced under /World/RuntimeSensors)
sensor_mount_xyz: [0.3, 0.0, 0.28]
sensor_mount_rpy: [0.0, -0.261799, 0.0]
real_rgb_sensor_available: true
real_depth_sensor_available: true
camera_params_available: true
camera_intrinsics_available: true
real_camera_pointcloud_available: true
camera_pointcloud_source: depth_backprojection
rtx_lidar_attempted: true
rtx_lidar_available: true
lidar_pointcloud_available: true
semantic_segmentation_available: true
instance_segmentation_available: true
geometry_proxy_used: false
mounted_geometry_proxy_used: false
step_count: 6
successful_steps: 6
rgb_valid_steps: 6
depth_valid_steps: 6
camera_pointcloud_valid_steps: 6
lidar_valid_steps: 2
camera_follows_base_rate: 1.0
average_rgb_nonzero_ratio: 0.8384
average_depth_valid_ratio: 0.8349
average_camera_pointcloud_count: 992.83
core_dump_found: false
safe_to_rerun_phase4_with_real_sensors: true
safe_to_rerun_phase5_with_real_sensors: true

## Caveats

- RTX LiDAR was attempted and produced valid pointcloud data in some short steps, but RGB-D plus depth-backprojection remains the hard gate.
- Runtime sensors and runtime light are in-memory only; the primary USD scene was not saved or overwritten.
- Only lightweight metadata and a few debug frames were saved. No raw frame dump, `.npz`, `.hdf5`, checkpoint, or rollout artifact was created.
- Do not enter Phase 6 until Phase 4 and Phase 5 are rerun with the real Isaac/Omniverse sensor route.

## Negative Scope

- training: false
- RL: false
- map_predict_mainline: false
- PI_action_finetuning: false
- A1_locomotion_training: false
- candidate_generation: false
- primary_rollout: false
- Phase_6_executed: false

## Next Phase

Rerun Phase 4 A1 mapping smoke with real Isaac/Omniverse sensors.
