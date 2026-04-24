"""Shared entity helpers for the Seymour integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .models import SeymourSystemInfo

MANUFACTURER = "Seymour-Screen Excellence"
SEYMOUR_NAME = "Seymour Screen Masking"


def get_device_info(system_info: SeymourSystemInfo) -> DeviceInfo:
    """Return shared device info for Seymour entities."""
    return DeviceInfo(
        identifiers={(DOMAIN, system_info.serial_number)},
        hw_version=system_info.protocol_version,
        name=SEYMOUR_NAME,
        manufacturer=MANUFACTURER,
        model=system_info.screen_model,
        serial_number=system_info.serial_number,
        suggested_area="Theater",
        configuration_url="https://www.seymourscreenexcellence.com/screens.php",
    )
