"""Service definitions and registration for Seymour."""

from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN
from .types import SeymourEntryData

_LOGGER = logging.getLogger(__name__)

SERVICE_HOME_MOTORS = "home_motors"
SERVICE_HALT_MOTORS = "halt_motors"
SERVICE_CALIBRATE_MOTORS = "calibrate_motors"
SERVICE_MOVE_MOTORS_TO_SAVED_RATIO = "move_motors_to_saved_ratio"

ATTR_RATIO_ID = "ratio_id"

SERVICE_SCHEMA_SIMPLE = vol.Schema({})

SERVICE_SCHEMA_MOVE_TO_RATIO = vol.Schema(
    {
        vol.Required(ATTR_RATIO_ID): vol.Any(str, int),
    }
)


def _normalize_ratio_id(value: str | int) -> str:
    """Normalize a ratio id to a 3-digit string."""
    if isinstance(value, int):
        if value < 0 or value > 999:
            raise HomeAssistantError(f"Invalid ratio_id: {value}")
        return f"{value:03d}"

    stripped = value.strip()
    if not stripped.isdigit():
        raise HomeAssistantError(f"Invalid ratio_id: {value}")

    number = int(stripped)
    if number < 0 or number > 999:
        raise HomeAssistantError(f"Invalid ratio_id: {value}")

    return f"{number:03d}"


def _get_entry_data(hass: HomeAssistant) -> SeymourEntryData:
    """Return the single configured Seymour entry."""
    entries: dict[str, SeymourEntryData] = hass.data.get(DOMAIN, {})
    if not entries:
        raise HomeAssistantError("No Seymour devices are configured")

    return next(iter(entries.values()))


async def _handle_home_motors(hass: HomeAssistant, _call: ServiceCall) -> None:
    """Handle home_motors service."""
    entry_data = _get_entry_data(hass)

    try:
        await hass.async_add_executor_job(
            entry_data["controller"].send_command,
            "home",
        )
    except RuntimeError:
        _LOGGER.debug(
            "Service %s ignored because controller is busy",
            SERVICE_HOME_MOTORS,
        )


async def _handle_halt_motors(hass: HomeAssistant, _call: ServiceCall) -> None:
    """Handle halt_motors service."""
    entry_data = _get_entry_data(hass)

    try:
        await hass.async_add_executor_job(
            entry_data["controller"].send_command,
            "halt",
        )
    except RuntimeError:
        _LOGGER.debug(
            "Service %s ignored because controller is busy",
            SERVICE_HALT_MOTORS,
        )


async def _handle_calibrate_motors(hass: HomeAssistant, _call: ServiceCall) -> None:
    """Handle calibrate_motors service."""
    entry_data = _get_entry_data(hass)

    try:
        await hass.async_add_executor_job(
            entry_data["controller"].send_command,
            "calibrate",
        )
    except RuntimeError:
        _LOGGER.debug(
            "Service %s ignored because controller is busy",
            SERVICE_CALIBRATE_MOTORS,
        )


async def _handle_move_motors_to_saved_ratio(
    hass: HomeAssistant,
    call: ServiceCall,
) -> None:
    """Handle move_motors_to_saved_ratio service."""
    ratio_id = _normalize_ratio_id(call.data[ATTR_RATIO_ID])
    entry_data = _get_entry_data(hass)

    try:
        await hass.async_add_executor_job(
            entry_data["controller"].move_to_aspect_ratio,
            ratio_id,
        )
    except RuntimeError:
        _LOGGER.debug(
            "Service %s ignored because controller is busy",
            SERVICE_MOVE_MOTORS_TO_SAVED_RATIO,
        )


def register_services(hass: HomeAssistant) -> None:
    """Register Seymour services."""

    async def async_home_motors(call: ServiceCall) -> None:
        await _handle_home_motors(hass, call)

    async def async_halt_motors(call: ServiceCall) -> None:
        await _handle_halt_motors(hass, call)

    async def async_calibrate_motors(call: ServiceCall) -> None:
        await _handle_calibrate_motors(hass, call)

    async def async_move_motors_to_saved_ratio(call: ServiceCall) -> None:
        await _handle_move_motors_to_saved_ratio(hass, call)

    if not hass.services.has_service(DOMAIN, SERVICE_HOME_MOTORS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_HOME_MOTORS,
            async_home_motors,
            schema=SERVICE_SCHEMA_SIMPLE,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_HALT_MOTORS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_HALT_MOTORS,
            async_halt_motors,
            schema=SERVICE_SCHEMA_SIMPLE,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_CALIBRATE_MOTORS):
        hass.services.async_register(
            DOMAIN,
            SERVICE_CALIBRATE_MOTORS,
            async_calibrate_motors,
            schema=SERVICE_SCHEMA_SIMPLE,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_MOVE_MOTORS_TO_SAVED_RATIO):
        hass.services.async_register(
            DOMAIN,
            SERVICE_MOVE_MOTORS_TO_SAVED_RATIO,
            async_move_motors_to_saved_ratio,
            schema=SERVICE_SCHEMA_MOVE_TO_RATIO,
        )


def unregister_services(hass: HomeAssistant) -> None:
    """Unregister Seymour services."""
    for service in (
        SERVICE_HOME_MOTORS,
        SERVICE_HALT_MOTORS,
        SERVICE_CALIBRATE_MOTORS,
        SERVICE_MOVE_MOTORS_TO_SAVED_RATIO,
    ):
        if hass.services.has_service(DOMAIN, service):
            hass.services.async_remove(DOMAIN, service)
