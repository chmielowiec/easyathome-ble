"""Easy@Home BLE Device."""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

if TYPE_CHECKING:
    from bleak.backends.device import BLEDevice
    from bleak.backends.scanner import AdvertisementData

    from .models import TemperatureMeasurement


SERVICE_UUID = UUID("00001809-0000-1000-8000-00805f9b34fb")
NOTIFY_CHAR_UUID = UUID("00002a1c-0000-1000-8000-00805f9b34fb")
CURRENT_TIME_SERVICE_UUID = UUID("00001805-0000-1000-8000-00805f9b34fb")
CURRENT_TIME_CHAR_UUID = UUID("00002a2b-0000-1000-8000-00805f9b34fb")


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

        await self._maybe_sync_time()
        await self._client.start_notify(NOTIFY_CHAR_UUID, self._notification_handler)

    async def disconnect(self) -> None:
        """Disconnect from device."""
        if self._client and self.connected:
            with contextlib.suppress(BleakError):
                await self._client.stop_notify(NOTIFY_CHAR_UUID)
            await self._client.disconnect()
            self.connected = False
            self._client = None

    async def _maybe_sync_time(self) -> None:
        """Best-effort time synchronization using Current Time Service if present."""

        if not self._client:
            return

        try:
            services = await self._client.get_services()
            if not services.get_service(CURRENT_TIME_SERVICE_UUID):
                return

            if not services.get_characteristic(CURRENT_TIME_CHAR_UUID):
                return

            now = datetime.now(tz=timezone.utc).astimezone()
            payload = (
                now.year.to_bytes(2, "little")
                + bytes(
                    [
                        now.month,
                        now.day,
                        now.hour,
                        now.minute,
                        now.second,
                        now.isoweekday(),
                        0,  # fractions256
                    ]
                )
            )

            await self._client.write_gatt_char(
                CURRENT_TIME_CHAR_UUID, payload, response=True
            )
        except Exception:
            # Device may not support CTS write; ignore failures
            return

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
