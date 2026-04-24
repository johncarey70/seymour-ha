"""Protocol response parsers for the Seymour integration."""

from __future__ import annotations

from .models import SeymourRatioInfo, SeymourSettingsInfo, SeymourSystemInfo


def parse_system_info_response(response: bytes) -> SeymourSystemInfo:
    """Parse the Seymour system info response into a validated model."""
    text = response.decode("ascii", errors="strict")

    if not text.startswith("[01") or not text.endswith("]"):
        raise ValueError(f"Invalid system info response: {text!r}")

    protocol_version = text[1:3]
    payload = text[3:-1]

    if len(payload) < 45:
        raise ValueError(f"System info response too short: {text!r}")

    parsed = {
        "protocol_version": protocol_version,
        "screen_model": payload[0:20].rstrip(),
        "width_inches": payload[20:26].strip(),
        "height_inches": payload[26:32].strip(),
        "serial_number": payload[32:45].rstrip(),
        "mask_ids": payload[45:].strip(),
        "raw_response": text,
    }

    return SeymourSystemInfo.model_validate(parsed)


def _parse_ratio_record(chunk: str, motor_count: int) -> SeymourRatioInfo:
    """Parse one ratio record from the settings response."""
    pos = 0

    ratio_id = chunk[pos : pos + 3]
    pos += 3

    label = chunk[pos : pos + 8].rstrip()
    pos += 8

    width_text = chunk[pos : pos + 6].strip()
    pos += 6

    height_text = chunk[pos : pos + 6].strip()
    pos += 6

    default_motor_positions: list[float] = []
    for _ in range(motor_count):
        default_motor_positions.append(float(chunk[pos : pos + 4]))
        pos += 4

    motor_position_adjustments: list[float] = []
    for _ in range(motor_count):
        motor_position_adjustments.append(float(chunk[pos : pos + 4]))
        pos += 4

    return SeymourRatioInfo.model_validate(
        {
            "ratio_id": ratio_id,
            "label": label,
            "width_inches": width_text,
            "height_inches": height_text,
            "default_motor_positions": default_motor_positions,
            "motor_position_adjustments": motor_position_adjustments,
        }
    )


def parse_settings_info_response(response: bytes) -> SeymourSettingsInfo:
    """Parse the Seymour settings info response into a validated model."""
    text = response.decode("ascii", errors="strict")

    if not text.startswith("[01") or not text.endswith("]"):
        raise ValueError(f"Invalid settings info response: {text!r}")

    protocol_version = text[1:3]
    payload = text[3:-1]

    if len(payload) < 3:
        raise ValueError(f"Settings info response too short: {text!r}")

    motor_count = int(payload[0:1])
    ratio_count = int(payload[1:3])
    record_len = 3 + 8 + 6 + 6 + (4 * motor_count) + (4 * motor_count)

    ratios: list[SeymourRatioInfo] = []
    cursor = 3

    for _ in range(ratio_count):
        chunk = payload[cursor : cursor + record_len]
        if len(chunk) != record_len:
            raise ValueError(f"Incomplete ratio record in settings response: {text!r}")

        ratios.append(_parse_ratio_record(chunk, motor_count))
        cursor += record_len

    return SeymourSettingsInfo.model_validate(
        {
            "protocol_version": protocol_version,
            "motor_count": motor_count,
            "ratio_count": ratio_count,
            "ratios": ratios,
            "raw_response": text,
        }
    )
