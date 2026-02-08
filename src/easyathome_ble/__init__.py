"""Easy@Home BLE Library."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

__version__ = "0.1.0"

__all__ = [
    "EasyHomeDevice",
    "TemperatureMeasurement",
    "parse_notification",
]


@dataclass
class TemperatureMeasurement:
    """Temperature measurement from EBT-300 thermometer."""

    temperature: float
    """Temperature in Celsius."""

    timestamp: datetime
    """Time when measurement was taken."""

    is_live: bool
    """True if live measurement, False if historical."""


from .device import EasyHomeDevice  # noqa: E402
from .parser import parse_notification  # noqa: E402
