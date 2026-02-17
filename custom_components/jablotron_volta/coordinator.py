"""Data update coordinator for Jablotron Volta."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DEVICE_ID,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    UPDATE_INTERVAL,
)
from .modbus_client import JablotronModbusClient

_LOGGER = logging.getLogger(__name__)


class JablotronVoltaCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Jablotron Volta data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize."""
        self.entry = entry
        self.client = JablotronModbusClient(
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            entry.data[CONF_DEVICE_ID],
        )

        # Store device information for entity registration
        self._serial_number: str | None = None
        self._firmware_version: str | None = None
        self._hardware_version: str | None = None
        self._mac_address: str | None = None
        self._ch2_available: bool = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},
            "name": f"{MANUFACTURER} {MODEL}",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": self._firmware_version,
            "hw_version": self._hardware_version,
            "serial_number": self._serial_number,
            "configuration_url": f"http://{self.entry.data[CONF_HOST]}",
        }

    @property
    def ch2_available(self) -> bool:
        """Return True if Heating Circuit 2 is available."""
        return self._ch2_available

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from device."""
        try:
            return await self.hass.async_add_executor_job(self._fetch_data)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with device: {err}") from err

    def _fetch_data(self) -> dict[str, Any]:
        """Fetch data from Modbus device (runs in executor)."""
        if not self.client.connect():
            raise UpdateFailed("Cannot connect to device")

        try:
            # Read all data using batched operations
            raw_data = self.client.read_all_data()

            if not raw_data:
                raise UpdateFailed("No data received from device")

            # Process and structure the data
            processed_data = self._process_raw_data(raw_data)

            # Update CH2 availability flag
            self._ch2_available = raw_data.get("ch2_available", False)

            return processed_data

        finally:
            self.client.close()

    def _process_raw_data(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """Process raw register data into structured format."""
        data: dict[str, Any] = {}

        # Process device information
        if "device_info" in raw_data:
            dev_info = raw_data["device_info"]
            if len(dev_info) >= 11:
                # Serial number (registers 0-1)
                self._serial_number = str(
                    self.client.registers_to_uint32(dev_info[0], dev_info[1])
                )

                # Firmware version (registers 9-10)
                fw_high = dev_info[9]
                fw_low = dev_info[10]
                self._firmware_version = f"{fw_high >> 8}.{fw_high & 0xFF}.{fw_low}"

                # Hardware version (registers 4-5)
                hw_high = dev_info[4]
                hw_low = dev_info[5]
                self._hardware_version = f"{hw_high >> 8}.{hw_high & 0xFF}.{hw_low}"

                # MAC address (registers 6-8)
                self._mac_address = self.client.registers_to_mac(
                    dev_info[6], dev_info[7], dev_info[8]
                )

        # Process network information
        if "network_info" in raw_data:
            net_info = raw_data["network_info"]
            if len(net_info) >= 6:
                data["ip_address"] = self.client.registers_to_ip(
                    net_info[0], net_info[1]
                )
                data["subnet_mask"] = self.client.registers_to_ip(
                    net_info[2], net_info[3]
                )
                data["gateway"] = self.client.registers_to_ip(net_info[4], net_info[5])

        # Process system status
        if "system_status" in raw_data:
            sys_status = raw_data["system_status"]
            if len(sys_status) >= 2:
                data["cpu_temperature"] = self.client.scale_temperature(sys_status[0])
                data["battery_voltage"] = self.client.scale_voltage(sys_status[1])

        # Process regulation
        if "regulation" in raw_data:
            reg = raw_data["regulation"]
            if len(reg) >= 3:
                data["regulation_mode_current"] = reg[0]
                data["outdoor_temp_damped"] = self.client.scale_temperature(reg[1])
                data["outdoor_temp_composite"] = self.client.scale_temperature(reg[2])

        # Process boiler status
        if "boiler_status" in raw_data:
            boiler = raw_data["boiler_status"]
            if len(boiler) >= 10:
                data["boiler_active_segments"] = boiler[0]
                data["boiler_inactive_segments"] = boiler[1]
                data["boiler_pressure"] = self.client.scale_pressure(boiler[2])
                data["boiler_water_input_temp"] = self.client.scale_temperature(
                    boiler[4]
                )
                data["boiler_water_return_temp"] = self.client.scale_temperature(
                    boiler[5]
                )
                data["boiler_pump_power"] = self.client.scale_percentage(boiler[6])
                data["boiler_heating_power"] = self.client.scale_percentage(boiler[7])
                data["boiler_analog_value"] = self.client.scale_voltage(boiler[8])
                data["boiler_pwm_value"] = boiler[9]

        # Process DHW status
        if "dhw_status" in raw_data:
            dhw = raw_data["dhw_status"]
            if len(dhw) >= 2:
                data["dhw_state_heat"] = bool(dhw[0])
                data["dhw_temperature_current"] = self.client.scale_temperature(dhw[1])

        # Process CH1 status
        if "ch1_status" in raw_data:
            ch1 = raw_data["ch1_status"]
            if len(ch1) >= 7:
                data["ch1_state_heat"] = bool(ch1[0])
                data["ch1_temperature_current"] = self.client.scale_temperature(ch1[1])
                data["ch1_water_input_temp"] = self.client.scale_temperature(ch1[2])
                data["ch1_water_return_temp"] = self.client.scale_temperature(ch1[3])
                data["ch1_pump_power"] = ch1[4]
                data["ch1_humidity"] = self.client.scale_percentage(ch1[5])
                data["ch1_co2"] = self.client.scale_percentage(ch1[6])

        # Process CH2 status (if available)
        if "ch2_status" in raw_data:
            ch2 = raw_data["ch2_status"]
            if len(ch2) >= 7:
                data["ch2_state_heat"] = bool(ch2[0])
                data["ch2_temperature_current"] = self.client.scale_temperature(ch2[1])
                data["ch2_water_input_temp"] = self.client.scale_temperature(ch2[2])
                data["ch2_water_return_temp"] = self.client.scale_temperature(ch2[3])
                data["ch2_pump_power"] = ch2[4]
                data["ch2_humidity"] = self.client.scale_percentage(ch2[5])
                data["ch2_co2"] = self.client.scale_percentage(ch2[6])

        # Process system alerts
        if "system_alerts" in raw_data:
            alerts = raw_data["system_alerts"]
            if len(alerts) >= 2:
                data["system_attention"] = self.client.registers_to_uint32(
                    alerts[0], alerts[1]
                )

        # Process regulation settings
        if "regulation_settings" in raw_data:
            reg_set = raw_data["regulation_settings"]
            if len(reg_set) >= 6:
                data["regulation_mode_user"] = reg_set[0]
                data["outdoor_temp_source"] = reg_set[1]
                data["building_momentum"] = reg_set[2]
                data["composite_filter_ratio"] = self.client.scale_ratio(reg_set[3])
                data["changeover_temp"] = self.client.scale_temperature(reg_set[4])
                data["outdoor_temp_manual"] = self.client.scale_temperature(reg_set[5])

        # Process boiler settings
        if "boiler_settings" in raw_data:
            boiler_set = raw_data["boiler_settings"]
            if len(boiler_set) >= 13:
                data["boiler_load_release"] = boiler_set[0]
                data["boiler_hdo_high_tariff"] = boiler_set[1]
                data["boiler_outdoor_temp_correction"] = (
                    self.client.scale_temperature(boiler_set[2])
                )
                data["boiler_total_energy"] = boiler_set[3]
                data["boiler_water_setpoint"] = self.client.scale_temperature(
                    boiler_set[4]
                )
                data["boiler_water_temp_max"] = self.client.scale_temperature(
                    boiler_set[5]
                )
                data["boiler_water_temp_min"] = self.client.scale_temperature(
                    boiler_set[6]
                )

        # Process DHW settings
        if "dhw_settings" in raw_data:
            dhw_set = raw_data["dhw_settings"]
            if len(dhw_set) >= 8:
                data["dhw_mode"] = dhw_set[0]
                data["dhw_temperature_desired"] = self.client.scale_temperature(
                    dhw_set[1]
                )
                data["dhw_temperature_min"] = self.client.scale_temperature(dhw_set[2])
                data["dhw_temperature_max"] = self.client.scale_temperature(dhw_set[3])
                data["dhw_temperature_manual"] = self.client.scale_temperature(
                    dhw_set[4]
                )
                data["dhw_hysteresis"] = self.client.scale_temperature(dhw_set[6])
                data["dhw_regulation_strategy"] = dhw_set[7]

        # Process CH1 settings
        if "ch1_settings" in raw_data:
            ch1_set = raw_data["ch1_settings"]
            if len(ch1_set) >= 20:
                data["ch1_mode"] = ch1_set[0]
                data["ch1_temperature_desired"] = self.client.scale_temperature(
                    ch1_set[1]
                )
                data["ch1_temperature_min"] = self.client.scale_temperature(ch1_set[2])
                data["ch1_temperature_max"] = self.client.scale_temperature(ch1_set[3])
                data["ch1_temperature_manual"] = self.client.scale_temperature(
                    ch1_set[4]
                )
                data["ch1_temperature_antifrost"] = self.client.scale_temperature(
                    ch1_set[5]
                )
                data["ch1_hysteresis"] = self.client.scale_temperature(ch1_set[6])
                data["ch1_regulation_strategy"] = ch1_set[7]
                data["ch1_water_temp_min"] = self.client.scale_temperature(ch1_set[8])
                data["ch1_water_temp_max"] = self.client.scale_temperature(ch1_set[9])
                data["ch1_water_setpoint"] = self.client.scale_temperature(ch1_set[10])
                data["ch1_equitherm_slope"] = ch1_set[11]
                data["ch1_equitherm_offset"] = self.client.scale_temperature(
                    ch1_set[12]
                )
                data["ch1_equitherm_room_effect"] = ch1_set[13]
                data["ch1_threshold_setpoint"] = self.client.scale_temperature(
                    ch1_set[14]
                )
                data["ch1_limit_heat_temp"] = self.client.scale_temperature(
                    ch1_set[15]
                )
                data["ch1_optimal_start"] = bool(ch1_set[16])
                data["ch1_fast_cooldown"] = bool(ch1_set[17])
                data["ch1_temp_correction"] = self.client.scale_temperature(
                    ch1_set[18]
                )
                data["ch1_humidity_correction"] = self.client.scale_percentage(
                    ch1_set[19]
                )

        # Process CH2 settings (if available)
        if "ch2_settings" in raw_data:
            ch2_set = raw_data["ch2_settings"]
            if len(ch2_set) >= 20:
                data["ch2_mode"] = ch2_set[0]
                data["ch2_temperature_desired"] = self.client.scale_temperature(
                    ch2_set[1]
                )
                data["ch2_temperature_min"] = self.client.scale_temperature(ch2_set[2])
                data["ch2_temperature_max"] = self.client.scale_temperature(ch2_set[3])
                data["ch2_temperature_manual"] = self.client.scale_temperature(
                    ch2_set[4]
                )
                data["ch2_temperature_antifrost"] = self.client.scale_temperature(
                    ch2_set[5]
                )
                data["ch2_hysteresis"] = self.client.scale_temperature(ch2_set[6])
                data["ch2_regulation_strategy"] = ch2_set[7]
                data["ch2_water_temp_min"] = self.client.scale_temperature(ch2_set[8])
                data["ch2_water_temp_max"] = self.client.scale_temperature(ch2_set[9])
                data["ch2_water_setpoint"] = self.client.scale_temperature(ch2_set[10])
                data["ch2_equitherm_slope"] = ch2_set[11]
                data["ch2_equitherm_offset"] = self.client.scale_temperature(
                    ch2_set[12]
                )
                data["ch2_equitherm_room_effect"] = ch2_set[13]
                data["ch2_threshold_setpoint"] = self.client.scale_temperature(
                    ch2_set[14]
                )
                data["ch2_limit_heat_temp"] = self.client.scale_temperature(
                    ch2_set[15]
                )
                data["ch2_optimal_start"] = bool(ch2_set[16])
                data["ch2_fast_cooldown"] = bool(ch2_set[17])
                data["ch2_temp_correction"] = self.client.scale_temperature(
                    ch2_set[18]
                )
                data["ch2_humidity_correction"] = self.client.scale_percentage(
                    ch2_set[19]
                )

        # Process system control (if available and authenticated)
        if "system_control" in raw_data:
            sys_ctrl = raw_data["system_control"]
            if len(sys_ctrl) >= 10:
                data["control_mode"] = sys_ctrl[1]
                data["error_code"] = sys_ctrl[3]
                data["master_fail_mode"] = sys_ctrl[5]
                data["master_timeout"] = sys_ctrl[6]
                data["circuit_mask"] = sys_ctrl[9]

        return data
