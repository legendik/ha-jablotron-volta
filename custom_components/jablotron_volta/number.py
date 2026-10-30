"""Number platform for Jablotron Volta integration."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
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
    REG_ELE_CORR_TEMP_OUTSIDE,
    REG_ELE_TEMPER_WATER_MAX,
    REG_ELE_TEMPER_WATER_MIN,
    REG_REGU_BUILDING_MOMENTUM,
    REG_REGU_COMPOSITE_FILTER_RATIO,
    REG_REGU_TEMPER_CHANGEOVER,
    REG_REGU_TEMPER_OUTSIDE,
)
from .coordinator import JablotronVoltaConfigEntry, JablotronVoltaCoordinator
from .entity import JablotronVoltaEntity
from .scaling import (
    unscale_ratio,
    unscale_signed_percentage,
    unscale_signed_temperature,
    unscale_temperature,
)

_LOGGER = logging.getLogger(__name__)


PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class JablotronVoltaNumberEntityDescription(NumberEntityDescription):
    """Describes Jablotron Volta number entity."""

    value_fn: Callable[[dict[str, Any]], float | None]
    register: int
    scale_fn: Callable[[float], int]
    exists_fn: Callable[[JablotronVoltaCoordinator], bool] | None = None


NUMBER_TYPES: tuple[JablotronVoltaNumberEntityDescription, ...] = (
    # Regulation Settings
    JablotronVoltaNumberEntityDescription(
        key="building_momentum",
        translation_key="building_momentum",
        native_min_value=0,
        native_max_value=200,
        native_step=1,
        native_unit_of_measurement=UnitOfTime.HOURS,
        mode=NumberMode.BOX,
        register=REG_REGU_BUILDING_MOMENTUM,
        value_fn=lambda data: data.get("building_momentum"),
        scale_fn=int,
    ),
    JablotronVoltaNumberEntityDescription(
        key="composite_filter_ratio",
        translation_key="composite_filter_ratio",
        native_min_value=0,
        native_max_value=1,
        native_step=0.1,
        mode=NumberMode.SLIDER,
        register=REG_REGU_COMPOSITE_FILTER_RATIO,
        value_fn=lambda data: data.get("composite_filter_ratio"),
        scale_fn=unscale_ratio,
    ),
    JablotronVoltaNumberEntityDescription(
        key="changeover_temp",
        translation_key="changeover_temperature",
        native_min_value=-20,
        native_max_value=30,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_REGU_TEMPER_CHANGEOVER,
        value_fn=lambda data: data.get("changeover_temp"),
        scale_fn=unscale_signed_temperature,
    ),
    JablotronVoltaNumberEntityDescription(
        key="outdoor_temp_manual",
        translation_key="outdoor_temperature_manual",
        native_min_value=-40,
        native_max_value=50,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_REGU_TEMPER_OUTSIDE,
        value_fn=lambda data: data.get("outdoor_temp_manual"),
        scale_fn=unscale_signed_temperature,
    ),
    # Boiler Settings
    JablotronVoltaNumberEntityDescription(
        key="boiler_outdoor_temp_correction",
        translation_key="boiler_outdoor_temperature_correction",
        native_min_value=-10,
        native_max_value=10,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_ELE_CORR_TEMP_OUTSIDE,
        value_fn=lambda data: data.get("boiler_outdoor_temp_correction"),
        scale_fn=unscale_signed_temperature,
    ),
    JablotronVoltaNumberEntityDescription(
        key="boiler_water_temp_max",
        translation_key="boiler_water_temperature_max",
        native_min_value=30,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_ELE_TEMPER_WATER_MAX,
        value_fn=lambda data: data.get("boiler_water_temp_max"),
        scale_fn=unscale_temperature,
    ),
    JablotronVoltaNumberEntityDescription(
        key="boiler_water_temp_min",
        translation_key="boiler_water_temperature_min",
        native_min_value=10,
        native_max_value=60,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_ELE_TEMPER_WATER_MIN,
        value_fn=lambda data: data.get("boiler_water_temp_min"),
        scale_fn=unscale_temperature,
    ),
    # CH1 Settings
    JablotronVoltaNumberEntityDescription(
        key="ch1_antifrost_temp",
        translation_key="ch1_antifrost_temperature",
        native_min_value=5,
        native_max_value=15,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_TEMPER_ANTIFROST,
        value_fn=lambda data: data.get("ch1_temperature_antifrost"),
        scale_fn=unscale_temperature,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_hysteresis",
        translation_key="ch1_hysteresis",
        native_min_value=0.5,
        native_max_value=5,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_TEMPER_HYSTERESIS,
        value_fn=lambda data: data.get("ch1_hysteresis"),
        scale_fn=unscale_temperature,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_water_temp_min",
        translation_key="ch1_water_temperature_min",
        native_min_value=10,
        native_max_value=50,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_TEMPER_WATER_MIN,
        value_fn=lambda data: data.get("ch1_water_temp_min"),
        scale_fn=unscale_temperature,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_water_temp_max",
        translation_key="ch1_water_temperature_max",
        native_min_value=20,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_TEMPER_WATER_MAX,
        value_fn=lambda data: data.get("ch1_water_temp_max"),
        scale_fn=unscale_temperature,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_equitherm_slope",
        translation_key="ch1_equitherm_slope",
        native_min_value=0,
        native_max_value=10,
        native_step=0.1,
        mode=NumberMode.BOX,
        register=REG_CH1_EQUITHERM_SLOPE,
        value_fn=lambda data: data.get("ch1_equitherm_slope"),
        scale_fn=unscale_ratio,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_equitherm_offset",
        translation_key="ch1_equitherm_offset",
        native_min_value=-20,
        native_max_value=20,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_EQUITHERM_OFFSET,
        value_fn=lambda data: data.get("ch1_equitherm_offset"),
        scale_fn=unscale_signed_temperature,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_equitherm_room_effect",
        translation_key="ch1_equitherm_room_effect",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        register=REG_CH1_EQUITHERM_ROOM_EFFECT,
        value_fn=lambda data: data.get("ch1_equitherm_room_effect"),
        scale_fn=int,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_threshold_setpoint",
        translation_key="ch1_threshold_setpoint",
        native_min_value=20,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_THRESHOLD_SETPOINT,
        value_fn=lambda data: data.get("ch1_threshold_setpoint"),
        scale_fn=unscale_temperature,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_limit_heat_temp",
        translation_key="ch1_limit_heat_temperature",
        native_min_value=0,
        native_max_value=10,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_LIMIT_HEAT_TEMPER,
        value_fn=lambda data: data.get("ch1_limit_heat_temp"),
        scale_fn=unscale_temperature,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_temp_correction",
        translation_key="ch1_temperature_correction",
        native_min_value=-5,
        native_max_value=5,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH1_UI_SENSOR_CORR_TEMP_78,
        value_fn=lambda data: data.get("ch1_temp_correction"),
        scale_fn=unscale_signed_temperature,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch1_humidity_correction",
        translation_key="ch1_humidity_correction",
        native_min_value=-20,
        native_max_value=20,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX,
        register=REG_CH1_UI_SENSOR_CORR_HUMI_79,
        value_fn=lambda data: data.get("ch1_humidity_correction"),
        scale_fn=unscale_signed_percentage,
    ),
    # CH2 Settings (conditional)
    JablotronVoltaNumberEntityDescription(
        key="ch2_antifrost_temp",
        translation_key="ch2_antifrost_temperature",
        native_min_value=5,
        native_max_value=15,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_TEMPER_ANTIFROST,
        value_fn=lambda data: data.get("ch2_temperature_antifrost"),
        scale_fn=unscale_temperature,
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_hysteresis",
        translation_key="ch2_hysteresis",
        native_min_value=0.5,
        native_max_value=5,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_TEMPER_HYSTERESIS,
        value_fn=lambda data: data.get("ch2_hysteresis"),
        scale_fn=unscale_temperature,
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_water_temp_min",
        translation_key="ch2_water_temperature_min",
        native_min_value=10,
        native_max_value=50,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_TEMPER_WATER_MIN,
        value_fn=lambda data: data.get("ch2_water_temp_min"),
        scale_fn=unscale_temperature,
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_water_temp_max",
        translation_key="ch2_water_temperature_max",
        native_min_value=20,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_TEMPER_WATER_MAX,
        value_fn=lambda data: data.get("ch2_water_temp_max"),
        scale_fn=unscale_temperature,
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_equitherm_slope",
        translation_key="ch2_equitherm_slope",
        native_min_value=0,
        native_max_value=10,
        native_step=0.1,
        mode=NumberMode.BOX,
        register=REG_CH2_EQUITHERM_SLOPE,
        value_fn=lambda data: data.get("ch2_equitherm_slope"),
        scale_fn=unscale_ratio,
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_equitherm_offset",
        translation_key="ch2_equitherm_offset",
        native_min_value=-20,
        native_max_value=20,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_EQUITHERM_OFFSET,
        value_fn=lambda data: data.get("ch2_equitherm_offset"),
        scale_fn=unscale_signed_temperature,
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_equitherm_room_effect",
        translation_key="ch2_equitherm_room_effect",
        native_min_value=0,
        native_max_value=100,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        register=REG_CH2_EQUITHERM_ROOM_EFFECT,
        value_fn=lambda data: data.get("ch2_equitherm_room_effect"),
        scale_fn=int,
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_threshold_setpoint",
        translation_key="ch2_threshold_setpoint",
        native_min_value=20,
        native_max_value=90,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_THRESHOLD_SETPOINT,
        value_fn=lambda data: data.get("ch2_threshold_setpoint"),
        scale_fn=unscale_temperature,
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_limit_heat_temp",
        translation_key="ch2_limit_heat_temperature",
        native_min_value=0,
        native_max_value=10,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_LIMIT_HEAT_TEMPER,
        value_fn=lambda data: data.get("ch2_limit_heat_temp"),
        scale_fn=unscale_temperature,
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_temp_correction",
        translation_key="ch2_temperature_correction",
        native_min_value=-5,
        native_max_value=5,
        native_step=0.5,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        register=REG_CH2_UI_SENSOR_CORR_TEMP_78,
        value_fn=lambda data: data.get("ch2_temp_correction"),
        scale_fn=unscale_signed_temperature,
        exists_fn=lambda coord: coord.ch2_available,
    ),
    JablotronVoltaNumberEntityDescription(
        key="ch2_humidity_correction",
        translation_key="ch2_humidity_correction",
        native_min_value=-20,
        native_max_value=20,
        native_step=1,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.BOX,
        register=REG_CH2_UI_SENSOR_CORR_HUMI_79,
        value_fn=lambda data: data.get("ch2_humidity_correction"),
        scale_fn=unscale_signed_percentage,
        exists_fn=lambda coord: coord.ch2_available,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JablotronVoltaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Jablotron Volta number entities."""
    coordinator = entry.runtime_data
    async_add_entities(
        JablotronVoltaNumber(coordinator, description)
        for description in NUMBER_TYPES
        if description.exists_fn is None or description.exists_fn(coordinator)
    )


class JablotronVoltaNumber(JablotronVoltaEntity, NumberEntity):
    """Representation of a Jablotron Volta number entity."""

    entity_description: JablotronVoltaNumberEntityDescription
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        description: JablotronVoltaNumberEntityDescription,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        return self.entity_description.value_fn(self.coordinator.data)

    async def async_set_native_value(self, value: float) -> None:
        """Update the setting."""
        await self._async_write_register(
            self.entity_description.register,
            self.entity_description.scale_fn(value),
        )
