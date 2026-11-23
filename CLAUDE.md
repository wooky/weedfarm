# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

weedfarm is a low-cost replacement for the controller PCB of a VegeHome Jardin Pro hydroponic garden (the original board was damaged by a water leak). It must:

- Run the pump for 1 minute every 30 minutes
- Turn the lamp on and off at user-configurable times
- Be driven by an external device (Android) connected to the custom PCB over USB
- Charge that device over USB

## Repository state

The `master` branch currently has only the README. No build system, tests, or lint configuration exists yet, so there are no commands to document. Update this file once tooling lands.

The README specifies this layout:

- `pcb/`: the PCB design to be manufactured and populated
- `firmware/`: firmware for the microcontroller on the PCB
- `android/`: Android module that connects to, monitors, and controls the PCB over USB

Responsibilities are split this way: the Android device holds the scheduling and user configuration and talks to the microcontroller over USB, the firmware drives the pump and lamp, and the PCB also supplies USB charging power to the phone.

## Branches

- `esphome` (the remote's default branch, and the PR target): the older design, a reusable ESPHome package that controls everything over WiFi. It is a separate lineage with unrelated history, so do not merge it into `master`.
- `master`: the new PCB, firmware, and Android design.
