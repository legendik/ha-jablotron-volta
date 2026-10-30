"""Select platform for Jablotron Volta integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONTROL_MODE_MAP,
    MASTER_FAIL_MAP,
    OUT_TEMP_SOURCE_MAP,
    REG_CH1_REGULATION_STRAT,
    REG_CH2_REGULATION_STRAT,
    REG_REGU_MODE_USER,
    REG_REGU_SOURCE_OUT_TEMPER,
    REG_SYS_CONTROL,
    REG_SYS_MASTER_FAIL,
    REGU_MODE_MAP,
    REGULATION_STRAT_MAP,
)
from .coordinator import JablotronVoltaConfigEntry, JablotronVoltaCoordinator
from .entity import JablotronVoltaEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class JablotronVoltaSelectEntityDescription(SelectEntityDescription):
    """Describes Jablotron Volta select entity."""

    value_fn: Callable[[dict[str, Any]], int | None]
    options_map: dict[int, str]
    register: int
    exists_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None


SELECT_TYPES: tuple[JablotronVoltaSelectEntityDescription, ...] = (
    JablotronVoltaSelectEntityDescription(
        key="regulation_mode",
        translation_key="regulation_mode",
        options_map=REGU_MODE_MAP,
        register=REG_REGU_MODE_USER,
        value_fn=lambda data: data.get("regulation_mode_user"),
    ),
    JablotronVoltaSelectEntityDescription(
        key="outdoor_temp_source",
        translation_key="outdoor_temperature_source",
        entity_category=EntityCategory.CONFIG,
        options_map=OUT_TEMP_SOURCE_MAP,
        register=REG_REGU_SOURCE_OUT_TEMPER,
        value_fn=lambda data: data.get("outdoor_temp_source"),
    ),
    JablotronVoltaSelectEntityDescription(
        key="ch1_regulation_strategy",
        translation_key="ch1_regulation_strategy",
        entity_category=EntityCategory.CONFIG,
        options_map=REGULATION_STRAT_MAP,
        register=REG_CH1_REGULATION_STRAT,
        value_fn=lambda data: data.get("ch1_regulation_strategy"),
    ),
    JablotronVoltaSelectEntityDescription(
        key="ch2_regulation_strategy",
        translation_key="ch2_regulation_strategy",
        entity_category=EntityCategory.CONFIG,
        options_map=REGULATION_STRAT_MAP,
        register=REG_CH2_REGULATION_STRAT,
        value_fn=lambda data: data.get("ch2_regulation_strategy"),
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSelectEntityDescription(
        key="control_mode",
        translation_key="control_mode",
        entity_category=EntityCategory.CONFIG,
        options_map=CONTROL_MODE_MAP,
        register=REG_SYS_CONTROL,
        value_fn=lambda data: data.get("control_mode"),
    ),
    JablotronVoltaSelectEntityDescription(
        key="master_fail_mode",
        translation_key="master_fail_mode",
        entity_category=EntityCategory.CONFIG,
        options_map=MASTER_FAIL_MAP,
        register=REG_SYS_MASTER_FAIL,
        value_fn=lambda data: data.get("master_fail_mode"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JablotronVoltaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Jablotron Volta select entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        JablotronVoltaSelect(coordinator, description)
        for description in SELECT_TYPES
        if description.exists_fn is None or description.exists_fn(coordinator)
    )


class JablotronVoltaSelect(JablotronVoltaEntity, SelectEntity):
    """Representation of a Jablotron Volta select entity."""

    entity_description: JablotronVoltaSelectEntityDescription

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        description: JablotronVoltaSelectEntityDescription,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_options = list(description.options_map.values())
        self._option_to_value = {
            option: value for value, option in description.options_map.items()
        }

    @property
    def current_option(self) -> str | None:
        """Return the selected option."""
        value = self.entity_description.value_fn(self.coordinator.data)
        if value is None:
            return None
        return self.entity_description.options_map.get(value)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        # SelectEntity validates the option against self.options before calling
        await self._async_write_register(
            self.entity_description.register, self._option_to_value[option]
        )
