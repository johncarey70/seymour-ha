"""Config flow for the Seymour integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_PORT
from homeassistant.core import callback
from homeassistant.helpers import selector
from serial import SerialException
from serial.tools import list_ports

from .const import (CONF_HOME_MOTORS_FIRST, CONF_MOVE_TIME, CONF_SYSTEM_INFO,
                    DEFAULT_HOME_MOTORS_FIRST, DEFAULT_MOVE_TIME, DEFAULT_NAME,
                    DOMAIN)
from .parser import parse_system_info_response
from .serial_controller import SeymourSerialController

_LOG = logging.getLogger(__name__)


def _get_serial_port_options() -> list[selector.SelectOptionDict]:
    """Return serial ports as selector options."""
    options: list[selector.SelectOptionDict] = []

    for port in sorted(list_ports.comports(), key=lambda item: item.device):
        label = port.device
        if port.description and port.description != "n/a":
            label = f"{port.device} - {port.description}"

        options.append(
            selector.SelectOptionDict(
                value=port.device,
                label=label,
            )
        )

    return options


def _read_system_info(port: str) -> dict[str, Any]:
    """Read system info from the Seymour controller."""
    controller = SeymourSerialController(port=port)

    try:
        response = controller.query_command("read_system_info")
        system_info = parse_system_info_response(response)
        return system_info.model_dump(
            exclude={"diagonal_inches", "aspect_ratio"}
        )
    finally:
        controller.disconnect()


class SeymourConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Seymour."""

    VERSION = 1

    def is_matching(self, other_flow: config_entries.ConfigFlow) -> bool:
        """Return True if another flow matches this one."""
        return False

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SeymourOptionsFlow:
        """Create the options flow."""
        return SeymourOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        port_options = await self.hass.async_add_executor_job(_get_serial_port_options)

        if user_input is not None:
            try:
                system_info = await self.hass.async_add_executor_job(
                    _read_system_info,
                    user_input[CONF_PORT],
                )
                _LOG.debug("Validated Seymour system info: %s", system_info)
            except (SerialException, OSError, RuntimeError, ValueError):
                _LOG.exception(
                    "Failed to read Seymour system info from %s",
                    user_input[CONF_PORT],
                )
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={
                        CONF_NAME: user_input[CONF_NAME],
                        CONF_PORT: user_input[CONF_PORT],
                        CONF_SYSTEM_INFO: system_info,
                    },
                    options={
                        CONF_MOVE_TIME: DEFAULT_MOVE_TIME,
                        CONF_HOME_MOTORS_FIRST: DEFAULT_HOME_MOTORS_FIRST,
                    },
                )

        if not port_options:
            errors["base"] = "no_serial_ports"

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_PORT): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=port_options,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )


class SeymourOptionsFlow(config_entries.OptionsFlow):
    """Handle Seymour options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Manage the Seymour options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_move_time = self._config_entry.options.get(
            CONF_MOVE_TIME,
            DEFAULT_MOVE_TIME,
        )
        current_home_motors_first = self._config_entry.options.get(
            CONF_HOME_MOTORS_FIRST,
            DEFAULT_HOME_MOTORS_FIRST,
        )
        data_schema = vol.Schema(
            {
                vol.Required(CONF_MOVE_TIME, default=current_move_time): vol.All(
                    vol.Coerce(float),
                    vol.Range(min=1, max=120),
                ),
                vol.Required(
                    CONF_HOME_MOTORS_FIRST,
                    default=current_home_motors_first,
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
