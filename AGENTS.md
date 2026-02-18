# Agent Guidelines for Jablotron Volta Integration

Home Assistant custom integration (HACS) for Jablotron Volta electric boilers via Modbus TCP.
Python 3.11+, depends on `pymodbus>=3.6,<4` and `homeassistant>=2025.9.0`.

## Build/Lint/Test Commands

```bash
# Setup
pip install -r requirements-dev.txt

# Lint (also checks tests/ — must pass CI)
ruff check custom_components/jablotron_volta/ tests/
ruff check --fix custom_components/jablotron_volta/ tests/

# Format (must pass CI)
ruff format custom_components/jablotron_volta/ tests/
ruff format --check custom_components/jablotron_volta/ tests/

# Run all tests
pytest -v

# Run a single test file
pytest tests/test_sensor.py -v

# Run a single test function
pytest tests/test_sensor.py::test_sensor_creation -v
```

No `pyproject.toml` or `ruff.toml` exists — ruff runs with defaults. CI uses Python 3.13.

## Code Style

### File Header
Every Python file must start with:
```python
"""Brief description of module purpose."""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)
```

### Import Order
1. `from __future__ import annotations` (always first)
2. Standard library (`logging`, `dataclasses`, `typing`)
3. Third-party (`pymodbus`, `homeassistant`)
4. Local (`.const`, `.coordinator`, etc.)

### Type Annotations
- Always type function parameters and return values
- Use `| None` not `Optional[]`, `dict[str, Any]` not `Dict[str, Any]`
- Use `Final` for constants in `const.py`

### Naming Conventions
- Classes: `PascalCase` (`JablotronVoltaSensor`)
- Functions: `snake_case` (`async_update_data`)
- Constants: `UPPER_SNAKE_CASE` (`DEFAULT_PORT`, `DOMAIN`)
- Private members: `_` prefix (`_attr_name`)

### Error Handling
```python
try:
    result = await some_async_operation()
except SomeSpecificException as err:
    _LOGGER.error("Failed to do something: %s", err)
    raise HomeAssistantError(f"Operation failed: {err}") from err
```

### Logging
- Use `_LOGGER` (module-level) with lazy formatting: `_LOGGER.debug("Value: %s", value)`
- Never use f-strings in log calls

### Entity Descriptions
Use frozen dataclasses with `value_fn` / `available_fn` lambdas:
```python
@dataclass(frozen=True)
class JablotronVoltaSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], StateType] | None = None
    available_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None
```
All entity classes set `_attr_has_entity_name = True` and use `translation_key`.

## Entity Naming (Critical)

This integration uses HA's translation-based entity naming. Getting this wrong breaks entity IDs and dashboards.

**Rules:**
1. Set `_attr_has_entity_name = True` in all entity classes
2. Use `translation_key` in EntityDescriptions, never hardcoded `name`
3. `translation_key` MUST use full words — HA auto-expands abbreviations in entity IDs (`temp` → `temperature`)
4. Add matching entries in **both** `translations/en.json` AND `translations/cs.json`

```python
# Correct:
JablotronVoltaSensorEntityDescription(
    key="outdoor_temp_damped",                      # data dict key (short OK)
    translation_key="outdoor_temperature_damped",   # MUST use full word
    value_fn=lambda data: data.get("outdoor_temp_damped"),
)
# Creates: sensor.jablotron_volta_outdoor_temperature_damped
```

## Architecture

```
custom_components/jablotron_volta/
├── __init__.py        # Integration setup, loads 7 platforms
├── const.py           # Constants, register addresses (1-based), enum maps
├── coordinator.py     # DataUpdateCoordinator, pure parse functions
├── modbus_client.py   # Modbus TCP client, delegates scaling to scaling.py
├── scaling.py         # Pure scaling/conversion functions (no I/O)
├── config_flow.py     # UI configuration flow
├── sensor.py          # ~30 sensors (temps, energy, pressure, voltages)
├── binary_sensor.py   # 4 binary sensors (heating states, alerts)
├── climate.py         # 3 climate entities (DHW, CH1, CH2)
├── number.py          # ~30 number entities (setpoints, corrections)
├── select.py          # 7 select entities (modes, strategies)
├── switch.py          # 4 switches (optimal start, fast cooldown)
├── button.py          # 2 buttons (reset error, restart)
└── translations/      # en.json, cs.json
```

**Data flow:** Coordinator polls every 30s → reads registers via ModbusClient → parses into dict → entities extract values via `value_fn` lambdas.

**Register addressing:** `const.py` uses 1-based indexing (matching Volta docs). pymodbus calls use 0-based (subtract 1).

**CH2 handling:** Heating Circuit 2 entities are only created when CH2 is detected. Use `available_fn` referencing `coordinator.ch2_available`.

**Scaling:** `scaling.py` contains pure functions for register↔human-value conversion. Coordinator parse functions are also pure (no I/O) for easy testing.

## Testing

Tests are unit-level using mocks from `tests/conftest.py` — no running HA instance needed. Key fixtures:
- `mock_coordinator` — provides `_make_coordinator_data()` with realistic pre-scaled values
- `mock_modbus_client` — mocked Modbus client
- `mock_config_entry` — mocked HA config entry

Test files: `test_scaling.py`, `test_coordinator.py`, `test_sensor.py`, `test_number.py`, `test_translations.py`.

## Git Conventions

- Main branch: `master`
- Feature branches: `feature/description`, fix branches: `fix/description`
- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`
- Releases via `release-please`; version lives in `manifest.json`

## Pre-Commit Checklist

- [ ] `ruff check --fix` and `ruff format` pass on both `custom_components/` and `tests/`
- [ ] `pytest -v` passes
- [ ] Translations exist in both `en.json` and `cs.json` for all new entities
- [ ] Entity IDs use full words (no abbreviations in `translation_key`)
- [ ] No duplicate keys, translation_keys, or register addresses
- [ ] CH2-specific entities have `available_fn`
