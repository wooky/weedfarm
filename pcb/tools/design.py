"""weedfarm sample board: single source of truth for parts and connectivity.

Each part maps symbol pin numbers to net names. Symbol pins that are not
listed get a no-connect flag in the schematic.

`sch` is the symbol origin on the A3 schematic sheet (mm).
`pcb` is the footprint position (x, y, rotation) on the board (mm, deg).
"""

GND = "GND"
V12 = "+12V"
V5 = "+5V"
V3 = "+3V3"
VBUS = "VBUS"

FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"
FP_C0805 = "Capacitor_SMD:C_0805_2012Metric"
FP_SMA = "Diode_SMD:D_SMA"


def part(ref, lib_id, value, footprint, pins, sch, pcb, lcsc=""):
    return dict(ref=ref, lib_id=lib_id, value=value, footprint=footprint,
                pins=pins, sch=sch, pcb=pcb, lcsc=lcsc)


def res(ref, value, a, b, sch, pcb, lcsc=""):
    return part(ref, "Device:R", value, FP_R, {"1": a, "2": b}, sch, pcb, lcsc)


def cap(ref, value, a, b, sch, pcb, fp=FP_C, lcsc=""):
    return part(ref, "Device:C", value, fp, {"1": a, "2": b}, sch, pcb, lcsc)


PARTS = [
    # ---------------------------------------------------------------- 12V input
    part("J1", "Connector:Barrel_Jack_Switch", "12V DC in",
         "Connector_BarrelJack:BarrelJack_Horizontal",
         {"1": "VIN_RAW", "2": GND}, sch=(25.4, 38.1), pcb=(10, 12, 0)),
    part("D1", "Device:D_Schottky", "SS54", "Diode_SMD:D_SMC",
         {"1": V12, "2": "VIN_RAW"}, sch=(50.8, 38.1), pcb=(25, 6, 0)),
    part("C1", "Device:C_Polarized", "220uF 25V", "Capacitor_SMD:CP_Elec_10x10",
         {"1": V12, "2": GND}, sch=(76.2, 38.1), pcb=(25, 20, 90)),
    part("FLG1", "power:PWR_FLAG", "PWR_FLAG", "", {"1": V12},
         sch=(76.2, 20.32), pcb=None),

    # ------------------------------------------------- 12V -> 5.3V buck (LM2596)
    part("U1", "Regulator_Switching:LM2596S-ADJ", "LM2596S-ADJ",
         "Package_TO_SOT_SMD:TO-263-5_TabPin3",
         {"1": V12, "2": "SW", "3": GND, "4": "FB", "5": GND},
         sch=(30.48, 83.82), pcb=(42, 12, 0)),
    part("D2", "Device:D_Schottky", "SS34", FP_SMA,
         {"1": "SW", "2": GND}, sch=(63.5, 83.82), pcb=(42, 26, 180), lcsc="C8678"),
    part("L1", "Device:L", "33uH 3A", "Inductor_SMD:L_12x12mm_H8mm",
         {"1": "SW", "2": V5}, sch=(83.82, 83.82), pcb=(60, 14, 0)),
    part("C2", "Device:C_Polarized", "220uF 10V", "Capacitor_SMD:CP_Elec_8x10",
         {"1": V5, "2": GND}, sch=(104.14, 83.82), pcb=(60, 30, 90)),
    # Vout = 1.23V * (1 + R1/R2) = 5.29V, so VBUS stays near 5V after D3.
    res("R1", "3.3k", V5, "FB", sch=(124.46, 83.82), pcb=(50, 24, 90)),
    res("R2", "1k", "FB", GND, sch=(139.7, 83.82), pcb=(52, 24, 90)),

    # ---------------------------------------------------- USB / phone charging
    # D3 keeps a PC's VBUS from back-feeding the buck during DFU updates.
    part("D3", "Device:D_Schottky", "SS34", FP_SMA,
         {"1": VBUS, "2": V5}, sch=(25.4, 129.54), pcb=(74, 22, 90), lcsc="C8678"),
    part("J2", "Connector:USB_B_Micro", "Micro-USB (phone / DFU)",
         "Connector_USB:USB_Micro-B_Molex-105017-0001",
         {"1": VBUS, "2": "USB_DM", "3": "USB_DP", "4": "USB_ID", "5": GND, "SH": GND},
         sch=(50.8, 129.54), pcb=(92, 6, 180)),
    # RID_A: tells an OTG phone it may charge while in host mode. Only works
    # if the cable passes ID through; see pcb/README.md.
    res("R3", "124k", "USB_ID", GND, sch=(76.2, 129.54), pcb=(84, 14, 0)),
    cap("C3", "10uF", VBUS, GND, sch=(91.44, 129.54), pcb=(78, 14, 90), fp=FP_C0805),

    # ------------------------------------------------------- 3.3V LDO (XC6206)
    part("U2", "Regulator_Linear:XC6206PxxxMR", "XC6206P332MR",
         "Package_TO_SOT_SMD:SOT-23-3",
         {"1": GND, "2": V3, "3": VBUS}, sch=(119.38, 129.54), pcb=(74, 34, 0),
         lcsc="C5446"),
    cap("C4", "1uF", VBUS, GND, sch=(139.7, 129.54), pcb=(68, 34, 90)),
    cap("C5", "1uF", V3, GND, sch=(152.4, 129.54), pcb=(80, 34, 90)),

    # ------------------------------------------------------------- STM32F103
    part("U3", "MCU_ST_STM32F1:STM32F103C8Tx", "STM32F103C8T6",
         "Package_QFP:LQFP-48_7x7mm_P0.5mm",
         {"1": V3, "24": V3, "36": V3, "48": V3, "9": V3,
          "23": GND, "35": GND, "47": GND, "8": GND,
          "7": "NRST", "44": "BOOT0", "20": "BOOT1",
          "5": "OSC_IN", "6": "OSC_OUT",
          "32": "USB_DM", "33": "USB_DP",
          "34": "SWDIO", "37": "SWCLK",
          "2": "LED",
          "18": "PUMP_CTRL", "19": "LAMP_CTRL"},
         sch=(254, 101.6), pcb=(85, 48, 0), lcsc="C8734"),
    cap("C6", "100nF", V3, GND, sch=(330.2, 45.72), pcb=(81, 41, 0)),
    cap("C7", "100nF", V3, GND, sch=(342.9, 45.72), pcb=(91, 48, 90)),
    cap("C8", "100nF", V3, GND, sch=(355.6, 45.72), pcb=(85, 55, 0)),
    cap("C9", "100nF", V3, GND, sch=(368.3, 45.72), pcb=(79, 48, 90)),
    cap("C10", "100nF", V3, GND, sch=(381, 45.72), pcb=(89, 41, 0)),
    cap("C11", "4.7uF", V3, GND, sch=(393.7, 45.72), pcb=(86, 36, 0), fp=FP_C0805),
    cap("C12", "100nF", "NRST", GND, sch=(330.2, 76.2), pcb=(76, 55, 90)),
    res("R4", "10k", "BOOT0", GND, sch=(342.9, 76.2), pcb=(79, 58, 90)),
    res("R5", "10k", "BOOT1", GND, sch=(355.6, 76.2), pcb=(82, 58, 90)),
    # 1.5k USB D+ pull-up (full-speed device). Blue Pill boards often use 10k.
    res("R6", "1.5k", "USB_DP", V3, sch=(368.3, 76.2), pcb=(92, 22, 90)),

    part("Y1", "Device:Crystal_GND24", "8MHz", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
         {"1": "OSC_IN", "2": GND, "3": "OSC_OUT", "4": GND},
         sch=(342.9, 106.68), pcb=(72, 46, 90)),
    cap("C13", "20pF", "OSC_IN", GND, sch=(330.2, 129.54), pcb=(69, 42, 90)),
    cap("C14", "20pF", "OSC_OUT", GND, sch=(355.6, 129.54), pcb=(69, 50, 90)),

    part("J3", "Connector_Generic:Conn_01x05", "SWD",
         "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
         {"1": V3, "2": "SWDIO", "3": "SWCLK", "4": "NRST", "5": GND},
         sch=(381, 106.68), pcb=(99, 52, 0)),

    res("R7", "1k", V3, "LED_A", sch=(381, 129.54), pcb=(66, 60, 0)),
    part("D4", "Device:LED", "Green", "LED_SMD:LED_0603_1608Metric",
         {"1": "LED", "2": "LED_A"}, sch=(393.7, 129.54), pcb=(66, 64, 0)),

    # ------------------------------------------------------ Pump output (PB0)
    res("R8", "100", "PUMP_CTRL", "PUMP_G", sch=(25.4, 190.5), pcb=(30, 46, 0)),
    res("R9", "10k", "PUMP_G", GND, sch=(38.1, 190.5), pcb=(30, 50, 90)),
    part("Q1", "Transistor_FET:AO3400A", "AO3400A", "Package_TO_SOT_SMD:SOT-23",
         {"1": "PUMP_G", "2": GND, "3": "PUMP_SW"}, sch=(55.88, 190.5),
         pcb=(24, 48, 0), lcsc="C20917"),
    part("D5", "Device:D_Schottky", "SS34", FP_SMA,
         {"1": V12, "2": "PUMP_SW"}, sch=(76.2, 190.5), pcb=(14, 40, 90), lcsc="C8678"),
    part("J4", "Connector:Screw_Terminal_01x02", "Pump",
         "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
         {"1": V12, "2": "PUMP_SW"}, sch=(101.6, 190.5), pcb=(9, 54, 90)),

    # ------------------------------------------------------ Lamp output (PB1)
    res("R10", "100", "LAMP_CTRL", "LAMP_G", sch=(25.4, 241.3), pcb=(46, 46, 0)),
    res("R11", "10k", "LAMP_G", GND, sch=(38.1, 241.3), pcb=(46, 50, 90)),
    part("Q2", "Transistor_FET:AO3400A", "AO3400A", "Package_TO_SOT_SMD:SOT-23",
         {"1": "LAMP_G", "2": GND, "3": "LAMP_SW"}, sch=(55.88, 241.3),
         pcb=(40, 48, 0), lcsc="C20917"),
    part("D6", "Device:D_Schottky", "SS34", FP_SMA,
         {"1": V12, "2": "LAMP_SW"}, sch=(76.2, 241.3), pcb=(34, 58, 0), lcsc="C8678"),
    part("J5", "Connector:Screw_Terminal_01x02", "Lamp booster",
         "TerminalBlock_Phoenix:TerminalBlock_Phoenix_MKDS-1,5-2-5.08_1x02_P5.08mm_Horizontal",
         {"1": V12, "2": "LAMP_SW"}, sch=(101.6, 241.3), pcb=(18, 66, 0)),
]

BOARD_W = 104
BOARD_H = 72
