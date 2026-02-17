"""Modbus TCP client for Jablotron Volta."""
from __future__ import annotations

import logging
from typing import Any

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import SYSTEM_PASSWORD

_LOGGER = logging.getLogger(__name__)


class JablotronModbusClient:
    """Wrapper for Modbus TCP client with batched reading support."""

    def __init__(self, host: str, port: int, device_id: int) -> None:
        """Initialize the Modbus client."""
        self.host = host
        self.port = port
        self.device_id = device_id
        self._client = ModbusTcpClient(host=host, port=port, timeout=5)
        self._authenticated = False

    def connect(self) -> bool:
        """Connect to the Modbus device."""
        try:
            result = self._client.connect()
            if result:
                _LOGGER.debug("Successfully connected to %s:%s", self.host, self.port)
            return result
        except Exception as err:
            _LOGGER.error("Connection failed to %s:%s - %s", self.host, self.port, err)
            return False

    def close(self) -> None:
        """Close the connection."""
        try:
            self._client.close()
            self._authenticated = False
            _LOGGER.debug("Connection closed to %s:%s", self.host, self.port)
        except Exception as err:
            _LOGGER.error("Error closing connection: %s", err)

    def authenticate_system_access(self) -> bool:
        """Authenticate for system register access (password 5586)."""
        if self._authenticated:
            return True

        try:
            result = self.write_register(3000, SYSTEM_PASSWORD)
            if result:
                self._authenticated = True
                _LOGGER.debug("System authentication successful")
            else:
                _LOGGER.warning("System authentication failed")
            return result
        except Exception as err:
            _LOGGER.error("Authentication error: %s", err)
            return False

    def read_input_registers(
        self, address: int, count: int = 1
    ) -> list[int] | None:
        """Read input registers (read-only monitoring data)."""
        try:
            _LOGGER.debug(
                "Reading input registers: address=%s, count=%s, unit=%s",
                address,
                count,
                self.device_id,
            )
            result = self._client.read_input_registers(
                address, count, unit=self.device_id
            )
            _LOGGER.debug("Read result: %s", result)
            
            # Check for errors - pymodbus 3.x compatibility
            if hasattr(result, 'isError') and result.isError():
                _LOGGER.error(
                    "Modbus error reading input registers at %s (count %s): %s",
                    address,
                    count,
                    result,
                )
                return None
            
            # Alternative error check for newer pymodbus versions
            if not hasattr(result, 'registers'):
                _LOGGER.error(
                    "Invalid response reading input registers at %s (count %s): %s",
                    address,
                    count,
                    result,
                )
                return None
                
            _LOGGER.debug("Successfully read %s registers from address %s: %s", 
                         len(result.registers), address, result.registers)
            return result.registers
        except ModbusException as err:
            _LOGGER.error("Modbus exception reading input registers: %s", err)
            return None
        except Exception as err:
            _LOGGER.exception("Unexpected error reading input registers: %s", err)
            return None

    def read_holding_registers(
        self, address: int, count: int = 1
    ) -> list[int] | None:
        """Read holding registers (configuration data)."""
        try:
            _LOGGER.debug(
                "Reading holding registers: address=%s, count=%s, unit=%s",
                address,
                count,
                self.device_id,
            )
            result = self._client.read_holding_registers(
                address, count, unit=self.device_id
            )
            _LOGGER.debug("Read result: %s", result)
            
            # Check for errors - pymodbus 3.x compatibility
            if hasattr(result, 'isError') and result.isError():
                _LOGGER.error(
                    "Modbus error reading holding registers at %s (count %s): %s",
                    address,
                    count,
                    result,
                )
                return None
            
            # Alternative error check for newer pymodbus versions
            if not hasattr(result, 'registers'):
                _LOGGER.error(
                    "Invalid response reading holding registers at %s (count %s): %s",
                    address,
                    count,
                    result,
                )
                return None
                
            _LOGGER.debug("Successfully read %s registers from address %s: %s",
                         len(result.registers), address, result.registers)
            return result.registers
        except ModbusException as err:
            _LOGGER.error("Modbus exception reading holding registers: %s", err)
            return None
        except Exception as err:
            _LOGGER.exception("Unexpected error reading holding registers: %s", err)
            return None

    def write_register(self, address: int, value: int) -> bool:
        """Write a single register."""
        try:
            _LOGGER.debug(
                "Writing register: address=%s, value=%s, unit=%s",
                address,
                value,
                self.device_id,
            )
            result = self._client.write_register(address, value, unit=self.device_id)
            _LOGGER.debug("Write result: %s", result)
            
            # Check for errors - pymodbus 3.x compatibility
            if hasattr(result, 'isError') and result.isError():
                _LOGGER.error(
                    "Modbus error writing register at %s with value %s: %s",
                    address,
                    value,
                    result,
                )
                return False
            
            _LOGGER.debug("Successfully wrote %s to register %s", value, address)
            return True
        except ModbusException as err:
            _LOGGER.error("Modbus exception writing register: %s", err)
            return False
        except Exception as err:
            _LOGGER.exception("Unexpected error writing register: %s", err)
            return False

    def read_all_data(self) -> dict[str, Any]:
        """Read all relevant data from the device in batched operations."""
        data: dict[str, Any] = {}

        # Batch 1: Device info and system status (input registers 0-48)
        # This includes: serial, device_id, hw_rev, mac, fw_rev, ip, cpu_temp,
        # battery, regulation, and boiler status
        batch1 = self.read_input_registers(0, 49)
        if batch1:
            data["device_info"] = batch1[0:11]
            data["network_info"] = batch1[11:17]
            data["system_status"] = batch1[19:21]
            data["regulation"] = batch1[29:32]
            data["boiler_status"] = batch1[39:49]

        # Batch 2: DHW status (input registers 100-101)
        batch2 = self.read_input_registers(100, 2)
        if batch2:
            data["dhw_status"] = batch2

        # Batch 3: CH1 status (input registers 199-205)
        batch3 = self.read_input_registers(199, 7)
        if batch3:
            data["ch1_status"] = batch3

        # Batch 4: CH2 status (input registers 299-305)
        # Only read if CH2 is available
        batch4 = self.read_input_registers(299, 7)
        if batch4:
            # Check if data is valid (not all zeros or 0xFFFF)
            if any(val != 0 and val != 0xFFFF for val in batch4):
                data["ch2_status"] = batch4
                data["ch2_available"] = True
            else:
                data["ch2_available"] = False

        # Batch 5: System alerts and ethernet config (holding registers 1000-1017)
        batch5 = self.read_holding_registers(1000, 18)
        if batch5:
            data["system_alerts"] = batch5[0:2]
            data["ethernet_config"] = batch5[9:18]

        # Batch 6: Regulation settings (holding registers 1029-1039)
        batch6 = self.read_holding_registers(1029, 11)
        if batch6:
            data["regulation_settings"] = batch6

        # Batch 7: Boiler settings (holding registers 1049-1061)
        batch7 = self.read_holding_registers(1049, 13)
        if batch7:
            data["boiler_settings"] = batch7

        # Batch 8: DHW settings (holding registers 1099-1106)
        batch8 = self.read_holding_registers(1099, 8)
        if batch8:
            data["dhw_settings"] = batch8

        # Batch 9: CH1 settings (holding registers 1199-1218)
        batch9 = self.read_holding_registers(1199, 20)
        if batch9:
            data["ch1_settings"] = batch9

        # Batch 10: CH2 settings (holding registers 1299-1318)
        # Only read if CH2 is available
        if data.get("ch2_available", False):
            batch10 = self.read_holding_registers(1299, 20)
            if batch10:
                data["ch2_settings"] = batch10

        # Batch 11: System control registers (holding registers 3000-3009)
        # These require authentication
        if self.authenticate_system_access():
            batch11 = self.read_holding_registers(3000, 10)
            if batch11:
                data["system_control"] = batch11

        return data

    @staticmethod
    def registers_to_ip(reg0: int, reg1: int) -> str:
        """Convert two registers to IP address."""
        return f"{reg0 >> 8}.{reg0 & 0xFF}.{reg1 >> 8}.{reg1 & 0xFF}"

    @staticmethod
    def ip_to_registers(ip: str) -> tuple[int, int]:
        """Convert IP address to two registers."""
        parts = [int(p) for p in ip.split(".")]
        reg0 = (parts[0] << 8) | parts[1]
        reg1 = (parts[2] << 8) | parts[3]
        return reg0, reg1

    @staticmethod
    def registers_to_mac(reg0: int, reg1: int, reg2: int) -> str:
        """Convert three registers to MAC address."""
        return (
            f"{reg0 >> 8:02X}:{reg0 & 0xFF:02X}:"
            f"{reg1 >> 8:02X}:{reg1 & 0xFF:02X}:"
            f"{reg2 >> 8:02X}:{reg2 & 0xFF:02X}"
        )

    @staticmethod
    def registers_to_uint32(reg0: int, reg1: int) -> int:
        """Convert two registers to 32-bit unsigned integer."""
        return (reg0 << 16) | reg1

    @staticmethod
    def scale_temperature(value: int) -> float:
        """Scale temperature value (0.1°C resolution)."""
        return value / 10.0

    @staticmethod
    def scale_voltage(value: int) -> float:
        """Scale voltage value (0.1V resolution)."""
        return value / 10.0

    @staticmethod
    def scale_pressure(value: int) -> float:
        """Scale pressure value (0.1 bar resolution)."""
        return value / 10.0

    @staticmethod
    def scale_percentage(value: int) -> float:
        """Scale percentage value (0.1% resolution)."""
        return value / 10.0

    @staticmethod
    def scale_ratio(value: int) -> float:
        """Scale ratio value (0.1 resolution)."""
        return value / 10.0

    @staticmethod
    def unscale_temperature(value: float) -> int:
        """Unscale temperature value for writing."""
        return int(value * 10)

    @staticmethod
    def unscale_voltage(value: float) -> int:
        """Unscale voltage value for writing."""
        return int(value * 10)

    @staticmethod
    def unscale_pressure(value: float) -> int:
        """Unscale pressure value for writing."""
        return int(value * 10)

    @staticmethod
    def unscale_percentage(value: float) -> int:
        """Unscale percentage value for writing."""
        return int(value * 10)

    @staticmethod
    def unscale_ratio(value: float) -> int:
        """Unscale ratio value for writing."""
        return int(value * 10)
