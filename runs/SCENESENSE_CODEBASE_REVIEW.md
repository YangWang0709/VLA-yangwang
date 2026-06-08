# SceneSense Codebase Review

phase: SceneSense official codebase review
workspace: /home/ubuntu22/VLA
repo_url: https://github.com/arpg/SceneSense
repo_path: /home/ubuntu22/VLA/external/SceneSense
commit_hash: af1517c26a8017251f940e76482d12ce3ceecde4
training_started: false
rollout_started: false
large_data_downloaded: false
external_repo_committed_to_vla: false

## Scope And Safety

This review cloned the official SceneSense repository and performed static code
inspection only. No training, no rollout, no model fine-tuning, no large data
download, and no VLA main logic changes were performed.

`external/SceneSense/` is intentionally excluded from the VLA repository through
the local Git exclude file so that the vendored external repository is not
accidentally committed.

## Directory Structure

Important top-level files and directories:

- README.md
- setup.bash
- setup.py
- example_results_h1.png
- example_results_h2.png
- SceneSense/example_prediction.py
- SceneSense/full_model_training.py
- SceneSense/training/train_model.py
- SceneSense/training/train_full_sim_model_short.py
- SceneSense/utils/pointnet2_scene_diffusion.py
- SceneSense/utils/pointnet2_utils.py
- SceneSense/utils/utils.py
- SceneSense/house_data/
- SceneSense/depricated/
- SceneSense/data/SceneSenseExData/

Repository size after clone is about 34 MB. No file over 50 MB was found in the
clone.

## Install Requirements

There is no requirements.txt. Dependencies are declared mainly in setup.bash:

- Python 3.9 venv
- torch, torchvision, torchaudio from PyTorch cu118 wheels
- diffusers[torch]
- transformers
- huggingface_hub
- natsort
- wandb
- spconv-cu120
- scipy
- matplotlib
- open3d
- opencv-python
- clean-fid
- git-lfs
- editable install with `pip install -e .`

Additional imports seen in code but not fully covered by setup.bash include:

- scikit-learn, used by frontier_id.py for DBSCAN
- bagpy and pypcd4, used by house_data/process_data.py and deprecated processing
- pandas and PyYAML, used in ROS bag style data processing

setup.py packages appear stale or inconsistent with the repo layout. It lists
`SceneSense.spot_data_processing` and `SceneSense.visualizations`, while those
folders exist under `SceneSense/depricated/` rather than as current top-level
packages.

## CUDA / spconv Requirement

SceneSense has a strong CUDA and spconv dependency:

- README states Ubuntu 20.04 and CUDA 11 or 12.
- README says to change `spconv-cuXXX` in setup.bash to match CUDA version.
- setup.bash installs PyTorch cu118 but also installs `spconv-cu120`.
- example_prediction.py creates `PointToVoxel(..., device=torch.device("cuda"))`.
- training scripts use `torch_device = "cuda"`.

For VLA integration, spconv should be treated as optional. The existing
`/home/ubuntu22/VLA/map_predict/voxelize.py` NumPy-style voxelization route is a
better default for portability inside the IsaacLab environment. If spconv is
enabled later, it should be behind an optional backend flag.

## Data Directory Expectation

README expects downloaded data to be placed under:

`SceneSense/SceneSense/data/`

The repo includes a small example dataset:

`SceneSense/SceneSense/data/SceneSenseExData/`

Included example files:

- `rgb_.png`: RGB image, 256 x 256.
- `sample_pcnpy.npy`: depth or RGB-D point cloud positions, shape `(65536, 3)`.
- `running_occ.pcd`: partial/running occupied map, 3707 points.
- `gt_occ_point.pcd`: full occupancy point cloud, 62802 points.
- `curr_pose.txt`: current robot pose.
- `curr_heading.txt`: current robot heading or rotation vector.
- `171`: PyTorch state dict for the PointNet conditioning model, about 3.9 MB.

Training scripts expect generated data folders such as:

- `data/full_gt_pointmaps/`
- `data/full_conditioning_rgbd/`
- `data/full_sim_pointnet_weights_more_pointnet_short/`

Several older scripts hard-code paths under `/home/arpg/Documents/...`,
`/home/brendan/realsense_data/...`, and `/hdd/...`; these are not reusable
without an adapter.

## Input Format

SceneSense does not use the VLA Phase 0 sample dictionary directly. It uses:

1. A local occupancy pointmap target.
   - Created by `utils.pc_to_pointmap`.
   - Shape is `[Z, X, Y]`, then used as a 2D diffusion tensor with Z as channels.
   - Common training shape is `[13, 40, 40]` for a local crop.
   - Older scripts also show `[22, 30, 30]`.
   - Typical voxel size is 0.1 m.
   - Typical local bounds are `x_y_bounds=[-2, 2]`, `z_bounds=[-1.4, 0.9]`.

2. A partial observation conditioning point cloud.
   - For example_prediction.py, `sample_pcnpy.npy` has XYZ points.
   - RGB colors are read from `rgb_.png` and appended to form XYZRGB.
   - Shape before network is effectively `[N, 6]`.
   - spconv `PointToVoxel` converts this to voxel point features.
   - The point feature array is reshaped/transposed to `[B, 6, N]` for PointNet.

3. Known occupied and known free inpainting masks.
   - Occupied partial observation comes from `running_occ.pcd`.
   - Free-space support exists in `utils.inpainting_pointmaps_w_freespace`, but
     example_prediction.py references a hard-coded external free-space PCD:
     `/home/arpg/Documents/habitat-lab/test_unoc.pcd`.

## Occupancy Encoding

Occupancy is encoded as binary pointmaps:

- 1.0 means occupied voxel.
- 0.0 means unoccupied or not predicted occupied.
- `pointmap_to_pc` converts predictions back to point clouds using a threshold,
  default `prediction_thresh=0.8`.

SceneSense does not cleanly separate `observed_free`, `observed_occupied`, and
`unknown_mask` in the same canonical tensor format we defined for VLA
map_predict. The freespace inpainting path treats free voxels by writing
`1 - unoccupied_grid` into the latent, which is useful as a design reference but
should not be copied directly without validation.

## Partial Observation Input

The partial observation path is SceneSense-style RGB-D or running occupancy:

- RGB image plus point cloud creates XYZRGB conditioning.
- Running occupancy PCD provides observed occupied points for inpainting.
- Optional free-space PCD can constrain known free cells.
- Current pose and heading are used to crop local GT and transform local points
  into the robot frame.

This aligns conceptually with VLA data:

- VLA has real Isaac RGB-D.
- VLA has depth_backprojection pointcloud.
- VLA has A1 pose.
- VLA has BEV explored maps and candidate tables.
- VLA now has dense-scan pseudo full occupancy GT prototypes for two scenes.

## Model Architecture Summary

SceneSense combines a PointNet++ style conditioning encoder with a 2D conditional
diffusion UNet:

- Conditioning encoder: `SceneSense/utils/pointnet2_scene_diffusion.py`
- Encoder structure:
  - PointNetSetAbstraction layers with sample counts 2048, 1024, 512, 256.
  - Feature propagation layers.
  - Final Conv1d and BatchNorm produce 128-dimensional point features.
  - Returned feature shape is used as cross-attention conditioning after axis
    swap, typically `[B, N, 128]`.
- Diffusion model: `diffusers.UNet2DConditionModel`
- Common active training configuration:
  - `sample_size=40`
  - `in_channels=13`
  - `out_channels=13`
  - `cross_attention_dim=128`
  - `block_out_channels=(128, 256, 512, 512)`
  - Cross-attention down blocks and up blocks
- Noise scheduler: `diffusers.DDPMScheduler(num_train_timesteps=1000)`

This is not a native 3D UNet. It represents height/depth slices as channels in a
2D diffusion model.

## Diffusion / Sampler

Reusable sampling helpers are in `SceneSense/utils/utils.py`:

- `denoise_guided_inference`
- `inpainting_pointmaps`
- `inpainting_pointmaps_w_freespace`

The sampler uses classifier-free guidance by concatenating zero conditioning and
PointNet conditioning, then runs `noise_scheduler.step`. The inpainting helpers
overwrite latent values at known occupied and known free coordinates during
denoising.

Caveats:

- Device defaults are inconsistent, for example `"cuda:1"` or `"cpu"` in helper
  defaults while top-level scripts use `"cuda"`.
- Some helper paths print heavily and are intended for experiments.
- The freespace inpainting math should be retested before reuse.
- No native uncertainty head exists. Uncertainty should be estimated in VLA by
  repeated stochastic samples, variance, entropy, or disagreement across samples.

## Inference Entrypoint

Main inference/demo entrypoint:

`SceneSense/example_prediction.py`

It performs the following:

- Loads a pretrained UNet from HuggingFace:
  `alre5639/full_rgbd_unet_512_more_pointnet`
- Uses revision:
  `b063adc01ea748b7a4dbfb7e180eedf741aef536`
- Builds PointNet conditioning model via `get_model()`.
- Loads local PointNet checkpoint:
  `data/SceneSenseExData/171`
- Reads example RGB, point cloud, running occupancy, GT occupancy, pose, heading.
- Builds RGB-D conditioning with spconv `PointToVoxel`.
- Converts local running occupancy to a pointmap.
- Runs inpainting with freespace support.
- Visualizes outputs using Open3D windows.

This entrypoint is not directly suitable for headless VLA pipeline use because
it has hard-coded relative data paths, CUDA assumptions, HuggingFace download
dependency, external free-space PCD path, and Open3D visualization calls.

## Training Entrypoint

Training-related entrypoints:

- `SceneSense/full_model_training.py`
- `SceneSense/training/train_model.py`
- `SceneSense/training/train_full_sim_model_short.py`
- deprecated variants under `SceneSense/depricated/`

Important warnings:

- Training scripts contain a hard-coded HuggingFace token.
- Training scripts call `wandb.init`.
- Training scripts push models to HuggingFace via `model.push_to_hub`.
- Training scripts save PointNet checkpoints to hard-coded local folders.
- Training scripts assume data folders that are absent from the cloned repo.
- Training scripts are not safe to run in VLA without cleanup.

No training was run during this review.

## Checkpoint And Sample Data

Checkpoint status:

- A PointNet conditioning checkpoint exists in the repo:
  `SceneSense/SceneSense/data/SceneSenseExData/171`
- It loads as an OrderedDict with 154 tensor keys.
- It appears to match the PointNet conditioning model.
- The full diffusion UNet weights are not stored in the repo; demo code loads
  them from HuggingFace.

Sample data status:

- Small sample data exists under `SceneSense/data/SceneSenseExData`.
- No large sample dataset was downloaded.
- README has a placeholder download link and instructs users to place data under
  `SceneSense/SceneSense/data/`.

## ROS / spconv Dependency

ROS:

- No active `rospy` node dependency was found for inference.
- Data processing scripts depend on ROS bag style data through `bagpy`.
- Processing scripts reference ROS topics such as `/tf`,
  `/d400/throttled_point_cloud`, and `/t265/odom/sample`.
- `sensor_msgs` imports are commented out in some files.

spconv:

- spconv is used directly for `PointToVoxel`.
- setup.bash installs `spconv-cu120`.
- This is a CUDA-version-sensitive dependency and should not be a hard
  requirement for the first VLA adapter.

## Reusable Modules

Potentially reusable with cleanup:

- `SceneSense/utils/pointnet2_scene_diffusion.py`
  - PointNet++ conditioning encoder design.
- `SceneSense/utils/pointnet2_utils.py`
  - PointNet set abstraction and feature propagation.
- `SceneSense/utils/utils.py`
  - Pointmap conversion and diffusion inpainting ideas.
- `SceneSense/example_prediction.py`
  - Useful as an inference recipe, not as importable production code.
- `SceneSense/house_data/gen_full_gt_pointmaps.py`
  - Useful as a reference for local GT pointmap generation.
- `SceneSense/house_data/gen_full_conditioning.py`
  - Useful as a reference for RGB-D/point cloud conditioning generation.
- `SceneSense/frontier_id.py`
  - Useful only as a rough frontier clustering idea.

## Incompatible Parts

Primary incompatibilities for direct VLA reuse:

- Hard-coded absolute paths to author machines.
- Hard-coded HuggingFace token in training scripts.
- HuggingFace `push_to_hub` and WandB side effects in training scripts.
- Open3D GUI visualization calls in demo and analysis scripts.
- CUDA-only assumptions and spconv dependency.
- Python package layout inconsistencies.
- Some import paths refer to `SceneDiffusion` or local `utils` instead of
  stable `SceneSense` package imports.
- Data format is 2D diffusion pointmap with Z as channels, not the VLA canonical
  `[D, H, W]` occupancy sample dictionary.
- Full occupancy GT data is expected as full scene PCD or pointmap files, while
  VLA currently has dense-scan pseudo GT `.npz` prototypes.
- No native uncertainty output, only stochastic diffusion behavior that can be
  sampled repeatedly.
- No clean headless CLI for inference without visualization.

## Integration Blockers

Before using SceneSense logic in `/home/ubuntu22/VLA/map_predict`, blockers are:

- Decide whether to keep VLA's 3D tensor contract or temporarily flatten to
  SceneSense-style `[Z, X, Y]` pointmaps for the diffusion core.
- Implement a safe adapter for observed free, observed occupied, unknown, and
  full occupancy masks.
- Avoid direct spconv dependency unless an optional CUDA backend is explicitly
  validated.
- Replace hard-coded data paths with explicit config paths.
- Disable all HuggingFace, WandB, and visualization side effects by default.
- Provide controlled checkpoint loading and require explicit approval before
  downloading model weights.
- Generate or validate local crop datasets from VLA dense-scan pseudo GT before
  any map_predict training.
- Add an uncertainty wrapper that runs multiple samples or accepts logits and
  returns `occupancy_probability` plus `uncertainty`.

## Recommended Adapter Design For /home/ubuntu22/VLA/map_predict

Recommended module plan:

1. Add a future `map_predict/scenesense_adapter.py`.
   - No training side effects.
   - No HuggingFace login.
   - No global CUDA initialization on import.
   - No Open3D visualization.

2. Convert VLA canonical samples to SceneSense pointmaps.
   - Input: `observed_free`, `observed_occupied`, `unknown_mask`,
     `frontier_mask`, `full_occupancy`, all `[D, H, W]`.
   - Output for a SceneSense-style core: pointmap `[D, H, W]`, using D as
     diffusion channels.
   - Preserve known occupied and known free cells during inpainting.
   - Keep `unknown_mask` as the only prediction region.

3. Build conditioning from VLA real-sensor data.
   - Use depth_backprojection pointcloud from real Isaac RGB-D.
   - Attach RGB channels when available to make XYZRGB `[N, 6]`.
   - Use `map_predict/voxelize.py` as default CPU/NumPy voxelizer.
   - Add optional spconv backend only after environment validation.

4. Wrap model architecture cleanly.
   - Keep existing VLA `model_3d_unet.py` path for native 3D experiments.
   - Add a separate SceneSense-style 2D diffusion wrapper if needed.
   - Do not replace the VLA feature-provider interface.

5. Wrap sampling and uncertainty.
   - Sampling returns:
     - `predicted_occupancy: [D, H, W]`
     - `occupancy_probability: [D, H, W]`
     - `uncertainty: [D, H, W]`
   - Estimate uncertainty from multiple stochastic diffusion samples, variance,
     or Bernoulli entropy.
   - Project uncertainty to BEV through `map_predict/bev_project.py`.

6. Feed candidate features only.
   - Enrich candidate tables through `map_predict/frontier_features.py`.
   - Do not emit navigation commands.
   - Preserve VLM-LA output contract:
     `Go to candidate <id>.`

7. Keep training blocked until user approval.
   - Current safe next engineering step is adapter and local crop dataset
     generation.
   - Do not start SceneSense training, VLA SFT, GDPO, RL, or rollout.

## Review Conclusion

SceneSense is valuable as a design reference for partial observation conditioned
occupancy completion. The most useful concepts are:

- local occupancy pointmaps,
- RGB-D or point cloud conditioning,
- PointNet++ conditioning into a conditional diffusion UNet,
- inpainting that preserves known observed cells,
- uncertainty through stochastic sampling.

Direct code reuse should be limited and carefully wrapped. The official codebase
is research-code style, path-specific, CUDA/spconv-specific, and contains
training side effects that should not enter the VLA main path.

recommended_next_step: MapPredict Phase 2 local voxel crop dataset generation or
a small SceneSense adapter prototype, without training.
