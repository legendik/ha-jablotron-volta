"""Binary sensor platform for Jablotron Volta integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import JablotronVoltaConfigEntry, JablotronVoltaCoordinator
from .entity import JablotronVoltaEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class JablotronVoltaBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Jablotron Volta binary sensor entity."""

    value_fn: Callable[[dict[str, Any]], bool | None]
    exists_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None


BINARY_SENSOR_TYPES: tuple[JablotronVoltaBinarySensorEntityDescription, ...] = (
    JablotronVoltaBinarySensorEntityDescription(
        key="ch1_heating",
        translation_key="ch1_heating",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda data: data.get("ch1_state_heat"),
    ),
    JablotronVoltaBinarySensorEntityDescription(
        key="ch2_heating",
        translation_key="ch2_heating",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda data: data.get("ch2_state_heat"),
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaBinarySensorEntityDescription(
        key="system_alert",
        translation_key="system_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: (
            None
            if (attention := data.get("system_attention")) is None
            else attention != 0
        ),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JablotronVoltaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Jablotron Volta binary sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        JablotronVoltaBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_TYPES
        if description.exists_fn is None or description.exists_fn(coordinator)
    )


class JablotronVoltaBinarySensor(JablotronVoltaEntity, BinarySensorEntity):
    """Representation of a Jablotron Volta binary sensor."""

    entity_description: JablotronVoltaBinarySensorEntityDescription

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        description: JablotronVoltaBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.entity_description.value_fn(self.coordinator.data)
