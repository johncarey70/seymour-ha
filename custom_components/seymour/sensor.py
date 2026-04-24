"""Sensor platform for the Seymour integration."""

from __future__ import annotations

from collections.abc import Callable

from homeassistant.components.sensor import (SensorEntity,
                                             SensorEntityDescription)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, UnitOfLength
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import get_device_info
from .models import SeymourSettingsInfo, SeymourSystemInfo
from .types import SeymourEntryData

ValueFnType  = Callable[[SeymourSystemInfo, SeymourSettingsInfo], str | int | float]

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:arrow-expand",
        key="actual_diagonal",
        name="Actual Screen Diagonal",
        translation_key="actual_diagonal",
        native_unit_of_measurement=UnitOfLength.INCHES,
    ),
    SensorEntityDescription(
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:arrow-expand-horizontal",
        key="actual_width",
        name="Actual Screen Width",
        translation_key="actual_width",
        native_unit_of_measurement=UnitOfLength.INCHES,
    ),
    SensorEntityDescription(
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:arrow-expand-vertical",
        key="actual_height",
        name="Actual Screen Height",
        translation_key="actual_height",
        native_unit_of_measurement=UnitOfLength.INCHES,
    ),
    SensorEntityDescription(
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:engine",
        key="num_motors",
        name="Number of Motors",
        translation_key="num_motors",
    ),
    SensorEntityDescription(
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:aspect-ratio",
        key="num_ratios",
        name="Number of Ratios",
        translation_key="num_ratios",
    ),
    SensorEntityDescription(
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:aspect-ratio",
        key="native_aspect_ratio",
        name="Native Aspect Ratio",
        translation_key="native_aspect_ratio",
    ),
)

VALUE_FNS: dict[str, ValueFnType ] = {
    "actual_diagonal": lambda system_info, settings_info: system_info.diagonal_inches,
    "actual_width": lambda system_info, settings_info: round(system_info.width_inches, 1),
    "actual_height": lambda system_info, settings_info: system_info.height_inches,
    "num_motors": lambda system_info, settings_info: settings_info.motor_count,
    "num_ratios": lambda system_info, settings_info: settings_info.ratio_count,
    "native_aspect_ratio": lambda system_info, settings_info: system_info.aspect_ratio,
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Seymour sensor entities from a config entry."""
    data: SeymourEntryData = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        SeymourDiagnosticSensor(
            system_info=data["system_info"],
            settings_info=data["settings_info"],
            description=description,
        )
        for description in SENSOR_DESCRIPTIONS
    )


class SeymourDiagnosticSensor(SensorEntity):
    """Representation of a Seymour diagnostic sensor."""

    _attr_has_entity_name = True
    entity_description: SensorEntityDescription

    def __init__(
        self,
        system_info: SeymourSystemInfo,
        settings_info: SeymourSettingsInfo,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self._system_info = system_info
        self._settings_info = settings_info
        self.entity_description = description

        self._attr_unique_id = f"{system_info.serial_number}_{description.key}"
        self._attr_device_info = get_device_info(system_info)

    @property
    def native_value(self) -> str | int | float | None:
        """Return the sensor value."""
        key = self.entity_description.key
        if key is None:
            return None
        return VALUE_FNS[key](self._system_info, self._settings_info)
