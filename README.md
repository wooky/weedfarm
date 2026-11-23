# weedfarm
An overcomplicated, low-cost replacement for the VegeHome Jardin Pro PCB which got damaged due to water leaking from the water reservoir.

## Features
Features of this package include:
* Activating the pump for 1 minute every 30 minutes
* User-configurable time to turn the lamp on and off
* Driven by an external device connected to the custom PCB over USB
* Ability to charge said device over USB

## Structure
This package is split up into subdirectories:
* pcb: the actual PCB to be manufactured and populated
* firmware: the extra firmware code that would need to be loaded onto the microcontroller on the PCB
* android: an Android module which is used to connect, monitor, and control the PCB over a USB connection

## Old Versions
[esphome](https://github.com/wooky/weedfarm/tree/esphome): a reusable package that can be used on an ESPHome installation which controls everything (but is bulky and only works over WiFi)
