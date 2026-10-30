"""Async Modbus TCP client for Jablotron Volta."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ModbusPDU

from .const import REG_SERIAL_NUMBER_0, REG_SYS_PASSWORD, SYSTEM_PASSWORD
from .scaling import registers_to_uint32

_LOGGER = logging.getLogger(__name__)

# Holding registers in this range are only accessible after writing the
# system password to REG_SYS_PASSWORD.
PROTECTED_REGISTERS = range(1000, 4000)

type _ReadMethod = Callable[..., Awaitable[ModbusPDU]]


class JablotronVoltaError(Exception):
    """Base error for Jablotron Volta communication."""


class JablotronVoltaConnectionError(JablotronVoltaError):
    """The device is unreachable or the connection dropped mid-request."""


class JablotronVoltaResponseError(JablotronVoltaError):
    """The device answered with a Modbus error response."""


class JablotronModbusClient:
    """Modbus TCP client keeping one connection open between requests.

    All device access is serialized through a single lock so the coordinator
    poll and entity writes never interleave on the same connection.
    """

    def __init__(self, host: str, port: int, device_id: int) -> None:
        """Initialize the client."""
        self.host = host
        self.port = port
        self.device_id = device_id
        # Reconnects are handled explicitly in _connect(); pymodbus' background
        # auto-reconnect is disabled so connection state stays predictable.
        self._client = AsyncModbusTcpClient(
            host, port=port, timeout=5, reconnect_delay=0
        )
        self._lock = asyncio.Lock()

    async def async_read_serial_number(self) -> str:
        """Connect, authenticate and read the device serial number.

        Used to validate connection settings; closes the connection afterwards.
        """
        async with self._lock:
            try:
                await self._connect()
                await self._authenticate()
                registers = await self._read(
                    self._client.read_input_registers, REG_SERIAL_NUMBER_0, 2
                )
            finally:
                self._client.close()
        if registers is None:
            raise JablotronVoltaResponseError("Device did not return its serial number")
        return str(registers_to_uint32(registers[0], registers[1]))

    async def async_read_all_data(self) -> dict[str, Any]:
        """Read all relevant registers in batches."""
        async with self._lock:
            await self._connect()
            # Authenticate on every poll: the device session state is not
            # documented, so never rely on an earlier login.
            await self._authenticate()
            return await self._read_all()

    async def async_write_register(self, address: int, value: int) -> None:
        """Write a single holding register."""
        async with self._lock:
            await self._connect()
            if address in PROTECTED_REGISTERS:
                await self._authenticate()
            await self._write(address, value)

    async def async_close(self) -> None:
        """Close the connection."""
        async with self._lock:
            self._client.close()

    async def _connect(self) -> None:
        """Open the connection if it is not open."""
        if self._client.connected:
            return
        _LOGGER.debug("Connecting to %s:%s", self.host, self.port)
        if not await self._client.connect():
            raise JablotronVoltaConnectionError(
                f"Cannot connect to {self.host}:{self.port}"
            )

    async def _authenticate(self) -> None:
        """Unlock protected holding registers."""
        await self._write(REG_SYS_PASSWORD, SYSTEM_PASSWORD)

    async def _read(
        self, method: _ReadMethod, address: int, count: int
    ) -> list[int] | None:
        """Read registers; None when the device rejects the request."""
        try:
            result = await method(address, count=count, device_id=self.device_id)
        except ModbusException as err:
            self._client.close()
            raise JablotronVoltaConnectionError(
                f"Reading registers {address}-{address + count - 1} failed: {err}"
            ) from err
        if result.isError():
            _LOGGER.debug(
                "Device rejected read of registers %s-%s: %s",
                address,
                address + count - 1,
                result,
            )
            return None
        return list(result.registers)

    async def _write(self, address: int, value: int) -> None:
        """Write a register, raising on any failure."""
        try:
            result = await self._client.write_register(
                address, value, device_id=self.device_id
            )
        except ModbusException as err:
            self._client.close()
            raise JablotronVoltaConnectionError(
                f"Writing register {address} failed: {err}"
            ) from err
        if result.isError():
            raise JablotronVoltaResponseError(
                f"Device rejected writing {value} to register {address}: {result}"
            )

    async def _read_input(self, address: int, count: int) -> list[int] | None:
        return await self._read(self._client.read_input_registers, address, count)

    async def _read_holding(self, address: int, count: int) -> list[int] | None:
        return await self._read(self._client.read_holding_registers, address, count)

    async def _read_all(self) -> dict[str, Any]:
        """Read every register batch the integration uses."""
        data: dict[str, Any] = {}

        # Input registers 1-49 are sparse; read the populated ranges and
        # re-assemble them with zero-filled gaps.
        batch1a = await self._read_input(1, 17)  # device + network info
        batch1b = await self._read_input(20, 2)  # system status
        batch1c = await self._read_input(30, 3)  # regulation
        batch1d = await self._read_input(40, 10)  # boiler status
        if batch1a and batch1b and batch1c and batch1d:
            batch1 = batch1a + [0, 0] + batch1b + [0] * 8 + batch1c + [0] * 7 + batch1d
            data["device_info"] = batch1[0:11]
            data["network_info"] = batch1[11:17]
            data["system_status"] = batch1[19:21]
            data["regulation"] = batch1[29:32]
            data["boiler_status"] = batch1[39:49]

        if ch1_status := await self._read_input(200, 7):
            data["ch1_status"] = ch1_status

        if ch2_status := await self._read_input(300, 7):
            # An absent circuit reports all zeros or 0xFFFF
            if any(val not in (0, 0xFFFF) for val in ch2_status):
                data["ch2_status"] = ch2_status
                data["ch2_available"] = True
            else:
                data["ch2_available"] = False

        if system_alerts := await self._read_holding(1001, 2):
            data["system_alerts"] = system_alerts

        if regulation_settings := await self._read_holding(1030, 6):
            data["regulation_settings"] = regulation_settings

        if boiler_settings := await self._read_holding(1050, 13):
            data["boiler_settings"] = boiler_settings

        if ch1_settings := await self._read_holding(1200, 20):
            data["ch1_settings"] = ch1_settings

        if data.get("ch2_available") and (
            ch2_settings := await self._read_holding(1300, 20)
        ):
            data["ch2_settings"] = ch2_settings

        if system_control := await self._read_holding(3001, 10):
            data["system_control"] = system_control

        return data
