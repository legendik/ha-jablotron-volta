"""Base entity for Jablotron Volta."""

from __future__ import annotations

import logging

from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JablotronVoltaCoordinator
from .modbus_client import JablotronVoltaError

_LOGGER = logging.getLogger(__name__)


class JablotronVoltaEntity(CoordinatorEntity[JablotronVoltaCoordinator]):
    """Common base for all Jablotron Volta entities."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: JablotronVoltaCoordinator, key: str) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{key}"
        self._attr_device_info = coordinator.device_info

    async def _async_write_register(
        self, register: int, value: int, *, refresh: bool = True
    ) -> None:
        """Write a register and refresh data; raise a user-facing error on failure."""
        try:
            await self.coordinator.client.async_write_register(register, value)
        except JablotronVoltaError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={
                    "entity_id": self.entity_id,
                    "error": str(err),
                },
            ) from err
        if refresh:
            await self.coordinator.async_request_refresh()
