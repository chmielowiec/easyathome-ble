"""Tests for easyathome_ble device."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bleak.exc import BleakError

from easyathome_ble import EasyHomeDevice, TemperatureMeasurement
from easyathome_ble.device import CURRENT_TIME_CHAR_UUID


@pytest.fixture
def services_with_cts():
    """Mock services exposing Current Time Service characteristic."""

    services = MagicMock()
    services.get_service.return_value = True
    services.get_characteristic.return_value = True
    return services


@pytest.fixture
def services_without_cts():
    """Mock services without Current Time Service."""

    services = MagicMock()
    services.get_service.return_value = None
    services.get_characteristic.return_value = None
    return services


def test_device_init():
    """Test device initialization."""
    callback = MagicMock()
    device = EasyHomeDevice(address="AA:BB:CC:DD:EE:FF", notify_callback=callback)

    assert device.address == "AA:BB:CC:DD:EE:FF"
    assert device.connected is False


@pytest.mark.asyncio
async def test_device_connect(mock_ble_device, services_with_cts):
    """Test device connection."""
    callback = MagicMock()
    device = EasyHomeDevice(
        address="AA:BB:CC:DD:EE:FF",
        notify_callback=callback,
        ble_device=mock_ble_device,
    )

    with patch("easyathome_ble.device.establish_connection") as mock_establish:
        mock_client = AsyncMock()
        mock_client.get_services.return_value = services_with_cts
        mock_establish.return_value = mock_client

        await device.connect()

        assert device.connected is True
        mock_establish.assert_called_once()
        mock_client.get_services.assert_called_once()
        mock_client.write_gatt_char.assert_called_once()
        args, kwargs = mock_client.write_gatt_char.call_args
        assert args[0] == CURRENT_TIME_CHAR_UUID
        assert len(args[1]) == 9  # CTS payload length
        mock_client.start_notify.assert_called_once()


@pytest.mark.asyncio
async def test_device_connect_no_cts(mock_ble_device, services_without_cts):
    """Connect without CTS; no time sync attempted."""

    device = EasyHomeDevice(
        address="AA:BB:CC:DD:EE:FF",
        notify_callback=lambda _: None,
        ble_device=mock_ble_device,
    )

    with patch("easyathome_ble.device.establish_connection") as mock_establish:
        mock_client = AsyncMock()
        mock_client.get_services.return_value = services_without_cts
        mock_establish.return_value = mock_client

        await device.connect()

        mock_client.write_gatt_char.assert_not_called()


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
def test_notification_handler():
    """Test notification handler processes data correctly."""
    received_measurements = []

    def callback(measurement: TemperatureMeasurement):
        received_measurements.append(measurement)

    device = EasyHomeDevice(address="AA:BB:CC:DD:EE:FF", notify_callback=callback)

    # Sample notification data: 37.55°C with timestamp
    notification_data = bytes(
        [
            0x02,
            0xAB,
            0x0E,
            0x00,
            0xFE,
            0xE8,
            0x07,
            0x02,
            0x09,
            0x0E,
            0x1E,
            0x00,
        ]
    )

    device._notification_handler(0, notification_data)

    assert len(received_measurements) == 1
    measurement = received_measurements[0]
    assert measurement.temperature == 37.55
    assert measurement.is_live is True


def test_update_ble_device(mock_ble_device, mock_advertisement_data):
    """Test updating BLE device."""
    callback = MagicMock()
    device = EasyHomeDevice(address="AA:BB:CC:DD:EE:FF", notify_callback=callback)

    device.update_ble_device(mock_ble_device, mock_advertisement_data)

    assert device._ble_device == mock_ble_device
    assert device._advertisement_data == mock_advertisement_data
