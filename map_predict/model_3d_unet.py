"""Small 3D U-Net baseline for occupancy completion."""

from __future__ import annotations


try:
    import torch
    from torch import nn
except Exception:  # pragma: no cover - torch may be unavailable in lint contexts.
    torch = None
    nn = None


if nn is not None:

    def _group_count(channels: int) -> int:
        for groups in (8, 4, 2, 1):
            if channels % groups == 0:
                return groups
        return 1


    class DoubleConv3d(nn.Module):
        def __init__(self, in_channels: int, out_channels: int) -> None:
            super().__init__()
            self.net = nn.Sequential(
                nn.Conv3d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
                nn.GroupNorm(_group_count(out_channels), out_channels),
                nn.SiLU(),
                nn.Conv3d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
                nn.GroupNorm(_group_count(out_channels), out_channels),
                nn.SiLU(),
            )

        def forward(self, x):
            return self.net(x)


    class OccupancyUNet3D(nn.Module):
        """Lightweight 3-level 3D U-Net: partial occupancy to occupancy logits."""

        def __init__(
            self,
            in_channels: int = 6,
            out_channels: int = 1,
            base_channels: int = 16,
            levels: int = 3,
        ) -> None:
            if levels != 3:
                raise ValueError("Phase 3 baseline currently supports levels=3")
            super().__init__()
            self.in_channels = int(in_channels)
            self.out_channels = int(out_channels)
            self.base_channels = int(base_channels)
            self.levels = int(levels)

            c1 = base_channels
            c2 = base_channels * 2
            c3 = base_channels * 4
            self.enc1 = DoubleConv3d(in_channels, c1)
            self.down1 = nn.MaxPool3d(2)
            self.enc2 = DoubleConv3d(c1, c2)
            self.down2 = nn.MaxPool3d(2)
            self.bottleneck = DoubleConv3d(c2, c3)
            self.up2 = nn.ConvTranspose3d(c3, c2, kernel_size=2, stride=2)
            self.dec2 = DoubleConv3d(c2 + c2, c2)
            self.up1 = nn.ConvTranspose3d(c2, c1, kernel_size=2, stride=2)
            self.dec1 = DoubleConv3d(c1 + c1, c1)
            self.occupancy_head = nn.Conv3d(c1, out_channels, kernel_size=1)

        def _upsample_to(self, x, target):
            if x.shape[-3:] == target.shape[-3:]:
                return x
            return torch.nn.functional.interpolate(x, size=target.shape[-3:], mode="trilinear", align_corners=False)

        def forward(self, x):
            e1 = self.enc1(x)
            e2 = self.enc2(self.down1(e1))
            b = self.bottleneck(self.down2(e2))
            d2 = self._upsample_to(self.up2(b), e2)
            d2 = self.dec2(torch.cat([e2, d2], dim=1))
            d1 = self._upsample_to(self.up1(d2), e1)
            d1 = self.dec1(torch.cat([e1, d1], dim=1))
            return self.occupancy_head(d1)


    def count_parameters(model: nn.Module) -> int:
        return int(sum(p.numel() for p in model.parameters() if p.requires_grad))

else:

    class OccupancyUNet3D:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            raise ImportError("torch is required for OccupancyUNet3D")
