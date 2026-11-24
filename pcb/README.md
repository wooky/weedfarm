# PCB

Replacement controller board for the VegeHome Jardin Pro. It mounts where the original board was. The Android phone holds the schedule, and this board only switches the loads when the phone tells it to.

## Manufacturing

- Designed in EasyEDA, then manufactured and assembled by JLCPCB.
- Prefer JLCPCB basic parts where possible, to avoid extended-part setup fees.
- The barrel jack and USB-A connector are soldered by hand, not by JLCPCB.
- JLCPCB has no MCU in its basic library. The CH32X035G8U6 (C7437027) is an extended part, so it adds the extended-part setup fee.

## Power

| Rail | Source | Feeds |
|------|--------|-------|
| 12V | DC adapter via barrel jack, through a reverse-polarity Schottky (SS54) | Pump; external lamp booster; buck regulator |
| 5V | LM2596S-ADJ buck from 12V, set to about 5.3V | 3.3V LDO; USB-A VBUS through a Schottky (SS34), so VBUS sits near 5V |
| 3.3V | XC6206P332MR LDO from 5V | CH32X035 |

The diode between 5V and VBUS drops the buck's 5.3V to about 5V and stops anything plugged into the USB port from back-feeding the buck. The board needs the 12V adapter to run, including while it's being programmed.

## Microcontroller

- CH32X035G8U6 (WCH, RISC-V, 4x4mm QFN-28), about $0.54 at JLCPCB. It's the cheapest MCU found there with USB host support that needs no crystal.
- No crystal. Per the datasheet, the USBFS module's 48MHz clock comes directly from the internal HSI.
  - USB full-speed allows ±0.25% clock error. Check the HSI accuracy figure in the datasheet. If it's looser, the link depends on the phone's tolerance, so test with the actual phone, including at warm temperatures under the lamp.
- USB full-speed **host** on PC16 (UDM) / PC17 (UDP). The 15kΩ D+/D- pull-downs are internal: WCH's host examples set the pins to input pull-down. No external USB resistors are fitted.
- Pins: PA0 drives the pump, PA1 the lamp, and PA2 the status LED (active low). PC14/CC1 and PC15/CC2 (USB-PD) are unused.
- Programming and debug: a 1x6 header (3.3V, DIO, DCK, TX, RX, GND).
  - Flash over WCH's 2-wire SDI (PC18 DIO / PC19 DCK) with a WCH-LinkE.
  - USART1 (PB10 TX / PB11 RX) for logs, since the USB port is in use by the phone.
  - This package has no NRST or BOOT pin.
- WCH's [EVT examples](https://github.com/openwch/ch32x035) include USBFS host code (`EVT/EXAM/USB/USBFS/HOST_*`) to start the firmware from.

## Loads

- **Pump:** 12V, switched on the low side by a logic-level N-MOSFET (e.g. AO3400A) with a flyback diode across the pump.
- **Lamp:** 12V to an external booster, also switched on the low side by a logic-level N-MOSFET.
- Both loads connect through screw terminals.
- The board has no sensors or buttons. It only drives these two outputs.

## USB / phone link

- The board is the USB host and the phone is an ordinary USB device. A standard USB-A to phone cable plugs into the board's USB-A port.
- The phone charges from VBUS while it's connected, because a phone in device mode charges like it does on any charger. This replaces the earlier ACA approach, which needed a custom cable with an ID resistor and support from the phone.
- Data uses [Android Open Accessory (AOA)](https://source.android.com/docs/core/interaction/accessories/protocol). The board sends the AOA control requests, the phone re-enumerates as an accessory, and the Android app talks to it through the `UsbAccessory` API with bulk transfers. No root is needed.
- The phone has a micro-USB port. The exact model hasn't been chosen.

## Open items

- **Charging current:** without BC1.2 charging-downstream-port signaling, the phone will likely draw only about 500 mA. Shorting D+ to D- (dedicated-charger signaling) would break the data link. Check that 500 mA keeps the chosen phone charged with its normal usage, for example by plugging it into a PC USB 2.0 port with the screen on. If it doesn't, add a CDP controller.
- **HSI accuracy in host mode:** see the Microcontroller section.
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
