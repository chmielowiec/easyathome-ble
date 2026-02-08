# easyathome-ble

[![Python Version](https://img.shields.io/pypi/pyversions/easyathome-ble.svg)](https://pypi.python.org/pypi/easyathome-ble)
[![PyPI version](https://badge.fury.io/py/easyathome-ble.svg)](https://badge.fury.io/py/easyathome-ble)

Python library for Easy@Home Bluetooth Low Energy (BLE) devices.

## Supported Devices

- **EBT-300**: Basal body temperature thermometer for fertility tracking

## Features

- Active BLE connection management
- Automatic time synchronization
- Temperature unit configuration (Celsius/Fahrenheit)
- Real-time temperature notifications
- Historical data support
- Timestamped measurements

## Installation

```bash
pip install easyathome-ble
```

## Quick Start

```python
from datetime import datetime
from easyathome_ble import EasyHomeDevice, TemperatureMeasurement

def handle_measurement(measurement: TemperatureMeasurement):
    print(f"Temperature: {measurement.temperature}°C")
    print(f"Time: {measurement.timestamp}")
    print(f"Live: {measurement.is_live}")

# Create device
device = EasyHomeDevice(
    address="AA:BB:CC:DD:EE:FF",
    notify_callback=handle_measurement
)

# Connect and start receiving measurements
await device.connect()

# Set datetime
await device.set_datetime(datetime.now().astimezone())

# Set unit to Celsius
await device.set_unit(celsius=True)

# Disconnect when done
await device.disconnect()
```

## Protocol Details

The EBT-300 uses the following BLE characteristics:

- **Service UUID**: `0000ffe0-0000-1000-8000-00805f9b34fb`
- **Write Characteristic**: `0000ffe1-0000-1000-8000-00805f9b34fb` (commands)
- **Notify Characteristic**: `0000ffe2-0000-1000-8000-00805f9b34fb` (temperature data)

### Commands

**Time Sync**: `[90, 3, 6, year-1970, month, day, hour, minute, second]`

**Unit Sync**: `[90, 6, 6, 1 or 2, 255, 255, 255, 255, 250]` (1=Celsius, 2=Fahrenheit)

### Notifications

Temperature readings are sent as 15-byte notifications:
- Bytes 4-5: Temperature (little-endian, divide by 100)
- Bytes 8-14: Timestamp (year, month, day, hour, minute, second)
- Byte 1: Message type (1=live, 17=historical)

## Development

```bash
# Clone repository
git clone https://github.com/chmielowiec/easyathome-ble.git
cd easyathome-ble

# Install dependencies
poetry install

# Run tests
pytest

# Run linting
ruff check src tests
mypy src
```

## License

MIT License - see LICENSE file for details.

## Credits

Developed by Robert Chmielowiec

Inspired by the thermopro-ble library structure.
