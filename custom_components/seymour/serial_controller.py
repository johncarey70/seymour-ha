"""Serial controller for Seymour masking."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass

import serial

from .const import (COMMANDS, DEFAULT_BAUDRATE, DEFAULT_HOME_MOTORS_FIRST,
                    DEFAULT_MOVE_TIME, DEFAULT_TIMEOUT, MOVEMENT_COMMAND_CODES,
                    PROTOCOL_VERSION, START_CHAR, STOP_CHAR)

_LOG = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SeymourControllerOptions:
    """Runtime options for the Seymour serial controller."""

    baudrate: int = DEFAULT_BAUDRATE
    timeout: float = DEFAULT_TIMEOUT
    move_time: float = DEFAULT_MOVE_TIME
    home_motors_first: bool = DEFAULT_HOME_MOTORS_FIRST


class SeymourSerialController:
    """Handle serial communication with the Seymour controller."""

    def __init__(
        self,
        port: str,
        options: SeymourControllerOptions | None = None,
    ) -> None:
        """Initialize the controller."""
        self._port = port
        self._options = options or SeymourControllerOptions()
        self._serial: serial.Serial | None = None
        self._busy_until: float = 0.0
        self._busy_command_code: str | None = None

    @property
    def is_busy(self) -> bool:
        """Return whether the controller is currently busy."""
        if time.monotonic() >= self._busy_until:
            self._busy_until = 0.0
            self._busy_command_code = None
            return False
        return True

    def _ensure_not_busy(self, operation: str, command_code: str | None = None) -> None:
        """Raise if the controller is currently busy."""
        if self.is_busy and command_code != "H":
            _LOG.debug(
                "Ignoring operation on %s because controller is busy: %s",
                self._port,
                operation,
            )
            raise RuntimeError(f"Controller busy, ignoring operation: {operation}")

    def _start_busy_window(
        self,
        command_code: str,
        duration: float | None = None,
    ) -> None:
        """Start the configured busy window."""
        busy_time = duration if duration is not None else self._options.move_time
        self._busy_until = time.monotonic() + busy_time
        self._busy_command_code = command_code

    def connect(self) -> None:
        """Open the serial port."""
        if self._serial and self._serial.is_open:
            return

        _LOG.debug("Opening serial port: %s", self._port)

        self._serial = serial.Serial(
            port=self._port,
            baudrate=self._options.baudrate,
            timeout=self._options.timeout,
            write_timeout=self._options.timeout,
        )

    def disconnect(self) -> None:
        """Close the serial port."""
        if self._serial and self._serial.is_open:
            _LOG.debug("Closing serial port: %s", self._port)
            self._serial.close()

        self._serial = None

    def _ensure_connected(self) -> serial.Serial:
        """Return an open serial object."""
        self.connect()

        if self._serial is None:
            raise RuntimeError("Serial port is not open")

        return self._serial

    @staticmethod
    def _build_command(
        *,
        code: str,
        motor: str | None = None,
        payload: str = "",
    ) -> bytes:
        """Build a Seymour protocol command."""
        command = f"{START_CHAR}{PROTOCOL_VERSION}{code}"
        if motor is not None:
            command += motor
        command += payload
        command += STOP_CHAR
        return command.encode("ascii")

    def _send_raw_command(self, command: bytes) -> None:
        """Send a raw command to the controller."""
        ser = self._ensure_connected()
        _LOG.debug(
            "Sending serial command on %s: %s",
            self._port,
            command.decode("ascii"),
        )
        ser.write(command)
        ser.flush()

    def send_command(self, command_name: str) -> None:
        """Send a named controller command."""
        command_def = COMMANDS.get(command_name)
        if command_def is None:
            raise ValueError(f"Unsupported command: {command_name}")

        self._ensure_not_busy(command_name, command_def.code)

        command = self._build_command(
            code=command_def.code,
            motor=command_def.motor,
            payload=command_def.payload,
        )
        self._send_raw_command(command)

        if command_def.code == "H":
            if self._busy_command_code != "C":
                self._busy_until = 0.0
                self._busy_command_code = None
            return

        if command_def.code in MOVEMENT_COMMAND_CODES:
            self._start_busy_window(command_def.code)

    def query_command(self, command_name: str) -> bytes:
        """Send a named controller query and return raw bytes."""
        command_def = COMMANDS.get(command_name)
        if command_def is None:
            raise ValueError(f"Unsupported command: {command_name}")

        self._ensure_not_busy(command_name, command_def.code)

        command = self._build_command(
            code=command_def.code,
            motor=command_def.motor,
            payload=command_def.payload,
        )

        ser = self._ensure_connected()
        ser.reset_input_buffer()
        _LOG.debug(
            "Sending serial query on %s: %s",
            self._port,
            command.decode("ascii"),
        )
        ser.write(command)
        ser.flush()

        response = ser.read_until(STOP_CHAR.encode("ascii"))

        _LOG.debug(
            "Received serial response on %s: %s",
            self._port,
            response.decode("ascii", errors="replace"),
        )

        if not response:
            raise RuntimeError("No response received from Seymour controller")

        return response

    def move_to_aspect_ratio(self, ratio_id: str) -> None:
        """Move the screen masking to a saved aspect ratio."""
        self._ensure_not_busy(f"move_to_aspect_ratio:{ratio_id}", "M")

        if self._options.home_motors_first:
            total_duration = self._options.move_time * 2
            self._start_busy_window("M", total_duration)

            home_command = self._build_command(code="A", motor="A")
            self._send_raw_command(home_command)

            time.sleep(self._options.move_time)

            move_command = self._build_command(code="M", payload=ratio_id)
            self._send_raw_command(move_command)
            return

        command = self._build_command(code="M", payload=ratio_id)
        self._send_raw_command(command)
        self._start_busy_window("M")
