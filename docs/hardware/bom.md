# Bill of Materials

All components needed to build one EduBot. Prices are approximate.

!!! tip "Where to buy"
    Most components are available on AliExpress, Amazon, or local electronics stores. Links are not provided since stock changes frequently — search by the exact part name.

---

## Core Electronics

| Component | Quantity | Notes |
|---|---|---|
| Raspberry Pi 4 (4 GB) | 1 | 2 GB works but 4 GB recommended for SLAM |
| Arduino Nano | 1 | Any clone works; CH340 USB chip is fine |
| Cytron MDD3A motor driver | 1 | Dual-channel, dual PWM mode |
| JGB37-520 DC motor with encoder | 2 | 12V, choose gear ratio for ~100–200 RPM at 12V |
| MPU-9265 IMU (GY-521 module) | 1 | I2C, breakout board |
| RPLidar A1 or A2 | 1 | USB, 360° laser scanner |
| USB webcam | 1 | 720p minimum, for gesture control |

## Power System

| Component | Quantity | Notes |
|---|---|---|
| 3S LiPo battery | 1 | 11.1V nominal, 2200–3000 mAh recommended |
| LiPo balance charger | 1 | Essential for safety |
| LiPo protection board / BMS | 1 | Prevents over-discharge |
| Step-down converter (DC-DC) | 1 | 12V → 5V 3A, for Raspberry Pi power |
| Power switch | 1 | Rated for at least 10A |
| XT60 connector pair | 2 | Battery-side connectors |

## Mechanical

| Component | Quantity | Notes |
|---|---|---|
| Robot chassis / acrylic frame | 1 | Custom or laser-cut; see dimensions in [Hardware Overview](overview.md) |
| Caster wheel | 1 | 15 mm radius ball caster |
| M3 standoffs and screws | assorted | For mounting boards |
| Wire (22 AWG, 18 AWG) | — | Signal wires (22 AWG), power wires (18 AWG) |

## Display (optional)

| Component | Quantity | Notes |
|---|---|---|
| lcdwiki 4" HDMI display (MPI4008) | 1 | Connects to Pi's HDMI port; used for dashboard |

## Tools Required

- Soldering iron and solder
- Wire stripper / crimper
- Multimeter
- Phillips-head screwdrivers (M2, M3)
- Hot glue gun (for mounting)

---

## Estimated Cost

| Category | Approximate Cost (USD) |
|---|---|
| Core electronics | $80–120 |
| Power system | $30–50 |
| Mechanical parts | $20–40 |
| RPLidar A1 | $90–110 |
| Raspberry Pi 4 (4 GB) | $55–75 |
| **Total** | **~$280–400** |

!!! warning "RPLidar note"
    The RPLidar A1 is the most expensive single item. If budget is tight, the software will still work without it — you just won't be able to do SLAM or autonomous navigation lessons.
