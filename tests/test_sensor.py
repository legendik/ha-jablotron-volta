"""Tests for sensor entities."""

from __future__ import annotations

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfTemperature

from custom_components.jablotron_volta.sensor import (
    SENSOR_TYPES,
    JablotronVoltaSensor,
)

from .conftest import _make_coordinator_data


# ---------------------------------------------------------------------------
# Descriptor-level validation (no fixtures needed)
# ---------------------------------------------------------------------------


def test_all_sensors_have_translation_key():
    """Test that all sensor descriptions have translation_key."""
    for sensor in SENSOR_TYPES:
        assert hasattr(sensor, "translation_key"), (
            f"Sensor {sensor.key} missing translation_key"
        )
        assert sensor.translation_key, f"Sensor {sensor.key} has empty translation_key"


def test_all_sensors_have_value_fn():
    """Test that all sensor descriptions have value_fn."""
    for sensor in SENSOR_TYPES:
        assert hasattr(sensor, "value_fn"), f"Sensor {sensor.key} missing value_fn"
        assert sensor.value_fn is not None, f"Sensor {sensor.key} has None value_fn"


def test_no_duplicate_sensor_keys():
    """Test that there are no duplicate sensor keys."""
    keys = [s.key for s in SENSOR_TYPES]
    duplicates = [k for k in keys if keys.count(k) > 1]
    assert not duplicates, f"Found duplicate sensor keys: {set(duplicates)}"


def test_no_duplicate_translation_keys():
    """Test that there are no duplicate translation keys."""
    translation_keys = [s.translation_key for s in SENSOR_TYPES]
    duplicates = [k for k in translation_keys if translation_keys.count(k) > 1]
    assert not duplicates, f"Found duplicate translation keys: {set(duplicates)}"


def test_translation_keys_use_full_words():
    """Test that translation_keys don't use abbreviations that HA auto-expands.

    Home Assistant auto-expands 'temp' to 'temperature' in entity IDs,
    so translation_key MUST already use the full word.
    """
    for sensor in SENSOR_TYPES:
        tk = sensor.translation_key
        # Check for 'temp' that isn't already 'temperature'
        if "temp" in tk and "temperature" not in tk:
            pytest.fail(
                f"Sensor {sensor.key}: translation_key '{tk}' uses abbreviation "
                "'temp' — use 'temperature' instead"
            )


def test_temperature_sensors_have_correct_attributes():
    """Test that temperature sensors have correct device class and units."""
    temperature_sensors = [
        s for s in SENSOR_TYPES if s.device_class == SensorDeviceClass.TEMPERATURE
    ]
    assert len(temperature_sensors) > 0, "No temperature sensors found"

    for sensor in temperature_sensors:
        assert sensor.native_unit_of_measurement == UnitOfTemperature.CELSIUS, (
            f"Sensor {sensor.key} should use CELSIUS"
        )
        assert sensor.state_class == SensorStateClass.MEASUREMENT, (
            f"Sensor {sensor.key} should have MEASUREMENT state class"
        )


def test_energy_sensor_has_correct_attributes():
    """Test that energy sensor has total_increasing state class."""
    energy_sensors = [
        s for s in SENSOR_TYPES if s.device_class == SensorDeviceClass.ENERGY
    ]
    assert len(energy_sensors) == 1, "Should have exactly one energy sensor"

    energy_sensor = energy_sensors[0]
    assert energy_sensor.state_class == SensorStateClass.TOTAL_INCREASING, (
        "Energy sensor should have TOTAL_INCREASING state class for Energy Dashboard"
    )


def test_ch2_sensors_have_available_fn():
    """Test that CH2 sensors have availability function."""
    ch2_sensors = [s for s in SENSOR_TYPES if "ch2" in s.key]
    assert len(ch2_sensors) > 0, "No CH2 sensors found"

    for sensor in ch2_sensors:
        assert sensor.available_fn is not None, (
            f"CH2 sensor {sensor.key} should have available_fn"
        )


def test_non_ch2_sensors_lack_available_fn():
    """Non-CH2 sensors should NOT have available_fn (always available)."""
    non_ch2_sensors = [s for s in SENSOR_TYPES if "ch2" not in s.key]
    for sensor in non_ch2_sensors:
        assert sensor.available_fn is None, (
            f"Non-CH2 sensor {sensor.key} should not have available_fn"
        )


# ---------------------------------------------------------------------------
# value_fn tests — use data from conftest._make_coordinator_data()
# ---------------------------------------------------------------------------


class TestSensorValueFunctions:
    """Test that each sensor's value_fn extracts the correct value from data."""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        """Set up coordinator data for all tests."""
        self.data = _make_coordinator_data()

    def _get_sensor(self, key: str):
        """Look up a sensor description by key."""
        for s in SENSOR_TYPES:
            if s.key == key:
                return s
        pytest.fail(f"Sensor with key '{key}' not found in SENSOR_TYPES")

    # --- Energy ---
    def test_boiler_total_energy(self):
        s = self._get_sensor("boiler_total_energy")
        assert s.value_fn(self.data) == 1234

    # --- System ---
    def test_cpu_temperature(self):
        s = self._get_sensor("cpu_temperature")
        assert s.value_fn(self.data) == 45.5

    def test_battery_voltage(self):
        s = self._get_sensor("battery_voltage")
        assert s.value_fn(self.data) == 3.3

    # --- Outdoor ---
    def test_outdoor_temp_damped(self):
        s = self._get_sensor("outdoor_temp_damped")
        assert s.value_fn(self.data) == -2.5

    def test_outdoor_temp_composite(self):
        s = self._get_sensor("outdoor_temp_composite")
        assert s.value_fn(self.data) == -1.8

    # --- Boiler ---
    def test_boiler_pressure(self):
        s = self._get_sensor("boiler_pressure")
        assert s.value_fn(self.data) == 1.5

    def test_boiler_water_input_temp(self):
        s = self._get_sensor("boiler_water_input_temp")
        assert s.value_fn(self.data) == 55.0

    def test_boiler_water_return_temp(self):
        s = self._get_sensor("boiler_water_return_temp")
        assert s.value_fn(self.data) == 45.0

    def test_boiler_water_setpoint(self):
        s = self._get_sensor("boiler_water_setpoint")
        assert s.value_fn(self.data) == 60.0

    def test_boiler_pump_power(self):
        s = self._get_sensor("boiler_pump_power")
        assert s.value_fn(self.data) == 80.0

    def test_boiler_heating_power(self):
        s = self._get_sensor("boiler_heating_power")
        assert s.value_fn(self.data) == 100.0

    def test_boiler_pwm_value(self):
        s = self._get_sensor("boiler_pwm_value")
        assert s.value_fn(self.data) == 0

    def test_boiler_active_segments(self):
        s = self._get_sensor("boiler_active_segments")
        assert s.value_fn(self.data) == 3

    def test_boiler_inactive_segments(self):
        s = self._get_sensor("boiler_inactive_segments")
        assert s.value_fn(self.data) == 0

    # --- DHW ---
    def test_dhw_temperature_current(self):
        s = self._get_sensor("dhw_temperature_current")
        assert s.value_fn(self.data) == 48.5

    # --- CH1 ---
    def test_ch1_temperature_current(self):
        s = self._get_sensor("ch1_temperature_current")
        assert s.value_fn(self.data) == 21.5

    def test_ch1_water_input_temp(self):
        s = self._get_sensor("ch1_water_input_temp")
        assert s.value_fn(self.data) == 40.0

    def test_ch1_water_return_temp(self):
        s = self._get_sensor("ch1_water_return_temp")
        assert s.value_fn(self.data) == 35.0

    def test_ch1_water_setpoint(self):
        s = self._get_sensor("ch1_water_setpoint")
        assert s.value_fn(self.data) == 40.0

    def test_ch1_pump_power(self):
        s = self._get_sensor("ch1_pump_power")
        assert s.value_fn(self.data) == 30.0

    def test_ch1_humidity(self):
        s = self._get_sensor("ch1_humidity")
        assert s.value_fn(self.data) == 55.0

    def test_ch1_co2(self):
        s = self._get_sensor("ch1_co2")
        assert s.value_fn(self.data) == 450.0

    # --- CH2 (returns None — no CH2 data in base fixture) ---
    def test_ch2_temperature_current(self):
        s = self._get_sensor("ch2_temperature_current")
        assert s.value_fn(self.data) is None

    def test_ch2_water_input_temp(self):
        s = self._get_sensor("ch2_water_input_temp")
        assert s.value_fn(self.data) is None

    def test_ch2_water_return_temp(self):
        s = self._get_sensor("ch2_water_return_temp")
        assert s.value_fn(self.data) is None

    def test_ch2_water_setpoint(self):
        s = self._get_sensor("ch2_water_setpoint")
        assert s.value_fn(self.data) is None

    def test_ch2_pump_power(self):
        s = self._get_sensor("ch2_pump_power")
        assert s.value_fn(self.data) is None

    def test_ch2_humidity(self):
        s = self._get_sensor("ch2_humidity")
        assert s.value_fn(self.data) is None

    def test_ch2_co2(self):
        s = self._get_sensor("ch2_co2")
        assert s.value_fn(self.data) is None

    # --- Network ---
    def test_ip_address(self):
        s = self._get_sensor("ip_address")
        assert s.value_fn(self.data) == "192.168.1.100"

    def test_subnet_mask(self):
        s = self._get_sensor("subnet_mask")
        assert s.value_fn(self.data) == "255.255.255.0"

    def test_gateway(self):
        s = self._get_sensor("gateway")
        assert s.value_fn(self.data) == "192.168.1.1"


class TestSensorValueFnWithCh2Data:
    """Test CH2 sensor value_fn when CH2 data is present."""

    def test_ch2_sensors_return_values_when_present(self):
        data = _make_coordinator_data()
        # Add CH2 data
        data.update(
            {
                "ch2_temperature_current": 20.0,
                "ch2_water_input_temp": 38.0,
                "ch2_water_return_temp": 33.0,
                "ch2_water_setpoint": 35.0,
                "ch2_pump_power": 25.0,
                "ch2_humidity": 60.0,
                "ch2_co2": 500.0,
            }
        )

        ch2_keys_values = {
            "ch2_temperature_current": 20.0,
            "ch2_water_input_temp": 38.0,
            "ch2_water_return_temp": 33.0,
            "ch2_water_setpoint": 35.0,
            "ch2_pump_power": 25.0,
            "ch2_humidity": 60.0,
            "ch2_co2": 500.0,
        }

        for key, expected in ch2_keys_values.items():
            sensor = next(s for s in SENSOR_TYPES if s.key == key)
            assert sensor.value_fn(data) == expected, (
                f"Sensor {key} expected {expected}, got {sensor.value_fn(data)}"
            )


class TestSensorValueFnEdgeCases:
    """Test value_fn behavior with missing/empty data."""

    def test_all_value_fns_return_none_for_empty_data(self):
        """Every sensor's value_fn should return None when data dict is empty."""
        empty_data: dict = {}
        for sensor in SENSOR_TYPES:
            result = sensor.value_fn(empty_data)
            assert result is None, (
                f"Sensor {sensor.key} returned {result} for empty data, expected None"
            )

    def test_value_fn_completeness(self):
        """Every sensor key that maps to a data key should exist in conftest data.

        CH2 sensors are excluded because conftest only has CH1 data.
        """
        data = _make_coordinator_data()
        for sensor in SENSOR_TYPES:
            if "ch2" in sensor.key:
                continue  # CH2 data not in base fixture
            result = sensor.value_fn(data)
            assert result is not None, (
                f"Sensor {sensor.key} returned None — data key may be missing "
                f"from _make_coordinator_data()"
            )


# ---------------------------------------------------------------------------
# Entity initialization tests (use mock fixtures)
# ---------------------------------------------------------------------------


def test_sensor_entity_initialization(mock_coordinator, mock_config_entry):
    """Test sensor entity initialization."""
    sensor_desc = SENSOR_TYPES[0]
    sensor = JablotronVoltaSensor(mock_coordinator, mock_config_entry, sensor_desc)

    assert sensor.entity_description == sensor_desc
    assert sensor._attr_unique_id == f"{mock_config_entry.entry_id}_{sensor_desc.key}"
    assert sensor.coordinator == mock_coordinator


def test_sensor_native_value(mock_coordinator, mock_config_entry):
    """Test sensor native_value property."""
    temp_sensor_desc = next(s for s in SENSOR_TYPES if s.key == "outdoor_temp_damped")
    sensor = JablotronVoltaSensor(mock_coordinator, mock_config_entry, temp_sensor_desc)

    assert sensor.native_value == -2.5


def test_sensor_handles_missing_data(mock_coordinator, mock_config_entry):
    """Test that sensor handles missing data gracefully."""
    temp_sensor_desc = next(s for s in SENSOR_TYPES if s.key == "outdoor_temp_damped")
    mock_coordinator.data = {}

    sensor = JablotronVoltaSensor(mock_coordinator, mock_config_entry, temp_sensor_desc)
    assert sensor.native_value is None
