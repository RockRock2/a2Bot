# Power System

EduBot runs on a 3-cell LiPo battery with two voltage rails: 11.1V for motors and 5V for the Raspberry Pi.

---

## Battery Specification

| Parameter | Value |
|---|---|
| Chemistry | LiPo (Lithium Polymer) |
| Cell count | 3S (3 cells in series) |
| Nominal voltage | 11.1 V |
| Fully charged voltage | 12.6 V |
| Minimum safe voltage | 9.9 V (3.3V per cell) |
| Recommended capacity | 2200–3000 mAh |
| Connector | XT60 |

!!! warning "LiPo safety"
    Never discharge a LiPo below 3.3V per cell (9.9V total). Never leave a charging LiPo unattended. Store at 3.8V per cell (storage charge) if not using for more than a week. A damaged or puffy LiPo should be disposed of safely — do not use it.

---

## Power Rails

### 11.1V — Motor Rail
Direct battery connection to the Cytron MDD3A motor driver. No regulation needed — the driver accepts 7–30V.

Current draw: up to ~5A peak when both motors stall. Use 18 AWG wire or thicker for the motor power lines.

### 5V — Logic Rail
A DC-DC step-down converter (buck converter) drops the battery voltage to 5V for the Raspberry Pi.

| Spec | Requirement |
|---|---|
| Input voltage | 9–15 V |
| Output voltage | 5.0–5.1 V (do not exceed 5.25V) |
| Output current | ≥ 3 A |
| Ripple | < 50 mV |

The Arduino Nano is powered from the Pi's USB port and draws ~200 mA — this is included in the Pi's power budget.

---

## Main Power Switch

Install a rocker or toggle switch rated for at least **10A at 12V** in the positive battery lead, before the distribution point. This cuts all power to both rails.

```
Battery (+) ──[SWITCH]──┬── Cytron MDD3A (11.1V)
                        │
                        └── DC-DC Converter IN (+)
                                └── Raspberry Pi (5V)
Battery (–) ───────────┴── All GND (common)
```

---

## Runtime Estimate

| Scenario | Estimated Runtime |
|---|---|
| Idle (Pi + sensors, motors stopped) | ~2–3 hours |
| Driving at half speed | ~1–1.5 hours |
| Full speed + SLAM running | ~45–60 minutes |

These are rough estimates for a 2200 mAh pack. A 3000 mAh pack adds ~35% more runtime.

---

## Low Battery Warning

The dashboard (`http://<pi-ip>:8888`) does not yet show battery voltage — this is a planned feature. For now, check battery voltage with a multimeter at the XT60 connector before each session. Stop when voltage drops below **10.5V** under load.

---

## Charging

Use a LiPo balance charger. Always charge in balance mode — this equalizes cell voltages and extends battery life.

Recommended charge rate: **1C** (e.g. 2200 mA for a 2200 mAh pack). Never exceed 2C.
