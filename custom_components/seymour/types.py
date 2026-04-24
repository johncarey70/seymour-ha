"""Typed runtime data structures for the Seymour integration."""

from __future__ import annotations

from typing import Any, TypedDict

from .models import SeymourSettingsInfo, SeymourSystemInfo
from .serial_controller import SeymourSerialController


class SeymourConfigData(TypedDict):
    """Stored config-entry data for Seymour."""

    name: str
    port: str
    system_info: dict[str, Any]


class SeymourEntryData(TypedDict):
    """Runtime data stored for a Seymour config entry."""

    config: SeymourConfigData
    controller: SeymourSerialController
    system_info: SeymourSystemInfo
    settings_info: SeymourSettingsInfo
