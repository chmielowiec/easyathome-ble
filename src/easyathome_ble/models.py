"""Data models for Easy@Home BLE."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TemperatureMeasurement:
    """Temperature measurement from EBT-300 thermometer."""

    temperature: float
    """Temperature in Celsius."""

    timestamp: datetime
    """Time when measurement was taken."""

    is_live: bool
    """True if live measurement, False if historical."""
