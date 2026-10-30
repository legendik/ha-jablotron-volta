"""Button platform for Jablotron Volta integration."""

from __future__ import annotations

import logging

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN, REG_SYS_ATTENTION_0, REG_SYS_ERROR_CODE, REG_SYS_RESET
from .coordinator import JablotronVoltaConfigEntry, JablotronVoltaCoordinator
from .entity import JablotronVoltaEntity
from .modbus_client import JablotronVoltaError

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

RESET_ERROR_BUTTON = ButtonEntityDescription(
    key="reset_error",
    translation_key="reset_error",
    entity_category=EntityCategory.CONFIG,
)
RESTART_BUTTON = ButtonEntityDescription(
    key="restart_device",
    translation_key="restart_device",
    device_class=ButtonDeviceClass.RESTART,
    entity_category=EntityCategory.CONFIG,
)
BUTTON_TYPES: tuple[ButtonEntityDescription, ...] = (
    RESET_ERROR_BUTTON,
    RESTART_BUTTON,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JablotronVoltaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Jablotron Volta button entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            JablotronVoltaResetErrorButton(coordinator),
            JablotronVoltaRestartButton(coordinator),
        ]
    )


class JablotronVoltaResetErrorButton(JablotronVoltaEntity, ButtonEntity):
    """Button to reset errors/attention notifications."""

    def __init__(self, coordinator: JablotronVoltaCoordinator) -> None:
        """Initialize the reset error button."""
        super().__init__(coordinator, RESET_ERROR_BUTTON.key)
        self.entity_description = RESET_ERROR_BUTTON

    async def async_press(self) -> None:
        """Clear the attention flags and the error code."""
        errors: list[JablotronVoltaError] = []
        for register in (REG_SYS_ATTENTION_0, REG_SYS_ERROR_CODE):
            try:
                await self.coordinator.client.async_write_register(register, 0)
            except JablotronVoltaError as err:
                _LOGGER.debug("Resetting register %s failed: %s", register, err)
                errors.append(err)

        # The device may refuse one of the two resets; only fail if both do
        if len(errors) == 2:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={
                    "entity_id": self.entity_id,
                    "error": str(errors[0]),
                },
            ) from errors[0]

        await self.coordinator.async_request_refresh()


class JablotronVoltaRestartButton(JablotronVoltaEntity, ButtonEntity):
    """Button to restart the device."""

    def __init__(self, coordinator: JablotronVoltaCoordinator) -> None:
        """Initialize the restart button."""
        super().__init__(coordinator, RESTART_BUTTON.key)
        self.entity_description = RESTART_BUTTON

    async def async_press(self) -> None:
        """Restart the device; it drops off the network briefly."""
        await self._async_write_register(REG_SYS_RESET, 1, refresh=False)
