# Go2-VLM-LA Explorer

Workspace: `/home/ubuntu22/VLA`

Research line: Go2-VLM-LA Explorer for 3D Active Exploration.

The project starts from an Isaac Sim USD indoor scene that is expected to already contain a Unitree Go2 robot. The main loop is:

```text
USD scene with existing Unitree Go2
-> Go2 pose / robot state
-> RGB-D / depth / pointcloud / LiDAR or proxy observation
-> explored_map / partial map
-> candidate viewpoints
-> BEV render with candidate IDs
-> VLM language output: Go to candidate <id>.
-> LA parser extracts candidate id
-> candidate table maps id to target viewpoint pose
-> planner / Go2 movement wrapper executes the target
```

Output contract:

```text
Go to candidate <id>.
```

Phase 0 is initialization only. No VLM training, RL, map_predict training, Go2 locomotion training, PI/openpi action-head fine-tuning, rollout, or scene-bundle commit is allowed in this phase.
