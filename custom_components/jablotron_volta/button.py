"""Button platform for Jablotron Volta integration."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_SYS_ATTENTION_0, REG_SYS_ERROR_CODE, REG_SYS_RESET
from .coordinator import JablotronVoltaCoordinator

_LOGGER = logging.getLogger(__name__)


BUTTON_TYPES: tuple[ButtonEntityDescription, ...] = (
    ButtonEntityDescription(
        key="reset_error",
        translation_key="reset_error",
        name="Reset Error",
    ),
    ButtonEntityDescription(
        key="restart_device",
        translation_key="restart_device",
        name="Restart Device",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jablotron Volta button entities."""
    coordinator: JablotronVoltaCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[ButtonEntity] = [
        JablotronVoltaResetErrorButton(coordinator, entry),
        JablotronVoltaRestartButton(coordinator, entry),
    ]

    async_add_entities(entities)


class JablotronVoltaButtonBase(CoordinatorEntity, ButtonEntity):
    """Base class for Jablotron Volta buttons."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        entry: ConfigEntry,
        key: str,
        name: str,
    ) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_name = name
        self._attr_translation_key = key
        self._attr_device_info = coordinator.device_info


class JablotronVoltaResetErrorButton(JablotronVoltaButtonBase):
    """Button to reset errors/attention notifications."""

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the reset error button."""
        super().__init__(coordinator, entry, "reset_error", "Reset Error")

    async def async_press(self) -> None:
        """Handle the button press."""
        # Write 0 to attention register to reset
        success1 = await self.hass.async_add_executor_job(
            self.coordinator.client.write_register,
            REG_SYS_ATTENTION_0,
            0,
        )

        # Also try to reset error code if system access is available
        success2 = await self.hass.async_add_executor_job(
            self.coordinator.client.write_register,
            REG_SYS_ERROR_CODE,
            0,
        )

        if success1 or success2:
            await self.coordinator.async_request_refresh()
            _LOGGER.info("Error/attention reset triggered")
        else:
            _LOGGER.error("Failed to reset errors")


class JablotronVoltaRestartButton(JablotronVoltaButtonBase):
    """Button to restart the device."""

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the restart button."""
        super().__init__(coordinator, entry, "restart_device", "Restart Device")

    async def async_press(self) -> None:
        """Handle the button press."""
        # Write non-zero value to trigger restart
        success = await self.hass.async_add_executor_job(
            self.coordinator.client.write_register,
            REG_SYS_RESET,
            1,
        )

        if success:
            _LOGGER.warning("Device restart triggered - device will be unavailable briefly")
        else:
            _LOGGER.error("Failed to restart device")
