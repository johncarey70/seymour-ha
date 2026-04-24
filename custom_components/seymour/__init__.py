"""The Seymour integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.loader import async_get_integration

from .const import (
    CONF_HOME_MOTORS_FIRST,
    CONF_MOVE_TIME,
    CONF_SYSTEM_INFO,
    DEFAULT_HOME_MOTORS_FIRST,
    DEFAULT_MOVE_TIME,
    DEFAULT_NAME,
    DOMAIN,
    STARTUP_MESSAGE,
)
from .models import SeymourSystemInfo
from .parser import parse_settings_info_response
from .serial_controller import SeymourControllerOptions, SeymourSerialController
from .services import register_services, unregister_services
from .types import SeymourConfigData, SeymourEntryData

PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.SELECT, Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)


async def async_setup(_hass: HomeAssistant, _config: dict) -> bool:
    """Set up the Seymour component."""
    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Seymour from a config entry."""
    integration = await async_get_integration(hass, DOMAIN)
    _LOGGER.info(STARTUP_MESSAGE, DEFAULT_NAME, integration.version)

    hass.data.setdefault(DOMAIN, {})
    register_services(hass)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    controller = SeymourSerialController(
        port=entry.data[CONF_PORT],
        options=SeymourControllerOptions(
            move_time=entry.options.get(CONF_MOVE_TIME, DEFAULT_MOVE_TIME),
            home_motors_first=entry.options.get(
                CONF_HOME_MOTORS_FIRST,
                DEFAULT_HOME_MOTORS_FIRST,
            ),
        ),
    )

    try:
        raw_system_info = dict(entry.data[CONF_SYSTEM_INFO])
        raw_system_info.pop("diagonal_inches", None)
        raw_system_info.pop("aspect_ratio", None)

        system_info = SeymourSystemInfo.model_validate(raw_system_info)

        settings_response = await hass.async_add_executor_job(
            controller.query_command,
            "read_settings_info",
        )
        settings_info = parse_settings_info_response(settings_response)
    except (RuntimeError, OSError):
        await hass.async_add_executor_job(controller.disconnect)
        raise ConfigEntryNotReady(
            "Unable to communicate with Seymour controller"
        ) from None

    config_data: SeymourConfigData = {
        "name": entry.data[CONF_NAME],
        "port": entry.data[CONF_PORT],
        "system_info": dict(entry.data[CONF_SYSTEM_INFO]),
    }

    entry_data: SeymourEntryData = {
        "config": config_data,
        "controller": controller,
        "system_info": system_info,
        "settings_info": settings_info,
    }
    hass.data[DOMAIN][entry.entry_id] = entry_data

    _LOGGER.debug("Validated Seymour system info: %s", system_info.model_dump())
    _LOGGER.debug("Validated Seymour settings info: %s", settings_info.model_dump())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Seymour config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if entry_data is not None:
            await hass.async_add_executor_job(entry_data["controller"].disconnect)

        if not hass.data[DOMAIN]:
            unregister_services(hass)
            hass.data.pop(DOMAIN, None)

    return unload_ok
