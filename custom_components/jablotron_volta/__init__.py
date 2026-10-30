"""The Jablotron Volta integration."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .coordinator import JablotronVoltaConfigEntry, JablotronVoltaCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.CLIMATE,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(
    hass: HomeAssistant, entry: JablotronVoltaConfigEntry
) -> bool:
    """Set up Jablotron Volta from a config entry."""
    coordinator = JablotronVoltaCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    _async_migrate_unique_id(hass, entry, coordinator.serial_number)

    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: JablotronVoltaConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


@callback
def _async_migrate_unique_id(
    hass: HomeAssistant, entry: JablotronVoltaConfigEntry, serial_number: str | None
) -> None:
    """Move entries created with the legacy "<host>_<device_id>" unique ID to the serial."""
    if serial_number is None or entry.unique_id == serial_number:
        return
    if hass.config_entries.async_entry_for_domain_unique_id(DOMAIN, serial_number):
        _LOGGER.warning(
            "Device with serial number %s is configured more than once; "
            "remove the duplicate entry",
            serial_number,
        )
        return
    hass.config_entries.async_update_entry(entry, unique_id=serial_number)
