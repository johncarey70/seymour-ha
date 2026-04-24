# Seymour Screen Masking for Home Assistant

Home Assistant custom integration for Seymour Screen Excellence masking systems connected by serial port.

## Features

- Config flow setup
- HACS installation support
- Select entity for saved mask ratios
- Button entities for:
  - Home
  - Halt
  - Calibrate
- Diagnostic sensors for:
  - Actual screen diagonal
  - Actual screen width
  - Actual screen height
  - Number of motors
  - Number of ratios
  - Native aspect ratio
- Services for:
  - `seymour.home_motors`
  - `seymour.halt_motors`
  - `seymour.calibrate_motors`
  - `seymour.move_motors_to_saved_ratio`

## Requirements

- Home Assistant `2025.1.0` or newer
- Seymour controller connected via serial port
- Working serial device path, for example:
  - `/dev/ttyS0`
  - `/dev/ttyUSB0`

## Installation

### HACS

1. Open HACS in Home Assistant
2. Open the menu and choose **Custom repositories**
3. Add this repository URL
4. Category: **Integration**
5. Install **Seymour**
6. Restart Home Assistant

### Manual

1. Copy `custom_components/seymour` into your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Configuration

1. In Home Assistant, go to **Settings ? Devices & Services**
2. Click **Add Integration**
3. Search for **Seymour**
4. Choose the serial port for the controller

During setup, the integration reads system information from the controller and creates the device automatically.

## Options

The integration supports these options:

- **Movement timeout (seconds)**  
  Time used to block additional movement commands while the controller is moving

- **Home motors first**  
  If enabled, the integration will send the Home command before moving to a selected aspect ratio

## Entities

### Select

- **Mask ratio**  
  Choose a saved masking ratio reported by the controller

### Buttons

- **Home**
- **Halt**
- **Calibrate**

### Diagnostic Sensors

- Actual Screen Diagonal
- Actual Screen Width
- Actual Screen Height
- Number of Motors
- Number of Ratios
- Native Aspect Ratio

## Services

### `seymour.home_motors`

Move the masking system to the home position.

Example:

```yaml
service: seymour.home_motors