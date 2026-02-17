"""Config flow for Jablotron Volta integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult

from .const import CONF_DEVICE_ID, DEFAULT_DEVICE_ID, DEFAULT_PORT, DOMAIN
from .modbus_client import JablotronModbusClient

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_DEVICE_ID, default=DEFAULT_DEVICE_ID): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=255)
        ),
    }
)


class JablotronVoltaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jablotron Volta."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Test connection
            client = JablotronModbusClient(
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input[CONF_DEVICE_ID],
            )

            try:
                # Test connection in executor
                connected = await self.hass.async_add_executor_job(client.connect)

                if connected:
                    # Try to read a basic register to verify communication
                    test_read = await self.hass.async_add_executor_job(
                        client.read_input_registers, 0, 1
                    )

                    await self.hass.async_add_executor_job(client.close)

                    if test_read is not None:
                        # Create unique ID based on host and device ID
                        await self.async_set_unique_id(
                            f"{user_input[CONF_HOST]}_{user_input[CONF_DEVICE_ID]}"
                        )
                        self._abort_if_unique_id_configured()

                        return self.async_create_entry(
                            title=f"Jablotron Volta ({user_input[CONF_HOST]})",
                            data=user_input,
                        )
                    else:
                        errors["base"] = "cannot_read"
                else:
                    errors["base"] = "cannot_connect"

            except Exception as err:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception during setup: %s", err)
                errors["base"] = "unknown"
            finally:
                # Ensure connection is closed
                try:
                    await self.hass.async_add_executor_job(client.close)
                except Exception:  # pylint: disable=broad-except
                    pass

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
