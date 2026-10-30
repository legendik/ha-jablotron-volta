"""Tests for setup, entities and actions against a real Home Assistant core."""

from __future__ import annotations

from unittest.mock import AsyncMock
from unittest.mock import call as call_args

import pytest
from homeassistant.components.button import SERVICE_PRESS
from homeassistant.components.climate import HVACAction, HVACMode
from homeassistant.components.number import ATTR_VALUE, SERVICE_SET_VALUE
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, CONF_HOST, SERVICE_TURN_OFF, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jablotron_volta.const import (
    CH_MODE_STANDBY,
    DOMAIN,
    REG_CH1_MODE,
    REG_REGU_BUILDING_MOMENTUM,
    REG_SYS_ATTENTION_0,
    REG_SYS_ERROR_CODE,
)
from custom_components.jablotron_volta.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.jablotron_volta.modbus_client import (
    JablotronVoltaConnectionError,
    JablotronVoltaResponseError,
)

from .conftest import ENTRY_DATA, HOST, SERIAL, make_raw_data

CLIMATE_CH1 = "climate.jablotron_volta_heating_circuit_1"
BUILDING_MOMENTUM = "number.jablotron_volta_building_momentum"


async def test_setup_and_unload(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Entry loads, exposes entities and closes the connection on unload."""
    assert init_integration.state is ConfigEntryState.LOADED
    assert hass.states.get(CLIMATE_CH1) is not None

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()

    assert init_integration.state is ConfigEntryState.NOT_LOADED
    mock_client.async_close.assert_awaited()


async def test_setup_retries_when_device_unreachable(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """A device that cannot be read puts the entry into setup retry."""
    mock_client.async_read_all_data.side_effect = JablotronVoltaConnectionError("down")
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_unique_ids_are_stable(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Entity unique IDs keep the "<entry_id>_<key>" format existing installs use."""
    entry_id = init_integration.entry_id
    assert entity_registry.async_get(CLIMATE_CH1).unique_id == f"{entry_id}_ch1_climate"
    assert (
        entity_registry.async_get(BUILDING_MOMENTUM).unique_id
        == f"{entry_id}_building_momentum"
    )


async def test_ch2_entities_follow_detection(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """CH2 entities are only created when the second circuit is detected."""
    mock_client.async_read_all_data.return_value = make_raw_data(ch2=True)
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("climate.jablotron_volta_heating_circuit_2") is not None
    assert hass.states.get("sensor.jablotron_volta_ch2_humidity") is not None


async def test_ch2_entities_absent_without_ch2(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Without CH2 no CH2 entity is created."""
    assert not [
        state.entity_id for state in hass.states.async_all() if "ch2" in state.entity_id
    ]
    assert hass.states.get("climate.jablotron_volta_heating_circuit_2") is None


async def test_legacy_unique_id_migrated_to_serial(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """Entries created with the "<host>_<device_id>" unique ID move to the serial."""
    entry = MockConfigEntry(domain=DOMAIN, data=dict(ENTRY_DATA), unique_id=f"{HOST}_1")
    entry.add_to_hass(hass)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.unique_id == SERIAL


async def test_climate_state(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Climate exposes mode, action and humidity from the circuit registers."""
    state = hass.states.get(CLIMATE_CH1)
    assert state.state == HVACMode.HEAT
    assert state.attributes["hvac_action"] == HVACAction.HEATING
    assert state.attributes["current_temperature"] == 21.5
    assert state.attributes["current_humidity"] == 55.0
    assert state.attributes["temperature"] == 22.0


async def test_climate_turn_off(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """climate.turn_off puts the circuit into standby."""
    await hass.services.async_call(
        Platform.CLIMATE,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: CLIMATE_CH1},
        blocking=True,
    )
    mock_client.async_write_register.assert_awaited_once_with(
        REG_CH1_MODE, CH_MODE_STANDBY
    )


async def test_number_write(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Setting a number writes the scaled value to its register."""
    await hass.services.async_call(
        Platform.NUMBER,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: BUILDING_MOMENTUM, ATTR_VALUE: 72},
        blocking=True,
    )
    mock_client.async_write_register.assert_awaited_once_with(
        REG_REGU_BUILDING_MOMENTUM, 72
    )


@pytest.mark.parametrize(
    "error",
    [JablotronVoltaConnectionError("down"), JablotronVoltaResponseError("rejected")],
)
async def test_failed_write_raises(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: AsyncMock,
    error: Exception,
) -> None:
    """A failed write surfaces as an action error instead of silently succeeding."""
    mock_client.async_write_register.side_effect = error
    with pytest.raises(HomeAssistantError) as exc_info:
        await hass.services.async_call(
            Platform.NUMBER,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: BUILDING_MOMENTUM, ATTR_VALUE: 72},
            blocking=True,
        )
    assert exc_info.value.translation_key == "write_failed"


@pytest.mark.parametrize(
    ("failures", "raises"),
    [(1, False), (2, True)],
)
async def test_reset_error_button(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_client: AsyncMock,
    failures: int,
    raises: bool,
) -> None:
    """Reset succeeds if either register is cleared and fails only if both fail."""
    mock_client.async_write_register.side_effect = [
        JablotronVoltaResponseError("rejected")
    ] * failures + [None] * (2 - failures)

    press = hass.services.async_call(
        Platform.BUTTON,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: "button.jablotron_volta_reset_error"},
        blocking=True,
    )
    if raises:
        with pytest.raises(HomeAssistantError):
            await press
    else:
        await press
    assert mock_client.async_write_register.await_args_list == [
        call_args(REG_SYS_ATTENTION_0, 0),
        call_args(REG_SYS_ERROR_CODE, 0),
    ]


async def test_diagnostics_redacts_network_details(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """Diagnostics never leak the host or network addresses."""
    diagnostics = await async_get_config_entry_diagnostics(hass, init_integration)

    assert diagnostics["entry_data"][CONF_HOST] == "**REDACTED**"
    assert diagnostics["data"]["ip_address"] == "**REDACTED**"
    assert HOST not in str(diagnostics)
    assert diagnostics["data"]["cpu_temperature"] == 45.5
