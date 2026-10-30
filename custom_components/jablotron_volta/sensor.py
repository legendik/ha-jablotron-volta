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
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPressure,
    UnitOfRatio,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import JablotronVoltaConfigEntry, JablotronVoltaCoordinator
from .entity import JablotronVoltaEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class JablotronVoltaSensorEntityDescription(SensorEntityDescription):
    """Describes Jablotron Volta sensor entity."""

    value_fn: Callable[[dict[str, Any]], StateType]
    exists_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None


def _temperature(
    key: str, translation_key: str, **kwargs: Any
) -> JablotronVoltaSensorEntityDescription:
    """Describe a Celsius temperature sensor reading data[key]."""
    return JablotronVoltaSensorEntityDescription(
        key=key,
        translation_key=translation_key,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        suggested_display_precision=1,
        value_fn=lambda data: data.get(key),
        **kwargs,
    )


def _percentage(key: str, **kwargs: Any) -> JablotronVoltaSensorEntityDescription:
    """Describe a percentage sensor reading data[key]."""
    return JablotronVoltaSensorEntityDescription(
        key=key,
        translation_key=key,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        value_fn=lambda data: data.get(key),
        **kwargs,
    )


def _ch2_available(coordinator: JablotronVoltaCoordinator) -> bool:
    return coordinator.ch2_available


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
    _temperature(
        "cpu_temperature",
        "cpu_temperature",
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    # Outdoor Temperatures
    _temperature("outdoor_temp_damped", "outdoor_temperature_damped"),
    _temperature("outdoor_temp_composite", "outdoor_temperature_composite"),
    # Room Temperatures (from thermostats)
    _temperature("ch1_temperature_current", "ch1_temperature_current"),
    _temperature(
        "ch2_temperature_current", "ch2_temperature_current", exists_fn=_ch2_available
    ),
    # Boiler Water Temperatures
    _temperature("boiler_water_input_temp", "boiler_water_input_temperature"),
    _temperature("boiler_water_return_temp", "boiler_water_return_temperature"),
    _temperature("boiler_water_setpoint", "boiler_water_setpoint"),
    # CH1 Water Temperatures
    _temperature("ch1_water_input_temp", "ch1_water_input_temperature"),
    _temperature("ch1_water_return_temp", "ch1_water_return_temperature"),
    _temperature("ch1_water_setpoint", "ch1_water_setpoint"),
    # CH2 Water Temperatures (conditional)
    _temperature(
        "ch2_water_input_temp", "ch2_water_input_temperature", exists_fn=_ch2_available
    ),
    _temperature(
        "ch2_water_return_temp",
        "ch2_water_return_temperature",
        exists_fn=_ch2_available,
    ),
    _temperature("ch2_water_setpoint", "ch2_water_setpoint", exists_fn=_ch2_available),
    # System Status
    JablotronVoltaSensorEntityDescription(
        key="battery_voltage",
        translation_key="battery_voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("battery_voltage"),
    ),
    # Boiler Status
    JablotronVoltaSensorEntityDescription(
        key="boiler_pressure",
        translation_key="boiler_pressure",
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfPressure.BAR,
        suggested_display_precision=1,
        value_fn=lambda data: data.get("boiler_pressure"),
    ),
    _percentage("boiler_pump_power"),
    _percentage("boiler_heating_power"),
    JablotronVoltaSensorEntityDescription(
        key="boiler_pwm_value",
        translation_key="boiler_pwm_value",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
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
    _percentage("ch1_humidity", device_class=SensorDeviceClass.HUMIDITY),
    JablotronVoltaSensorEntityDescription(
        key="ch1_co2",
        translation_key="ch1_co2",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfRatio.PARTS_PER_MILLION,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("ch1_co2"),
    ),
    _percentage("ch1_pump_power"),
    # CH2 Environmental (conditional)
    _percentage(
        "ch2_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        exists_fn=_ch2_available,
    ),
    JablotronVoltaSensorEntityDescription(
        key="ch2_co2",
        translation_key="ch2_co2",
        device_class=SensorDeviceClass.CO2,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfRatio.PARTS_PER_MILLION,
        suggested_display_precision=0,
        value_fn=lambda data: data.get("ch2_co2"),
        exists_fn=_ch2_available,
    ),
    _percentage("ch2_pump_power", exists_fn=_ch2_available),
    # Network Information
    JablotronVoltaSensorEntityDescription(
        key="ip_address",
        translation_key="ip_address",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("ip_address"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="subnet_mask",
        translation_key="subnet_mask",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("subnet_mask"),
    ),
    JablotronVoltaSensorEntityDescription(
        key="gateway",
        translation_key="gateway",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: data.get("gateway"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JablotronVoltaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Jablotron Volta sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        JablotronVoltaSensor(coordinator, description)
        for description in SENSOR_TYPES
        if description.exists_fn is None or description.exists_fn(coordinator)
    )


class JablotronVoltaSensor(JablotronVoltaEntity, SensorEntity):
    """Representation of a Jablotron Volta sensor."""

    entity_description: JablotronVoltaSensorEntityDescription

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        description: JablotronVoltaSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return self.entity_description.value_fn(self.coordinator.data)
