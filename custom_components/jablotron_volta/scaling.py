"""Pure scaling and conversion functions for Jablotron Volta.

All functions in this module are pure (no I/O, no side effects) and can be
tested without mocking. They convert between raw Modbus register values
and human-readable values.
"""

from __future__ import annotations


# ---------------------------------------------------------------------------
# int16 helpers
# ---------------------------------------------------------------------------


def to_signed_int16(value: int) -> int:
    """Convert unsigned uint16 to signed int16.

    Modbus registers are unsigned 16-bit. Values > 32767 represent negative
    numbers in two's complement.

    Example: 65516 (0xFFEC) -> -20
    """
    if value > 32767:
        return value - 65536
    return value


def to_unsigned_int16(value: int) -> int:
    """Convert signed int16 to unsigned uint16.

    Example: -20 -> 65516 (0xFFEC)
    """
    if value < 0:
        return value + 65536
    return value


# ---------------------------------------------------------------------------
# Scaling: register -> human-readable
# ---------------------------------------------------------------------------


def scale_temperature(value: int) -> float:
    """Scale unsigned temperature value (0.1 C resolution)."""
    return value / 10.0


def scale_signed_temperature(value: int) -> float:
    """Scale signed temperature value (0.1 C resolution).

    Converts unsigned int16 to signed int16 first, then scales.
    Example: 65516 (0xFFEC) -> -20 -> -2.0 C
    """
    return to_signed_int16(value) / 10.0


def scale_voltage(value: int) -> float:
    """Scale voltage value (0.1 V resolution)."""
    return value / 10.0


def scale_pressure(value: int) -> float:
    """Scale pressure value (0.1 bar resolution)."""
    return value / 10.0


def scale_percentage(value: int) -> float:
    """Scale percentage value (0.1% resolution)."""
    return value / 10.0


def scale_signed_percentage(value: int) -> float:
    """Scale signed percentage value (0.1% resolution).

    Converts unsigned int16 to signed int16 first, then scales.
    """
    return to_signed_int16(value) / 10.0


def scale_ratio(value: int) -> float:
    """Scale ratio value (0.1 resolution)."""
    return value / 10.0


# ---------------------------------------------------------------------------
# Unscaling: human-readable -> register
# ---------------------------------------------------------------------------


def unscale_temperature(value: float) -> int:
    """Unscale unsigned temperature value for writing."""
    return int(value * 10)


def unscale_signed_temperature(value: float) -> int:
    """Unscale signed temperature value for writing.

    Scales value and converts signed int16 to unsigned int16.
    Example: -2.0 C -> -20 -> 65516 (0xFFEC)
    """
    return to_unsigned_int16(int(value * 10))


def unscale_voltage(value: float) -> int:
    """Unscale voltage value for writing."""
    return int(value * 10)


def unscale_pressure(value: float) -> int:
    """Unscale pressure value for writing."""
    return int(value * 10)


def unscale_percentage(value: float) -> int:
    """Unscale percentage value for writing."""
    return int(value * 10)


def unscale_signed_percentage(value: float) -> int:
    """Unscale signed percentage value for writing.

    Scales value and converts signed int16 to unsigned int16.
    """
    return to_unsigned_int16(int(value * 10))


def unscale_ratio(value: float) -> int:
    """Unscale ratio value for writing."""
    return int(value * 10)


# ---------------------------------------------------------------------------
# Register <-> network/multi-register helpers
# ---------------------------------------------------------------------------


def registers_to_ip(reg0: int, reg1: int) -> str:
    """Convert two registers to IP address."""
    return f"{reg0 >> 8}.{reg0 & 0xFF}.{reg1 >> 8}.{reg1 & 0xFF}"


def ip_to_registers(ip: str) -> tuple[int, int]:
    """Convert IP address to two registers."""
    parts = [int(p) for p in ip.split(".")]
    reg0 = (parts[0] << 8) | parts[1]
    reg1 = (parts[2] << 8) | parts[3]
    return reg0, reg1


def registers_to_mac(reg0: int, reg1: int, reg2: int) -> str:
    """Convert three registers to MAC address."""
    return (
        f"{reg0 >> 8:02X}:{reg0 & 0xFF:02X}:"
        f"{reg1 >> 8:02X}:{reg1 & 0xFF:02X}:"
        f"{reg2 >> 8:02X}:{reg2 & 0xFF:02X}"
    )


def registers_to_uint32(reg0: int, reg1: int) -> int:
    """Convert two registers to 32-bit unsigned integer."""
    return (reg0 << 16) | reg1
