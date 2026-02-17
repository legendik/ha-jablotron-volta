"""Climate platform for Jablotron Volta integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CH_MODE_MANUAL,
    CH_MODE_SCHEDULE,
    CH_MODE_STANDBY,
    DHW_MODE_MANUAL,
    DHW_MODE_SCHEDULE,
    DHW_MODE_STANDBY,
    DOMAIN,
    REG_CH1_MODE,
    REG_CH1_TEMPER_MANUAL,
    REG_CH2_MODE,
    REG_CH2_TEMPER_MANUAL,
    REG_DHW_MODE,
    REG_DHW_TEMPER_MANUAL,
)
from .coordinator import JablotronVoltaCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Jablotron Volta climate entities."""
    coordinator: JablotronVoltaCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[ClimateEntity] = [
        JablotronVoltaDHWClimate(coordinator, entry),
        JablotronVoltaHeatingCircuitClimate(coordinator, entry, 1),
    ]

    # Add CH2 if available
    if coordinator.ch2_available:
        entities.append(JablotronVoltaHeatingCircuitClimate(coordinator, entry, 2))

    async_add_entities(entities)


class JablotronVoltaClimateBase(CoordinatorEntity, ClimateEntity):
    """Base class for Jablotron Volta climate entities."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the climate entity."""
        super().__init__(coordinator)
        self._attr_device_info = coordinator.device_info


class JablotronVoltaDHWClimate(JablotronVoltaClimateBase):
    """Climate entity for Domestic Hot Water (DHW)."""

    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize DHW climate entity."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_dhw_climate"
        self._attr_translation_key = "dhw"

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data.get("dhw_temperature_current")

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self.coordinator.data.get("dhw_temperature_desired")

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return self.coordinator.data.get("dhw_temperature_min", 30.0)

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return self.coordinator.data.get("dhw_temperature_max", 70.0)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        mode = self.coordinator.data.get("dhw_mode")
        if mode == DHW_MODE_STANDBY:
            return HVACMode.OFF
        elif mode == DHW_MODE_MANUAL:
            return HVACMode.HEAT
        elif mode == DHW_MODE_SCHEDULE:
            return HVACMode.AUTO
        return HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        mode_value = DHW_MODE_STANDBY
        if hvac_mode == HVACMode.HEAT:
            mode_value = DHW_MODE_MANUAL
        elif hvac_mode == HVACMode.AUTO:
            mode_value = DHW_MODE_SCHEDULE

        success = await self.hass.async_add_executor_job(
            self.coordinator.client.write_register,
            REG_DHW_MODE,
            mode_value,
        )

        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set DHW HVAC mode to %s", hvac_mode)

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        # Write to manual temperature register
        temp_value = self.coordinator.client.unscale_temperature(temperature)

        success = await self.hass.async_add_executor_job(
            self.coordinator.client.write_register,
            REG_DHW_TEMPER_MANUAL,
            temp_value,
        )

        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error("Failed to set DHW temperature to %s", temperature)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        return {
            "regulation_strategy": self.coordinator.data.get("dhw_regulation_strategy"),
            "hysteresis": self.coordinator.data.get("dhw_hysteresis"),
        }


class JablotronVoltaHeatingCircuitClimate(JablotronVoltaClimateBase):
    """Climate entity for Heating Circuit (CH1 or CH2)."""

    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]

    def __init__(
        self,
        coordinator: JablotronVoltaCoordinator,
        entry: ConfigEntry,
        circuit_number: int,
    ) -> None:
        """Initialize heating circuit climate entity."""
        super().__init__(coordinator, entry)
        self._circuit = circuit_number
        self._attr_unique_id = f"{entry.entry_id}_ch{circuit_number}_climate"
        self._attr_translation_key = f"ch{circuit_number}"

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.coordinator.data.get(f"ch{self._circuit}_temperature_current")

    @property
    def target_temperature(self) -> float | None:
        """Return the target temperature."""
        return self.coordinator.data.get(f"ch{self._circuit}_temperature_desired")

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return self.coordinator.data.get(f"ch{self._circuit}_temperature_min", 5.0)

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return self.coordinator.data.get(f"ch{self._circuit}_temperature_max", 30.0)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return current HVAC mode."""
        mode = self.coordinator.data.get(f"ch{self._circuit}_mode")
        if mode == CH_MODE_STANDBY:
            return HVACMode.OFF
        elif mode == CH_MODE_MANUAL:
            return HVACMode.HEAT
        elif mode == CH_MODE_SCHEDULE:
            return HVACMode.AUTO
        return HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new HVAC mode."""
        mode_value = CH_MODE_STANDBY
        if hvac_mode == HVACMode.HEAT:
            mode_value = CH_MODE_MANUAL
        elif hvac_mode == HVACMode.AUTO:
            mode_value = CH_MODE_SCHEDULE

        mode_register = REG_CH1_MODE if self._circuit == 1 else REG_CH2_MODE

        success = await self.hass.async_add_executor_job(
            self.coordinator.client.write_register,
            mode_register,
            mode_value,
        )

        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(
                "Failed to set CH%s HVAC mode to %s", self._circuit, hvac_mode
            )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return

        # Write to manual temperature register
        temp_value = self.coordinator.client.unscale_temperature(temperature)

        temp_register = (
            REG_CH1_TEMPER_MANUAL if self._circuit == 1 else REG_CH2_TEMPER_MANUAL
        )

        success = await self.hass.async_add_executor_job(
            self.coordinator.client.write_register,
            temp_register,
            temp_value,
        )

        if success:
            await self.coordinator.async_request_refresh()
        else:
            _LOGGER.error(
                "Failed to set CH%s temperature to %s", self._circuit, temperature
            )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        attrs = {
            "regulation_strategy": self.coordinator.data.get(
                f"ch{self._circuit}_regulation_strategy"
            ),
            "water_setpoint": self.coordinator.data.get(
                f"ch{self._circuit}_water_setpoint"
            ),
            "water_input_temp": self.coordinator.data.get(
                f"ch{self._circuit}_water_input_temp"
            ),
            "water_return_temp": self.coordinator.data.get(
                f"ch{self._circuit}_water_return_temp"
            ),
            "hysteresis": self.coordinator.data.get(f"ch{self._circuit}_hysteresis"),
        }

        # Add humidity and CO2 if available
        if (
            humidity := self.coordinator.data.get(f"ch{self._circuit}_humidity")
        ) is not None:
            attrs["humidity"] = humidity

        if (co2 := self.coordinator.data.get(f"ch{self._circuit}_co2")) is not None:
            attrs["co2"] = co2

        return attrs
