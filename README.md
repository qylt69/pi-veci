# Raspberry Pi Zero W LED Web Control

This project allows you to control an LED connected to your Raspberry Pi Zero W via a web interface. You can turn the LED on/off and set the blink delay from your browser.

## Features
- Blink an LED on GPIO17 (Pin 11)
- Web interface for ON/OFF and blink delay
- Console status updates

## Hardware
- Raspberry Pi Zero W
- 1x LED
- 1x 330Ω resistor
- Breadboard and jumper wires

**Wiring:**
- Connect the long leg (anode) of the LED to GPIO17 (Pin 11) through the resistor
- Connect the short leg (cathode) to a GND pin

## Software Setup
1. Copy the `pico` file to your Raspberry Pi.
2. Install dependencies:
   ```sh
   pip install flask RPi.GPIO
   ```
3. Run the script:
   ```sh
   python pico
   ```
4. Open a browser and go to `http://<your-pi-ip>:5000`

## File Structure
- `pico` - Main Python script
- `README.md` - This file

## License
MIT
