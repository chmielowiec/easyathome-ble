"""Parse Easy@Home BLE notifications."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from . import TemperatureMeasurement

_LOGGER = logging.getLogger(__name__)


def _decode_ieee_11073_float(raw: bytes) -> float:
    """Decode IEEE-11073 32-bit float used by the Health Thermometer spec."""

    if len(raw) != 4:
        raise ValueError("IEEE-11073 float must be 4 bytes")

    mantissa = int.from_bytes(raw[:3], "little", signed=True)
    exponent_raw = raw[3]
    exponent = exponent_raw - 0x100 if exponent_raw & 0x80 else exponent_raw
    return mantissa * (10**exponent)


def parse_notification(data: bytes) -> TemperatureMeasurement | None:
    """Parse Health Thermometer measurement notifications.

    The Yuncheng A33 advertises the standard Health Thermometer service
    (0x1809) and sends temperature measurements on the Temperature
    Measurement characteristic (0x2A1C). The payload matches the Bluetooth
    SIG specification:

    - Byte 0: Flags
      bit 0 -> 0 = Celsius, 1 = Fahrenheit
      bit 1 -> Timestamp present
      bit 2 -> Temperature type present (ignored)
    - Bytes 1-4: IEEE-11073 FLOAT temperature value
    - Bytes 5-11: Optional timestamp (year LE, month, day, hour, minute, second)
    - Remaining bytes: Optional temperature type (ignored)
    """

    if len(data) < 5:
        _LOGGER.debug("Notification data too short: %d bytes", len(data))
        return None

    flags = data[0]
    fahrenheit = bool(flags & 0x01)
    timestamp_present = bool(flags & 0x02)

    try:
        temperature_c = _decode_ieee_11073_float(data[1:5])
    except ValueError as ex:
        _LOGGER.debug("Invalid temperature payload: %s", ex)
        return None

    if fahrenheit:
        temperature_c = (temperature_c - 32.0) * 5.0 / 9.0

    offset = 5
    timestamp = None

    if timestamp_present:
        if len(data) < offset + 7:
            _LOGGER.debug(
                "Timestamp flag set but payload too short: %d bytes", len(data)
            )
            return None

        year = int.from_bytes(data[offset : offset + 2], "little")
        month, day, hour, minute, second = data[offset + 2 : offset + 7]

        try:
            timestamp = datetime(
                year, month, day, hour, minute, second, tzinfo=timezone.utc
            )
        except ValueError as ex:
            _LOGGER.debug("Invalid timestamp in payload: %s", ex)
            return None

    if timestamp is None:
        timestamp = datetime.now(tz=timezone.utc)

    return TemperatureMeasurement(
        temperature=round(temperature_c, 2),
        timestamp=timestamp,
        is_live=True,
    )
