# Tests for Jablotron Volta Integration

Tests run against a real Home Assistant core using
[`pytest-homeassistant-custom-component`](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component).
No device is needed: the Modbus client is mocked.

## Structure

```
tests/
├── conftest.py             # Fixtures (mock client, config entry, setup helper)
├── test_config_flow.py     # User + reconfigure flows, error handling, unique ID
├── test_init.py            # Setup/unload, unique ID migration, entities, actions, diagnostics
├── test_modbus_client.py   # Connection handling and request serialization
├── test_coordinator.py     # Pure register parse functions
├── test_scaling.py         # Pure scaling functions
├── test_sensor.py          # Sensor descriptions and value_fn
├── test_number.py          # Number descriptions, value_fn and scale_fn
└── test_translations.py    # Translation coverage (entity names, select states, en/cs parity)
```

## Running

```bash
pip install -r requirements-dev.txt
pytest                                   # all tests
pytest tests/test_config_flow.py         # one file
pytest tests/test_init.py::test_climate_turn_off
pytest --cov=custom_components.jablotron_volta --cov-report=term-missing  # needs pytest-cov
```

`pytest.ini` sets `asyncio_mode = auto`, so async tests need no marker.

## Fixtures

| Fixture | Purpose |
|---|---|
| `mock_client` | Patches `JablotronModbusClient` in the coordinator and config flow. `async_read_all_data` returns `make_raw_data()`; `async_read_serial_number` returns `SERIAL`. |
| `mock_config_entry` | `MockConfigEntry` for a boiler at `HOST` with unique ID `SERIAL`. |
| `init_integration` | Adds `mock_config_entry` and sets it up with `mock_client`. |
| `_make_coordinator_data()` | Pre-scaled coordinator data for pure `value_fn` tests. |

Use `make_raw_data(ch2=True)` to simulate a boiler with Heating Circuit 2.

## Continuous Integration

`.github/workflows/tests.yml` runs Ruff plus pytest against the latest Home Assistant
(`requirements-dev.txt`) and the minimum supported version (2026.7.0).
