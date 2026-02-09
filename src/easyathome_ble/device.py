"""Easy@Home BLE Device."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData

    from .models import TemperatureMeasurement


SERVICE_UUID = UUID("0000ffe0-0000-1000-8000-00805f9b34fb")
WRITE_CHAR_UUID = UUID("0000ffe1-0000-1000-8000-00805f9b34fb")
NOTIFY_CHAR_UUID = UUID("0000ffe2-0000-1000-8000-00805f9b34fb")


class EasyHomeDevice:
    """Easy@Home BLE device (EBT-300 Basal Thermometer)."""

    def __init__(
        self,
        address: str,
        notify_callback: Callable[[TemperatureMeasurement], None],
        *,
        ble_device: BLEDevice | None = None,
        advertisement_data: AdvertisementData | None = None,
    ) -> None:
        """Initialize the device."""
        self.address = address
        self._notify_callback = notify_callback
        self._ble_device = ble_device
        self._advertisement_data = advertisement_data
        self._client: BleakClient | None = None
        self.connected: bool = False

    def update_ble_device(
        self,
        ble_device: BLEDevice,
        advertisement_data: AdvertisementData | None = None,
    ) -> None:
        """Update the BLE device."""
        self._ble_device = ble_device
        if advertisement_data:
            self._advertisement_data = advertisement_data

    async def connect(self) -> None:
        """Connect to device and start notifications."""
        if self.connected:
            return

        if not self._ble_device:
            raise BleakError("No BLE device available")

        self._client = await establish_connection(
            BleakClient,
            self._ble_device,
            self.address,
            disconnected_callback=lambda _client: self.device_disconnected_handler(),
        )
        self.connected = True

        # Send time synchronization
        await self._send_time_sync()

        # Send unit synchronization (Celsius)
        await self._send_unit_sync(celsius=True)
        await self._client.start_notify(NOTIFY_CHAR_UUID, self._notification_handler)

    async def disconnect(self) -> None:
        """Disconnect from device."""
        if self._client and self.connected:
            with contextlib.suppress(BleakError):
                await self._client.stop_notify(NOTIFY_CHAR_UUID)
            await self._client.disconnect()
            self.connected = False
            self._client = None

    async def set_datetime(self, dt: datetime) -> None:
        """Set device datetime.

        Args:
            dt: Datetime to set (should be timezone aware)

        Raises:
            BleakError: If device not connected
            ValueError: If datetime is not timezone aware

        """
        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            raise ValueError("timezone aware datetime object expected")

        if not self._client or not self.connected:
            raise BleakError("Device not connected")

        await self._send_time_sync(dt)

    async def set_unit(self, celsius: bool = True) -> None:
        """Set temperature unit.

        Args:
            celsius: True for Celsius, False for Fahrenheit

        Raises:
            BleakError: If device not connected

        """
        if not self._client or not self.connected:
            raise BleakError("Device not connected")

        await self._send_unit_sync(celsius)

    async def _send_time_sync(self, dt: datetime | None = None) -> None:
        """Send time synchronization command.

        Args:
            dt: Datetime to sync, defaults to current time

        """
        if dt is None:
            dt = datetime.now().astimezone()

        if dt.tzinfo is None or dt.tzinfo.utcoffset(dt) is None:
            raise ValueError("timezone aware datetime object expected")

        # Command format: [90, 3, 6, year-1970, month, day, hour, minute, second]
        year_offset = dt.year - 1970
        command = bytes([
            90,                  # Command header
            3,                   # Command type
            6,                   # Length
            year_offset,         # Year since 1970
            dt.month,            # Month (1-12)
            dt.day,              # Day (1-31)
            dt.hour,             # Hour (0-23)
            dt.minute,           # Minute (0-59)
            dt.second,           # Second (0-59)
        ])

        if self._client:
            await self._client.write_gatt_char(WRITE_CHAR_UUID, command, response=True)

    async def _send_unit_sync(self, celsius: bool = True) -> None:
        """Send unit synchronization command.

        Args:
            celsius: True for Celsius, False for Fahrenheit

        """
        # Command format: [90, 6, 6, unit_type, 255, 255, 255, 255, 250]
        # unit_type: 1 = Celsius, 2 = Fahrenheit
        unit_type = 1 if celsius else 2
        command = bytes([90, 6, 6, unit_type, 255, 255, 255, 255, 250])

        if self._client:
            await self._client.write_gatt_char(WRITE_CHAR_UUID, command, response=True)

    def _notification_handler(
        self, characteristic: object, data: bytearray
    ) -> None:
        """Handle notification from device."""

        from . import parse_notification

        measurement = parse_notification(bytes(data))
        if measurement:
            self._notify_callback(measurement)

    def device_disconnected_handler(self, *, notify: bool = True) -> None:
        """Handle device disconnection."""

        self.connected = False
        self._client = None
