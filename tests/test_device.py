"""Tests for easyathome_ble device."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bleak.exc import BleakError

from easyathome_ble import EasyHomeDevice, TemperatureMeasurement


@pytest.mark.asyncio
async def test_device_init():
    """Test device initialization."""
    callback = MagicMock()
    device = EasyHomeDevice(address="AA:BB:CC:DD:EE:FF", notify_callback=callback)

    assert device.address == "AA:BB:CC:DD:EE:FF"
    assert device.connected is False


@pytest.mark.asyncio
async def test_device_connect(mock_ble_device):
    """Test device connection."""
    callback = MagicMock()
    device = EasyHomeDevice(
        address="AA:BB:CC:DD:EE:FF",
        notify_callback=callback,
        ble_device=mock_ble_device,
    )

    with patch("easyathome_ble.device.establish_connection") as mock_establish:
        mock_client = AsyncMock()
        mock_establish.return_value = mock_client

        await device.connect()

        assert device.connected is True
        mock_establish.assert_called_once()
        # Verify time sync was sent (2 write calls: time + unit)
        assert mock_client.write_gatt_char.call_count == 2
        # Verify notifications started
        mock_client.start_notify.assert_called_once()


@pytest.mark.asyncio
async def test_device_connect_no_ble_device():
    """Test connection fails without BLE device."""
    callback = MagicMock()
    device = EasyHomeDevice(address="AA:BB:CC:DD:EE:FF", notify_callback=callback)

    with pytest.raises(BleakError, match="No BLE device available"):
        await device.connect()


@pytest.mark.asyncio
async def test_device_disconnect(mock_ble_device):
    """Test device disconnection."""
    callback = MagicMock()
    device = EasyHomeDevice(
        address="AA:BB:CC:DD:EE:FF",
        notify_callback=callback,
        ble_device=mock_ble_device,
    )

    with patch("easyathome_ble.device.establish_connection") as mock_establish:
        mock_client = AsyncMock()
        mock_establish.return_value = mock_client
        device._client = mock_client
        device.connected = True

        await device.disconnect()

        assert device.connected is False
        mock_client.stop_notify.assert_called_once()
        mock_client.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_set_datetime(mock_ble_device):
    """Test setting device datetime."""
    callback = MagicMock()
    device = EasyHomeDevice(
        address="AA:BB:CC:DD:EE:FF",
        notify_callback=callback,
        ble_device=mock_ble_device,
    )

    mock_client = AsyncMock()
    device._client = mock_client
    device.connected = True

    test_dt = datetime(2026, 2, 8, 14, 30, 25, tzinfo=UTC)
    await device.set_datetime(test_dt)

    # Verify time sync command was sent
    mock_client.write_gatt_char.assert_called_once()
    call_args = mock_client.write_gatt_char.call_args
    command = call_args[0][1]

    assert command[0] == 90  # Header
    assert command[1] == 3   # Command type
    assert command[2] == 6   # Length
    assert command[3] == 56  # Year (2026 - 1970)
    assert command[4] == 2   # Month
    assert command[5] == 8   # Day
    assert command[6] == 14  # Hour
    assert command[7] == 30  # Minute
    assert command[8] == 25  # Second


@pytest.mark.asyncio
async def test_set_datetime_no_timezone():
    """Test setting datetime without timezone raises ValueError."""
    callback = MagicMock()
    device = EasyHomeDevice(address="AA:BB:CC:DD:EE:FF", notify_callback=callback)

    mock_client = AsyncMock()
    device._client = mock_client
    device.connected = True

    test_dt = datetime(2026, 2, 8, 14, 30, 25)  # No timezone

    with pytest.raises(ValueError, match="timezone aware"):
        await device.set_datetime(test_dt)


@pytest.mark.asyncio
async def test_set_unit_celsius(mock_ble_device):
    """Test setting unit to Celsius."""
    callback = MagicMock()
    device = EasyHomeDevice(
        address="AA:BB:CC:DD:EE:FF",
        notify_callback=callback,
        ble_device=mock_ble_device,
    )

    mock_client = AsyncMock()
    device._client = mock_client
    device.connected = True

    await device.set_unit(celsius=True)

    mock_client.write_gatt_char.assert_called_once()
    call_args = mock_client.write_gatt_char.call_args
    command = call_args[0][1]

    expected = bytes([90, 6, 6, 1, 255, 255, 255, 255, 250])
    assert command == expected


@pytest.mark.asyncio
async def test_set_unit_fahrenheit(mock_ble_device):
    """Test setting unit to Fahrenheit."""
    callback = MagicMock()
    device = EasyHomeDevice(
        address="AA:BB:CC:DD:EE:FF",
        notify_callback=callback,
        ble_device=mock_ble_device,
    )

    mock_client = AsyncMock()
    device._client = mock_client
    device.connected = True

    await device.set_unit(celsius=False)

    call_args = mock_client.write_gatt_char.call_args
    command = call_args[0][1]

    expected = bytes([90, 6, 6, 2, 255, 255, 255, 255, 250])
    assert command == expected


@pytest.mark.asyncio
async def test_notification_handler():
    """Test notification handler processes data correctly."""
    received_measurements = []

    def callback(measurement: TemperatureMeasurement):
        received_measurements.append(measurement)

    device = EasyHomeDevice(address="AA:BB:CC:DD:EE:FF", notify_callback=callback)

    # Sample notification data: 36.52°C on 2026-02-08 14:30:25
    notification_data = bytes([
        0x00, 0x01, 0x00, 0x00,
        0x44, 0x0E,  # 36.52°C
        0x00, 0x00,
        0x38, 0x00,  # 2026
        0x02, 0x08, 0x0E, 0x1E, 0x19,
    ])

    device._notification_handler(0, notification_data)

    assert len(received_measurements) == 1
    measurement = received_measurements[0]
    assert measurement.temperature == 36.52
    assert measurement.is_live is True


@pytest.mark.asyncio
async def test_update_ble_device(mock_ble_device, mock_advertisement_data):
    """Test updating BLE device."""
    callback = MagicMock()
    device = EasyHomeDevice(address="AA:BB:CC:DD:EE:FF", notify_callback=callback)

    device.update_ble_device(mock_ble_device, mock_advertisement_data)

    assert device._ble_device == mock_ble_device
    assert device._advertisement_data == mock_advertisement_data
