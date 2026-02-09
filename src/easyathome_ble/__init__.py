"""Easy@Home BLE Library."""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = [
    "EasyHomeDevice",
    "TemperatureMeasurement",
    "parse_notification",
]

from .device import EasyHomeDevice
from .models import TemperatureMeasurement
from .parser import parse_notification
