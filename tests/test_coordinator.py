"""Tests for coordinator parse functions.

These tests call the REAL pure parse functions from coordinator.py
with realistic register data and verify the output dictionaries.
No mocking needed — these are pure functions.
"""

from __future__ import annotations


from custom_components.jablotron_volta.coordinator import (
    parse_boiler_settings,
    parse_boiler_status,
    parse_ch_settings,
    parse_ch_status,
    parse_device_info,
    parse_dhw_settings,
    parse_dhw_status,
    parse_network_info,
    parse_regulation,
    parse_regulation_settings,
    parse_system_alerts,
    parse_system_control,
    parse_system_status,
    process_raw_data,
)


class TestParseDeviceInfo:
    """Test parse_device_info."""

    def test_normal(self):
        # registers: [serial_hi, serial_lo, dev_id_0, dev_id_1,
        #             hw_hi, hw_lo, mac0, mac1, mac2, fw_hi, fw_lo]
        regs = [0x0001, 0x0002, 0, 0, 0x0102, 3, 0x0011, 0x2233, 0x4455, 0x0305, 7]
        result = parse_device_info(regs)

        assert result["serial_number"] == str((1 << 16) | 2)  # "65538"
        assert result["firmware_version"] == "3.5.7"
        assert result["hardware_version"] == "1.2.3"
        assert result["mac_address"] == "00:11:22:33:44:55"

    def test_too_short(self):
        assert parse_device_info([1, 2, 3]) == {}


class TestParseNetworkInfo:
    """Test parse_network_info."""

    def test_normal(self):
        # IP: 192.168.1.100 -> (192<<8|168, 1<<8|100) = (49320, 356)
        # Mask: 255.255.255.0 -> (0xFFFF, 0xFF00)
        # GW: 192.168.1.1 -> (49320, 257)
        regs = [49320, 356, 0xFFFF, 0xFF00, 49320, 257]
        result = parse_network_info(regs)

        assert result["ip_address"] == "192.168.1.100"
        assert result["subnet_mask"] == "255.255.255.0"
        assert result["gateway"] == "192.168.1.1"

    def test_too_short(self):
        assert parse_network_info([1]) == {}


class TestParseSystemStatus:
    """Test parse_system_status."""

    def test_normal(self):
        # cpu_temp=455 -> 45.5C, battery=33 -> 3.3V
        result = parse_system_status([455, 33])
        assert result["cpu_temperature"] == 45.5
        assert result["battery_voltage"] == 3.3

    def test_too_short(self):
        assert parse_system_status([100]) == {}


class TestParseRegulation:
    """Test parse_regulation."""

    def test_normal_positive_temps(self):
        result = parse_regulation([2, 105, 110])
        assert result["regulation_mode_current"] == 2
        assert result["outdoor_temp_damped"] == 10.5
        assert result["outdoor_temp_composite"] == 11.0

    def test_negative_temps(self):
        # -2.5C = -25 -> 65511, -1.8C = -18 -> 65518
        result = parse_regulation([2, 65511, 65518])
        assert result["outdoor_temp_damped"] == -2.5
        assert result["outdoor_temp_composite"] == -1.8

    def test_too_short(self):
        assert parse_regulation([1]) == {}


class TestParseBoilerStatus:
    """Test parse_boiler_status."""

    def test_normal(self):
        # [active, inactive, pressure, req_mask, water_in, water_ret,
        #  pump, heating, analog, pwm]
        regs = [3, 0, 15, 0, 550, 450, 800, 1000, 0, 50]
        result = parse_boiler_status(regs)

        assert result["boiler_active_segments"] == 3
        assert result["boiler_inactive_segments"] == 0
        assert result["boiler_pressure"] == 1.5
        assert result["boiler_water_input_temp"] == 55.0
        assert result["boiler_water_return_temp"] == 45.0
        assert result["boiler_pump_power"] == 80.0
        assert result["boiler_heating_power"] == 100.0
        assert result["boiler_analog_value"] == 0.0
        assert result["boiler_pwm_value"] == 50

    def test_too_short(self):
        assert parse_boiler_status([1, 2, 3]) == {}


class TestParseDhwStatus:
    """Test parse_dhw_status."""

    def test_heating(self):
        result = parse_dhw_status([1, 485])
        assert result["dhw_state_heat"] is True
        assert result["dhw_temperature_current"] == 48.5

    def test_not_heating(self):
        result = parse_dhw_status([0, 500])
        assert result["dhw_state_heat"] is False
        assert result["dhw_temperature_current"] == 50.0

    def test_too_short(self):
        assert parse_dhw_status([1]) == {}


class TestParseChStatus:
    """Test parse_ch_status for CH1 and CH2."""

    def test_ch1(self):
        regs = [0, 215, 400, 350, 300, 550, 4500]
        result = parse_ch_status(regs, "ch1")

        assert result["ch1_state_heat"] is False
        assert result["ch1_temperature_current"] == 21.5
        assert result["ch1_water_input_temp"] == 40.0
        assert result["ch1_water_return_temp"] == 35.0
        assert result["ch1_pump_power"] == 30.0
        assert result["ch1_humidity"] == 55.0
        assert result["ch1_co2"] == 450.0

    def test_ch2(self):
        regs = [1, 230, 500, 400, 500, 600, 5000]
        result = parse_ch_status(regs, "ch2")

        assert result["ch2_state_heat"] is True
        assert result["ch2_temperature_current"] == 23.0

    def test_too_short(self):
        assert parse_ch_status([1, 2], "ch1") == {}


class TestParseSystemAlerts:
    """Test parse_system_alerts."""

    def test_no_alert(self):
        result = parse_system_alerts([0, 0])
        assert result["system_attention"] == 0

    def test_with_alert(self):
        result = parse_system_alerts([0, 5])
        assert result["system_attention"] == 5

    def test_large_value(self):
        result = parse_system_alerts([1, 0])
        assert result["system_attention"] == 65536

    def test_too_short(self):
        assert parse_system_alerts([1]) == {}


class TestParseRegulationSettings:
    """Test parse_regulation_settings."""

    def test_normal(self):
        # [mode_user, outdoor_src, momentum, ratio, changeover, manual_outdoor]
        # changeover = 5.0C -> 50, manual_outdoor = -5.0C -> 65486
        regs = [2, 1, 48, 5, 50, 65486]
        result = parse_regulation_settings(regs)

        assert result["regulation_mode_user"] == 2
        assert result["outdoor_temp_source"] == 1
        assert result["building_momentum"] == 48
        assert result["composite_filter_ratio"] == 0.5
        assert result["changeover_temp"] == 5.0
        assert result["outdoor_temp_manual"] == -5.0

    def test_too_short(self):
        assert parse_regulation_settings([1]) == {}


class TestParseBoilerSettings:
    """Test parse_boiler_settings."""

    def test_normal(self):
        # [load_rel, hdo, outdoor_corr, total_energy, setpoint, max, min, ...]
        # outdoor_corr = 0 -> 0.0C
        regs = [0, 1, 0, 1234, 600, 800, 300, 0, 0, 0, 0, 0, 0]
        result = parse_boiler_settings(regs)

        assert result["boiler_load_release"] == 0
        assert result["boiler_hdo_high_tariff"] == 1
        assert result["boiler_outdoor_temp_correction"] == 0.0
        assert result["boiler_total_energy"] == 1234
        assert result["boiler_water_setpoint"] == 60.0
        assert result["boiler_water_temp_max"] == 80.0
        assert result["boiler_water_temp_min"] == 30.0

    def test_too_short(self):
        assert parse_boiler_settings([1, 2]) == {}


class TestParseDhwSettings:
    """Test parse_dhw_settings."""

    def test_normal(self):
        # [mode, desired, min, max, manual, GAP, hysteresis, strategy]
        regs = [1, 500, 350, 650, 500, 0, 20, 0]
        result = parse_dhw_settings(regs)

        assert result["dhw_mode"] == 1
        assert result["dhw_temperature_desired"] == 50.0
        assert result["dhw_temperature_min"] == 35.0
        assert result["dhw_temperature_max"] == 65.0
        assert result["dhw_temperature_manual"] == 50.0
        assert result["dhw_hysteresis"] == 2.0
        assert result["dhw_regulation_strategy"] == 0

    def test_too_short(self):
        assert parse_dhw_settings([1, 2, 3]) == {}


class TestParseChSettings:
    """Test parse_ch_settings for CH1."""

    def test_normal(self):
        # 20 registers for CH1
        # [mode, desired, min, max, manual, antifrost, hysteresis, strategy,
        #  water_min, water_max, water_setpoint, equi_slope, equi_offset,
        #  equi_room_effect, threshold, limit_heat, optimal_start, fast_cooldown,
        #  temp_correction, humidity_correction]
        regs = [
            2,  # mode
            220,  # desired = 22.0
            150,  # min = 15.0
            280,  # max = 28.0
            220,  # manual = 22.0
            80,  # antifrost = 8.0
            10,  # hysteresis = 1.0
            3,  # strategy
            250,  # water_min = 25.0
            550,  # water_max = 55.0
            400,  # water_setpoint = 40.0
            15,  # equi_slope = 1.5
            65516,  # equi_offset = -2.0C
            50,  # equi_room_effect = 50
            450,  # threshold = 45.0
            30,  # limit_heat = 3.0
            1,  # optimal_start = True
            0,  # fast_cooldown = False
            65531,  # temp_correction = -0.5C
            0,  # humidity_correction = 0.0
        ]
        result = parse_ch_settings(regs, "ch1")

        assert result["ch1_mode"] == 2
        assert result["ch1_temperature_desired"] == 22.0
        assert result["ch1_temperature_antifrost"] == 8.0
        assert result["ch1_hysteresis"] == 1.0
        assert result["ch1_equitherm_slope"] == 1.5
        assert result["ch1_equitherm_offset"] == -2.0
        assert result["ch1_equitherm_room_effect"] == 50
        assert result["ch1_optimal_start"] is True
        assert result["ch1_fast_cooldown"] is False
        assert result["ch1_temp_correction"] == -0.5
        assert result["ch1_humidity_correction"] == 0.0

    def test_ch2_prefix(self):
        regs = [0] * 20
        regs[0] = 1
        result = parse_ch_settings(regs, "ch2")
        assert result["ch2_mode"] == 1
        assert "ch1_mode" not in result

    def test_too_short(self):
        assert parse_ch_settings([1, 2, 3], "ch1") == {}


class TestParseSystemControl:
    """Test parse_system_control."""

    def test_normal(self):
        # indices: [0=pwd, 1=control_mode, 2=reset, 3=error, 4=rtu_speed,
        #           5=master_fail, 6=master_timeout, 7=req_power, 8=dev_type, 9=circuit_mask]
        regs = [5586, 1, 0, 0, 0, 0, 60, 0, 0, 3]
        result = parse_system_control(regs)

        assert result["control_mode"] == 1
        assert result["error_code"] == 0
        assert result["master_fail_mode"] == 0
        assert result["master_timeout"] == 60
        assert result["circuit_mask"] == 3

    def test_too_short(self):
        assert parse_system_control([1, 2]) == {}


class TestProcessRawData:
    """Test the top-level process_raw_data function."""

    def test_empty_input(self):
        result = process_raw_data({})
        assert result == {}

    def test_with_system_status(self):
        raw = {"system_status": [455, 33]}
        result = process_raw_data(raw)
        assert result["cpu_temperature"] == 45.5
        assert result["battery_voltage"] == 3.3

    def test_with_device_info(self):
        regs = [0x0001, 0x0002, 0, 0, 0x0102, 3, 0x0011, 0x2233, 0x4455, 0x0305, 7]
        raw = {"device_info": regs}
        result = process_raw_data(raw)

        # Device metadata stored under _device_meta
        assert "_device_meta" in result
        assert result["_device_meta"]["serial_number"] == "65538"

    def test_full_dataset(self):
        """Test with a realistic full raw_data dict."""
        raw = {
            "device_info": [0, 1, 0, 0, 0x0100, 1, 0, 0, 0, 0x0100, 1],
            "network_info": [49320, 356, 0xFFFF, 0xFF00, 49320, 257],
            "system_status": [455, 33],
            "regulation": [2, 65511, 65518],
            "boiler_status": [3, 0, 15, 0, 550, 450, 800, 1000, 0, 50],
            "dhw_status": [1, 485],
            "ch1_status": [0, 215, 400, 350, 300, 550, 4500],
            "system_alerts": [0, 0],
            "regulation_settings": [2, 1, 48, 5, 50, 65486],
            "boiler_settings": [0, 1, 0, 1234, 600, 800, 300, 0, 0, 0, 0, 0, 0],
            "dhw_settings": [1, 500, 350, 650, 500, 0, 20, 0],
            "ch1_settings": [
                2,
                220,
                150,
                280,
                220,
                80,
                10,
                3,
                250,
                550,
                400,
                15,
                65516,
                50,
                450,
                30,
                1,
                0,
                65531,
                0,
            ],
            "system_control": [5586, 1, 0, 0, 0, 0, 60, 0, 0, 3],
        }
        result = process_raw_data(raw)

        # Spot-check a few values from different sections
        assert result["cpu_temperature"] == 45.5
        assert result["outdoor_temp_damped"] == -2.5
        assert result["boiler_pressure"] == 1.5
        assert result["dhw_state_heat"] is True
        assert result["ch1_temperature_current"] == 21.5
        assert result["system_attention"] == 0
        assert result["ch1_equitherm_offset"] == -2.0
        assert result["control_mode"] == 1
        assert result["ip_address"] == "192.168.1.100"

    def test_ch2_included_when_present(self):
        raw = {
            "ch2_status": [1, 230, 500, 400, 500, 600, 5000],
        }
        result = process_raw_data(raw)
        assert result["ch2_state_heat"] is True
        assert result["ch2_temperature_current"] == 23.0

    def test_ch2_not_included_when_absent(self):
        raw = {"system_status": [455, 33]}
        result = process_raw_data(raw)
        assert "ch2_state_heat" not in result
