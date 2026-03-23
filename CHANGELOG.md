# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] - 2026-03-23

### Fixed
- Handle BLE command writes using the characteristic-supported write mode
- Retry command writes without response when a device rejects
	write-with-response with ATT error 0x06 (`Request not supported`)

### Tests
- Add a regression test for command-write fallback on unsupported requests

## [0.2.1] - 2026-02-09

### Added
- Improve project metadata and package layout
- Update dependencies and internal structure

## [0.1.0] - 2026-02-08

### Added
- Initial release
- Support for Easy@Home EBT-300 basal body temperature thermometer
- Active BLE connection management with bleak-retry-connector
- Temperature measurement parsing (live and historical)
- Time synchronization command
- Temperature unit configuration (Celsius/Fahrenheit)
- GATT notification support for real-time measurements
- Comprehensive test suite with >95% coverage
- Full type hint support (PEP 561 compliant)

### Features
- Parse 15-byte notification protocol
- Timestamped measurements
- Distinguish between live and historical readings
- Automatic reconnection support via bleak-retry-connector
- Async/await API

[0.2.2]: https://github.com/chmielowiec/easyathome-ble/releases/tag/v0.2.2
[0.2.1]: https://github.com/chmielowiec/easyathome-ble/releases/tag/v0.2.1
[0.1.0]: https://github.com/chmielowiec/easyathome-ble/releases/tag/v0.1.0
