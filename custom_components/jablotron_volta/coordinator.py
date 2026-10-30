"""Data update coordinator for Jablotron Volta."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import (
    CONNECTION_NETWORK_MAC,
    DeviceInfo,
    format_mac,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_DEVICE_ID,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    UPDATE_INTERVAL,
)
from .modbus_client import JablotronModbusClient, JablotronVoltaError
from .scaling import (
    registers_to_ip,
    registers_to_mac,
    registers_to_uint32,
    scale_percentage,
    scale_pressure,
    scale_ratio,
    scale_signed_percentage,
    scale_signed_temperature,
    scale_temperature,
    scale_voltage,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pure parse functions: list[int] -> dict[str, Any]
# Each takes the raw register array from a specific batch and returns
# the parsed key-value pairs. No I/O, no side effects, easy to test.
# ---------------------------------------------------------------------------


def parse_device_info(registers: list[int]) -> dict[str, Any]:
    """Parse device information registers (11 registers).

    Returns serial_number, firmware_version, hardware_version, mac_address.
    """
    if len(registers) < 11:
        return {}

    serial_number = str(registers_to_uint32(registers[0], registers[1]))

    fw_high = registers[9]
    fw_low = registers[10]
    firmware_version = f"{fw_high >> 8}.{fw_high & 0xFF}.{fw_low}"

    hw_high = registers[4]
    hw_low = registers[5]
    hardware_version = f"{hw_high >> 8}.{hw_high & 0xFF}.{hw_low}"

    mac_address = registers_to_mac(registers[6], registers[7], registers[8])

    return {
        "serial_number": serial_number,
        "firmware_version": firmware_version,
        "hardware_version": hardware_version,
        "mac_address": mac_address,
    }


def parse_network_info(registers: list[int]) -> dict[str, Any]:
    """Parse network information registers (6 registers)."""
    if len(registers) < 6:
        return {}
    return {
        "ip_address": registers_to_ip(registers[0], registers[1]),
        "subnet_mask": registers_to_ip(registers[2], registers[3]),
        "gateway": registers_to_ip(registers[4], registers[5]),
    }


def parse_system_status(registers: list[int]) -> dict[str, Any]:
    """Parse system status registers (2 registers)."""
    if len(registers) < 2:
        return {}
    return {
        "cpu_temperature": scale_temperature(registers[0]),
        "battery_voltage": scale_voltage(registers[1]),
    }


def parse_regulation(registers: list[int]) -> dict[str, Any]:
    """Parse regulation registers (3 registers)."""
    if len(registers) < 3:
        return {}
    return {
        "regulation_mode_current": registers[0],
        "outdoor_temp_damped": scale_signed_temperature(registers[1]),
        "outdoor_temp_composite": scale_signed_temperature(registers[2]),
    }


def parse_boiler_status(registers: list[int]) -> dict[str, Any]:
    """Parse boiler status registers (10 registers)."""
    if len(registers) < 10:
        return {}
    return {
        "boiler_active_segments": registers[0],
        "boiler_inactive_segments": registers[1],
        "boiler_pressure": scale_pressure(registers[2]),
        "boiler_water_input_temp": scale_temperature(registers[4]),
        "boiler_water_return_temp": scale_temperature(registers[5]),
        "boiler_pump_power": scale_percentage(registers[6]),
        "boiler_heating_power": scale_percentage(registers[7]),
        "boiler_analog_value": scale_voltage(registers[8]),
        "boiler_pwm_value": registers[9],
    }


def parse_ch_status(registers: list[int], prefix: str) -> dict[str, Any]:
    """Parse heating circuit status registers (7 registers).

    Args:
        registers: Raw register values.
        prefix: "ch1" or "ch2".
    """
    if len(registers) < 7:
        return {}
    return {
        f"{prefix}_state_heat": bool(registers[0]),
        f"{prefix}_temperature_current": scale_temperature(registers[1]),
        f"{prefix}_water_input_temp": scale_temperature(registers[2]),
        f"{prefix}_water_return_temp": scale_temperature(registers[3]),
        f"{prefix}_pump_power": scale_percentage(registers[4]),
        f"{prefix}_humidity": scale_percentage(registers[5]),
        f"{prefix}_co2": scale_percentage(registers[6]),
    }


def parse_system_alerts(registers: list[int]) -> dict[str, Any]:
    """Parse system alert registers (2 registers)."""
    if len(registers) < 2:
        return {}
    return {
        "system_attention": registers_to_uint32(registers[0], registers[1]),
    }


def parse_regulation_settings(registers: list[int]) -> dict[str, Any]:
    """Parse regulation settings registers (6 registers)."""
    if len(registers) < 6:
        return {}
    return {
        "regulation_mode_user": registers[0],
        "outdoor_temp_source": registers[1],
        "building_momentum": registers[2],
        "composite_filter_ratio": scale_ratio(registers[3]),
        "changeover_temp": scale_signed_temperature(registers[4]),
        "outdoor_temp_manual": scale_signed_temperature(registers[5]),
    }


def parse_boiler_settings(registers: list[int]) -> dict[str, Any]:
    """Parse boiler settings registers (13 registers, we use first 7)."""
    if len(registers) < 7:
        return {}
    return {
        "boiler_load_release": registers[0],
        "boiler_hdo_high_tariff": registers[1],
        "boiler_outdoor_temp_correction": scale_signed_temperature(registers[2]),
        "boiler_total_energy": registers[3],
        "boiler_water_setpoint": scale_temperature(registers[4]),
        "boiler_water_temp_max": scale_temperature(registers[5]),
        "boiler_water_temp_min": scale_temperature(registers[6]),
    }


def parse_ch_settings(registers: list[int], prefix: str) -> dict[str, Any]:
    """Parse heating circuit settings registers (20 registers).

    Args:
        registers: Raw register values.
        prefix: "ch1" or "ch2".
    """
    if len(registers) < 20:
        return {}
    return {
        f"{prefix}_mode": registers[0],
        f"{prefix}_temperature_desired": scale_temperature(registers[1]),
        f"{prefix}_temperature_min": scale_temperature(registers[2]),
        f"{prefix}_temperature_max": scale_temperature(registers[3]),
        f"{prefix}_temperature_manual": scale_temperature(registers[4]),
        f"{prefix}_temperature_antifrost": scale_temperature(registers[5]),
        f"{prefix}_hysteresis": scale_temperature(registers[6]),
        f"{prefix}_regulation_strategy": registers[7],
        f"{prefix}_water_temp_min": scale_temperature(registers[8]),
        f"{prefix}_water_temp_max": scale_temperature(registers[9]),
        f"{prefix}_water_setpoint": scale_temperature(registers[10]),
        f"{prefix}_equitherm_slope": scale_ratio(registers[11]),
        f"{prefix}_equitherm_offset": scale_signed_temperature(registers[12]),
        f"{prefix}_equitherm_room_effect": registers[13],
        f"{prefix}_threshold_setpoint": scale_temperature(registers[14]),
        f"{prefix}_limit_heat_temp": scale_temperature(registers[15]),
        f"{prefix}_optimal_start": bool(registers[16]),
        f"{prefix}_fast_cooldown": bool(registers[17]),
        f"{prefix}_temp_correction": scale_signed_temperature(registers[18]),
        f"{prefix}_humidity_correction": scale_signed_percentage(registers[19]),
    }


def parse_system_control(registers: list[int]) -> dict[str, Any]:
    """Parse system control registers (10 registers)."""
    if len(registers) < 10:
        return {}
    return {
        "control_mode": registers[1],
        "error_code": registers[3],
        "master_fail_mode": registers[5],
        "master_timeout": registers[6],
        "circuit_mask": registers[9],
    }


def process_raw_data(raw_data: dict[str, Any]) -> dict[str, Any]:
    """Process raw register data into structured format.

    This is a pure function (no side effects). Device-info metadata
    (serial, firmware, etc.) is returned under the "device_info" key
    instead of being set on the coordinator instance.
    """
    data: dict[str, Any] = {}

    if "device_info" in raw_data:
        # Store parsed device info — coordinator extracts metadata from it
        data["_device_meta"] = parse_device_info(raw_data["device_info"])

    if "network_info" in raw_data:
        data.update(parse_network_info(raw_data["network_info"]))

    if "system_status" in raw_data:
        data.update(parse_system_status(raw_data["system_status"]))

    if "regulation" in raw_data:
        data.update(parse_regulation(raw_data["regulation"]))

    if "boiler_status" in raw_data:
        data.update(parse_boiler_status(raw_data["boiler_status"]))

    if "ch1_status" in raw_data:
        data.update(parse_ch_status(raw_data["ch1_status"], "ch1"))

    if "ch2_status" in raw_data:
        data.update(parse_ch_status(raw_data["ch2_status"], "ch2"))

    if "system_alerts" in raw_data:
        data.update(parse_system_alerts(raw_data["system_alerts"]))

    if "regulation_settings" in raw_data:
        data.update(parse_regulation_settings(raw_data["regulation_settings"]))

    if "boiler_settings" in raw_data:
        data.update(parse_boiler_settings(raw_data["boiler_settings"]))

    if "ch1_settings" in raw_data:
        data.update(parse_ch_settings(raw_data["ch1_settings"], "ch1"))

    if "ch2_settings" in raw_data:
        data.update(parse_ch_settings(raw_data["ch2_settings"], "ch2"))

    if "system_control" in raw_data:
        data.update(parse_system_control(raw_data["system_control"]))

    return data


# ---------------------------------------------------------------------------
# Coordinator class
# ---------------------------------------------------------------------------

type JablotronVoltaConfigEntry = ConfigEntry[JablotronVoltaCoordinator]


class JablotronVoltaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching Jablotron Volta data."""

    config_entry: JablotronVoltaConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: JablotronVoltaConfigEntry,
        client: JablotronModbusClient | None = None,
    ) -> None:
        """Initialize.

        Args:
            hass: Home Assistant instance.
            entry: Config entry.
            client: Optional pre-built Modbus client (for testing / DI).
        """
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client or JablotronModbusClient(
            entry.data[CONF_HOST],
            entry.data[CONF_PORT],
            entry.data[CONF_DEVICE_ID],
        )

        # Device metadata, filled from the device-info registers on each poll
        self.serial_number: str | None = None
        self.firmware_version: str | None = None
        self.hardware_version: str | None = None
        self.mac_address: str | None = None
        self._ch2_available: bool = False

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        info = DeviceInfo(
            identifiers={(DOMAIN, self.config_entry.entry_id)},
            name=f"{MANUFACTURER} {MODEL}",
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=self.firmware_version,
            hw_version=self.hardware_version,
            serial_number=self.serial_number,
            configuration_url=f"http://{self.config_entry.data[CONF_HOST]}",
        )
        if self.mac_address:
            info["connections"] = {
                (CONNECTION_NETWORK_MAC, format_mac(self.mac_address))
            }
        return info

    @property
    def ch2_available(self) -> bool:
        """Return True if Heating Circuit 2 is available."""
        return self._ch2_available

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from device."""
        try:
            raw_data = await self.client.async_read_all_data()
        except JablotronVoltaError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="update_failed",
                translation_placeholders={"error": str(err)},
            ) from err

        if not raw_data:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="no_data",
            )

        processed_data = process_raw_data(raw_data)

        if device_meta := processed_data.pop("_device_meta", {}):
            self.serial_number = device_meta.get("serial_number")
            self.firmware_version = device_meta.get("firmware_version")
            self.hardware_version = device_meta.get("hardware_version")
            self.mac_address = device_meta.get("mac_address")

        self._ch2_available = raw_data.get("ch2_available", False)

        return processed_data

    async def async_shutdown(self) -> None:
        """Stop polling and close the device connection."""
        await super().async_shutdown()
        await self.client.async_close()
