"""Small 3D U-Net interface draft for occupancy completion.

This module defines the intended model surface only. It is safe to import
without starting training.
"""

from __future__ import annotations


try:
    import torch
    from torch import nn
except Exception:  # pragma: no cover - torch may be unavailable in lint contexts.
    torch = None
    nn = None


if nn is not None:

    class DoubleConv3d(nn.Module):
        def __init__(self, in_channels: int, out_channels: int) -> None:
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv3d(in_channels, out_channels, kernel_size=3, padding=1),
                nn.GroupNorm(4, out_channels),
                nn.SiLU(),
                nn.Conv3d(out_channels, out_channels, kernel_size=3, padding=1),
                nn.GroupNorm(4, out_channels),
                nn.SiLU(),
            )

        def forward(self, x):
            return self.net(x)


    class OccupancyUNet3D(nn.Module):
        """Minimal 3D U-Net draft: partial occupancy to logits and uncertainty."""

        def __init__(self, in_channels: int = 4, base_channels: int = 24) -> None:
            super().__init__()
            self.enc1 = DoubleConv3d(in_channels, base_channels)
            self.down = nn.MaxPool3d(2)
            self.enc2 = DoubleConv3d(base_channels, base_channels * 2)
            self.up = nn.ConvTranspose3d(base_channels * 2, base_channels, kernel_size=2, stride=2)
            self.dec1 = DoubleConv3d(base_channels * 2, base_channels)
            self.occupancy_head = nn.Conv3d(base_channels, 1, kernel_size=1)
            self.uncertainty_head = nn.Conv3d(base_channels, 1, kernel_size=1)

        def forward(self, x):
            e1 = self.enc1(x)
            e2 = self.enc2(self.down(e1))
            up = self.up(e2)
            if up.shape[-3:] != e1.shape[-3:]:
                up = torch.nn.functional.interpolate(up, size=e1.shape[-3:], mode="trilinear", align_corners=False)
            dec = self.dec1(torch.cat([e1, up], dim=1))
            return {
                "occupancy_logits": self.occupancy_head(dec),
                "uncertainty_logits": self.uncertainty_head(dec),
            }

else:

    class OccupancyUNet3D:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            raise ImportError("torch is required for OccupancyUNet3D")
