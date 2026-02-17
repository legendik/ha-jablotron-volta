"""Binary sensor platform for Jablotron Volta integration."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JablotronVoltaCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class JablotronVoltaBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Jablotron Volta binary sensor entity."""

    value_fn: Callable[[dict], bool] | None = None
    available_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None


BINARY_SENSOR_TYPES: tuple[JablotronVoltaBinarySensorEntityDescription, ...] = (
    JablotronVoltaBinarySensorEntityDescription(
        key="dhw_heating",
        translation_key="dhw_heating",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda data: data.get("dhw_state_heat", False),
    ),
    JablotronVoltaBinarySensorEntityDescription(
        key="ch1_heating",
        translation_key="ch1_heating",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda data: data.get("ch1_state_heat", False),
    ),
    JablotronVoltaBinarySensorEntityDescription(
        key="ch2_heating",
        translation_key="ch2_heating",
        device_class=BinarySensorDeviceClass.HEAT,
        value_fn=lambda data: data.get("ch2_state_heat", False),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaBinarySensorEntityDescription(
        key="system_alert",
        translation_key="system_alert",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda data: data.get("system_attention", 0) != 0,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jablotron Volta binary sensors."""
    coordinator: JablotronVoltaCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[BinarySensorEntity] = []

    for description in BINARY_SENSOR_TYPES:
        if description.available_fn and not description.available_fn(coordinator):
            continue

        entities.append(JablotronVoltaBinarySensor(coordinator, entry, description))

    async_add_entities(entities)


class JablotronVoltaBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a Jablotron Volta binary sensor."""

    entity_description: JablotronVoltaBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        entry: ConfigEntry,
        description: JablotronVoltaBinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return False
