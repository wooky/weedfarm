# PCB

Replacement controller board for the VegeHome Jardin Pro. It mounts where the original board was. The Android phone holds the schedule, and this board only switches the loads when the phone tells it to.

## Manufacturing

- Designed in EasyEDA, then manufactured and assembled by JLCPCB.
- Prefer JLCPCB basic parts where possible, to avoid extended-part setup fees.
- The barrel jack and micro-USB connector are soldered by hand, not by JLCPCB.

## Power

| Rail | Source | Feeds |
|------|--------|-------|
| 12V | DC adapter via barrel jack, through a reverse-polarity Schottky (SS54) | Pump; external lamp booster; buck regulator |
| 5V | LM2596S-ADJ buck from 12V, set to about 5.3V | Micro-USB VBUS through a Schottky (SS34), so VBUS sits near 5V |
| 3.3V | XC6206P332MR LDO from VBUS | STM32 |

The diode between 5V and VBUS stops a PC's VBUS from back-feeding the buck during DFU updates. Because the 3.3V LDO runs from VBUS, the MCU can be flashed over USB without the 12V adapter plugged in.

## Microcontroller

- STM32F103C8T6: the cheapest MCU with USB available from JLCPCB.
- USB full-speed device on PA11/PA12. Put a 1.5kΩ pull-up on D+ (PA12). Blue Pill boards often get this value wrong.
- Programming:
  - An SWD header (SWDIO, SWCLK, NRST, 3.3V, GND) for an ST-Link.
  - Flash a USB DFU bootloader once over SWD. After that, update the firmware over the micro-USB port.
  - The F103's ROM bootloader only supports UART, which is why the DFU bootloader is needed.
- 8MHz HSE crystal, needed for the USB clock.

## Loads

- **Pump:** 12V, switched on the low side by a logic-level N-MOSFET (e.g. AO3400A) with a flyback diode across the pump.
- **Lamp:** 12V to an external booster, also switched on the low side by a logic-level N-MOSFET.
- Both loads connect through screw terminals.
- The board has no sensors or buttons. It only drives these two outputs.

## USB / phone link

- A single micro-USB connector does three jobs: data link to the phone, phone charging, and DFU firmware updates.
- The phone has a micro-USB port. The exact model hasn't been chosen.

## Open items

- **Charging while connected:** the phone must act as USB host to talk to the STM32, but it also has to accept charge from the board. The leading option is the Accessory Charger Adapter (ACA) approach:
  - The board supplies 5V on VBUS.
  - The phone's ID pin is tied to ground through about 124kΩ (RID_A), which signals "host mode, charging allowed".
  - A standard OTG cable grounds the ID pin directly, so this needs a custom cable or adapter that carries the resistor.
  - Phone support for this varies. Test it on the chosen phone before committing to the design.
- **Board outline:** still to be measured from the original Jardin Pro PCB. This includes the outline dimensions, mounting holes, and connector positions.
- **Load currents:** measure the pump and lamp booster current draw, to size the MOSFETs, traces, and adapter.
- **Part selection:** confirm the JLCPCB part numbers and stock for all components. The LCSC numbers in the sample design are unverified.

## Sample design (KiCad)

[`weedfarm/`](weedfarm/) holds a sample schematic and board, both generated from [`tools/design.py`](tools/design.py). That file is the only place parts, nets, and placement are defined. Edit it, then regenerate:

```sh
python3 pcb/tools/generate.py   # needs KiCad 10 (uses its pcbnew Python module)
cd pcb/weedfarm
kicad-cli sch erc weedfarm.kicad_sch
kicad-cli pcb drc --schematic-parity weedfarm.kicad_pcb
```

Regenerating overwrites both KiCad files, so any edits made in the KiCad GUI are lost.

Current state:

- **Schematic:** ERC has no errors, and its exported netlist matches `design.py`. Connections are made with net labels, not drawn wires.
- **Board:** 104 x 72 mm, two layers, with a GND pour on the bottom. Parts are placed but not routed, so DRC reports unconnected items, plus a few cosmetic silkscreen warnings.
- **Not done:** routing, an outline and mounting holes matching the Jardin Pro, Gerbers, and a JLCPCB BOM/CPL.

To finish the design in EasyEDA Pro, import the KiCad project and route it there (EasyEDA has an autorouter).
