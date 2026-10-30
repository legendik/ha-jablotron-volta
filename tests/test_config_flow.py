"""Tests for the Jablotron Volta config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.jablotron_volta.const import DOMAIN
from custom_components.jablotron_volta.modbus_client import (
    JablotronVoltaConnectionError,
    JablotronVoltaResponseError,
)

from .conftest import ENTRY_DATA, HOST, SERIAL

NEW_HOST = "192.168.1.200"


async def test_user_flow_creates_entry(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """A reachable device creates an entry keyed by its serial number."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], dict(ENTRY_DATA)
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Jablotron Volta ({HOST})"
    assert result["data"] == ENTRY_DATA
    assert result["result"].unique_id == SERIAL


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (JablotronVoltaConnectionError("down"), "cannot_connect"),
        (JablotronVoltaResponseError("rejected"), "cannot_read"),
        (RuntimeError("boom"), "unknown"),
    ],
)
async def test_user_flow_errors_recover(
    hass: HomeAssistant,
    mock_client: AsyncMock,
    side_effect: Exception,
    error: str,
) -> None:
    """Validation errors are shown and the form can be resubmitted."""
    mock_client.async_read_serial_number.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], dict(ENTRY_DATA)
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error}

    mock_client.async_read_serial_number.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], dict(ENTRY_DATA)
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_already_configured(
    hass: HomeAssistant, mock_client: AsyncMock, mock_config_entry: MockConfigEntry
) -> None:
    """The same device (by serial) cannot be added twice, even under a new IP."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST: NEW_HOST}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reconfigure_updates_host(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Reconfigure stores the new host and refreshes the generated title."""
    result = await init_integration.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST: NEW_HOST}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert init_integration.data[CONF_HOST] == NEW_HOST
    assert init_integration.title == f"Jablotron Volta ({NEW_HOST})"


async def test_reconfigure_keeps_custom_title(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """A title renamed by the user survives reconfiguration."""
    hass.config_entries.async_update_entry(init_integration, title="Kotel")
    result = await init_integration.start_reconfigure_flow(hass)
    await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST: NEW_HOST}
    )
    await hass.async_block_till_done()
    assert init_integration.title == "Kotel"


async def test_reconfigure_wrong_device(
    hass: HomeAssistant, init_integration: MockConfigEntry, mock_client: AsyncMock
) -> None:
    """Pointing an entry at a different boiler is refused."""
    result = await init_integration.start_reconfigure_flow(hass)
    mock_client.async_read_serial_number.return_value = "999"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST: NEW_HOST}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "wrong_device"
    assert init_integration.data[CONF_HOST] == HOST


async def test_reconfigure_legacy_entry_adopts_serial(
    hass: HomeAssistant, mock_client: AsyncMock
) -> None:
    """An entry still on the legacy "<host>_<id>" unique ID can be moved to a new IP."""
    entry = MockConfigEntry(domain=DOMAIN, data=dict(ENTRY_DATA), unique_id=f"{HOST}_1")
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**ENTRY_DATA, CONF_HOST: NEW_HOST}
    )
    await hass.async_block_till_done()

    assert result["reason"] == "reconfigure_successful"
    assert entry.unique_id == SERIAL
    assert entry.data[CONF_HOST] == NEW_HOST
