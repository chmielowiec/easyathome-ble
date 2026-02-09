"""Tests for easyathome_ble parser."""

from datetime import UTC, datetime

from easyathome_ble import TemperatureMeasurement, parse_notification


def test_parse_measurement_with_timestamp():
    """Test parsing a temperature measurement with timestamp in Celsius."""

    # Flags: 0b00000010 -> Celsius, timestamp present
    # Temp: mantissa=3755, exponent=-2 -> 37.55°C
    data = bytes(
        [
            0x02,
            0xAB,
            0x0E,
            0x00,
            0xFE,
            0xE8,
            0x07,  # 2024 LE
            0x02,  # month
            0x09,  # day
            0x0E,  # hour
            0x1E,  # minute
            0x00,  # second
        ]
    )

    result = parse_notification(data)

    assert result is not None
    assert isinstance(result, TemperatureMeasurement)
    assert result.temperature == 37.55
    assert result.timestamp == datetime(2024, 2, 9, 14, 30, tzinfo=UTC)
    assert result.is_live is True


def test_parse_measurement_fahrenheit():
    """Test parsing a Fahrenheit value converted to Celsius."""

    # Flags: 0b00000001 -> Fahrenheit, no timestamp
    # Temp: 99.5°F (mantissa=9950, exponent=-2)
    data = bytes(
        [
            0x01,
            0xDE,
            0x26,
            0x00,
            0xFE,
        ]
    )

    result = parse_notification(data)

    assert result is not None
    # 99.5°F = 37.5°C
    assert result.temperature == 37.5
    assert result.is_live is True


def test_parse_invalid_short_data():
    """Test that short data returns None."""
    data = bytes([0x00, 0x01, 0x00])

    result = parse_notification(data)

    assert result is None


def test_parse_invalid_timestamp():
    """Test that invalid timestamp returns None."""
    # Timestamp flag set but payload too short
    data = bytes(
        [
            0x02,
            0xAB,
            0x0E,
            0x00,
            0xFE,
            0xE8,
            0x07,
            0x13,  # Invalid month 19
        ]
    )

    result = parse_notification(data)

    assert result is None


def test_parse_edge_case_temperatures():
    """Test parsing edge case temperatures."""
    # Low temperature (0.00°C)
    data_low = bytes(
        [
            0x00,
            0x00,
            0x00,
            0x00,
            0x00,
        ]
    )

    result_low = parse_notification(data_low)
    assert result_low is not None
    assert result_low.temperature == 0.00

    # High temperature (42.00°C)
    data_high = bytes(
        [
            0x00,
            0xA8,
            0x19,
            0x00,
            0xFE,  # 0x19A8 mantissa=6568 -> 65.68°C
        ]
    )

    result_high = parse_notification(data_high)
    assert result_high is not None
    assert result_high.temperature == 42.00
