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
    # The board is the USB host and the phone is a normal USB device (Android
    # Open Accessory), so the phone charges from VBUS like on any charger.
    # Without BC1.2 CDP signaling, expect only about 500 mA; see pcb/README.md.
    # D3 drops the 5.3V buck output to about 5V on VBUS and stops anything
    # plugged into the port from back-feeding the buck.
    part("D3", "Device:D_Schottky", "SS34", FP_SMA,
         {"1": VBUS, "2": V5}, sch=(25.4, 129.54), pcb=(74, 22, 90), lcsc="C8678"),
    part("J2", "Connector:USB_A", "USB-A (phone, host port)",
         "Connector_USB:USB_A_Molex_67643_Horizontal",
         {"1": VBUS, "2": "USB_DM", "3": "USB_DP", "4": GND, "SH": GND},
         sch=(50.8, 129.54), pcb=(92, 10, 180)),
    cap("C3", "10uF", VBUS, GND, sch=(91.44, 129.54), pcb=(78, 14, 90), fp=FP_C0805),
    # The USB-A symbol's pins are power inputs, so mark the supplies as driven.
    part("FLG2", "power:PWR_FLAG", "PWR_FLAG", "", {"1": VBUS},
         sch=(91.44, 114.3), pcb=None),
    part("FLG3", "power:PWR_FLAG", "PWR_FLAG", "", {"1": V5},
         sch=(104.14, 66.04), pcb=None),
    part("FLG4", "power:PWR_FLAG", "PWR_FLAG", "", {"1": GND},
         sch=(76.2, 55.88), pcb=None),

    # ------------------------------------------------------- 3.3V LDO (XC6206)
    part("U2", "Regulator_Linear:XC6206PxxxMR", "XC6206P332MR",
         "Package_TO_SOT_SMD:SOT-23-3",
         {"1": GND, "2": V3, "3": V5}, sch=(119.38, 129.54), pcb=(74, 34, 0),
         lcsc="C5446"),
    cap("C4", "1uF", V5, GND, sch=(139.7, 129.54), pcb=(68, 34, 90)),
    cap("C5", "1uF", V3, GND, sch=(152.4, 129.54), pcb=(80, 34, 90)),

    # ------------------------------------------------------------- CH32X035
    # USB clock comes from the internal 48MHz HSI: no crystal. In host mode
    # the D+/D- 15k pull-downs are internal (GPIO_Mode_IPD), so none here.
    # The G8U6 package has no NRST or BOOT pin. Program it over the 2-wire
    # SDI debug port (DIO/DCK) with a WCH-LinkE.
    part("U3", "MCU_WCH_RiscV:CH32X035G8U6", "CH32X035G8U6",
         "Package_DFN_QFN:WQFN-28-1EP_4x4mm_P0.4mm_EP2.7x2.7mm",
         {"2": V3, "29": GND,
          "26": "USB_DM", "27": "USB_DP",
          "25": "SWDIO", "24": "SWCLK",
          "21": "UART_TX", "22": "UART_RX",
          "5": "PUMP_CTRL", "6": "LAMP_CTRL", "7": "LED"},
         sch=(254, 101.6), pcb=(85, 48, 0), lcsc="C7437027"),
    cap("C6", "100nF", V3, GND, sch=(330.2, 45.72), pcb=(81, 43, 0)),
    cap("C7", "4.7uF", V3, GND, sch=(342.9, 45.72), pcb=(81, 40, 0), fp=FP_C0805),

    # Debug header: WCH-LinkE SDI plus USART1 (PB10 TX / PB11 RX) for logs,
    # since the USB port is busy talking to the phone.
    part("J3", "Connector_Generic:Conn_01x06", "SDI / UART",
         "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
         {"1": V3, "2": "SWDIO", "3": "SWCLK", "4": "UART_TX", "5": "UART_RX", "6": GND},
         sch=(381, 106.68), pcb=(99, 52, 0)),

    res("R7", "1k", V3, "LED_A", sch=(381, 129.54), pcb=(66, 60, 0)),
    part("D4", "Device:LED", "Green", "LED_SMD:LED_0603_1608Metric",
         {"1": "LED", "2": "LED_A"}, sch=(393.7, 129.54), pcb=(66, 64, 0)),

    # ------------------------------------------------------ Pump output (PA0)
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

    # ------------------------------------------------------ Lamp output (PA1)
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
