"""Fixtures for Jablotron Volta tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

from custom_components.jablotron_volta.const import (
    CONF_DEVICE_ID,
    DEFAULT_DEVICE_ID,
    DEFAULT_PORT,
    DOMAIN,
)


@pytest.fixture
def mock_modbus_client():
    """Mock Modbus client."""
    from custom_components.jablotron_volta.modbus_client import JablotronModbusClient

    client = MagicMock(spec=JablotronModbusClient)
    client.connect = MagicMock(return_value=True)
    client.close = MagicMock()
    client.read_input_registers = MagicMock(return_value=[0] * 100)
    client.read_holding_registers = MagicMock(return_value=[0] * 100)
    client.write_register = MagicMock(return_value=True)
    return client


@pytest.fixture
def mock_config_entry():
    """Mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    entry.data = {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: DEFAULT_PORT,
        CONF_DEVICE_ID: DEFAULT_DEVICE_ID,
    }
    entry.title = "Jablotron Volta"
    return entry


def _make_coordinator_data() -> dict:
    """Build a realistic coordinator data dict with correct keys and values.

    All values here are ALREADY SCALED (as produced by process_raw_data).
    """
    return {
        # System status
        "cpu_temperature": 45.5,
        "battery_voltage": 3.3,
        # Regulation
        "regulation_mode_current": 2,
        "outdoor_temp_damped": -2.5,
        "outdoor_temp_composite": -1.8,
        # Boiler status
        "boiler_active_segments": 3,
        "boiler_inactive_segments": 0,
        "boiler_pressure": 1.5,
        "boiler_water_input_temp": 55.0,
        "boiler_water_return_temp": 45.0,
        "boiler_pump_power": 80.0,
        "boiler_heating_power": 100.0,
        "boiler_analog_value": 0.0,
        "boiler_pwm_value": 0,
        # DHW status
        "dhw_state_heat": True,
        "dhw_temperature_current": 48.5,
        # CH1 status
        "ch1_state_heat": False,
        "ch1_temperature_current": 21.5,
        "ch1_water_input_temp": 40.0,
        "ch1_water_return_temp": 35.0,
        "ch1_pump_power": 30.0,
        "ch1_humidity": 55.0,
        "ch1_co2": 450.0,
        # System alerts
        "system_attention": 0,
        # Regulation settings
        "regulation_mode_user": 2,
        "outdoor_temp_source": 1,
        "building_momentum": 48,
        "composite_filter_ratio": 0.5,
        "changeover_temp": 5.0,
        "outdoor_temp_manual": -5.0,
        # Boiler settings
        "boiler_load_release": 0,
        "boiler_hdo_high_tariff": 1,
        "boiler_outdoor_temp_correction": 0.0,
        "boiler_total_energy": 1234,
        "boiler_water_setpoint": 60.0,
        "boiler_water_temp_max": 80.0,
        "boiler_water_temp_min": 30.0,
        # DHW settings
        "dhw_mode": 1,
        "dhw_temperature_desired": 50.0,
        "dhw_temperature_min": 35.0,
        "dhw_temperature_max": 65.0,
        "dhw_temperature_manual": 50.0,
        "dhw_hysteresis": 2.0,
        "dhw_regulation_strategy": 0,
        # CH1 settings
        "ch1_mode": 2,
        "ch1_temperature_desired": 22.0,
        "ch1_temperature_min": 15.0,
        "ch1_temperature_max": 28.0,
        "ch1_temperature_manual": 22.0,
        "ch1_temperature_antifrost": 8.0,
        "ch1_hysteresis": 1.0,
        "ch1_regulation_strategy": 3,
        "ch1_water_temp_min": 25.0,
        "ch1_water_temp_max": 55.0,
        "ch1_water_setpoint": 40.0,
        "ch1_equitherm_slope": 1.5,
        "ch1_equitherm_offset": -2.0,
        "ch1_equitherm_room_effect": 50,
        "ch1_threshold_setpoint": 45.0,
        "ch1_limit_heat_temp": 3.0,
        "ch1_optimal_start": True,
        "ch1_fast_cooldown": False,
        "ch1_temp_correction": -0.5,
        "ch1_humidity_correction": 0.0,
        # Network
        "ip_address": "192.168.1.100",
        "subnet_mask": "255.255.255.0",
        "gateway": "192.168.1.1",
        # System control
        "control_mode": 1,
        "error_code": 0,
        "master_fail_mode": 0,
        "master_timeout": 60,
        "circuit_mask": 3,
    }


@pytest.fixture
def mock_coordinator(mock_modbus_client):
    """Mock coordinator with realistic data."""
    from custom_components.jablotron_volta.coordinator import (
        JablotronVoltaCoordinator,
    )

    coordinator = MagicMock(spec=JablotronVoltaCoordinator)
    coordinator.data = _make_coordinator_data()
    coordinator.ch2_available = False
    coordinator.async_request_refresh = AsyncMock()
    coordinator.client = mock_modbus_client
    coordinator.device_info = {
        "identifiers": {(DOMAIN, "test_entry_id")},
        "name": "Jablotron Volta",
        "manufacturer": "Jablotron",
        "model": "Volta",
    }
    return coordinator


@pytest.fixture
def hass():
    """Mock Home Assistant instance."""
    return MagicMock(spec=HomeAssistant)
