"""Test fixtures for easyathome_ble tests."""

import pytest
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData


@pytest.fixture
def mock_ble_device():
    """Mock BLE device."""
    return BLEDevice(
        address="AA:BB:CC:DD:EE:FF",
        name="EBT-300",
        details={},
        rssi=-60,
    )


@pytest.fixture
def mock_advertisement_data():
    """Mock advertisement data."""
    return AdvertisementData(
        local_name="EBT-300",
        manufacturer_data={},
        service_data={},
        service_uuids=["0000ffe0-0000-1000-8000-00805f9b34fb"],
        rssi=-60,
        platform_data=(),
    )
