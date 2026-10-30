# Agent Guidelines for Jablotron Volta Integration

Home Assistant custom integration (HACS) for Jablotron Volta electric boilers via Modbus TCP.
Supports Home Assistant 2026.7.0+ (`hacs.json`). Depends on `pymodbus>=3.13,<4` (async client).

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

No `pyproject.toml` or `ruff.toml` exists — ruff runs with defaults. `pytest.ini` enables `asyncio_mode = auto`.
CI runs the tests twice: latest HA (`requirements-dev.txt`) and the minimum HA 2026.7.0, both on Python 3.14.
Raising the minimum HA version means updating `hacs.json`, the CI matrix pin and this file together.

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
Entity actions must raise translated `HomeAssistantError`s (keys under `exceptions` in the translation files) instead of only logging:
```python
try:
    await self.coordinator.client.async_write_register(register, value)
except JablotronVoltaError as err:
    raise HomeAssistantError(
        translation_domain=DOMAIN,
        translation_key="write_failed",
        translation_placeholders={"entity_id": self.entity_id, "error": str(err)},
    ) from err
```
Entities get this for free via `JablotronVoltaEntity._async_write_register()`.

### Logging
- Use `_LOGGER` (module-level) with lazy formatting: `_LOGGER.debug("Value: %s", value)`
- Never use f-strings in log calls

### Entity Descriptions
Use frozen, keyword-only dataclasses with `value_fn` / `exists_fn` lambdas:
```python
@dataclass(frozen=True, kw_only=True)
class JablotronVoltaSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], StateType]
    exists_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None
```
`exists_fn` decides at setup whether the entity is created; runtime availability comes from the coordinator.
All entity classes inherit `JablotronVoltaEntity` (`entity.py`), which sets `_attr_has_entity_name = True`, the unique ID and device info. Use `translation_key`, and set `entity_category` for configuration/diagnostic entities.

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
├── __init__.py        # Setup/unload, entry.runtime_data, legacy unique ID migration
├── const.py           # Constants, register addresses, enum maps
├── coordinator.py     # DataUpdateCoordinator, JablotronVoltaConfigEntry type, pure parse functions
├── modbus_client.py   # Async Modbus TCP client (one connection, lock-serialized)
├── entity.py          # JablotronVoltaEntity base class (unique ID, device info, writes)
├── scaling.py         # Pure scaling/conversion functions (no I/O)
├── config_flow.py     # User + reconfigure flows, unique ID = device serial number
├── diagnostics.py     # Config entry diagnostics (network details redacted)
├── sensor.py          # ~30 sensors (temps, energy, pressure, voltages)
├── binary_sensor.py   # 3 binary sensors (heating states, alerts)
├── climate.py         # 2 climate entities (CH1, CH2)
├── number.py          # ~30 number entities (setpoints, corrections)
├── select.py          # 6 select entities (modes, strategies)
├── switch.py          # 4 switches (optimal start, fast cooldown)
├── button.py          # 2 buttons (reset error, restart)
├── quality_scale.yaml # HA quality scale self-assessment (not validated for custom integrations)
└── translations/      # en.json, cs.json (no strings.json; en.json is the source)
```

**Data flow:** Coordinator polls every 30s → `JablotronModbusClient.async_read_all_data()` → parses into dict → entities extract values via `value_fn` lambdas.

**Modbus access:** All reads and writes go through `JablotronModbusClient`, which keeps one TCP connection open and serializes requests with an `asyncio.Lock`. Every poll and every protected write (holding registers 1000-3999) first writes the system password. Transport errors close the connection; the next call reconnects.

**Register addressing:** `const.py` addresses match the Volta documentation and are passed to pymodbus unchanged.

**CH2 handling:** Heating Circuit 2 entities are only created when CH2 is detected. Use `exists_fn` referencing `coordinator.ch2_available`.

**Scaling:** `scaling.py` contains pure functions for register↔human-value conversion. Coordinator parse functions are also pure (no I/O) for easy testing.

## Testing

Tests run against a real Home Assistant core via `pytest-homeassistant-custom-component`. Key fixtures in `tests/conftest.py`:
- `mock_client` — patches `JablotronModbusClient` (coordinator + config flow); raw register data from `make_raw_data()`
- `mock_config_entry` — `MockConfigEntry` for a device with serial `SERIAL`
- `init_integration` — sets up the entry with `mock_client`
- `_make_coordinator_data()` — pre-scaled data dict for pure `value_fn` tests

Test files: `test_scaling.py`, `test_coordinator.py`, `test_sensor.py`, `test_number.py`, `test_translations.py`, `test_modbus_client.py`, `test_config_flow.py`, `test_init.py`.

## Git Conventions

- Main branch: `master`
- Feature branches: `feature/description`, fix branches: `fix/description`
- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`
- Releases via `release-please`; version lives in `manifest.json`

## Pre-Commit Checklist

- [ ] `ruff check --fix` and `ruff format` pass on both `custom_components/` and `tests/`
- [ ] `pytest -v` passes
- [ ] Translations exist in both `en.json` and `cs.json` for all new entities (and select option `state`s)
- [ ] Entity IDs use full words (no abbreviations in `translation_key`)
- [ ] No duplicate keys, translation_keys, or register addresses
- [ ] Entity unique IDs (`<entry_id>_<key>`) of existing entities never change
- [ ] CH2-specific entities have `exists_fn`
