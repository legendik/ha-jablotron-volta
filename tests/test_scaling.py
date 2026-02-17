"""Tests for scaling.py — pure scaling and conversion functions."""

from __future__ import annotations

import pytest

from custom_components.jablotron_volta.scaling import (
    ip_to_registers,
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
    to_signed_int16,
    to_unsigned_int16,
    unscale_percentage,
    unscale_pressure,
    unscale_ratio,
    unscale_signed_percentage,
    unscale_signed_temperature,
    unscale_temperature,
    unscale_voltage,
)


# ---------------------------------------------------------------------------
# int16 helpers
# ---------------------------------------------------------------------------


class TestSignedConversion:
    """Test to_signed_int16 / to_unsigned_int16."""

    def test_positive_stays_positive(self):
        assert to_signed_int16(100) == 100

    def test_zero_stays_zero(self):
        assert to_signed_int16(0) == 0

    def test_max_positive(self):
        assert to_signed_int16(32767) == 32767

    def test_min_negative(self):
        # 32768 = 0x8000 = -32768 as signed int16
        assert to_signed_int16(32768) == -32768

    def test_minus_one(self):
        # 65535 = 0xFFFF = -1
        assert to_signed_int16(65535) == -1

    def test_minus_twenty(self):
        # 65516 = 0xFFEC = -20
        assert to_signed_int16(65516) == -20

    def test_unsigned_positive(self):
        assert to_unsigned_int16(100) == 100

    def test_unsigned_zero(self):
        assert to_unsigned_int16(0) == 0

    def test_unsigned_negative(self):
        assert to_unsigned_int16(-20) == 65516

    def test_unsigned_minus_one(self):
        assert to_unsigned_int16(-1) == 65535

    def test_roundtrip_positive(self):
        assert to_unsigned_int16(to_signed_int16(215)) == 215

    def test_roundtrip_negative(self):
        assert to_unsigned_int16(to_signed_int16(65516)) == 65516


# ---------------------------------------------------------------------------
# scale_* functions
# ---------------------------------------------------------------------------


class TestScaleTemperature:
    """Test scale_temperature (unsigned)."""

    def test_normal(self):
        assert scale_temperature(215) == 21.5

    def test_zero(self):
        assert scale_temperature(0) == 0.0

    def test_high(self):
        assert scale_temperature(900) == 90.0


class TestScaleSignedTemperature:
    """Test scale_signed_temperature."""

    def test_positive(self):
        assert scale_signed_temperature(215) == 21.5

    def test_zero(self):
        assert scale_signed_temperature(0) == 0.0

    def test_negative(self):
        # 65516 -> -20 -> -2.0
        assert scale_signed_temperature(65516) == -2.0

    def test_large_negative(self):
        # 65136 -> -400 -> -40.0
        assert scale_signed_temperature(65136) == -40.0

    def test_minus_half(self):
        # 65531 -> -5 -> -0.5
        assert scale_signed_temperature(65531) == -0.5


class TestScaleVoltage:
    """Test scale_voltage."""

    def test_normal(self):
        assert scale_voltage(33) == 3.3


class TestScalePressure:
    """Test scale_pressure (NOT /100, it is /10)."""

    def test_normal(self):
        assert scale_pressure(15) == 1.5

    def test_zero(self):
        assert scale_pressure(0) == 0.0


class TestScalePercentage:
    """Test scale_percentage."""

    def test_normal(self):
        assert scale_percentage(500) == 50.0

    def test_full(self):
        assert scale_percentage(1000) == 100.0


class TestScaleSignedPercentage:
    """Test scale_signed_percentage."""

    def test_positive(self):
        assert scale_signed_percentage(100) == 10.0

    def test_negative(self):
        # 65486 -> -50 -> -5.0
        assert scale_signed_percentage(65486) == -5.0


class TestScaleRatio:
    """Test scale_ratio."""

    def test_normal(self):
        assert scale_ratio(15) == 1.5


# ---------------------------------------------------------------------------
# unscale_* functions
# ---------------------------------------------------------------------------


class TestUnscaleTemperature:
    """Test unscale_temperature."""

    def test_normal(self):
        assert unscale_temperature(21.5) == 215

    def test_zero(self):
        assert unscale_temperature(0.0) == 0


class TestUnscaleSignedTemperature:
    """Test unscale_signed_temperature."""

    def test_positive(self):
        assert unscale_signed_temperature(21.5) == 215

    def test_zero(self):
        assert unscale_signed_temperature(0.0) == 0

    def test_negative(self):
        assert unscale_signed_temperature(-2.0) == 65516

    def test_minus_half(self):
        assert unscale_signed_temperature(-0.5) == 65531


class TestUnscaleVoltage:
    """Test unscale_voltage."""

    def test_normal(self):
        assert unscale_voltage(3.3) == 33


class TestUnscalePressure:
    """Test unscale_pressure."""

    def test_normal(self):
        assert unscale_pressure(1.5) == 15


class TestUnscalePercentage:
    """Test unscale_percentage."""

    def test_normal(self):
        assert unscale_percentage(50.0) == 500


class TestUnscaleSignedPercentage:
    """Test unscale_signed_percentage."""

    def test_positive(self):
        assert unscale_signed_percentage(10.0) == 100

    def test_negative(self):
        assert unscale_signed_percentage(-5.0) == 65486


class TestUnscaleRatio:
    """Test unscale_ratio."""

    def test_normal(self):
        assert unscale_ratio(1.5) == 15


# ---------------------------------------------------------------------------
# Roundtrip tests: scale -> unscale -> same register value
# ---------------------------------------------------------------------------


class TestRoundtrip:
    """Test that scale -> unscale round-trips correctly."""

    @pytest.mark.parametrize("reg_val", [0, 100, 215, 500, 900])
    def test_temperature_roundtrip(self, reg_val):
        assert unscale_temperature(scale_temperature(reg_val)) == reg_val

    @pytest.mark.parametrize("reg_val", [0, 215, 32767, 65516, 65136])
    def test_signed_temperature_roundtrip(self, reg_val):
        assert unscale_signed_temperature(scale_signed_temperature(reg_val)) == reg_val

    @pytest.mark.parametrize("reg_val", [0, 15, 30])
    def test_pressure_roundtrip(self, reg_val):
        assert unscale_pressure(scale_pressure(reg_val)) == reg_val


# ---------------------------------------------------------------------------
# Network / multi-register helpers
# ---------------------------------------------------------------------------


class TestRegistersToIp:
    """Test registers_to_ip."""

    def test_normal(self):
        # 192.168.1.100 -> reg0 = (192 << 8) | 168 = 49320, reg1 = (1 << 8) | 100 = 356
        assert registers_to_ip(49320, 356) == "192.168.1.100"

    def test_all_zeros(self):
        assert registers_to_ip(0, 0) == "0.0.0.0"

    def test_all_max(self):
        assert registers_to_ip(0xFFFF, 0xFFFF) == "255.255.255.255"


class TestIpToRegisters:
    """Test ip_to_registers."""

    def test_normal(self):
        assert ip_to_registers("192.168.1.100") == (49320, 356)

    def test_roundtrip(self):
        ip = "10.0.0.1"
        reg0, reg1 = ip_to_registers(ip)
        assert registers_to_ip(reg0, reg1) == ip


class TestRegistersToMac:
    """Test registers_to_mac."""

    def test_normal(self):
        # 0x0011, 0x2233, 0x4455
        result = registers_to_mac(0x0011, 0x2233, 0x4455)
        assert result == "00:11:22:33:44:55"

    def test_all_ff(self):
        result = registers_to_mac(0xFFFF, 0xFFFF, 0xFFFF)
        assert result == "FF:FF:FF:FF:FF:FF"


class TestRegistersToUint32:
    """Test registers_to_uint32."""

    def test_normal(self):
        # (1 << 16) | 2 = 65538
        assert registers_to_uint32(1, 2) == 65538

    def test_zero(self):
        assert registers_to_uint32(0, 0) == 0

    def test_max(self):
        assert registers_to_uint32(0xFFFF, 0xFFFF) == 0xFFFFFFFF
