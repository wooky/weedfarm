# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

weedfarm is a low-cost replacement for the controller PCB of a VegeHome Jardin Pro hydroponic garden (the original board was damaged by a water leak). It must:

- Run the pump for 1 minute every 30 minutes
- Turn the lamp on and off at user-configurable times
- Be driven by an external device (Android) connected to the custom PCB over USB
- Charge that device over USB

## Repository state

Only `pcb/` has content so far. `firmware/` and `android/` don't exist yet.

### PCB (KiCad 10)

`pcb/weedfarm/weedfarm.kicad_sch` and `.kicad_pcb` are generated, so never hand-edit them. The single source of truth is `pcb/tools/design.py`: each part's symbol, footprint, pin-to-net map, schematic position, and board placement. `pcb/tools/generate.py` reads it and does the following:
- Flattens the KiCad library symbols and embeds them in the schematic.
- Connects every pin with a short wire and a net label. Unlisted pins get no-connect flags.
- Builds the board through the `pcbnew` Python module, naming nets to match the schematic (`/NET`, and `unconnected-(...)` for no-connect pins) so the parity check passes.

```sh
python3 pcb/tools/generate.py                                   # regenerate both files
cd pcb/weedfarm
kicad-cli sch erc weedfarm.kicad_sch                            # expect only library-table warnings
kicad-cli pcb drc --schematic-parity weedfarm.kicad_pcb         # expect only unconnected items (board is unrouted) and silkscreen warnings
kicad-cli pcb render --side top -o /tmp/top.png weedfarm.kicad_pcb
```

The ERC/DRC "library not in configuration" warnings appear when KiCad's global library tables haven't been set up (for example, KiCad has never been launched). They're harmless.

The final design is meant to be finished in EasyEDA and built and assembled by JLCPCB. `pcb/README.md` records the hardware decisions and open items.

The README specifies this layout:

- `pcb/`: the PCB design to be manufactured and populated
- `firmware/`: firmware for the microcontroller on the PCB
- `android/`: Android module that connects to, monitors, and controls the PCB over USB

Responsibilities are split this way: the Android device holds the scheduling and user configuration and talks to the microcontroller over USB, the firmware drives the pump and lamp, and the PCB also supplies USB charging power to the phone.

## Branches

- `esphome` (the remote's default branch, and the PR target): the older design, a reusable ESPHome package that controls everything over WiFi. It is a separate lineage with unrelated history, so do not merge it into `master`.
- `master`: the new PCB, firmware, and Android design.
