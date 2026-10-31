"""Fixtures for Jablotron Volta tests."""

from __future__ import annotations

from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jablotron_volta.const import (
    CONF_DEVICE_ID,
    DEFAULT_DEVICE_ID,
    DEFAULT_PORT,
    DOMAIN,
)

HOST = "192.168.1.100"
SERIAL = "123456"
ENTRY_DATA = {
    CONF_HOST: HOST,
    CONF_PORT: DEFAULT_PORT,
    CONF_DEVICE_ID: DEFAULT_DEVICE_ID,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Allow loading the custom integration in every test."""


def make_raw_data(*, ch2: bool = False) -> dict[str, Any]:
    """Build raw register batches as returned by async_read_all_data()."""
    ch1_status = [1, 215, 400, 350, 300, 550, 4500]
    ch1_settings = [1, 220, 150, 280, 220, 80, 10, 3, 250, 550]
    ch1_settings += [400, 15, 65516, 50, 450, 30, 1, 0, 65531, 0]
    raw: dict[str, Any] = {
        # serial 1 << 16 | 57920 == 123456
        "device_info": [1, 57920, 0, 0, 0x0102, 3, 0xAABB, 0xCCDD, 0xEEFF, 0x0203, 4],
        # Volta reports IPv4 words low word first (192.168.1.100, 255.255.255.0, 192.168.1.1)
        "network_info": [0x0164, 0xC0A8, 0xFF00, 0xFFFF, 0x0101, 0xC0A8],
        "system_status": [455, 33],
        "regulation": [2, 65511, 65518],
        "boiler_status": [3, 0, 15, 0, 550, 450, 800, 1000, 0, 0],
        "ch1_status": ch1_status,
        "system_alerts": [0, 0],
        "regulation_settings": [2, 1, 48, 5, 50, 65486],
        "boiler_settings": [0, 1, 0, 1234, 600, 800, 300, 0, 0, 0, 0, 0, 0],
        "ch1_settings": ch1_settings,
        "system_control": [0, 1, 0, 0, 0, 0, 60, 0, 0, 3],
        "ch2_available": ch2,
    }
    if ch2:
        raw["ch2_status"] = list(ch1_status)
        raw["ch2_settings"] = list(ch1_settings)
    return raw


@pytest.fixture
def mock_client() -> Generator[AsyncMock]:
    """Patch the Modbus client used by the coordinator and the config flow."""
    with (
        patch(
            "custom_components.jablotron_volta.coordinator.JablotronModbusClient",
            autospec=True,
        ) as client_class,
        patch(
            "custom_components.jablotron_volta.config_flow.JablotronModbusClient",
            new=client_class,
        ),
    ):
        client = client_class.return_value
        client.async_read_all_data.return_value = make_raw_data()
        client.async_read_serial_number.return_value = SERIAL
        yield client


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Config entry for a Volta at HOST."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=f"Jablotron Volta ({HOST})",
        data=dict(ENTRY_DATA),
        unique_id=SERIAL,
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> MockConfigEntry:
    """Set up the integration with the mocked client."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    return mock_config_entry


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
