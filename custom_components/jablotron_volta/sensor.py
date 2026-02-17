"""Sensor platform for Jablotron Volta integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfElectricPotential,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JablotronVoltaCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class JablotronVoltaSensorEntityDescription(SensorEntityDescription):
    """Describes Jablotron Volta sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType] | None = None
    available_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None


SENSOR_TYPES: tuple[JablotronVoltaSensorEntityDescription, ...] = (
    # Energy - For Energy Dashboard
    JablotronVoltaSensorEntityDescription(
        key="boiler_total_energy",
        translation_key="boiler_total_energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda data: data.get("boiler_total_energy"),
    ),
    # System Temperatures
    JablotronVoltaSensorEntityDescription(
        key="cpu_temperature",
        translation_key="cpu_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("cpu_temperature"),
    ),
    # Outdoor Temperatures
    JablotronVoltaSensorEntityDescription(
        key="outdoor_temp_damped",
        translation_key="outdoor_temperature_damped",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("outdoor_temp_damped"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="outdoor_temp_composite",
        translation_key="outdoor_temperature_composite",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("outdoor_temp_composite"),
    ),
    # Room Temperatures (from thermostats)
    JablotronVoltaSensorEntityDescription(
        key="ch1_temperature_current",
        translation_key="ch1_temperature_current",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch1_temperature_current"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch2_temperature_current",
        translation_key="ch2_temperature_current",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch2_temperature_current"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSensorEntityDescription(
        key="dhw_temperature_current",
        translation_key="dhw_temperature_current",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("dhw_temperature_current"),
    ),
    # Boiler Water Temperatures
    JablotronVoltaSensorEntityDescription(
        key="boiler_water_input_temp",
        translation_key="boiler_water_input_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("boiler_water_input_temp"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_water_return_temp",
        translation_key="boiler_water_return_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("boiler_water_return_temp"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_water_setpoint",
        translation_key="boiler_water_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("boiler_water_setpoint"),
    ),
    # CH1 Water Temperatures
    JablotronVoltaSensorEntityDescription(
        key="ch1_water_input_temp",
        translation_key="ch1_water_input_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch1_water_input_temp"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch1_water_return_temp",
        translation_key="ch1_water_return_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch1_water_return_temp"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch1_water_setpoint",
        translation_key="ch1_water_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch1_water_setpoint"),
    ),
    # CH2 Water Temperatures (conditional)
    JablotronVoltaSensorEntityDescription(
        key="ch2_water_input_temp",
        translation_key="ch2_water_input_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch2_water_input_temp"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch2_water_return_temp",
        translation_key="ch2_water_return_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch2_water_return_temp"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch2_water_setpoint",
        translation_key="ch2_water_setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch2_water_setpoint"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    # System Status
    JablotronVoltaSensorEntityDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda data: data.get("battery_voltage"),
    ),
    # Boiler Status
    JablotronVoltaSensorEntityDescription(
        key="boiler_pressure",
        translation_key="boiler_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        value_fn=lambda data: data.get("boiler_pressure"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_pump_power",
        translation_key="boiler_pump_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("boiler_pump_power"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_heating_power",
        translation_key="boiler_heating_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("boiler_heating_power"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_pwm_value",
        translation_key="boiler_pwm_value",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("boiler_pwm_value"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_active_segments",
        translation_key="boiler_active_segments",
        value_fn=lambda data: data.get("boiler_active_segments"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_inactive_segments",
        translation_key="boiler_inactive_segments",
        value_fn=lambda data: data.get("boiler_inactive_segments"),
    ),
    # CH1 Environmental
    JablotronVoltaSensorEntityDescription(
        key="ch1_humidity",
        translation_key="ch1_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("ch1_humidity"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch1_co2",
        translation_key="ch1_co2",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        value_fn=lambda data: data.get("ch1_co2"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch1_pump_power",
        translation_key="ch1_pump_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("ch1_pump_power"),
    ),
    # CH2 Environmental (conditional)
    JablotronVoltaSensorEntityDescription(
        key="ch2_humidity",
        translation_key="ch2_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("ch2_humidity"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch2_co2",
        translation_key="ch2_co2",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        value_fn=lambda data: data.get("ch2_co2"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch2_pump_power",
        translation_key="ch2_pump_power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("ch2_pump_power"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    # Device Information
    JablotronVoltaSensorEntityDescription(
        key="ip_address",
        translation_key="ip_address",
        value_fn=lambda data: data.get("ip_address"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="subnet_mask",
        translation_key="subnet_mask",
        value_fn=lambda data: data.get("subnet_mask"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="gateway",
        translation_key="gateway",
        value_fn=lambda data: data.get("gateway"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jablotron Volta sensors."""
    coordinator: JablotronVoltaCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    for description in SENSOR_TYPES:
        # Check if entity should be created based on availability function
        if description.available_fn and not description.available_fn(coordinator):
            continue

        entities.append(JablotronVoltaSensor(coordinator, entry, description))

    async_add_entities(entities)


class JablotronVoltaSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Jablotron Volta sensor."""

    entity_description: JablotronVoltaSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        entry: ConfigEntry,
        description: JablotronVoltaSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None
