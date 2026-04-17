# Wiring Guide

This page shows how to connect all components. Always **power off** before making wiring changes.

!!! warning "Work safely"
    Never connect or disconnect wires while the battery is connected. LiPo batteries can deliver dangerous currents. Double-check polarity before connecting power.

---

## Arduino Nano → Cytron MDD3A

The Cytron MDD3A is used in **dual PWM mode**. Each motor gets two PWM pins: one for each direction. Only one pin is driven at a time — the other stays at 0.

| Arduino Pin | Cytron Pin | Motor |
|---|---|---|
| D5 (PWM) | AIN1 | Left motor forward |
| D6 (PWM) | AIN2 | Left motor reverse |
| D9 (PWM) | BIN1 | Right motor forward |
| D10 (PWM) | BIN2 | Right motor reverse |
| GND | GND | Common ground |

!!! tip "PWM capable pins"
    On the Arduino Nano, PWM-capable pins are marked with `~`: D3, D5, D6, D9, D10, D11. Only use these for motor control.

## Arduino Nano → Encoder Inputs

Each motor has a quadrature encoder with two channels (A and B). Only channel A is used for interrupt-driven counting; channel B determines direction.

| Arduino Pin | Encoder | Motor |
|---|---|---|
| D2 (INT0) | Left ENC_A | Left motor (interrupt) |
| D8 | Left ENC_B | Left motor (direction) |
| D3 (INT1) | Right ENC_A | Right motor (interrupt) |
| D11 | Right ENC_B | Right motor (direction) |
| 5V | VCC | Both encoders |
| GND | GND | Both encoders |

!!! tip "Why interrupts?"
    Encoder channels A are on interrupt pins (D2, D3) so the Arduino never misses a tick, even at high speed. If you use non-interrupt pins you will lose encoder counts.

## Arduino Nano → Raspberry Pi (USB Serial)

Connect the Arduino Nano to the Pi using a USB-A to Micro-USB cable. The Pi will see it as `/dev/ttyUSB0` or `/dev/ttyACM0`.

Create a udev symlink for reliable naming:

```bash
# Find your device rule
udevadm info -a -n /dev/ttyUSB0 | grep -E 'ATTRS{idVendor}|ATTRS{idProduct}'

# Create /etc/udev/rules.d/99-arduino.rules:
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="arduino"
```

After creating the rule: `sudo udevadm control --reload-rules && sudo udevadm trigger`

The hardware interface expects `/dev/arduino` at 115200 baud.

## Raspberry Pi → MPU-9265 IMU (I2C)

| Pi Pin | GPIO | IMU Pin |
|---|---|---|
| Pin 1 | 3.3V | VCC |
| Pin 6 | GND | GND |
| Pin 3 | GPIO2 (SDA1) | SDA |
| Pin 5 | GPIO3 (SCL1) | SCL |

Enable I2C on the Pi:
```bash
sudo raspi-config
# Interface Options → I2C → Enable
```

Verify the IMU is detected:
```bash
sudo i2cdetect -y 1
# Should show 0x68 in the address grid
```

## Raspberry Pi → RPLidar (USB)

Connect RPLidar via USB. Create a udev rule for reliable naming:

```bash
# /etc/udev/rules.d/99-rplidar.rules
KERNEL=="ttyUSB*", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="rplidar"
```

Add your user to the `dialout` group:
```bash
sudo usermod -aG dialout rock
# Log out and back in for the group to take effect
```

## Power Distribution

```
3S LiPo (11.1V)
    │
    ├── [Main switch]
    │
    ├── [Cytron MDD3A] — direct 11.1V motor power
    │       ├── Left motor
    │       └── Right motor
    │
    └── [DC-DC 12V→5V 3A]
            └── Raspberry Pi 4 (USB-C 5V 3A)
                    └── Arduino Nano (via USB)
```

!!! warning "Pi power"
    The Raspberry Pi 4 requires a **stable 5V 3A** supply. Thin wires or cheap DC-DC converters will cause brownouts and SD card corruption. Use a quality converter with at least 3A output.

## Wiring Checklist

- [ ] All grounds are connected together (Arduino GND = Cytron GND = Pi GND)
- [ ] Motor driver supply connected to battery (via switch)
- [ ] Pi powered from DC-DC converter, not directly from battery
- [ ] Arduino powered from Pi USB (no separate supply needed)
- [ ] Encoder VCC connected to Arduino 5V (not 3.3V)
- [ ] IMU VCC connected to Pi 3.3V (not 5V)
- [ ] `/dev/arduino` symlink created and tested
- [ ] `/dev/rplidar` symlink created and tested
