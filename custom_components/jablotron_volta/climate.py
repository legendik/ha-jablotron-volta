"""Climate platform for Jablotron Volta integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CH_MODE_MANUAL,
    CH_MODE_SCHEDULE,
    CH_MODE_STANDBY,
    REG_CH1_MODE,
    REG_CH1_TEMPER_MANUAL,
    REG_CH2_MODE,
    REG_CH2_TEMPER_MANUAL,
)
from .coordinator import JablotronVoltaConfigEntry, JablotronVoltaCoordinator
from .entity import JablotronVoltaEntity
from .scaling import unscale_temperature

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

CH_MODE_TO_HVAC_MODE: dict[int, HVACMode] = {
    CH_MODE_STANDBY: HVACMode.OFF,
    CH_MODE_MANUAL: HVACMode.HEAT,
    CH_MODE_SCHEDULE: HVACMode.AUTO,
}
HVAC_MODE_TO_CH_MODE: dict[HVACMode, int] = {
    hvac_mode: ch_mode for ch_mode, hvac_mode in CH_MODE_TO_HVAC_MODE.items()
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JablotronVoltaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Jablotron Volta climate entities."""
    coordinator = entry.runtime_data
    circuits = [1, 2] if coordinator.ch2_available else [1]
    async_add_entities(
        JablotronVoltaHeatingCircuitClimate(coordinator, circuit)
        for circuit in circuits
    )


class JablotronVoltaHeatingCircuitClimate(JablotronVoltaEntity, ClimateEntity):
    """Climate entity for Heating Circuit (CH1 or CH2)."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 0.5
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        circuit_number: int,
    ) -> None:
        """Initialize heating circuit climate entity."""
        super().__init__(coordinator, f"ch{circuit_number}_climate")
        self._prefix = f"ch{circuit_number}"
        self._attr_translation_key = self._prefix
        self._attr_hvac_modes = list(HVAC_MODE_TO_CH_MODE)
        self._mode_register = REG_CH1_MODE if circuit_number == 1 else REG_CH2_MODE
        self._temperature_register = (
            REG_CH1_TEMPER_MANUAL if circuit_number == 1 else REG_CH2_TEMPER_MANUAL
        )

    def _value(self, name: str) -> Any:
        return self.coordinator.data.get(f"{self._prefix}_{name}")

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._value("temperature_current")

    @property
    def current_humidity(self) -> float | None:
        """Return the current room humidity."""
        return self._value("humidity")

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self._value("temperature_desired")

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        value = self._value("temperature_min")
        return 5.0 if value is None else value

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        value = self._value("temperature_max")
        return 30.0 if value is None else value

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return current HVAC mode."""
        return CH_MODE_TO_HVAC_MODE.get(self._value("mode"))

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return what the circuit is currently doing."""
        if self.hvac_mode is HVACMode.OFF:
            return HVACAction.OFF
        heating = self._value("state_heat")
        if heating is None:
            return None
        return HVACAction.HEATING if heating else HVACAction.IDLE

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        await self._async_write_register(
            self._mode_register, HVAC_MODE_TO_CH_MODE[hvac_mode]
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature (written to the manual setpoint)."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        await self._async_write_register(
            self._temperature_register, unscale_temperature(temperature)
        )
