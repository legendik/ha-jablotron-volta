# Agent Guidelines for Jablotron Volta Integration

This document provides coding guidelines and commands for AI agents working on this Home Assistant custom integration.

## Project Overview

**Jablotron Volta** is a Home Assistant custom integration for controlling Jablotron Volta electric boilers via Modbus TCP. The integration provides climate control, sensors, configuration entities, and energy monitoring.

- **Type**: Home Assistant Custom Integration (HACS)
- **Protocol**: Modbus TCP
- **Language**: Python 3.11+
- **Framework**: Home Assistant Core API
- **Main Dependencies**: `pymodbus>=3.6,<4`, `homeassistant>=2025.9.0`

## Build/Lint/Test Commands

### Setup Development Environment
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Or install specific packages
pip install pymodbus==3.11.2 homeassistant>=2025.9.0 pytest pytest-asyncio ruff
```

### Code Quality
```bash
# Run Ruff linter (checks code style, imports, errors)
ruff check custom_components/jablotron_volta/

# Auto-fix issues
ruff check --fix custom_components/jablotron_volta/

# Format code
ruff format custom_components/jablotron_volta/
```

### Testing
```bash
# Run all tests (when tests exist)
pytest

# Run specific test file
pytest tests/test_sensor.py

# Run specific test function
pytest tests/test_sensor.py::test_sensor_creation

# Run with verbose output
pytest -v

# Run with output capture disabled (see print statements)
pytest -s
```

### Validation (CI/CD)
```bash
# HACS validation (run locally if HACS CLI installed)
hacs validate

# Home Assistant hassfest validation
# (requires Home Assistant dev environment)
python -m homeassistant.scripts.hassfest --action validate
```

### Manual Testing
```bash
# Test Modbus connection directly
python test_modbus_connection.py

# Start Home Assistant in development mode
# (from HA config directory with this integration in custom_components/)
hass -c . --debug
```

## Code Style Guidelines

### File Header
Every Python file must start with:
```python
"""Brief description of module purpose."""
from __future__ import annotations

import logging
# ... other imports

_LOGGER = logging.getLogger(__name__)
```

### Import Order
Follow standard Python import order:
1. `from __future__ import annotations` (always first)
2. Standard library imports
3. Third-party imports (e.g., pymodbus, homeassistant)
4. Local imports (from .const, .coordinator, etc.)

Example:
```python
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import JablotronVoltaCoordinator
```

### Type Annotations
- **Always use type hints** for function parameters and return types
- Use `from __future__ import annotations` for forward references
- Use `| None` instead of `Optional[]` (Python 3.10+ union syntax)
- Use `dict[str, Any]` instead of `Dict[str, Any]`

```python
async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensor entities."""
```

### Naming Conventions
- **Classes**: `PascalCase` (e.g., `JablotronVoltaSensor`)
- **Functions/Methods**: `snake_case` (e.g., `async_update_data`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_PORT`, `DOMAIN`)
- **Private members**: Prefix with `_` (e.g., `_attr_name`, `_async_update`)
- **Type annotations**: Use `Final` for constants in const.py

### Entity Attributes
Use Home Assistant's attribute naming pattern:
```python
class MySensor(SensorEntity):
    """My sensor class."""
    
    _attr_has_entity_name = True  # Use translation-based naming
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
```

### Dataclass Patterns
Use frozen dataclasses for entity descriptions:
```python
@dataclass(frozen=True)
class JablotronVoltaSensorEntityDescription(SensorEntityDescription):
    """Describes Jablotron Volta sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType] | None = None
    available_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None
```

### Error Handling
```python
try:
    result = await some_async_operation()
except SomeSpecificException as err:
    _LOGGER.error("Failed to do something: %s", err)
    raise HomeAssistantError(f"Operation failed: {err}") from err
```

### Logging
- Use `_LOGGER` (module-level logger)
- Log levels: `debug`, `info`, `warning`, `error`
- Use lazy formatting: `_LOGGER.debug("Value: %s", value)` not f-strings

```python
_LOGGER.debug("Updating data for %s", self.name)
_LOGGER.error("Failed to read register %s: %s", register, err)
```

## Entity Naming System

**CRITICAL**: This integration uses Home Assistant's translation-based entity naming.

### Key Rules:
1. **Set `_attr_has_entity_name = True`** in all entity classes
2. **Use `translation_key`** instead of hardcoded `name` in EntityDescriptions
3. **Entity IDs are created from**: `{domain}.{device_name}_{translation_key}`
4. **Home Assistant auto-expands abbreviations**: `temp` → `temperature` in entity IDs

### Example:
```python
# In sensor.py
JablotronVoltaSensorEntityDescription(
    key="outdoor_temp_damped",  # Data dictionary key (short form OK)
    translation_key="outdoor_temperature_damped",  # MUST use full word!
    device_class=SensorDeviceClass.TEMPERATURE,
    value_fn=lambda data: data.get("outdoor_temp_damped"),  # Match data key
)
```

This creates: `sensor.jablotron_volta_outdoor_temperature_damped`

### Translation Files
- Located in: `custom_components/jablotron_volta/translations/`
- Files: `en.json`, `cs.json`
- Structure:
```json
{
  "entity": {
    "sensor": {
      "outdoor_temperature_damped": {
        "name": "Outdoor Temperature (Damped)"
      }
    }
  }
}
```

### Common Pitfalls:
- ❌ Using `translation_key="outdoor_temp_damped"` → HA expands to `outdoor_temperature_damped`
- ✅ Use full words in `translation_key` to match expected entity IDs
- ❌ Removing `translation_key` and using `name` → breaks translation system
- ✅ Always provide matching translation in both `en.json` and `cs.json`

## Architecture

### File Structure
```
custom_components/jablotron_volta/
├── __init__.py           # Integration setup, platform loading
├── config_flow.py        # UI configuration flow
├── const.py              # Constants, register addresses, maps
├── coordinator.py        # DataUpdateCoordinator, data fetching
├── modbus_client.py      # Modbus TCP communication layer
├── binary_sensor.py      # Binary sensors (heating states, alerts)
├── button.py             # Buttons (reset, restart)
├── climate.py            # Climate entities (DHW, CH1, CH2)
├── number.py             # Number entities (setpoints, corrections)
├── select.py             # Select entities (modes, strategies)
├── sensor.py             # Sensors (temperature, pressure, etc.)
├── switch.py             # Switches (optimal start, fast cooldown)
├── manifest.json         # Integration metadata
└── translations/
    ├── en.json           # English translations
    └── cs.json           # Czech translations
```

### Data Flow
1. **Coordinator** (`coordinator.py`) polls Modbus device every 30s
2. Reads holding + input registers via **ModbusClient** (`modbus_client.py`)
3. Parses raw data into Python dict with named keys
4. Entities subscribe to coordinator updates
5. Entities extract values using `value_fn` lambdas from descriptions

### Register Addressing
- **Input registers** (read-only): System status, measurements
- **Holding registers** (read/write): Configuration, setpoints
- Register addresses in `const.py` use **1-based indexing** (documentation format)
- pymodbus uses **0-based indexing** (subtract 1 when calling API)

## Git Workflow

### Branching
- Main branch: `master`
- Feature branches: `feature/description`
- Fix branches: `fix/description`

### Commit Messages
Use [Conventional Commits](https://www.conventionalcommits.org/):
```
feat: add support for outdoor temperature sensor
fix: correct entity ID naming for temperature entities
docs: update README with dashboard installation
refactor: simplify coordinator data parsing
```

### Release Process
- Uses `release-please` automation
- Version in `manifest.json` is auto-updated
- Create releases via GitHub (creates git tags)
- Users update via HACS

## Important Notes for Agents

1. **Never break Home Assistant compatibility** - test changes with HA core API
2. **Maintain backward compatibility** - users shouldn't need to reconfigure
3. **Follow HA entity patterns** - use proper device classes, state classes, units
4. **Keep coordinator efficient** - minimize Modbus reads, batch operations
5. **Handle missing CH2 gracefully** - only create entities if circuit exists
6. **Preserve register constants** - names/values match Volta documentation
7. **Update translations** - add entries to both `en.json` AND `cs.json`
8. **Dashboard compatibility** - entity ID changes break dashboards, communicate clearly

## Testing Checklist

Before committing:
- [ ] Run `ruff check --fix` and `ruff format`
- [ ] Verify `manifest.json` version matches current release
- [ ] Check translations exist for all new entities (en + cs)
- [ ] Test with actual device if possible
- [ ] Verify no Home Assistant startup errors in logs
- [ ] Check entity IDs match expected format
- [ ] Update README.md if adding features
- [ ] Update CHANGELOG.md following existing format

## Resources

- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [HA Entity Integration](https://developers.home-assistant.io/docs/core/entity)
- [Modbus Integration Best Practices](https://developers.home-assistant.io/docs/creating_component_generic_discovery)
- [pymodbus Documentation](https://pymodbus.readthedocs.io/)
