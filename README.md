# Jablotron Volta Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A comprehensive Home Assistant integration for Jablotron Volta electric boilers via Modbus TCP.

## Features

### Climate Control
- **Hot Water (DHW)**: Full thermostat control with off/heat/auto modes
- **Heating Circuit 1**: Temperature control with multiple regulation strategies
- **Heating Circuit 2**: Automatic detection and conditional entity creation

### Energy Monitoring
- **Total Heating Energy**: Tracks cumulative energy consumption (kWh)
- **Energy Dashboard Integration**: Compatible with Home Assistant Energy Dashboard using `total_increasing` state class

### Comprehensive Sensors
- **Temperature Sensors**: CPU, outdoor (damped & composite), boiler water (input/return/setpoint), circuit water temperatures
- **System Sensors**: Battery voltage, IP address, network info
- **Boiler Sensors**: Water pressure, pump power, heating power, PWM value, active/inactive segments
- **Environmental Sensors**: Room humidity and CO2 levels (per heating circuit)

### Advanced Controls
- **Regulation Modes**: Standby, Auto Summer/Winter, Summer, Winter
- **Regulation Strategies**: Direct setpoint, constant water temp, equitherm with room influence, room PID, floor drying modes, analog 0-10V
- **Temperature Limits**: Configurable min/max for boiler and circuit water temperatures
- **Equitherm Settings**: Slope, offset, and room effect parameters
- **Corrections**: Temperature and humidity corrections for room sensors

### Binary Sensors
- Heating states for DHW and circuits
- System alert notifications

### Switches
- Optimal start/stop functionality
- Fast cooldown mode

### Buttons
- Reset errors/attention notifications
- Device restart

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/legendik/ha-jablotron-volta`
6. Select category: "Integration"
7. Click "Add"
8. Find "Jablotron Volta" in the integration list
9. Click "Download"
10. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/jablotron_volta` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

### Prerequisites

- Jablotron Volta electric boiler with Modbus TCP enabled
- Network connectivity between Home Assistant and the Volta device
- Volta device IP address (static IP recommended)

### Setup

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Jablotron Volta"
4. Enter the following information:
   - **IP Address**: Your Volta device IP address
   - **Port**: 502 (default Modbus TCP port)
   - **Device ID**: 1 (default Modbus slave ID)
5. Click **Submit**

The integration will:
- Test the connection
- Read device information
- Automatically detect available heating circuits (CH2 created only if detected)
- Create all relevant entities

## Entities

### Climate Entities
- `climate.hot_water` - Hot Water (DHW) thermostat
- `climate.heating_circuit_1` - Heating Circuit 1 thermostat
- `climate.heating_circuit_2` - Heating Circuit 2 thermostat (if available)

### Sensors

**Energy**
- `sensor.total_heating_energy` - Total energy consumption (Energy Dashboard compatible)

**Temperatures**
- `sensor.cpu_temperature`
- `sensor.outdoor_temperature_damped`
- `sensor.outdoor_temperature_composite`
- `sensor.boiler_water_input_temperature`
- `sensor.boiler_water_return_temperature`
- `sensor.boiler_water_setpoint`
- `sensor.ch1_water_input_temperature`
- `sensor.ch1_water_return_temperature`
- `sensor.ch1_water_setpoint`
- `sensor.ch2_water_*` (if CH2 available)

**System**
- `sensor.battery_voltage`
- `sensor.ip_address`
- `sensor.subnet_mask`
- `sensor.gateway`

**Boiler**
- `sensor.boiler_water_pressure`
- `sensor.boiler_pump_power`
- `sensor.boiler_heating_power`
- `sensor.boiler_pwm_value`
- `sensor.boiler_active_segments`
- `sensor.boiler_inactive_segments`

**Environmental (per circuit)**
- `sensor.ch1_humidity`
- `sensor.ch1_co2`
- `sensor.ch1_pump_power`

### Binary Sensors
- `binary_sensor.dhw_heating`
- `binary_sensor.ch1_heating`
- `binary_sensor.ch2_heating` (if available)
- `binary_sensor.system_alert`

### Select Entities
- `select.regulation_mode` - Standby/Auto/Summer/Winter
- `select.outdoor_temp_source` - None/Boiler/Cloud/IoModule
- `select.dhw_regulation_strategy`
- `select.ch1_regulation_strategy`
- `select.ch2_regulation_strategy` (if available)
- `select.control_mode` - Monitoring/Full Control/Power Control
- `select.master_fail_mode` - Standby/No Action

### Number Entities

**Regulation**
- `number.building_thermal_momentum` (hours)
- `number.composite_filter_ratio`
- `number.changeover_temperature` (°C)
- `number.outdoor_temperature_manual` (°C)

**Boiler**
- `number.outdoor_temperature_correction` (°C)
- `number.boiler_max_water_temperature` (°C)
- `number.boiler_min_water_temperature` (°C)

**DHW**
- `number.dhw_hysteresis` (°C)

**Heating Circuits (CH1/CH2)**
- `number.ch*_antifrost_temperature` (°C)
- `number.ch*_hysteresis` (°C)
- `number.ch*_min_water_temperature` (°C)
- `number.ch*_max_water_temperature` (°C)
- `number.ch*_equitherm_slope`
- `number.ch*_equitherm_offset` (°C)
- `number.ch*_equitherm_room_effect` (%)
- `number.ch*_threshold_setpoint` (°C)
- `number.ch*_heat_limit_temperature` (°C)
- `number.ch*_temperature_correction` (°C)
- `number.ch*_humidity_correction` (%)

### Switch Entities
- `switch.ch1_optimal_start` - Optimal start/stop
- `switch.ch1_fast_cooldown`
- `switch.ch2_optimal_start` (if available)
- `switch.ch2_fast_cooldown` (if available)

### Button Entities
- `button.reset_error` - Reset errors/attention notifications
- `button.restart_device` - Restart the Volta device

## Energy Dashboard Setup

To add heating energy consumption to the Energy Dashboard:

1. Go to **Settings** → **Dashboards** → **Energy**
2. Click **Add Consumption**
3. Select `sensor.total_heating_energy`
4. Configure as needed
5. Save

The sensor uses `state_class: total_increasing` which is perfect for tracking cumulative energy usage.

## Regulation Strategies

The integration supports multiple regulation strategies for heating circuits:

- **Direct Setpoint (0)**: Manual water temperature setpoint
- **Constant Water Temp (1)**: On/off regulation with constant water temperature
- **Equitherm with Room (3)**: Weather-compensated with room temperature influence
- **Room PID (4)**: Pure room temperature PID control
- **Floor Drying (5-7)**: Special modes for drying underfloor heating
- **Analog 0-10V (8)**: External analog control

## Troubleshooting

### Connection Issues

- Verify the Volta device IP address is correct and reachable
- Check that Modbus TCP is enabled on the device (port 502)
- Ensure there are no firewall rules blocking communication
- Try pinging the device from Home Assistant host

### Missing CH2 Entities

Heating Circuit 2 entities are only created if the second circuit is detected and active. Check:
- Physical wiring for second circuit
- Device configuration for enabled circuits
- Register 3010 (`circuit_mask`) value

### Data Not Updating

- Check connection status in integration diagnostics
- Verify network stability
- Review Home Assistant logs for errors
- Default update interval is 30 seconds

### Error Messages

Use the **Reset Error** button to clear error/attention notifications. Check system logs for details about specific errors.

## Technical Details

- **Protocol**: Modbus TCP
- **Port**: 502
- **Device ID**: 1 (configurable)
- **Update Interval**: 30 seconds (default)
- **Register Types**: Input registers (read-only monitoring), Holding registers (read/write configuration)
- **Data Scaling**: Most temperature values use 0.1°C resolution, automatically handled by the integration

## Example Automations

### Night Setback for Heating

Automatically reduce heating circuit temperature at night:

```yaml
automation:
  - alias: "Heating Night Setback"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.heating_circuit_1
        data:
          temperature: 18

  - alias: "Heating Morning Boost"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.heating_circuit_1
        data:
          temperature: 21
```

### DHW Heating During Off-Peak Hours

Heat water during cheaper electricity hours:

```yaml
automation:
  - alias: "DHW Off-Peak Heating"
    trigger:
      - platform: time
        at: "23:00:00"
    condition:
      - condition: numeric_state
        entity_id: climate.hot_water
        attribute: current_temperature
        below: 55
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.hot_water
        data:
          temperature: 60

  - alias: "DHW Peak Hours Standby"
    trigger:
      - platform: time
        at: "07:00:00"
    action:
      - service: climate.set_hvac_mode
        target:
          entity_id: climate.hot_water
        data:
          hvac_mode: "off"
```

### High Energy Consumption Alert

Notify when total energy exceeds threshold:

```yaml
automation:
  - alias: "High Energy Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.total_heating_energy
        above: 1000  # kWh
    action:
      - service: notify.notify
        data:
          title: "Volta Energy Alert"
          message: "Total heating energy has exceeded 1000 kWh"
```

### System Alert Notification

Get notified about system errors:

```yaml
automation:
  - alias: "Volta System Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.system_alert
        to: "on"
    action:
      - service: notify.notify
        data:
          title: "Volta System Alert"
          message: "Check your Jablotron Volta system - alert active"
```

### Outdoor Temperature Dependent Regulation

Switch regulation mode based on outdoor temperature:

```yaml
automation:
  - alias: "Auto Summer Mode"
    trigger:
      - platform: numeric_state
        entity_id: sensor.outdoor_temperature_composite
        above: 15
        for:
          hours: 24
    action:
      - service: select.select_option
        target:
          entity_id: select.regulation_mode
        data:
          option: "Summer"

  - alias: "Auto Winter Mode"
    trigger:
      - platform: numeric_state
        entity_id: sensor.outdoor_temperature_composite
        below: 12
        for:
          hours: 24
    action:
      - service: select.select_option
        target:
          entity_id: select.regulation_mode
        data:
          option: "Winter"
```

### Low Pressure Warning

Alert when boiler pressure is too low:

```yaml
automation:
  - alias: "Low Boiler Pressure Warning"
    trigger:
      - platform: numeric_state
        entity_id: sensor.boiler_water_pressure
        below: 1.0
    action:
      - service: notify.notify
        data:
          title: "Low Boiler Pressure"
          message: "Boiler pressure is {{ states('sensor.boiler_water_pressure') }} bar - please check"
```

## Supported Firmware

- Firmware version: EBA.P.01.76, EBA.P.00.76
- Documentation version: 1.01

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License.

## Disclaimer

This integration is not affiliated with or endorsed by Jablotron. Use at your own risk.
