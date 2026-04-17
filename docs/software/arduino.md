# Arduino Firmware

The Arduino Nano runs `robot_firmware.ino` — it handles all real-time motor control and encoder reading. The Raspberry Pi sends velocity commands; the Arduino executes them and reports back.

---

## Role in the System

```
Raspberry Pi                Arduino Nano
─────────────────           ─────────────────────────
ros2_control   ──(USB)────► parseVelocityCommand()
               ◄──────────  50Hz encoder feedback
```

The Pi never touches the motors or encoders directly. The Arduino is the real-time layer.

---

## Serial Protocol

**Command (Pi → Arduino):**
```
V<left_rad_s>,<right_rad_s>\n
```
Example: `V1.047,-1.047\n` (forward-left, backward-right = rotate)

**Feedback (Arduino → Pi):**
```
F<left_pos_rad>,<right_pos_rad>,<left_vel_rad_s>,<right_vel_rad_s>\n
```
Example: `F3.1416,3.1416,1.0472,1.0472\n`

| Parameter | Value |
|---|---|
| Baud rate | 115200 |
| Feedback rate | 50 Hz (every 20 ms) |
| Velocity units | rad/s (radians per second) |
| Position units | rad (cumulative, no wrap) |

---

## Pin Assignments

### Motor Control (Cytron MDD3A — Dual PWM Mode)

| Arduino Pin | Signal | Motor |
|---|---|---|
| D5 | LEFT_AIN1 | Left — forward |
| D6 | LEFT_AIN2 | Left — reverse |
| D9 | RIGHT_BIN1 | Right — forward |
| D10 | RIGHT_BIN2 | Right — reverse |

In dual PWM mode one pin is driven, the other stays at 0. To go forward at half speed: `AIN1 = 60 PWM`, `AIN2 = 0`.

### Encoder Inputs

| Arduino Pin | Signal | Notes |
|---|---|---|
| D2 | LEFT_ENC_A | Interrupt (INT0) |
| D8 | LEFT_ENC_B | Direction detection |
| D3 | RIGHT_ENC_A | Interrupt (INT1) |
| D11 | RIGHT_ENC_B | Direction detection |

---

## Motor Parameters

```cpp
const float WHEEL_RADIUS    = 0.033;   // meters
const int   TICKS_PER_REV   = 360;     // encoder ticks per wheel revolution
const float MAX_MOTOR_RAD_S = 5.0;     // rad/s at full PWM
const int   MAX_PWM         = 120;     // software cap (hardware max is 255)
const int   PWM_DEADBAND    = 30;      // minimum PWM to overcome static friction
```

!!! tip "Tuning MAX_MOTOR_RAD_S"
    Set `MAX_MOTOR_RAD_S` by spinning the motor at full PWM and reading the velocity from the serial feedback. If your robot overshoots commands, lower this value. If it undershoots, raise it.

---

## How `setMotorRadS()` Works

```cpp
void setMotorRadS(int pin1, int pin2, float radS) {
    int dir   = (radS >= 0) ? 1 : 0;
    float ratio = abs(radS) / MAX_MOTOR_RAD_S;  // 0.0 → 1.0
    int pwm   = (int)(ratio * MAX_PWM);

    if (pwm > 0 && pwm < PWM_DEADBAND) pwm = PWM_DEADBAND;  // overcome stiction
    pwm = constrain(pwm, 0, MAX_PWM);

    if      (pwm == 0) { analogWrite(pin1, 0);   analogWrite(pin2, 0);   }
    else if (dir == 1) { analogWrite(pin1, pwm); analogWrite(pin2, 0);   }
    else               { analogWrite(pin1, 0);   analogWrite(pin2, pwm); }
}
```

1. Convert rad/s to a 0–1 ratio
2. Scale to 0–`MAX_PWM`
3. Apply deadband (no output below `PWM_DEADBAND` — avoids jitter at rest)
4. Drive one PWM pin; zero the other

---

## Encoder Interrupts

```cpp
void leftEncoderISR() {
    leftTicks += (digitalRead(LEFT_ENC_B) == HIGH) ? 1 : -1;
}
```

On every rising edge of ENC_A, the ISR reads ENC_B to determine direction. `+1` = forward, `−1` = reverse. Ticks accumulate without overflow protection — at 360 ticks/rev and 5 rad/s, overflow takes ~200 hours of continuous running.

---

## Velocity Feedback Calculation

Every 20 ms (50 Hz):

```
radPerTick = 2π / TICKS_PER_REV
velocity   = (ticks_now - ticks_prev) * radPerTick / dt
position   = ticks_now * radPerTick
```

The feedback line is sent regardless of whether the motors are moving.

---

## Uploading the Firmware

1. Install Arduino IDE (or VS Code + Arduino extension)
2. Open `robot_firmware.ino/robot_firmware.ino.ino`
3. Select **Board:** Arduino Nano, **Processor:** ATmega328P (Old Bootloader) for Chinese clones
4. Select the correct COM/ttyUSB port
5. Click Upload

---

## Tuning Checklist

- [ ] `TICKS_PER_REV` matches your actual encoder (360 for JGB37-520 default)
- [ ] `MAX_MOTOR_RAD_S` measured from actual feedback at full PWM
- [ ] `MAX_PWM` set to prevent overspeeding (120 is conservative — safe for classroom)
- [ ] `PWM_DEADBAND` tuned until motors start cleanly with no jitter at rest
- [ ] Serial monitor at 115200 baud shows `F...` lines at ~50 Hz
