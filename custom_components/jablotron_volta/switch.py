"""Switch platform for Jablotron Volta integration."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_CH1_FAST_COOLDOWN,
    REG_CH1_OPTIMAL_ON_OFF_ENABLE,
    REG_CH2_FAST_COOLDOWN,
    REG_CH2_OPTIMAL_ON_OFF_ENABLE,
)
from .coordinator import JablotronVoltaCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class JablotronVoltaSwitchEntityDescription(SwitchEntityDescription):
    """Describes Jablotron Volta switch entity."""

    value_fn: Callable[[dict[str, Any]], bool] | None = None
    register: int | None = None
    available_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None


SWITCH_TYPES: tuple[JablotronVoltaSwitchEntityDescription, ...] = (
    JablotronVoltaSwitchEntityDescription(
        key="ch1_optimal_start",
        translation_key="ch1_optimal_start",
        name="CH1 Optimal Start/Stop",
        register=REG_CH1_OPTIMAL_ON_OFF_ENABLE,
        value_fn=lambda data: data.get("ch1_optimal_start", False),
    ),
    JablotronVoltaSwitchEntityDescription(
        key="ch1_fast_cooldown",
        translation_key="ch1_fast_cooldown",
        name="CH1 Fast Cooldown",
        register=REG_CH1_FAST_COOLDOWN,
        value_fn=lambda data: data.get("ch1_fast_cooldown", False),
    ),
    JablotronVoltaSwitchEntityDescription(
        key="ch2_optimal_start",
        translation_key="ch2_optimal_start",
        name="CH2 Optimal Start/Stop",
        register=REG_CH2_OPTIMAL_ON_OFF_ENABLE,
        value_fn=lambda data: data.get("ch2_optimal_start", False),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSwitchEntityDescription(
        key="ch2_fast_cooldown",
        translation_key="ch2_fast_cooldown",
        name="CH2 Fast Cooldown",
        register=REG_CH2_FAST_COOLDOWN,
        value_fn=lambda data: data.get("ch2_fast_cooldown", False),
        available_fn=lambda coord: coord.ch2_available,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jablotron Volta switch entities."""
    coordinator: JablotronVoltaCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SwitchEntity] = []

    for description in SWITCH_TYPES:
        if description.available_fn and not description.available_fn(coordinator):
            continue

        entities.append(JablotronVoltaSwitch(coordinator, entry, description))

    async_add_entities(entities)


class JablotronVoltaSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a Jablotron Volta switch."""

    entity_description: JablotronVoltaSwitchEntityDescription

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        entry: ConfigEntry,
        description: JablotronVoltaSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return False

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        if not self.entity_description.register:
            return

        success = await self.hass.async_add_executor_job(
            self.coordinator.client.write_register,
            self.entity_description.register,
            1,
        )

        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to turn on %s", self.entity_description.key)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        if not self.entity_description.register:
            return

        success = await self.hass.async_add_executor_job(
            self.coordinator.client.write_register,
            self.entity_description.register,
            0,
        )

        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to turn off %s", self.entity_description.key)
