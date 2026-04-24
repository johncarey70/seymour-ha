"""Button platform for the Seymour integration."""

from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import get_device_info
from .models import SeymourSystemInfo
from .serial_controller import SeymourSerialController
from .types import SeymourEntryData

_LOG = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Seymour button entities from a config entry."""
    data: SeymourEntryData = hass.data[DOMAIN][entry.entry_id]
    controller = data["controller"]
    system_info = data["system_info"]

    async_add_entities(
        [
            SeymourCommandButton(system_info, controller, "home", "Home"),
            SeymourCommandButton(system_info, controller, "halt", "Halt"),
            SeymourCommandButton(system_info, controller, "calibrate", "Calibrate"),
        ]
    )


class SeymourCommandButton(ButtonEntity):
    """Representation of a Seymour command button."""

    _attr_has_entity_name = True

    def __init__(
        self,
        system_info: SeymourSystemInfo,
        controller: SeymourSerialController,
        command_name: str,
        name: str,
    ) -> None:
        """Initialize the button."""
        self._controller = controller
        self._command_name = command_name
        self._attr_name = name
        self._attr_unique_id = f"{system_info.serial_number}_{command_name}"
        self._attr_translation_key = command_name
        self._attr_device_info = get_device_info(system_info)

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOG.debug("%s button pressed", self._command_name)
        try:
            await self.hass.async_add_executor_job(
                self._controller.send_command,
                self._command_name,
            )
        except RuntimeError:
            _LOG.debug(
                "%s button ignored because controller is busy",
                self._command_name,
            )
            return

        _LOG.debug("%s button command completed", self._command_name)

    def press(self) -> None:
        """Handle the button press."""
        raise NotImplementedError
