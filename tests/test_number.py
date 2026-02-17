"""Tests for number entities."""

from __future__ import annotations

import pytest

from custom_components.jablotron_volta.number import (
    NUMBER_TYPES,
    JablotronVoltaNumber,
)
from custom_components.jablotron_volta.scaling import (
    unscale_ratio,
    unscale_signed_percentage,
    unscale_signed_temperature,
    unscale_temperature,
)

from .conftest import _make_coordinator_data


# ---------------------------------------------------------------------------
# Descriptor-level validation (no fixtures needed)
# ---------------------------------------------------------------------------


def test_all_numbers_have_translation_key():
    """Test that all number descriptions have translation_key."""
    for number in NUMBER_TYPES:
        assert hasattr(number, "translation_key"), (
            f"Number {number.key} missing translation_key"
        )
        assert number.translation_key, f"Number {number.key} has empty translation_key"


def test_all_numbers_have_register():
    """Test that all number descriptions have register address."""
    for number in NUMBER_TYPES:
        assert hasattr(number, "register"), f"Number {number.key} missing register"
        assert number.register is not None, f"Number {number.key} has None register"


def test_all_numbers_have_scale_fn():
    """Test that all number descriptions have scale_fn for writing."""
    for number in NUMBER_TYPES:
        assert hasattr(number, "scale_fn"), f"Number {number.key} missing scale_fn"
        assert number.scale_fn is not None, f"Number {number.key} has None scale_fn"


def test_all_numbers_have_valid_range():
    """Test that all numbers have valid min/max ranges."""
    for number in NUMBER_TYPES:
        assert number.native_min_value is not None, (
            f"Number {number.key} missing native_min_value"
        )
        assert number.native_max_value is not None, (
            f"Number {number.key} missing native_max_value"
        )
        assert number.native_min_value < number.native_max_value, (
            f"Number {number.key}: min {number.native_min_value} "
            f"should be < max {number.native_max_value}"
        )


def test_no_duplicate_number_keys():
    """Test that there are no duplicate number keys."""
    keys = [n.key for n in NUMBER_TYPES]
    duplicates = [k for k in keys if keys.count(k) > 1]
    assert not duplicates, f"Found duplicate number keys: {set(duplicates)}"


def test_no_duplicate_translation_keys():
    """Test that there are no duplicate translation keys."""
    translation_keys = [n.translation_key for n in NUMBER_TYPES]
    duplicates = [k for k in translation_keys if translation_keys.count(k) > 1]
    assert not duplicates, f"Found duplicate translation keys: {set(duplicates)}"


def test_no_duplicate_registers():
    """Test that there are no duplicate register addresses."""
    registers = [n.register for n in NUMBER_TYPES]
    duplicates = [r for r in registers if registers.count(r) > 1]
    assert not duplicates, f"Found duplicate register addresses: {set(duplicates)}"


def test_translation_keys_use_full_words():
    """Test that translation_keys don't use 'temp' abbreviation."""
    for number in NUMBER_TYPES:
        tk = number.translation_key
        if tk and "temp" in tk and "temperature" not in tk:
            pytest.fail(
                f"Number {number.key}: translation_key '{tk}' uses abbreviation "
                "'temp' — use 'temperature' instead"
            )


def test_ch2_numbers_have_available_fn():
    """Test that CH2 numbers have availability function."""
    ch2_numbers = [n for n in NUMBER_TYPES if "ch2" in n.key]
    assert len(ch2_numbers) > 0, "No CH2 numbers found"

    for number in ch2_numbers:
        assert number.available_fn is not None, (
            f"CH2 number {number.key} should have available_fn"
        )


def test_non_ch2_numbers_lack_available_fn():
    """Non-CH2 numbers should NOT have available_fn."""
    non_ch2_numbers = [n for n in NUMBER_TYPES if "ch2" not in n.key]
    for number in non_ch2_numbers:
        assert number.available_fn is None, (
            f"Non-CH2 number {number.key} should not have available_fn"
        )


# ---------------------------------------------------------------------------
# value_fn tests — verify each number reads correct key from coordinator data
# ---------------------------------------------------------------------------


class TestNumberValueFunctions:
    """Test that each number's value_fn extracts the correct value from data."""

    @pytest.fixture(autouse=True)
    def setup_data(self):
        self.data = _make_coordinator_data()

    def _get_number(self, key: str):
        for n in NUMBER_TYPES:
            if n.key == key:
                return n
        pytest.fail(f"Number with key '{key}' not found in NUMBER_TYPES")

    # --- Regulation ---
    def test_building_momentum(self):
        n = self._get_number("building_momentum")
        assert n.value_fn(self.data) == 48

    def test_composite_filter_ratio(self):
        n = self._get_number("composite_filter_ratio")
        assert n.value_fn(self.data) == 0.5

    def test_changeover_temp(self):
        n = self._get_number("changeover_temp")
        assert n.value_fn(self.data) == 5.0

    def test_outdoor_temp_manual(self):
        n = self._get_number("outdoor_temp_manual")
        assert n.value_fn(self.data) == -5.0

    # --- Boiler ---
    def test_boiler_outdoor_temp_correction(self):
        n = self._get_number("boiler_outdoor_temp_correction")
        assert n.value_fn(self.data) == 0.0

    def test_boiler_water_temp_max(self):
        n = self._get_number("boiler_water_temp_max")
        assert n.value_fn(self.data) == 80.0

    def test_boiler_water_temp_min(self):
        n = self._get_number("boiler_water_temp_min")
        assert n.value_fn(self.data) == 30.0

    # --- DHW ---
    def test_dhw_hysteresis(self):
        n = self._get_number("dhw_hysteresis")
        assert n.value_fn(self.data) == 2.0

    # --- CH1 ---
    def test_ch1_antifrost_temp(self):
        n = self._get_number("ch1_antifrost_temp")
        assert n.value_fn(self.data) == 8.0

    def test_ch1_hysteresis(self):
        n = self._get_number("ch1_hysteresis")
        assert n.value_fn(self.data) == 1.0

    def test_ch1_water_temp_min(self):
        n = self._get_number("ch1_water_temp_min")
        assert n.value_fn(self.data) == 25.0

    def test_ch1_water_temp_max(self):
        n = self._get_number("ch1_water_temp_max")
        assert n.value_fn(self.data) == 55.0

    def test_ch1_equitherm_slope(self):
        n = self._get_number("ch1_equitherm_slope")
        assert n.value_fn(self.data) == 1.5

    def test_ch1_equitherm_offset(self):
        n = self._get_number("ch1_equitherm_offset")
        assert n.value_fn(self.data) == -2.0

    def test_ch1_equitherm_room_effect(self):
        n = self._get_number("ch1_equitherm_room_effect")
        assert n.value_fn(self.data) == 50

    def test_ch1_threshold_setpoint(self):
        n = self._get_number("ch1_threshold_setpoint")
        assert n.value_fn(self.data) == 45.0

    def test_ch1_limit_heat_temp(self):
        n = self._get_number("ch1_limit_heat_temp")
        assert n.value_fn(self.data) == 3.0

    def test_ch1_temp_correction(self):
        n = self._get_number("ch1_temp_correction")
        assert n.value_fn(self.data) == -0.5

    def test_ch1_humidity_correction(self):
        n = self._get_number("ch1_humidity_correction")
        assert n.value_fn(self.data) == 0.0

    # --- CH2 (returns None — no CH2 data in base fixture) ---
    def test_ch2_numbers_return_none_without_data(self):
        """All CH2 numbers should return None when CH2 data is absent."""
        ch2_numbers = [n for n in NUMBER_TYPES if "ch2" in n.key]
        for number in ch2_numbers:
            result = number.value_fn(self.data)
            assert result is None, (
                f"CH2 number {number.key} returned {result}, expected None"
            )


class TestNumberValueFnWithCh2Data:
    """Test CH2 number value_fn when CH2 data is present."""

    def test_ch2_numbers_return_values_when_present(self):
        data = _make_coordinator_data()
        data.update(
            {
                "ch2_temperature_antifrost": 7.0,
                "ch2_hysteresis": 1.5,
                "ch2_water_temp_min": 20.0,
                "ch2_water_temp_max": 60.0,
                "ch2_equitherm_slope": 1.2,
                "ch2_equitherm_offset": -1.0,
                "ch2_equitherm_room_effect": 40,
                "ch2_threshold_setpoint": 50.0,
                "ch2_limit_heat_temp": 4.0,
                "ch2_temp_correction": 0.5,
                "ch2_humidity_correction": -5.0,
            }
        )

        expected = {
            "ch2_antifrost_temp": 7.0,
            "ch2_hysteresis": 1.5,
            "ch2_water_temp_min": 20.0,
            "ch2_water_temp_max": 60.0,
            "ch2_equitherm_slope": 1.2,
            "ch2_equitherm_offset": -1.0,
            "ch2_equitherm_room_effect": 40,
            "ch2_threshold_setpoint": 50.0,
            "ch2_limit_heat_temp": 4.0,
            "ch2_temp_correction": 0.5,
            "ch2_humidity_correction": -5.0,
        }

        for key, exp_val in expected.items():
            number = next(n for n in NUMBER_TYPES if n.key == key)
            assert number.value_fn(data) == exp_val, (
                f"Number {key} expected {exp_val}, got {number.value_fn(data)}"
            )


class TestNumberValueFnEdgeCases:
    """Test value_fn behavior with empty data."""

    def test_all_value_fns_return_none_for_empty_data(self):
        empty_data: dict = {}
        for number in NUMBER_TYPES:
            result = number.value_fn(empty_data)
            assert result is None, (
                f"Number {number.key} returned {result} for empty data, expected None"
            )

    def test_value_fn_completeness(self):
        """Every non-CH2 number should return a value from conftest data."""
        data = _make_coordinator_data()
        for number in NUMBER_TYPES:
            if "ch2" in number.key:
                continue
            result = number.value_fn(data)
            assert result is not None, (
                f"Number {number.key} returned None — data key may be missing "
                f"from _make_coordinator_data()"
            )


# ---------------------------------------------------------------------------
# scale_fn tests — verify register values are computed correctly
# ---------------------------------------------------------------------------


class TestNumberScaleFunctions:
    """Test that each number's scale_fn produces the correct register value."""

    def _get_number(self, key: str):
        for n in NUMBER_TYPES:
            if n.key == key:
                return n
        pytest.fail(f"Number with key '{key}' not found in NUMBER_TYPES")

    # --- Unsigned temperatures (unscale_temperature: value * 10) ---
    def test_scale_fn_unsigned_temperature(self):
        """Unsigned temp numbers: 55.0 -> 550."""
        unsigned_temp_keys = [
            "boiler_water_temp_max",
            "boiler_water_temp_min",
            "dhw_hysteresis",
            "ch1_antifrost_temp",
            "ch1_hysteresis",
            "ch1_water_temp_min",
            "ch1_water_temp_max",
            "ch1_threshold_setpoint",
            "ch1_limit_heat_temp",
        ]
        for key in unsigned_temp_keys:
            n = self._get_number(key)
            assert n.scale_fn(55.0) == 550, f"{key}: scale_fn(55.0) should be 550"
            assert n.scale_fn(0.0) == 0, f"{key}: scale_fn(0.0) should be 0"

    # --- Signed temperatures (unscale_signed_temperature) ---
    def test_scale_fn_signed_temperature_positive(self):
        """Positive signed temp: 5.0 -> 50."""
        signed_temp_keys = [
            "changeover_temp",
            "outdoor_temp_manual",
            "boiler_outdoor_temp_correction",
            "ch1_equitherm_offset",
            "ch1_temp_correction",
        ]
        for key in signed_temp_keys:
            n = self._get_number(key)
            assert n.scale_fn(5.0) == 50, f"{key}: scale_fn(5.0) should be 50"

    def test_scale_fn_signed_temperature_negative(self):
        """Negative signed temp: -2.0 -> 65516 (two's complement)."""
        signed_temp_keys = [
            "changeover_temp",
            "outdoor_temp_manual",
            "boiler_outdoor_temp_correction",
            "ch1_equitherm_offset",
            "ch1_temp_correction",
        ]
        for key in signed_temp_keys:
            n = self._get_number(key)
            assert n.scale_fn(-2.0) == 65516, (
                f"{key}: scale_fn(-2.0) should be 65516 (two's complement)"
            )

    def test_scale_fn_signed_temperature_zero(self):
        """Zero signed temp: 0.0 -> 0."""
        n = self._get_number("changeover_temp")
        assert n.scale_fn(0.0) == 0

    # --- Ratio (unscale_ratio: value * 10) ---
    def test_scale_fn_ratio(self):
        """Ratio numbers: 1.5 -> 15."""
        ratio_keys = ["composite_filter_ratio", "ch1_equitherm_slope"]
        for key in ratio_keys:
            n = self._get_number(key)
            assert n.scale_fn(1.5) == 15, f"{key}: scale_fn(1.5) should be 15"
            assert n.scale_fn(0.0) == 0, f"{key}: scale_fn(0.0) should be 0"

    # --- Signed percentage (unscale_signed_percentage) ---
    def test_scale_fn_signed_percentage_positive(self):
        """Positive signed %: 5.0 -> 50."""
        n = self._get_number("ch1_humidity_correction")
        assert n.scale_fn(5.0) == 50

    def test_scale_fn_signed_percentage_negative(self):
        """Negative signed %: -5.0 -> 65486 (two's complement)."""
        n = self._get_number("ch1_humidity_correction")
        assert n.scale_fn(-5.0) == 65486

    # --- Integer passthrough (lambda x: int(x)) ---
    def test_scale_fn_integer_passthrough(self):
        """Integer passthrough numbers: 48 -> 48."""
        int_keys = ["building_momentum", "ch1_equitherm_room_effect"]
        for key in int_keys:
            n = self._get_number(key)
            assert n.scale_fn(48.0) == 48, f"{key}: scale_fn(48.0) should be 48"
            assert n.scale_fn(0.0) == 0, f"{key}: scale_fn(0.0) should be 0"

    # --- CH2 scale_fn ---
    def test_ch2_scale_fns_match_ch1(self):
        """CH2 scale_fn should produce same results as CH1 equivalents."""
        pairs = [
            ("ch1_antifrost_temp", "ch2_antifrost_temp"),
            ("ch1_hysteresis", "ch2_hysteresis"),
            ("ch1_water_temp_min", "ch2_water_temp_min"),
            ("ch1_water_temp_max", "ch2_water_temp_max"),
            ("ch1_equitherm_slope", "ch2_equitherm_slope"),
            ("ch1_equitherm_offset", "ch2_equitherm_offset"),
            ("ch1_equitherm_room_effect", "ch2_equitherm_room_effect"),
            ("ch1_threshold_setpoint", "ch2_threshold_setpoint"),
            ("ch1_limit_heat_temp", "ch2_limit_heat_temp"),
            ("ch1_temp_correction", "ch2_temp_correction"),
            ("ch1_humidity_correction", "ch2_humidity_correction"),
        ]
        test_values = [0.0, 1.0, -2.5, 50.0]
        for ch1_key, ch2_key in pairs:
            ch1 = self._get_number(ch1_key)
            ch2 = self._get_number(ch2_key)
            for val in test_values:
                # Skip values outside valid range for unsigned-only numbers
                if ch1.native_min_value is not None and val < ch1.native_min_value:
                    continue
                assert ch1.scale_fn(val) == ch2.scale_fn(val), (
                    f"scale_fn({val}) differs between {ch1_key} and {ch2_key}"
                )


class TestScaleFnRoundtrip:
    """Test that value_fn(data) -> scale_fn -> matches original register value."""

    def test_roundtrip_unsigned_temperature(self):
        """scale_fn(value) should reverse what scale_temperature did."""
        # 55.0 C is 550 in register -> scale gives 55.0 -> unscale gives 550
        assert unscale_temperature(55.0) == 550
        assert unscale_temperature(0.0) == 0

    def test_roundtrip_signed_temperature(self):
        """scale_fn(value) should reverse what scale_signed_temperature did."""
        # -2.0 C was 65516 in register -> scale gives -2.0 -> unscale gives 65516
        assert unscale_signed_temperature(-2.0) == 65516
        assert unscale_signed_temperature(5.0) == 50
        assert unscale_signed_temperature(0.0) == 0

    def test_roundtrip_ratio(self):
        assert unscale_ratio(1.5) == 15
        assert unscale_ratio(0.0) == 0

    def test_roundtrip_signed_percentage(self):
        assert unscale_signed_percentage(-5.0) == 65486
        assert unscale_signed_percentage(5.0) == 50
        assert unscale_signed_percentage(0.0) == 0


# ---------------------------------------------------------------------------
# Entity initialization tests (use mock fixtures)
# ---------------------------------------------------------------------------


def test_number_entity_initialization(mock_coordinator, mock_config_entry):
    """Test number entity initialization."""
    number_desc = NUMBER_TYPES[0]
    number = JablotronVoltaNumber(mock_coordinator, mock_config_entry, number_desc)

    assert number.entity_description == number_desc
    assert number._attr_unique_id == f"{mock_config_entry.entry_id}_{number_desc.key}"
    assert number.coordinator == mock_coordinator
