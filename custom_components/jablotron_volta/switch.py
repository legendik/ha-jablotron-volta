"""Switch platform for Jablotron Volta integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    REG_CH1_FAST_COOLDOWN,
    REG_CH1_OPTIMAL_ON_OFF_ENABLE,
    REG_CH2_FAST_COOLDOWN,
    REG_CH2_OPTIMAL_ON_OFF_ENABLE,
)
from .coordinator import JablotronVoltaConfigEntry, JablotronVoltaCoordinator
from .entity import JablotronVoltaEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class JablotronVoltaSwitchEntityDescription(SwitchEntityDescription):
    """Describes Jablotron Volta switch entity."""

    value_fn: Callable[[dict[str, Any]], bool | None]
    register: int
    exists_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None


SWITCH_TYPES: tuple[JablotronVoltaSwitchEntityDescription, ...] = (
    JablotronVoltaSwitchEntityDescription(
        key="ch1_optimal_start",
        translation_key="ch1_optimal_start",
        register=REG_CH1_OPTIMAL_ON_OFF_ENABLE,
        value_fn=lambda data: data.get("ch1_optimal_start"),
    ),
    JablotronVoltaSwitchEntityDescription(
        key="ch1_fast_cooldown",
        translation_key="ch1_fast_cooldown",
        register=REG_CH1_FAST_COOLDOWN,
        value_fn=lambda data: data.get("ch1_fast_cooldown"),
    ),
    JablotronVoltaSwitchEntityDescription(
        key="ch2_optimal_start",
        translation_key="ch2_optimal_start",
        register=REG_CH2_OPTIMAL_ON_OFF_ENABLE,
        value_fn=lambda data: data.get("ch2_optimal_start"),
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSwitchEntityDescription(
        key="ch2_fast_cooldown",
        translation_key="ch2_fast_cooldown",
        register=REG_CH2_FAST_COOLDOWN,
        value_fn=lambda data: data.get("ch2_fast_cooldown"),
        exists_fn=lambda coord: coord.ch2_available,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JablotronVoltaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Jablotron Volta switch entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        JablotronVoltaSwitch(coordinator, description)
        for description in SWITCH_TYPES
        if description.exists_fn is None or description.exists_fn(coordinator)
    )


class JablotronVoltaSwitch(JablotronVoltaEntity, SwitchEntity):
    """Representation of a Jablotron Volta switch."""

    entity_description: JablotronVoltaSwitchEntityDescription
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        description: JablotronVoltaSwitchEntityDescription,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._async_write_register(self.entity_description.register, 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._async_write_register(self.entity_description.register, 0)
