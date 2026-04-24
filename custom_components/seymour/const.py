"""Constants for the Seymour integration."""

from __future__ import annotations

from dataclasses import dataclass

DOMAIN = "seymour"
DEFAULT_NAME = "Seymour Screen Masking"
DEFAULT_BAUDRATE = 115200
DEFAULT_TIMEOUT = 5
DEFAULT_MOVE_TIME = 10.0

CONF_SYSTEM_INFO = "system_info"
CONF_MOVE_TIME = "move_time"

CONF_HOME_MOTORS_FIRST = "home_motors_first"
DEFAULT_HOME_MOTORS_FIRST = False

START_CHAR = "["
PROTOCOL_VERSION = "01"
STOP_CHAR = "]"


@dataclass(frozen=True, slots=True)
class SeymourCommand:
    """Command definition for the Seymour protocol."""

    code: str
    motor: str | None = None
    payload: str = ""


COMMANDS: dict[str, SeymourCommand] = {
    "halt": SeymourCommand(code="H", motor="A"),
    "home": SeymourCommand(code="A", motor="A"),
    "calibrate": SeymourCommand(code="C", motor="A"),
    "read_system_info": SeymourCommand(code="Y"),
    "read_settings_info": SeymourCommand(code="R"),
}

MOVEMENT_COMMAND_CODES = frozenset({"O", "I", "M", "A", "C"})

STARTUP_MESSAGE = """
-------------------------------------------------------------------
%s
Integration Version: %s
This is a custom integration!
If you have any issues with this you need to open an issue here:
https://github.com/johncarey70/seymour-ha/issues
-------------------------------------------------------------------
"""
