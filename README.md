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
2. Search "Jablotron Volta" → Enter boiler IP address
3. Done! All entities auto-create

## Features

### Climate Control
- 3 thermostats: Hot water, Heating Circuit 1 & 2
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

## Requirements
- Home Assistant 2025.9.0+
- Jablotron Volta with Modbus TCP enabled
- Network connection (port 502)

## Links
- [Issues](https://github.com/legendik/ha-jablotron-volta/issues)
- [Discussions](https://github.com/legendik/ha-jablotron-volta/discussions)
- [Development](AGENTS.md)