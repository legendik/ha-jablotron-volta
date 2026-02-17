"""Select platform for Jablotron Volta integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONTROL_MODE_MAP,
    DOMAIN,
    MASTER_FAIL_MAP,
    OUT_TEMP_SOURCE_MAP,
    REGULATION_STRAT_MAP,
    REGU_MODE_MAP,
    REG_CH1_REGULATION_STRAT,
    REG_CH2_REGULATION_STRAT,
    REG_DHW_REGULATION_STRAT,
    REG_REGU_MODE_USER,
    REG_REGU_SOURCE_OUT_TEMPER,
    REG_SYS_CONTROL,
    REG_SYS_MASTER_FAIL,
)
from .coordinator import JablotronVoltaCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class JablotronVoltaSelectEntityDescription(SelectEntityDescription):
    """Describes Jablotron Volta select entity."""

    value_fn: Callable[[dict[str, Any]], int | None] | None = None
    options_map: dict[int, str] | None = None
    register: int | None = None
    available_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None


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
        options_map=OUT_TEMP_SOURCE_MAP,
        register=REG_REGU_SOURCE_OUT_TEMPER,
        value_fn=lambda data: data.get("outdoor_temp_source"),
    ),
    JablotronVoltaSelectEntityDescription(
        key="dhw_regulation_strategy",
        translation_key="dhw_regulation_strategy",
        options_map={0: "strategy_0", 1: "strategy_1", 2: "strategy_2"},
        register=REG_DHW_REGULATION_STRAT,
        value_fn=lambda data: data.get("dhw_regulation_strategy"),
    ),
    JablotronVoltaSelectEntityDescription(
        key="ch1_regulation_strategy",
        translation_key="ch1_regulation_strategy",
        options_map=REGULATION_STRAT_MAP,
        register=REG_CH1_REGULATION_STRAT,
        value_fn=lambda data: data.get("ch1_regulation_strategy"),
    ),
    JablotronVoltaSelectEntityDescription(
        key="ch2_regulation_strategy",
        translation_key="ch2_regulation_strategy",
        options_map=REGULATION_STRAT_MAP,
        register=REG_CH2_REGULATION_STRAT,
        value_fn=lambda data: data.get("ch2_regulation_strategy"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSelectEntityDescription(
        key="control_mode",
        translation_key="control_mode",
        options_map=CONTROL_MODE_MAP,
        register=REG_SYS_CONTROL,
        value_fn=lambda data: data.get("control_mode"),
    ),
    JablotronVoltaSelectEntityDescription(
        key="master_fail_mode",
        translation_key="master_fail_mode",
        options_map=MASTER_FAIL_MAP,
        register=REG_SYS_MASTER_FAIL,
        value_fn=lambda data: data.get("master_fail_mode"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jablotron Volta select entities."""
    coordinator: JablotronVoltaCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SelectEntity] = []

    for description in SELECT_TYPES:
        if description.available_fn and not description.available_fn(coordinator):
            continue

        entities.append(JablotronVoltaSelect(coordinator, entry, description))

    async_add_entities(entities)


class JablotronVoltaSelect(CoordinatorEntity, SelectEntity):
    """Representation of a Jablotron Volta select entity."""

    entity_description: JablotronVoltaSelectEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        entry: ConfigEntry,
        description: JablotronVoltaSelectEntityDescription,
    ) -> None:
        """Initialize the select entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

        # Set options from the map
        if description.options_map:
            self._attr_options = list(description.options_map.values())

    @property
    def current_option(self) -> str | None:
        """Return the selected option."""
        if self.entity_description.value_fn and self.entity_description.options_map:
            value = self.entity_description.value_fn(self.coordinator.data)
            if value is not None:
                return self.entity_description.options_map.get(value)
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        if (
            not self.entity_description.options_map
            or not self.entity_description.register
        ):
            return

        # Find the value for the selected option
        value = None
        for key, val in self.entity_description.options_map.items():
            if val == option:
                value = key
                break

        if value is None:
            _LOGGER.error(
                "Invalid option %s for %s", option, self.entity_description.key
            )
            return

        success = await self.hass.async_add_executor_job(
            self.coordinator.client.write_register,
            self.entity_description.register,
            value,
        )

        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set %s to %s", self.entity_description.key, option)
