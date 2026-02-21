# Jablotron Volta Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

**Control your Jablotron Volta electric boiler from Home Assistant!**

This integration connects your Jablotron Volta boiler to Home Assistant via Modbus TCP, giving you complete control over heating, hot water, and energy monitoring - all from your smartphone or computer.

## 🎯 Why You'll Love This

- **Complete Control**: Manage heating, hot water, and room temperatures from anywhere
- **Energy Savings**: Monitor consumption and optimize heating schedules automatically  
- **Smart Automation**: Set up intelligent heating based on weather, time, or occupancy
- **Professional Dashboard**: Beautiful 7-tab interface included - no coding required!
- **Easy Setup**: Install in minutes through HACS with guided configuration

## 🚀 Quick Start

### 1. Install via HACS (Easiest Way)

1. Open **HACS** in Home Assistant
2. Click **Integrations** → **⋮** (three dots) → **Custom repositories**
3. Add: `https://github.com/legendik/ha-jablotron-volta`
4. Select **Integration** category → **Add**
5. Find **Jablotron Volta** → **Download**
6. **Restart Home Assistant**

### 2. Manual Installation

Copy the `custom_components/jablotron_volta` folder to your Home Assistant `custom_components` directory, then restart.

### 3. Connect Your Boiler

1. Go to **Settings** → **Devices & Services** → **+ Add Integration**
2. Search for **"Jablotron Volta"**
3. Enter your boiler's IP address (find this in your Volta settings)
4. Leave port as **502** and device ID as **1** (default)
5. Click **Submit** - you're done!

**That's it!** The integration will automatically discover your heating circuits and create all the entities you need.

## 📱 What You Get

### 🌡️ Climate Control (3 Thermostats)
- **Hot Water**: Set your water temperature and schedule
- **Heating Circuit 1**: Control main heating zone  
- **Heating Circuit 2**: Second heating zone (auto-detected)

### 📊 Energy Monitoring
- **Total Energy Consumption**: Track your heating costs in the Energy Dashboard
- **Real-time Usage**: See exactly how much energy you're using right now

### 🌡️ Temperature Sensors (15+ Sensors)
- **Outdoor**: Current, damped, and composite temperatures
- **Boiler**: Water input/return temperatures and setpoint
- **Rooms**: Circuit temperatures, humidity, and CO2 levels
- **System**: CPU temperature and battery voltage

### ⚙️ Smart Controls
- **Regulation Modes**: Auto, Summer, Winter, Standby
- **Heating Strategies**: Weather-compensated, room-based, or direct control
- **Temperature Limits**: Set safe minimum/maximum temperatures
- **Optimal Start/Stop**: Save energy with smart scheduling

### 🔔 Alerts & Notifications
- **System Alerts**: Get notified about errors or maintenance needs
- **Low Pressure**: Warning when boiler pressure drops
- **Heating Status**: Know when your heating is actually running

## 🎨 Professional Dashboard Included

Get a complete 7-tab dashboard that looks like it was designed by a pro:

✅ **Thermostat Cards** - Quick temperature control  
✅ **Equitherm Visualization** - See your heating curve in action  
✅ **Gauge Displays** - Temperature and pressure at a glance  
✅ **24/48h History** - Track performance over time  
✅ **Recommended Settings** - Optimal values for floor heating  
✅ **Diagnostics** - Everything about your system in one place

**Installation takes 2 minutes:**
1. Settings → Dashboards → + Add Dashboard
2. Name it "Jablotron Volta"
3. Edit → ⋮ → Raw configuration editor
4. Paste the contents of `dashboard_jablotron_volta.yaml`
5. Save and enjoy your new dashboard!

## 🏠 Real-World Examples

### Save Money with Night Setback
Automatically lower temperature at night, raise it in the morning:

```yaml
# Night mode at 10 PM
automation:
  - alias: "Night Heating"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.heating_circuit_1
        data:
          temperature: 18

# Morning boost at 6 AM  
  - alias: "Morning Heating"
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

### Heat Water During Cheap Hours
Heat your hot water during off-peak electricity times:

```yaml
automation:
  - alias: "DHW Off-Peak Heating"
    trigger:
      - platform: time
        at: "23:00:00"  # Cheap electricity starts
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.hot_water
        data:
          temperature: 60  # Heat to 60°C
```

### Get Alerted About Problems
```yaml
automation:
  - alias: "Low Boiler Pressure Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.boiler_water_pressure
        below: 1.0  # Below 1 bar
    action:
      - service: notify.notify
        data:
          title: "Boiler Problem"
          message: "Water pressure is low: {{ states('sensor.boiler_water_pressure') }} bar"
```

## 🔧 Troubleshooting Made Simple

### "Integration won't connect"
- **Check IP**: Can you ping your boiler's IP from Home Assistant?
- **Check Port**: Ensure Modbus TCP is enabled (port 502)
- **Check Network**: No firewall blocking the connection

### "Missing heating circuit 2"
- **Check Wiring**: Is the second circuit physically connected?
- **Check Settings**: Is CH2 enabled in your Volta settings?
- **Check Detection**: The integration auto-detects - if it's not there, CH2 isn't active

### "Data not updating"
- **Check Connection**: Look at integration diagnostics
- **Check Network**: WiFi stability issues?
- **Be Patient**: Updates every 30 seconds by default

### "Error messages keep appearing"
- **Reset Errors**: Use the "Reset Error" button
- **Check Pressure**: Low pressure causes many errors
- **Check Logs**: Home Assistant logs show specific error details

## 📋 Requirements

- **Home Assistant**: 2025.9.0 or newer
- **Jablotron Volta**: With Modbus TCP enabled
- **Network**: Boiler must be on same network as Home Assistant

## 🤝 Need Help?

- **Issues**: Report problems on our [GitHub Issues](https://github.com/legendik/ha-jablotron-volta/issues)
- **Discussions**: Join the conversation in [GitHub Discussions](https://github.com/legendik/ha-jablotron-volta/discussions)
- **Documentation**: Check the detailed guides in the repository

## 🔧 For Developers

Want to contribute or understand how it works?

- **Architecture**: Clean separation between data acquisition, processing, and presentation
- **Testing**: Comprehensive unit tests with mocks (no HA instance needed)
- **Code Style**: Well-documented with type hints and proper error handling
- **Extensible**: Easy to add new entities or features

See [AGENTS.md](AGENTS.md) for development guidelines and contribution instructions.

## 📄 License

MIT License - feel free to use, modify, and share!

## ⚠️ Disclaimer

This is a community project, not affiliated with Jablotron. Use at your own risk.

---

**Ready to take control of your heating?** Install now and start saving energy while staying comfortable! 🏠❄️🔥