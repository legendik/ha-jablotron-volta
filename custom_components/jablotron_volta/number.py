"""Number platform for Jablotron Volta integration."""
from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import NumberEntity, NumberEntityDescription, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    REG_CH1_EQUITHERM_OFFSET,
    REG_CH1_EQUITHERM_ROOM_EFFECT,
    REG_CH1_EQUITHERM_SLOPE,
    REG_CH1_LIMIT_HEAT_TEMPER,
    REG_CH1_TEMPER_ANTIFROST,
    REG_CH1_TEMPER_HYSTERESIS,
    REG_CH1_TEMPER_WATER_MAX,
    REG_CH1_TEMPER_WATER_MIN,
    REG_CH1_THRESHOLD_SETPOINT,
    REG_CH1_UI_SENSOR_CORR_HUMI_79,
    REG_CH1_UI_SENSOR_CORR_TEMP_78,
    REG_CH2_EQUITHERM_OFFSET,
    REG_CH2_EQUITHERM_ROOM_EFFECT,
    REG_CH2_EQUITHERM_SLOPE,
    REG_CH2_LIMIT_HEAT_TEMPER,
    REG_CH2_TEMPER_ANTIFROST,
    REG_CH2_TEMPER_HYSTERESIS,
    REG_CH2_TEMPER_WATER_MAX,
    REG_CH2_TEMPER_WATER_MIN,
    REG_CH2_THRESHOLD_SETPOINT,
    REG_CH2_UI_SENSOR_CORR_HUMI_79,
    REG_CH2_UI_SENSOR_CORR_TEMP_78,
    REG_DHW_TEMPER_HYSTERESIS,
    REG_ELE_CORR_TEMP_OUTSIDE,
    REG_ELE_TEMPER_WATER_MAX,
    REG_ELE_TEMPER_WATER_MIN,
    REG_REGU_BUILDING_MOMENTUM,
    REG_REGU_COMPOSITE_FILTER_RATIO,
    REG_REGU_TEMPER_CHANGEOVER,
    REG_REGU_TEMPER_OUTSIDE,
)
from .coordinator import JablotronVoltaCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class JablotronVoltaNumberEntityDescription(NumberEntityDescription):
    """Describes Jablotron Volta number entity."""

    value_fn: Callable[[dict[str, Any]], float | None] | None = None
    register: int | None = None
    scale_fn: Callable[[float], int] | None = None
    available_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None


NUMBER_TYPES: tuple[JablotronVoltaNumberEntityDescription, ...] = (
    # Regulation Settings
    JablotronVoltaNumberEntityDescription(
        key="building_momentum",
        translation_key="building_momentum",
        name="Building Thermal Momentum",
        native_min_value=0,
        native_max_value=200,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.HOURS,
        mode=NumberMode.BOX,
        register=REG_REGU_BUILDING_MOMENTUM,
        value_fn=lambda data: data.get("building_momentum"),
        scale_fn=lambda x: int(x),
    ),
    JablotronVoltaNumberEntityDescription(
        key="composite_filter_ratio",
        translation_key="composite_filter_ratio",
        name="Composite Filter Ratio",
        native_min_value=0,
        native_max_value=1,
        native_step=0.1,
        mode=NumberMode.SLIDER,
        register=REG_REGU_COMPOSITE_FILTER_RATIO,
        value_fn=lambda data: data.get("composite_filter_ratio"),
        scale_fn=lambda x: int(x * 10),
    ),
    JablotronVoltaNumberEntityDescription(
        key="changeover_temp",
        translation_key="changeover_temp",
        name="Changeover Temperature",
        native_min_value=-20,
        native_max_value=30,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_REGU_TEMPER_CHANGEOVER,
        value_fn=lambda data: data.get("changeover_temp"),
        scale_fn=lambda x: int(x * 10) if x >= 0 else int(x * 10) + 65536,
    ),
    JablotronVoltaNumberEntityDescription(
        key="outdoor_temp_manual",
        translation_key="outdoor_temp_manual",
        name="Outdoor Temperature (Manual)",
        native_min_value=-40,
        native_max_value=50,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_REGU_TEMPER_OUTSIDE,
        value_fn=lambda data: data.get("outdoor_temp_manual"),
        scale_fn=lambda x: int(x * 10) if x >= 0 else int(x * 10) + 65536,
    ),
    # Boiler Settings
    JablotronVoltaNumberEntityDescription(
        key="boiler_outdoor_temp_correction",
        translation_key="boiler_outdoor_temp_correction",
        name="Outdoor Temperature Correction",
        native_min_value=-10,
        native_max_value=10,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_ELE_CORR_TEMP_OUTSIDE,
        value_fn=lambda data: data.get("boiler_outdoor_temp_correction"),
        scale_fn=lambda x: int(x * 10) if x >= 0 else int(x * 10) + 65536,
    ),
    JablotronVoltaNumberEntityDescription(
        key="boiler_water_temp_max",
        translation_key="boiler_water_temp_max",
        name="Boiler Max Water Temperature",
        native_min_value=30,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_ELE_TEMPER_WATER_MAX,
        value_fn=lambda data: data.get("boiler_water_temp_max"),
        scale_fn=lambda x: int(x * 10),
    ),
    JablotronVoltaNumberEntityDescription(
        key="boiler_water_temp_min",
        translation_key="boiler_water_temp_min",
        name="Boiler Min Water Temperature",
        native_min_value=10,
        native_max_value=60,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_ELE_TEMPER_WATER_MIN,
        value_fn=lambda data: data.get("boiler_water_temp_min"),
        scale_fn=lambda x: int(x * 10),
    ),
    # DHW Settings
    JablotronVoltaNumberEntityDescription(
        key="dhw_hysteresis",
        translation_key="dhw_hysteresis",
        name="DHW Hysteresis",
        native_min_value=0.5,
        native_max_value=10,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_DHW_TEMPER_HYSTERESIS,
        value_fn=lambda data: data.get("dhw_hysteresis"),
        scale_fn=lambda x: int(x * 10),
    ),
    # CH1 Settings
    JablotronVoltaNumberEntityDescription(
        key="ch1_antifrost_temp",
        translation_key="ch1_antifrost_temp",
        name="CH1 Antifrost Temperature",
        native_min_value=5,
        native_max_value=15,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_TEMPER_ANTIFROST,
        value_fn=lambda data: data.get("ch1_temperature_antifrost"),
        scale_fn=lambda x: int(x * 10),
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_hysteresis",
        translation_key="ch1_hysteresis",
        name="CH1 Hysteresis",
        native_min_value=0.5,
        native_max_value=5,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_TEMPER_HYSTERESIS,
        value_fn=lambda data: data.get("ch1_hysteresis"),
        scale_fn=lambda x: int(x * 10),
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_water_temp_min",
        translation_key="ch1_water_temp_min",
        name="CH1 Min Water Temperature",
        native_min_value=10,
        native_max_value=50,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_TEMPER_WATER_MIN,
        value_fn=lambda data: data.get("ch1_water_temp_min"),
        scale_fn=lambda x: int(x * 10),
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_water_temp_max",
        translation_key="ch1_water_temp_max",
        name="CH1 Max Water Temperature",
        native_min_value=20,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_TEMPER_WATER_MAX,
        value_fn=lambda data: data.get("ch1_water_temp_max"),
        scale_fn=lambda x: int(x * 10),
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_equitherm_slope",
        translation_key="ch1_equitherm_slope",
        name="CH1 Equitherm Slope",
        native_min_value=0,
        native_max_value=10,
        native_step=0.1,
        mode=NumberMode.BOX,
        register=REG_CH1_EQUITHERM_SLOPE,
        value_fn=lambda data: data.get("ch1_equitherm_slope"),
        scale_fn=lambda x: int(x * 10),
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_equitherm_offset",
        translation_key="ch1_equitherm_offset",
        name="CH1 Equitherm Offset",
        native_min_value=-20,
        native_max_value=20,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_EQUITHERM_OFFSET,
        value_fn=lambda data: data.get("ch1_equitherm_offset"),
        scale_fn=lambda x: int(x * 10) if x >= 0 else int(x * 10) + 65536,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_equitherm_room_effect",
        translation_key="ch1_equitherm_room_effect",
        name="CH1 Equitherm Room Effect",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement="%",
        mode=NumberMode.SLIDER,
        register=REG_CH1_EQUITHERM_ROOM_EFFECT,
        value_fn=lambda data: data.get("ch1_equitherm_room_effect"),
        scale_fn=lambda x: int(x),
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_threshold_setpoint",
        translation_key="ch1_threshold_setpoint",
        name="CH1 Threshold Setpoint",
        native_min_value=20,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_THRESHOLD_SETPOINT,
        value_fn=lambda data: data.get("ch1_threshold_setpoint"),
        scale_fn=lambda x: int(x * 10),
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_limit_heat_temp",
        translation_key="ch1_limit_heat_temp",
        name="CH1 Heat Limit Temperature",
        native_min_value=0,
        native_max_value=10,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_LIMIT_HEAT_TEMPER,
        value_fn=lambda data: data.get("ch1_limit_heat_temp"),
        scale_fn=lambda x: int(x * 10),
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_temp_correction",
        translation_key="ch1_temp_correction",
        name="CH1 Temperature Correction",
        native_min_value=-5,
        native_max_value=5,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_UI_SENSOR_CORR_TEMP_78,
        value_fn=lambda data: data.get("ch1_temp_correction"),
        scale_fn=lambda x: int(x * 10) if x >= 0 else int(x * 10) + 65536,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_humidity_correction",
        translation_key="ch1_humidity_correction",
        name="CH1 Humidity Correction",
        native_min_value=-20,
        native_max_value=20,
        native_step=1,
        native_unit_of_measurement="%",
        mode=NumberMode.BOX,
        register=REG_CH1_UI_SENSOR_CORR_HUMI_79,
        value_fn=lambda data: data.get("ch1_humidity_correction"),
        scale_fn=lambda x: int(x * 10) if x >= 0 else int(x * 10) + 65536,
    ),
    # CH2 Settings (conditional)
    JablotronVoltaNumberEntityDescription(
        key="ch2_antifrost_temp",
        translation_key="ch2_antifrost_temp",
        name="CH2 Antifrost Temperature",
        native_min_value=5,
        native_max_value=15,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_TEMPER_ANTIFROST,
        value_fn=lambda data: data.get("ch2_temperature_antifrost"),
        scale_fn=lambda x: int(x * 10),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_hysteresis",
        translation_key="ch2_hysteresis",
        name="CH2 Hysteresis",
        native_min_value=0.5,
        native_max_value=5,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_TEMPER_HYSTERESIS,
        value_fn=lambda data: data.get("ch2_hysteresis"),
        scale_fn=lambda x: int(x * 10),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_water_temp_min",
        translation_key="ch2_water_temp_min",
        name="CH2 Min Water Temperature",
        native_min_value=10,
        native_max_value=50,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_TEMPER_WATER_MIN,
        value_fn=lambda data: data.get("ch2_water_temp_min"),
        scale_fn=lambda x: int(x * 10),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_water_temp_max",
        translation_key="ch2_water_temp_max",
        name="CH2 Max Water Temperature",
        native_min_value=20,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_TEMPER_WATER_MAX,
        value_fn=lambda data: data.get("ch2_water_temp_max"),
        scale_fn=lambda x: int(x * 10),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_equitherm_slope",
        translation_key="ch2_equitherm_slope",
        name="CH2 Equitherm Slope",
        native_min_value=0,
        native_max_value=10,
        native_step=0.1,
        mode=NumberMode.BOX,
        register=REG_CH2_EQUITHERM_SLOPE,
        value_fn=lambda data: data.get("ch2_equitherm_slope"),
        scale_fn=lambda x: int(x * 10),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_equitherm_offset",
        translation_key="ch2_equitherm_offset",
        name="CH2 Equitherm Offset",
        native_min_value=-20,
        native_max_value=20,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_EQUITHERM_OFFSET,
        value_fn=lambda data: data.get("ch2_equitherm_offset"),
        scale_fn=lambda x: int(x * 10) if x >= 0 else int(x * 10) + 65536,
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_equitherm_room_effect",
        translation_key="ch2_equitherm_room_effect",
        name="CH2 Equitherm Room Effect",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement="%",
        mode=NumberMode.SLIDER,
        register=REG_CH2_EQUITHERM_ROOM_EFFECT,
        value_fn=lambda data: data.get("ch2_equitherm_room_effect"),
        scale_fn=lambda x: int(x),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_threshold_setpoint",
        translation_key="ch2_threshold_setpoint",
        name="CH2 Threshold Setpoint",
        native_min_value=20,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_THRESHOLD_SETPOINT,
        value_fn=lambda data: data.get("ch2_threshold_setpoint"),
        scale_fn=lambda x: int(x * 10),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_limit_heat_temp",
        translation_key="ch2_limit_heat_temp",
        name="CH2 Heat Limit Temperature",
        native_min_value=0,
        native_max_value=10,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_LIMIT_HEAT_TEMPER,
        value_fn=lambda data: data.get("ch2_limit_heat_temp"),
        scale_fn=lambda x: int(x * 10),
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_temp_correction",
        translation_key="ch2_temp_correction",
        name="CH2 Temperature Correction",
        native_min_value=-5,
        native_max_value=5,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_UI_SENSOR_CORR_TEMP_78,
        value_fn=lambda data: data.get("ch2_temp_correction"),
        scale_fn=lambda x: int(x * 10) if x >= 0 else int(x * 10) + 65536,
        available_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_humidity_correction",
        translation_key="ch2_humidity_correction",
        name="CH2 Humidity Correction",
        native_min_value=-20,
        native_max_value=20,
        native_step=1,
        native_unit_of_measurement="%",
        mode=NumberMode.BOX,
        register=REG_CH2_UI_SENSOR_CORR_HUMI_79,
        value_fn=lambda data: data.get("ch2_humidity_correction"),
        scale_fn=lambda x: int(x * 10) if x >= 0 else int(x * 10) + 65536,
        available_fn=lambda coord: coord.ch2_available,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jablotron Volta number entities."""
    coordinator: JablotronVoltaCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[NumberEntity] = []

    for description in NUMBER_TYPES:
        if description.available_fn and not description.available_fn(coordinator):
            continue

        entities.append(JablotronVoltaNumber(coordinator, entry, description))

    async_add_entities(entities)


class JablotronVoltaNumber(CoordinatorEntity, NumberEntity):
    """Representation of a Jablotron Volta number entity."""

    entity_description: JablotronVoltaNumberEntityDescription

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        entry: ConfigEntry,
        description: JablotronVoltaNumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = coordinator.device_info

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return None

    async def async_set_native_value(self, value: float) -> None:
        """Update the setting."""
        if not self.entity_description.register or not self.entity_description.scale_fn:
            return

        scaled_value = self.entity_description.scale_fn(value)

        success = await self.hass.async_add_executor_job(
            self.coordinator.client.write_register,
            self.entity_description.register,
            scaled_value,
        )

        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(
                "Failed to set %s to %s", self.entity_description.key, value
            )
