"""Tests for the async Modbus client wrapper."""

from __future__ import annotations

import asyncio
from collections.abc import Generator
from types import SimpleNamespace
from typing import Any
from unittest.mock import patch

import pytest
from pymodbus.exceptions import ModbusIOException

from custom_components.jablotron_volta.const import REG_CH1_MODE, REG_SYS_PASSWORD
from custom_components.jablotron_volta.modbus_client import (
    JablotronModbusClient,
    JablotronVoltaConnectionError,
    JablotronVoltaResponseError,
)


def _response(*, error: bool = False, count: int = 0) -> SimpleNamespace:
    return SimpleNamespace(isError=lambda: error, registers=[1] * count)


class FakeModbusClient:
    """Stand-in for pymodbus' AsyncModbusTcpClient recording every call."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.connected = False
        self.calls: list[tuple[str, int] | str] = []
        self.fail_next: Exception | None = None
        self.reject_writes = False

    async def connect(self) -> bool:
        self.calls.append("connect")
        self.connected = True
        return True

    def close(self) -> None:
        self.calls.append("close")
        self.connected = False

    async def _request(self, name: str, address: int) -> None:
        self.calls.append((name, address))
        # Yield so concurrent callers could interleave without the client lock
        await asyncio.sleep(0)
        if self.fail_next is not None:
            err, self.fail_next = self.fail_next, None
            raise err

    async def read_input_registers(
        self, address: int, *, count: int, device_id: int
    ) -> SimpleNamespace:
        await self._request("read", address)
        return _response(count=count)

    async def read_holding_registers(
        self, address: int, *, count: int, device_id: int
    ) -> SimpleNamespace:
        await self._request("read", address)
        return _response(count=count)

    async def write_register(
        self, address: int, value: int, *, device_id: int
    ) -> SimpleNamespace:
        await self._request("write", address)
        return _response(error=self.reject_writes and address != REG_SYS_PASSWORD)


@pytest.fixture
def fake() -> Generator[FakeModbusClient]:
    instance = FakeModbusClient()
    with patch(
        "custom_components.jablotron_volta.modbus_client.AsyncModbusTcpClient",
        return_value=instance,
    ):
        yield instance


async def test_poll_and_write_do_not_interleave(fake: FakeModbusClient) -> None:
    """A write issued during a poll runs as one block: login, then the write."""
    client = JablotronModbusClient("host", 502, 1)

    await asyncio.gather(
        client.async_read_all_data(), client.async_write_register(REG_CH1_MODE, 1)
    )

    requests = [call for call in fake.calls if isinstance(call, tuple)]
    write_index = requests.index(("write", REG_CH1_MODE))
    # The protected write is directly preceded by its own login
    assert requests[write_index - 1] == ("write", REG_SYS_PASSWORD)
    # All poll reads are contiguous (nothing from the write slipped in between)
    read_indexes = [i for i, call in enumerate(requests) if call[0] == "read"]
    assert read_indexes == list(range(read_indexes[0], read_indexes[-1] + 1))
    # One connection shared by both operations
    assert fake.calls.count("connect") == 1


async def test_connection_error_closes_and_reconnects(fake: FakeModbusClient) -> None:
    """A transport error drops the connection; the next call reconnects."""
    client = JablotronModbusClient("host", 502, 1)
    fake.fail_next = ModbusIOException("timeout")

    with pytest.raises(JablotronVoltaConnectionError):
        await client.async_read_all_data()
    assert not fake.connected

    await client.async_read_all_data()
    assert fake.calls.count("connect") == 2


async def test_rejected_write_raises(fake: FakeModbusClient) -> None:
    """An error response to a write is reported instead of being swallowed."""
    client = JablotronModbusClient("host", 502, 1)
    fake.reject_writes = True

    with pytest.raises(JablotronVoltaResponseError):
        await client.async_write_register(REG_CH1_MODE, 1)


async def test_read_serial_number_closes_connection(fake: FakeModbusClient) -> None:
    """Validation logs in, reads the serial and does not keep the socket open."""
    client = JablotronModbusClient("host", 502, 1)

    serial = await client.async_read_serial_number()

    assert serial == str((1 << 16) | 1)
    assert ("write", REG_SYS_PASSWORD) in fake.calls
    assert not fake.connected
