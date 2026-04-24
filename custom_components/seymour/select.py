"""Select platform for the Seymour integration."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .entity import get_device_info
from .models import SeymourSettingsInfo, SeymourSystemInfo
from .serial_controller import SeymourSerialController
from .types import SeymourEntryData

_LOG = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Seymour select entities from a config entry."""
    data: SeymourEntryData = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            SeymourMaskSelect(
                data["controller"],
                data["system_info"],
                data["settings_info"],
            )
        ]
    )


class SeymourMaskSelect(SelectEntity):
    """Representation of the Seymour mask ratio select."""

    _attr_has_entity_name = True

    def __init__(
        self,
        controller: SeymourSerialController,
        system_info: SeymourSystemInfo,
        settings_info: SeymourSettingsInfo,
    ) -> None:
        """Initialize the select entity."""
        self._controller = controller
        self._option_to_ratio_id: dict[str, str] = {}

        self._attr_unique_id = f"{system_info.serial_number}_mask_ratio"
        self._attr_translation_key = "mask_ratio"
        self._attr_device_info = get_device_info(system_info)

        options: list[str] = []
        for ratio in settings_info.ratios:
            option = ratio.label.strip() or ratio.aspect_ratio

            if option in self._option_to_ratio_id:
                option = f"{option} ({ratio.ratio_id})"

            self._option_to_ratio_id[option] = ratio.ratio_id
            options.append(option)

        self._attr_options = options
        self._attr_current_option = options[0] if options else None

        _LOG.debug(
            "Initialized mask select with options=%s",
            self._attr_options,
        )

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        return self._attr_current_option

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if option not in self.options:
            return

        ratio_id = self._option_to_ratio_id[option]

        _LOG.debug(
            "Select option requested: option=%s ratio_id=%s",
            option,
            ratio_id,
        )
        try:
            await self.hass.async_add_executor_job(
                self._controller.move_to_aspect_ratio,
                ratio_id,
            )
        except RuntimeError:
            _LOG.debug(
                "Select option ignored because controller is busy: option=%s ratio_id=%s",
                option,
                ratio_id,
            )
            return

        _LOG.debug(
            "Select option completed: option=%s ratio_id=%s",
            option,
            ratio_id,
        )

        self._attr_current_option = option
        self.async_write_ha_state()

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        raise NotImplementedError
