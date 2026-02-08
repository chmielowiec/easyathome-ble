"""Tests for easyathome_ble parser."""

from datetime import datetime

import pytest

from easyathome_ble import TemperatureMeasurement, parse_notification


def test_parse_live_measurement():
    """Test parsing a live temperature measurement."""
    # Sample notification: live reading of 36.52°C on 2026-02-08 14:30:25
    data = bytes([
        0x00,          # Byte 0: header
        0x01,          # Byte 1: message type (1 = live)
        0x00, 0x00,    # Bytes 2-3: unknown
        0x44, 0x0E,    # Bytes 4-5: temperature (3652 / 100 = 36.52°C) little-endian
        0x00, 0x00,    # Bytes 6-7: unknown
        0x38, 0x00,    # Bytes 8-9: year (56 + 1970 = 2026) little-endian
        0x02,          # Byte 10: month (February)
        0x08,          # Byte 11: day
        0x0E,          # Byte 12: hour (14:00)
        0x1E,          # Byte 13: minute (30)
        0x19,          # Byte 14: second (25)
    ])

    result = parse_notification(data)

    assert result is not None
    assert isinstance(result, TemperatureMeasurement)
    assert result.temperature == 36.52
    assert result.timestamp == datetime(2026, 2, 8, 14, 30, 25)
    assert result.is_live is True


def test_parse_historical_measurement():
    """Test parsing a historical temperature measurement."""
    # Sample notification: historical reading of 37.10°C on 2026-02-07 22:15:00
    data = bytes([
        0x00,          # Byte 0: header
        0x11,          # Byte 1: message type (17 = historical)
        0x00, 0x00,    # Bytes 2-3: unknown
        0x7E, 0x0E,    # Bytes 4-5: temperature (3710 / 100 = 37.10°C) little-endian
        0x00, 0x00,    # Bytes 6-7: unknown
        0x38, 0x00,    # Bytes 8-9: year (56 + 1970 = 2026) little-endian
        0x02,          # Byte 10: month (February)
        0x07,          # Byte 11: day
        0x16,          # Byte 12: hour (22:00)
        0x0F,          # Byte 13: minute (15)
        0x00,          # Byte 14: second (0)
    ])

    result = parse_notification(data)

    assert result is not None
    assert result.temperature == 37.10
    assert result.timestamp == datetime(2026, 2, 7, 22, 15, 0)
    assert result.is_live is False


def test_parse_invalid_short_data():
    """Test that short data returns None."""
    data = bytes([0x00, 0x01, 0x00])

    result = parse_notification(data)

    assert result is None


def test_parse_invalid_message_type():
    """Test that invalid message type returns None."""
    data = bytes([0x00, 0x99] + [0x00] * 13)  # Invalid message type

    result = parse_notification(data)

    assert result is None


def test_parse_invalid_timestamp():
    """Test that invalid timestamp returns None."""
    # Invalid month (13)
    data = bytes([
        0x00, 0x01, 0x00, 0x00,
        0x44, 0x0E,  # Temperature
        0x00, 0x00,
        0x38, 0x00,  # Year 2026
        0x0D,        # Month 13 (invalid)
        0x08, 0x0E, 0x1E, 0x19,
    ])

    result = parse_notification(data)

    assert result is None


def test_parse_edge_case_temperatures():
    """Test parsing edge case temperatures."""
    # Low temperature (0.00°C)
    data_low = bytes([
        0x00, 0x01, 0x00, 0x00,
        0x00, 0x00,  # 0 / 100 = 0.00°C
        0x00, 0x00,
        0x38, 0x00, 0x02, 0x08, 0x0E, 0x1E, 0x19,
    ])

    result_low = parse_notification(data_low)
    assert result_low is not None
    assert result_low.temperature == 0.00

    # High temperature (42.00°C)
    data_high = bytes([
        0x00, 0x01, 0x00, 0x00,
        0x68, 0x10,  # 4200 / 100 = 42.00°C
        0x00, 0x00,
        0x38, 0x00, 0x02, 0x08, 0x0E, 0x1E, 0x19,
    ])

    result_high = parse_notification(data_high)
    assert result_high is not None
    assert result_high.temperature == 42.00
