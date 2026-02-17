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
        name="Total Heating Energy",
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda data: data.get("boiler_total_energy"),
    ),
    # System Temperatures
    JablotronVoltaSensorEntityDescription(
        key="cpu_temperature",
        translation_key="cpu_temperature",
        name="CPU Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("cpu_temperature"),
    ),
    # Outdoor Temperatures
    JablotronVoltaSensorEntityDescription(
        key="outdoor_temp_damped",
        translation_key="outdoor_temp_damped",
        name="Outdoor Temperature (Damped)",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("outdoor_temp_damped"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="outdoor_temp_composite",
        translation_key="outdoor_temp_composite",
        name="Outdoor Temperature (Composite)",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("outdoor_temp_composite"),
    ),
    # Boiler Water Temperatures
    JablotronVoltaSensorEntityDescription(
        key="boiler_water_input_temp",
        translation_key="boiler_water_input_temp",
        name="Boiler Water Input Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("boiler_water_input_temp"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_water_return_temp",
        translation_key="boiler_water_return_temp",
        name="Boiler Water Return Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("boiler_water_return_temp"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_water_setpoint",
        translation_key="boiler_water_setpoint",
        name="Boiler Water Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("boiler_water_setpoint"),
    ),
    # CH1 Water Temperatures
    JablotronVoltaSensorEntityDescription(
        key="ch1_water_input_temp",
        translation_key="ch1_water_input_temp",
        name="CH1 Water Input Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch1_water_input_temp"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch1_water_return_temp",
        translation_key="ch1_water_return_temp",
        name="CH1 Water Return Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch1_water_return_temp"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch1_water_setpoint",
        translation_key="ch1_water_setpoint",
        name="CH1 Water Setpoint",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch1_water_setpoint"),
    ),
    # CH2 Water Temperatures (conditional)
    JablotronVoltaSensorEntityDescription(
        key="ch2_water_input_temp",
        translation_key="ch2_water_input_temp",
        name="CH2 Water Input Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch2_water_input_temp"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch2_water_return_temp",
        translation_key="ch2_water_return_temp",
        name="CH2 Water Return Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("ch2_water_return_temp"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch2_water_setpoint",
        translation_key="ch2_water_setpoint",
        name="CH2 Water Setpoint",
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
        name="Battery Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        value_fn=lambda data: data.get("battery_voltage"),
    ),
    # Boiler Status
    JablotronVoltaSensorEntityDescription(
        key="boiler_pressure",
        translation_key="boiler_pressure",
        name="Boiler Water Pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        value_fn=lambda data: data.get("boiler_pressure"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_pump_power",
        translation_key="boiler_pump_power",
        name="Boiler Pump Power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("boiler_pump_power"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_heating_power",
        translation_key="boiler_heating_power",
        name="Boiler Heating Power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("boiler_heating_power"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_pwm_value",
        translation_key="boiler_pwm_value",
        name="Boiler PWM Value",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("boiler_pwm_value"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_active_segments",
        translation_key="boiler_active_segments",
        name="Boiler Active Segments",
        value_fn=lambda data: data.get("boiler_active_segments"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="boiler_inactive_segments",
        translation_key="boiler_inactive_segments",
        name="Boiler Inactive Segments",
        value_fn=lambda data: data.get("boiler_inactive_segments"),
    ),
    # CH1 Environmental
    JablotronVoltaSensorEntityDescription(
        key="ch1_humidity",
        translation_key="ch1_humidity",
        name="CH1 Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("ch1_humidity"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch1_co2",
        translation_key="ch1_co2",
        name="CH1 CO2",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        value_fn=lambda data: data.get("ch1_co2"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch1_pump_power",
        translation_key="ch1_pump_power",
        name="CH1 Pump Power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("ch1_pump_power"),
    ),
    # CH2 Environmental (conditional)
    JablotronVoltaSensorEntityDescription(
        key="ch2_humidity",
        translation_key="ch2_humidity",
        name="CH2 Humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("ch2_humidity"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch2_co2",
        translation_key="ch2_co2",
        name="CH2 CO2",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        value_fn=lambda data: data.get("ch2_co2"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch2_pump_power",
        translation_key="ch2_pump_power",
        name="CH2 Pump Power",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: data.get("ch2_pump_power"),
        available_fn=lambda coord: coord.ch2_available,
    ),
    # Device Information
    JablotronVoltaSensorEntityDescription(
        key="ip_address",
        translation_key="ip_address",
        name="IP Address",
        value_fn=lambda data: data.get("ip_address"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="subnet_mask",
        translation_key="subnet_mask",
        name="Subnet Mask",
        value_fn=lambda data: data.get("subnet_mask"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="gateway",
        translation_key="gateway",
        name="Gateway",
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
