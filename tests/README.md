# Tests for Jablotron Volta Integration

This directory contains unit tests for the Jablotron Volta Home Assistant integration.

## Test Structure

```
tests/
├── __init__.py                  # Test package
├── conftest.py                  # Pytest fixtures and mocks
├── test_translations.py         # Translation validation tests
├── test_entity_naming.py        # Entity naming convention tests
├── test_sensor.py              # Sensor entity tests
├── test_number.py              # Number entity tests
├── test_coordinator.py         # Coordinator tests
└── README.md                   # This file
```

## Running Tests

### Run All Tests
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_translations.py
pytest tests/test_sensor.py
```

### Run Specific Test
```bash
pytest tests/test_translations.py::test_translation_keys_match_between_languages
```

### Run with Verbose Output
```bash
pytest -v
```

### Run with Coverage
```bash
pytest --cov=custom_components.jablotron_volta --cov-report=html
```

## Test Categories

### 1. Translation Tests (`test_translations.py`)
Validates translation key consistency and coverage:
- ✓ Translation files exist (en.json, cs.json)
- ✓ Valid JSON syntax
- ✓ Keys match between languages
- ✓ All code translation_key values exist in JSON
- ✓ No abbreviations (must use `_temperature` not `_temp`)
- ✓ Proper naming conventions
- ✓ All entries have 'name' property
- ✓ Translation coverage > 90%

### 2. Entity Naming Tests (`test_entity_naming.py`)
Validates entity naming conventions:
- ✓ All entity classes have `_attr_has_entity_name = True`
- ✓ No hardcoded names in EntityDescriptions
- ✓ Entity ID format compliance

### 3. Sensor Tests (`test_sensor.py`)
Validates sensor entities:
- ✓ All sensors have translation_key
- ✓ All sensors have value_fn
- ✓ Temperature sensors have correct attributes
- ✓ Energy sensor has TOTAL_INCREASING state class
- ✓ CH2 sensors have availability function
- ✓ No duplicate keys or translation_keys

### 4. Number Tests (`test_number.py`)
Validates number entities:
- ✓ All numbers have translation_key
- ✓ All numbers have register address
- ✓ Valid min/max ranges
- ✓ Temperature numbers use full word `_temperature`
- ✓ CH2 numbers have availability function
- ✓ No duplicate keys, translation_keys, or registers

### 5. Coordinator Tests (`test_coordinator.py`)
Validates data coordinator:
- ✓ Temperature scaling (0.1°C resolution)
- ✓ Pressure scaling (0.01 bar resolution)
- ✓ Percentage scaling (0.1% resolution)
- ✓ CH2 detection logic
- ✓ Data key naming (short form in dict, full form in translation_key)

## Key Testing Principles

### Translation-Based Entity Naming
This integration uses Home Assistant's translation-based entity naming system:

```python
# In entity descriptions:
translation_key="outdoor_temperature_damped"  # Full word!

# In coordinator data:
data["outdoor_temp_damped"] = 10.5  # Short form OK here

# Results in entity ID:
sensor.jablotron_volta_outdoor_temperature_damped
```

**Critical Rule**: `translation_key` MUST use full words (e.g., `_temperature`) because Home Assistant auto-expands abbreviations in entity IDs.

### Test-Driven Entity Changes
When adding/modifying entities:

1. **Add to entity description** (sensor.py, number.py, etc.)
   - Use full words in `translation_key`
   - Ensure `value_fn` matches coordinator data key

2. **Add to translations** (en.json AND cs.json)
   - Use same key as `translation_key`
   - Provide meaningful name

3. **Run tests**
   ```bash
   pytest tests/test_translations.py tests/test_sensor.py
   ```

4. **Verify** no duplicate keys, proper naming

## Fixtures

### `mock_modbus_client`
Mock Modbus client with basic operations.

### `mock_config_entry`
Mock Home Assistant config entry with default values.

### `mock_coordinator`
Mock coordinator with sample data for all entities.

## Common Test Patterns

### Test Translation Key Exists
```python
def test_my_entity_has_translation():
    """Test that my entity has translation."""
    from custom_components.jablotron_volta.sensor import SENSOR_TYPES
    
    my_sensor = next(s for s in SENSOR_TYPES if s.key == "my_sensor")
    assert my_sensor.translation_key == "my_sensor"
```

### Test Entity Initialization
```python
def test_entity_init(mock_coordinator, mock_config_entry):
    """Test entity initialization."""
    from custom_components.jablotron_volta.sensor import JablotronVoltaSensor, SENSOR_TYPES
    
    desc = SENSOR_TYPES[0]
    sensor = JablotronVoltaSensor(mock_coordinator, mock_config_entry, desc)
    
    assert sensor.coordinator == mock_coordinator
```

## Continuous Integration

Tests run automatically on:
- Every push to `master`
- Every pull request
- Via GitHub Actions (see `.github/workflows/`)

## Requirements

Install test dependencies:
```bash
pip install -r requirements-dev.txt
```

This includes:
- pytest>=7.0.0
- pytest-asyncio>=0.21.0
- homeassistant>=2025.9.0

## Writing New Tests

When adding new tests:

1. **Follow existing patterns** - Look at similar tests
2. **Use descriptive names** - `test_temperature_sensors_use_celsius`
3. **Add docstrings** - Explain what you're testing
4. **Use fixtures** - Reuse mocks from `conftest.py`
5. **Test edge cases** - Missing data, None values, etc.
6. **Keep tests fast** - Mock external dependencies

## Test Coverage Goals

- Translation validation: 100%
- Entity descriptions: 100%
- Entity initialization: >80%
- Data handling: >70%
- Modbus communication: >60% (with mocks)

Run coverage report:
```bash
pytest --cov=custom_components.jablotron_volta --cov-report=term-missing
```
