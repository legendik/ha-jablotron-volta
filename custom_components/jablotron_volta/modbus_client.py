"""Modbus TCP client for Jablotron Volta."""

from __future__ import annotations

import logging
from typing import Any

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import SYSTEM_PASSWORD
from .scaling import (
    ip_to_registers as _ip_to_registers,
    registers_to_ip as _registers_to_ip,
    registers_to_mac as _registers_to_mac,
    registers_to_uint32 as _registers_to_uint32,
    scale_percentage as _scale_percentage,
    scale_pressure as _scale_pressure,
    scale_ratio as _scale_ratio,
    scale_signed_percentage as _scale_signed_percentage,
    scale_signed_temperature as _scale_signed_temperature,
    scale_temperature as _scale_temperature,
    scale_voltage as _scale_voltage,
    unscale_percentage as _unscale_percentage,
    unscale_pressure as _unscale_pressure,
    unscale_ratio as _unscale_ratio,
    unscale_signed_temperature as _unscale_signed_temperature,
    unscale_temperature as _unscale_temperature,
    unscale_voltage as _unscale_voltage,
)

_LOGGER = logging.getLogger(__name__)


class JablotronModbusClient:
    """Wrapper for Modbus TCP client with batched reading support."""

    def __init__(self, host: str, port: int, device_id: int) -> None:
        """Initialize the Modbus client."""
        self.host = host
        self.port = port
        self.device_id = device_id
        # Initialize client with slave/unit ID - PyModbus 3.11.2
        self._client = ModbusTcpClient(
            host=host,
            port=port,
            timeout=5,
            # Slave ID is now set globally on the client
            # In 3.11.2 it's called 'slave' in constructor
        )
        self._authenticated = False

    def connect(self) -> bool:
        """Connect to the Modbus device."""
        try:
            _LOGGER.info("Connecting to Modbus device at %s:%s", self.host, self.port)
            result = self._client.connect()
            if result:
                _LOGGER.info("Successfully connected to %s:%s", self.host, self.port)
                # Authenticate immediately after connection
                # This is required for reading/writing holding registers
                if not self.authenticate_system_access():
                    _LOGGER.error("Failed to authenticate after connection")
                    return False
                _LOGGER.info("Connection and authentication complete")
            else:
                _LOGGER.error("Connection failed (result was False)")
            return result
        except Exception as err:
            _LOGGER.error(
                "Connection failed to %s:%s - %s",
                self.host,
                self.port,
                err,
                exc_info=True,
            )
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
            _LOGGER.debug("Already authenticated, skipping")
            return True

        try:
            # Write password directly without calling write_register to avoid recursion
            _LOGGER.info(
                "Authenticating with password %s to register 3001", SYSTEM_PASSWORD
            )
            result = self._client.write_register(
                3001, SYSTEM_PASSWORD, device_id=self.device_id
            )

            _LOGGER.info("Authentication result: %s (type: %s)", result, type(result))

            # Check for errors
            if hasattr(result, "isError") and result.isError():
                _LOGGER.error("System authentication failed with error: %s", result)
                return False

            # Check if result indicates success
            if not hasattr(result, "function_code"):
                _LOGGER.error("Unexpected authentication response format: %s", result)
                return False

            self._authenticated = True
            _LOGGER.info("System authentication successful!")
            return True
        except Exception as err:
            _LOGGER.error("Authentication exception: %s", err, exc_info=True)
            return False

    def read_input_registers(self, address: int, count: int = 1) -> list[int] | None:
        """Read input registers (read-only monitoring data)."""
        try:
            _LOGGER.debug(
                "Reading input registers: address=%s, count=%s, device_id=%s",
                address,
                count,
                self.device_id,
            )
            # PyModbus 3.11.2: count and device_id are keyword-only arguments
            result = self._client.read_input_registers(
                address, count=count, device_id=self.device_id
            )
            _LOGGER.debug("Read result: %s", result)

            # Check for errors - pymodbus 3.x compatibility
            if hasattr(result, "isError") and result.isError():
                _LOGGER.error(
                    "Modbus error reading input registers at %s (count %s): %s",
                    address,
                    count,
                    result,
                )
                return None

            # Alternative error check for newer pymodbus versions
            if not hasattr(result, "registers"):
                _LOGGER.error(
                    "Invalid response reading input registers at %s (count %s): %s",
                    address,
                    count,
                    result,
                )
                return None

            _LOGGER.debug(
                "Successfully read %s registers from address %s: %s",
                len(result.registers),
                address,
                result.registers,
            )
            return result.registers
        except ModbusException as err:
            _LOGGER.error("Modbus exception reading input registers: %s", err)
            return None
        except Exception as err:
            _LOGGER.exception("Unexpected error reading input registers: %s", err)
            return None

    def read_holding_registers(self, address: int, count: int = 1) -> list[int] | None:
        """Read holding registers (configuration data).

        Note: Authentication must be performed before calling this method.
        Use authenticate_system_access() before reading holding registers.
        """
        try:
            _LOGGER.debug(
                "Reading holding registers: address=%s, count=%s, device_id=%s",
                address,
                count,
                self.device_id,
            )
            # PyModbus 3.11.2: count and device_id are keyword-only arguments
            result = self._client.read_holding_registers(
                address, count=count, device_id=self.device_id
            )
            _LOGGER.debug("Read result: %s", result)

            # Check for errors - pymodbus 3.x compatibility
            if hasattr(result, "isError") and result.isError():
                _LOGGER.error(
                    "Modbus error reading holding registers at %s (count %s): %s",
                    address,
                    count,
                    result,
                )
                return None

            # Alternative error check for newer pymodbus versions
            if not hasattr(result, "registers"):
                _LOGGER.error(
                    "Invalid response reading holding registers at %s (count %s): %s",
                    address,
                    count,
                    result,
                )
                return None

            _LOGGER.debug(
                "Successfully read %s registers from address %s: %s",
                len(result.registers),
                address,
                result.registers,
            )
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
            # Holding registers (1000-3999) require authentication
            # Authenticate before writing to any holding register
            if 1000 <= address <= 3999:
                if not self.authenticate_system_access():
                    _LOGGER.error(
                        "Failed to authenticate before writing to register %s",
                        address,
                    )
                    return False

            _LOGGER.debug(
                "Writing register: address=%s, value=%s, device_id=%s",
                address,
                value,
                self.device_id,
            )
            # PyModbus 3.11.2: device_id is a keyword-only argument
            result = self._client.write_register(
                address, value, device_id=self.device_id
            )
            _LOGGER.debug("Write result: %s", result)

            # Check for errors - pymodbus 3.x compatibility
            if hasattr(result, "isError") and result.isError():
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

        # Authentication is already done in connect() method
        # No need to authenticate again here

        # Batch 1: Device info and system status (input registers)
        # Note: Not all registers exist - we read in chunks to avoid gaps

        # 1-17: Serial, device ID, HW/FW versions, MAC, IP
        batch1a = self.read_input_registers(1, 17)
        # 20-21: System info
        batch1b = self.read_input_registers(20, 2)
        # 30-32: Regulation info
        batch1c = self.read_input_registers(30, 3)
        # 40-49: Boiler status
        batch1d = self.read_input_registers(40, 10)

        if batch1a and batch1b and batch1c and batch1d:
            # Combine with gaps filled as zeros
            batch1 = batch1a + [0, 0] + batch1b + [0] * 8 + batch1c + [0] * 7 + batch1d
            data["device_info"] = batch1[0:11]
            data["network_info"] = batch1[11:17]
            data["system_status"] = batch1[19:21]
            data["regulation"] = batch1[29:32]
            data["boiler_status"] = batch1[39:49]

        # Batch 2: DHW status (input registers 101-102)
        batch2 = self.read_input_registers(101, 2)
        if batch2:
            data["dhw_status"] = batch2

        # Batch 3: CH1 status (input registers 200-206)
        batch3 = self.read_input_registers(200, 7)
        if batch3:
            data["ch1_status"] = batch3

        # Batch 4: CH2 status (input registers 300-306)
        # Only read if CH2 is available
        batch4 = self.read_input_registers(300, 7)
        if batch4:
            # Check if data is valid (not all zeros or 0xFFFF)
            if any(val != 0 and val != 0xFFFF for val in batch4):
                data["ch2_status"] = batch4
                data["ch2_available"] = True
            else:
                data["ch2_available"] = False

        # Batch 5a: System alerts (holding registers 1001-1002)
        batch5a = self.read_holding_registers(1001, 2)
        if batch5a:
            data["system_alerts"] = batch5a

        # Batch 5b: Ethernet config (holding registers 1010-1018)
        batch5b = self.read_holding_registers(1010, 9)
        if batch5b:
            data["ethernet_config"] = batch5b

        # Batch 6a: Regulation settings (holding registers 1030-1035)
        batch6a = self.read_holding_registers(1030, 6)
        if batch6a:
            data["regulation_settings"] = batch6a

        # Batch 6b: Regulation setting (holding register 1040)
        batch6b = self.read_holding_registers(1040, 1)
        if batch6b:
            # Append to regulation_settings if it exists
            if "regulation_settings" in data:
                data["regulation_settings"].extend([0, 0, 0, 0])  # Fill gaps 1036-1039
                data["regulation_settings"].extend(batch6b)  # Add 1040
            else:
                data["regulation_settings"] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0] + batch6b

        # Batch 7: Boiler settings (holding registers 1050-1062)
        batch7 = self.read_holding_registers(1050, 13)
        if batch7:
            data["boiler_settings"] = batch7

        # Batch 8a: DHW settings (holding registers 1100-1104)
        batch8a = self.read_holding_registers(1100, 5)
        if batch8a:
            data["dhw_settings"] = batch8a

        # Batch 8b: DHW settings (holding registers 1106-1107)
        batch8b = self.read_holding_registers(1106, 2)
        if batch8b:
            if "dhw_settings" in data:
                data["dhw_settings"].append(0)  # Fill gap at 1105
                data["dhw_settings"].extend(batch8b)  # Add 1106-1107
            else:
                data["dhw_settings"] = [0, 0, 0, 0, 0, 0] + batch8b

        # Batch 9: CH1 settings (holding registers 1200-1219)
        batch9 = self.read_holding_registers(1200, 20)
        if batch9:
            data["ch1_settings"] = batch9

        # Batch 10: CH2 settings (holding registers 1300-1319)
        # Only read if CH2 is available
        if data.get("ch2_available", False):
            batch10 = self.read_holding_registers(1300, 20)
            if batch10:
                data["ch2_settings"] = batch10

        # Batch 11: System control registers (holding registers 3001-3010)
        # Already authenticated at the beginning
        batch11 = self.read_holding_registers(3001, 10)
        if batch11:
            data["system_control"] = batch11

        return data

    # ------------------------------------------------------------------
    # Delegated scaling helpers (thin wrappers for backward compat)
    # The real implementations live in scaling.py for easy testing.
    # ------------------------------------------------------------------

    @staticmethod
    def registers_to_ip(reg0: int, reg1: int) -> str:
        """Convert two registers to IP address."""
        return _registers_to_ip(reg0, reg1)

    @staticmethod
    def ip_to_registers(ip: str) -> tuple[int, int]:
        """Convert IP address to two registers."""
        return _ip_to_registers(ip)

    @staticmethod
    def registers_to_mac(reg0: int, reg1: int, reg2: int) -> str:
        """Convert three registers to MAC address."""
        return _registers_to_mac(reg0, reg1, reg2)

    @staticmethod
    def registers_to_uint32(reg0: int, reg1: int) -> int:
        """Convert two registers to 32-bit unsigned integer."""
        return _registers_to_uint32(reg0, reg1)

    @staticmethod
    def scale_temperature(value: int) -> float:
        """Scale temperature value (0.1 C resolution)."""
        return _scale_temperature(value)

    @staticmethod
    def scale_signed_temperature(value: int) -> float:
        """Scale signed temperature value (0.1 C resolution)."""
        return _scale_signed_temperature(value)

    @staticmethod
    def scale_voltage(value: int) -> float:
        """Scale voltage value (0.1V resolution)."""
        return _scale_voltage(value)

    @staticmethod
    def scale_pressure(value: int) -> float:
        """Scale pressure value (0.1 bar resolution)."""
        return _scale_pressure(value)

    @staticmethod
    def scale_percentage(value: int) -> float:
        """Scale percentage value (0.1% resolution)."""
        return _scale_percentage(value)

    @staticmethod
    def scale_signed_percentage(value: int) -> float:
        """Scale signed percentage value (0.1% resolution)."""
        return _scale_signed_percentage(value)

    @staticmethod
    def scale_ratio(value: int) -> float:
        """Scale ratio value (0.1 resolution)."""
        return _scale_ratio(value)

    @staticmethod
    def unscale_temperature(value: float) -> int:
        """Unscale temperature value for writing."""
        return _unscale_temperature(value)

    @staticmethod
    def unscale_signed_temperature(value: float) -> int:
        """Unscale signed temperature value for writing."""
        return _unscale_signed_temperature(value)

    @staticmethod
    def unscale_voltage(value: float) -> int:
        """Unscale voltage value for writing."""
        return _unscale_voltage(value)

    @staticmethod
    def unscale_pressure(value: float) -> int:
        """Unscale pressure value for writing."""
        return _unscale_pressure(value)

    @staticmethod
    def unscale_percentage(value: float) -> int:
        """Unscale percentage value for writing."""
        return _unscale_percentage(value)

    @staticmethod
    def unscale_ratio(value: float) -> int:
        """Unscale ratio value for writing."""
        return _unscale_ratio(value)
