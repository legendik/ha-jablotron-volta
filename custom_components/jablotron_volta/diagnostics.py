"""Diagnostics support for Jablotron Volta."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant

from .coordinator import JablotronVoltaConfigEntry

_LOGGER = logging.getLogger(__name__)

TO_REDACT = {CONF_HOST, "ip_address", "subnet_mask", "gateway"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: JablotronVoltaConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "device": {
            "firmware_version": coordinator.firmware_version,
            "hardware_version": coordinator.hardware_version,
            "ch2_available": coordinator.ch2_available,
        },
        "data": async_redact_data(coordinator.data, TO_REDACT),
    }
