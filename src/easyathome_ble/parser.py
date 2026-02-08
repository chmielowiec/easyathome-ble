"""Parse Easy@Home BLE notifications."""

from __future__ import annotations

import logging
from datetime import datetime

from . import TemperatureMeasurement

_LOGGER = logging.getLogger(__name__)


def parse_notification(data: bytes) -> TemperatureMeasurement | None:
    """Parse temperature notification from EBT-300 thermometer.

    Data format (15 bytes):
    Byte[0]: Header
    Byte[1]: Message type (1 = live, 17 = historical)
    Byte[2-3]: Unknown
    Byte[4-5]: Temperature (little-endian, divide by 100.0)
    Byte[6-7]: Unknown
    Byte[8-9]: Year (little-endian, add 1970)
    Byte[10]: Month (1-12)
    Byte[11]: Day (1-31)
    Byte[12]: Hour (0-23)
    Byte[13]: Minute (0-59)
    Byte[14]: Second (0-59)

    Args:
        data: Raw notification data

    Returns:
        TemperatureMeasurement if valid, None otherwise

    """
    if len(data) < 15:
        _LOGGER.debug("Notification data too short: %d bytes", len(data))
        return None

    message_type = data[1]

    # Only process live (1) or historical (17) measurements
    if message_type not in (1, 17):
        _LOGGER.debug("Unknown message type: %d", message_type)
        return None

    try:
        # Parse temperature (little-endian 16-bit integer, divide by 100)
        temp_raw = (data[5] << 8) | data[4]
        temperature = temp_raw / 100.0

        # Parse timestamp
        year = 1970 + data[8] + (data[9] << 8)
        month = data[10]
        day = data[11]
        hour = data[12]
        minute = data[13]
        second = data[14]

        # Validate timestamp components
        if not (1970 <= year <= 2100):
            _LOGGER.debug("Invalid year: %d", year)
            return None
        if not (1 <= month <= 12):
            _LOGGER.debug("Invalid month: %d", month)
            return None
        if not (1 <= day <= 31):
            _LOGGER.debug("Invalid day: %d", day)
            return None
        if not (0 <= hour <= 23):
            _LOGGER.debug("Invalid hour: %d", hour)
            return None
        if not (0 <= minute <= 59):
            _LOGGER.debug("Invalid minute: %d", minute)
            return None
        if not (0 <= second <= 59):
            _LOGGER.debug("Invalid second: %d", second)
            return None

        timestamp = datetime(year, month, day, hour, minute, second)
        is_live = message_type == 1

        return TemperatureMeasurement(
            temperature=temperature,
            timestamp=timestamp,
            is_live=is_live,
        )

    except (ValueError, IndexError) as ex:
        _LOGGER.debug("Failed to parse notification: %s", ex)
        return None
