# Jablotron Volta Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

Control your Jablotron Volta electric boiler from Home Assistant via Modbus TCP.

## Quick Start

### Install via HACS
1. Open HACS → Integrations → Custom repositories
2. Add: `https://github.com/legendik/ha-jablotron-volta`
3. Download, restart Home Assistant

### Configure
1. Settings → Devices & Services → Add Integration
2. Search "Jablotron Volta" and fill in:
   - **IP Address** – address of the boiler
   - **Port** – Modbus TCP port (default `502`)
   - **Device ID** – Modbus unit ID set on the boiler (default `1`)
3. Done! All entities auto-create

Changed the boiler's IP? Use **Reconfigure** on the integration entry; history and entity IDs are kept.

## Features

### Climate Control
- 2 thermostats: Heating Circuit 1 & 2 (off / heat = manual / auto = schedule)
- Auto-detects CH2 availability

### Sensors (30+)
- **Temperatures**: Outdoor (composite/damped), boiler input/return, room temps
- **Energy**: Total consumption, real-time usage
- **System**: Pressure, CPU temp, battery voltage

### Controls
- Regulation modes: Auto, Summer, Winter, Standby
- Equitherm curve settings (slope/offset)
- Temperature limits, optimal start/stop

### Dashboard Included
Import `dashboard.yaml` for complete 7-tab interface:
- Overview, equitherm visualization, settings, diagnostics
- Pre-configured for floor heating optimization

## How It Works
The integration polls the boiler every 30 seconds over one persistent Modbus TCP connection. Changes made from Home Assistant are written immediately and followed by a refresh.

## Known Limitations
- Heating Circuit 2 is detected when the integration loads; reload the integration after enabling CH2 on the boiler.
- Setting the thermostat target temperature writes the circuit's manual setpoint.

## Troubleshooting
- Make sure Modbus TCP is enabled on the boiler and the device ID matches.
- Download diagnostics from the integration's device page (network details are redacted) and attach them to issues.
- For verbose logs, enable debug logging on the integration entry.

## Removal
Settings → Devices & Services → Jablotron Volta → ⋮ → Delete, then remove the repository from HACS.

## Requirements
- Home Assistant 2026.7.0+
- Jablotron Volta with Modbus TCP enabled
- Network connection (port 502)

## Links
- [Issues](https://github.com/legendik/ha-jablotron-volta/issues)
- [Discussions](https://github.com/legendik/ha-jablotron-volta/discussions)
- [Development](AGENTS.md)
