"""Config flow for Jablotron Volta integration."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import CONF_DEVICE_ID, DEFAULT_DEVICE_ID, DEFAULT_PORT, DOMAIN
from .modbus_client import (
    JablotronModbusClient,
    JablotronVoltaConnectionError,
    JablotronVoltaResponseError,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=65535)
        ),
        vol.Optional(CONF_DEVICE_ID, default=DEFAULT_DEVICE_ID): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=255)
        ),
    }
)


def _legacy_unique_id(data: Mapping[str, Any]) -> str:
    """Return the unique ID format used before the serial number was adopted."""
    return f"{data[CONF_HOST]}_{data[CONF_DEVICE_ID]}"


def _entry_title(data: Mapping[str, Any]) -> str:
    return f"Jablotron Volta ({data[CONF_HOST]})"


class JablotronVoltaConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jablotron Volta."""

    VERSION = 1

    async def _async_read_serial(
        self, user_input: dict[str, Any], errors: dict[str, str]
    ) -> str | None:
        """Validate the connection settings; fill errors and return None on failure."""
        client = JablotronModbusClient(
            user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_DEVICE_ID]
        )
        try:
            return await client.async_read_serial_number()
        except JablotronVoltaConnectionError:
            errors["base"] = "cannot_connect"
        except JablotronVoltaResponseError:
            errors["base"] = "cannot_read"
        except Exception:
            _LOGGER.exception("Unexpected exception while validating connection")
            errors["base"] = "unknown"
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None and (
            serial := await self._async_read_serial(user_input, errors)
        ):
            await self.async_set_unique_id(serial)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=_entry_title(user_input), data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change connection settings of an existing entry."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}

        if user_input is not None and (
            serial := await self._async_read_serial(user_input, errors)
        ):
            await self.async_set_unique_id(serial)
            if entry.unique_id == _legacy_unique_id(entry.data):
                # Entry never got migrated to the serial (e.g. the device moved
                # to a new IP before the upgrade), so there is nothing to compare.
                self._abort_if_unique_id_configured()
            else:
                self._abort_if_unique_id_mismatch(reason="wrong_device")
            return self.async_update_reload_and_abort(
                entry,
                unique_id=serial,
                # Keep titles the user renamed; refresh the generated one
                title=_entry_title(user_input)
                if entry.title == _entry_title(entry.data)
                else entry.title,
                data_updates=user_input,
            )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input or entry.data
            ),
            errors=errors,
        )
