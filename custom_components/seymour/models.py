"""Pydantic models for the Seymour integration."""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, computed_field


def _format_aspect_ratio(width: float, height: float) -> str:
    """Format an aspect ratio like 2.40:1."""
    ratio = width / height
    return f"{ratio:.2f}:1"


class SeymourSystemInfo(BaseModel):
    """Validated Seymour system information."""

    model_config = ConfigDict(extra="forbid")

    protocol_version: str
    screen_model: str
    width_inches: float
    height_inches: float
    serial_number: str
    mask_ids: str
    raw_response: str

    @computed_field
    @property
    def diagonal_inches(self) -> float:
        """Return the actual screen diagonal in inches."""
        return round(math.hypot(self.width_inches, self.height_inches), 1)

    @computed_field
    @property
    def aspect_ratio(self) -> str:
        """Return the native aspect ratio."""
        return _format_aspect_ratio(self.width_inches, self.height_inches)


class SeymourRatioInfo(BaseModel):
    """Validated Seymour ratio information."""

    model_config = ConfigDict(extra="forbid")

    ratio_id: str
    label: str
    width_inches: float
    height_inches: float
    default_motor_positions: list[float]
    motor_position_adjustments: list[float]

    @computed_field
    @property
    def aspect_ratio(self) -> str:
        """Return the ratio aspect ratio."""
        return _format_aspect_ratio(self.width_inches, self.height_inches)


class SeymourSettingsInfo(BaseModel):
    """Validated Seymour settings information."""

    model_config = ConfigDict(extra="forbid")

    protocol_version: str
    motor_count: int
    ratio_count: int
    ratios: list[SeymourRatioInfo]
    raw_response: str
