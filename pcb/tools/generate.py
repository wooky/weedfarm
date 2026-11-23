#!/usr/bin/env python3
"""Generate weedfarm.kicad_sch and weedfarm.kicad_pcb from design.py.

Run with the system python3 (needs KiCad's `pcbnew` module):
    python3 pcb/tools/generate.py
"""
import copy
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from sexpr import Sym, dump, find, find1, parse  # noqa: E402
import design  # noqa: E402

OUT_DIR = os.path.normpath(os.path.join(HERE, "..", "weedfarm"))
NAME = "weedfarm"
SYM_DIR = "/usr/share/kicad/symbols"
FP_DIR = "/usr/share/kicad/footprints"
STUB = 2.54

# Deterministic UUIDs so regenerating gives stable diffs.
_NS = uuid.UUID("6f1c3a52-2f0e-4c1e-9d55-7c8e0b1d2a11")


def uid(*key):
    return str(uuid.uuid5(_NS, "/".join(map(str, key))))


ROOT_UUID = uid("root")

# --------------------------------------------------------------- symbol libs
_libs = {}


def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _libs:
        with open(os.path.join(SYM_DIR, lib + ".kicad_sym")) as f:
            _libs[lib] = {s[1]: s for s in find(parse(f.read()), "symbol")}
    syms = _libs[lib]
    sym = copy.deepcopy(syms[name])
    ext = find1(sym, "extends")
    if ext:
        # Flatten: take the base symbol's graphics/pins, keep derived properties.
        base = lib_symbol(f"{lib}:{ext[1]}")
        props = {p[1]: p for p in find(sym, "property")}
        flat = [Sym("symbol"), name]
        for item in base[2:]:
            if isinstance(item, list) and item and item[0] == "property" and item[1] in props:
                flat.append(props.pop(item[1]))
            elif isinstance(item, list) and item and item[0] == "symbol":
                sub = copy.deepcopy(item)
                sub[1] = name + sub[1][len(ext[1]):]
                flat.append(sub)
            else:
                flat.append(item)
        flat[2:2] = list(props.values())
        sym = flat
    return sym


def embedded(lib_id):
    sym = lib_symbol(lib_id)
    sym[1] = lib_id
    return sym


def symbol_pins(lib_id):
    """Yield (number, x, y, angle) in library coordinates (Y up)."""
    for unit in find(lib_symbol(lib_id), "symbol"):
        for p in find(unit, "pin"):
            at = find1(p, "at")
            yield find1(p, "number")[1], float(at[1]), float(at[2]), int(float(at[3]))


def pin_names(lib_id):
    return {find1(p, "number")[1]: find1(p, "name")[1]
            for unit in find(lib_symbol(lib_id), "symbol") for p in find(unit, "pin")}


# ---------------------------------------------------------------- schematic
def effects(justify=None, hide=False):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), 1.27, 1.27]]]
    if justify:
        e.append([Sym("justify")] + [Sym(j) for j in justify])
    if hide:
        e.append([Sym("hide"), Sym("yes")])
    return e


def rnd(v):
    return round(v, 4)


def build_schematic():
    items = []
    lib_ids = []
    for p in design.PARTS:
        if p["lib_id"] not in lib_ids:
            lib_ids.append(p["lib_id"])

    for p in design.PARTS:
        sx, sy = p["sch"]
        ref, su = p["ref"], uid("sym", p["ref"])
        is_power = p["lib_id"].startswith("power:")
        props = [
            ("Reference", ("#" + ref) if is_power else ref, (sx + 5.08, sy - 6.35), is_power),
            ("Value", p["value"], (sx + 5.08, sy - 3.81), False),
            ("Footprint", p["footprint"], (sx, sy), True),
            ("Datasheet", "", (sx, sy), True),
        ]
        if p["lcsc"]:
            props.append(("LCSC", p["lcsc"], (sx, sy), True))
        sym = [Sym("symbol"), [Sym("lib_id"), p["lib_id"]], [Sym("at"), sx, sy, 0],
               [Sym("unit"), 1], [Sym("exclude_from_sim"), Sym("no")],
               [Sym("in_bom"), Sym("no" if is_power else "yes")],
               [Sym("on_board"), Sym("no" if is_power else "yes")],
               [Sym("dnp"), Sym("no")], [Sym("uuid"), su]]
        for name, val, (px, py), hide in props:
            sym.append([Sym("property"), name, val, [Sym("at"), rnd(px), rnd(py), 0],
                        effects(["left"], hide)])
        seen = {}
        for num, lx, ly, ang in symbol_pins(p["lib_id"]):
            sym.append([Sym("pin"), num, [Sym("uuid"), uid("pin", ref, num)]])
            net = p["pins"].get(num)
            # Schematic coordinates: Y grows downward.
            x, y = sx + lx, sy - ly
            key = (rnd(x), rnd(y))
            if key in seen:
                if seen[key] != net:
                    sys.exit(f"{ref}: stacked pins at {key} disagree ({seen[key]} vs {net})")
                continue
            seen[key] = net
            if net is None:
                items.append([Sym("no_connect"), [Sym("at"), rnd(x), rnd(y)],
                              [Sym("uuid"), uid("nc", ref, num)]])
                continue
            # Stub points away from the body (pin angle points toward it).
            dx, dy = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[ang]
            ex, ey = x + dx * STUB, y + dy * STUB
            items.append([Sym("wire"), [Sym("pts"), [Sym("xy"), rnd(x), rnd(y)],
                                        [Sym("xy"), rnd(ex), rnd(ey)]],
                          [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]],
                          [Sym("uuid"), uid("wire", ref, num)]])
            lang, just = {(-1, 0): (180, ["right", "bottom"]), (1, 0): (0, ["left", "bottom"]),
                          (0, 1): (270, ["right", "bottom"]), (0, -1): (90, ["left", "bottom"])}[(dx, dy)]
            items.append([Sym("label"), net, [Sym("at"), rnd(ex), rnd(ey), lang],
                          effects(just), [Sym("uuid"), uid("label", ref, num)]])
        sym.append([Sym("instances"), [Sym("project"), NAME,
                    [Sym("path"), "/" + ROOT_UUID, [Sym("reference"), ("#" + ref) if is_power else ref],
                     [Sym("unit"), 1]]]])
        items.append(sym)

    sch = [Sym("kicad_sch"), [Sym("version"), 20250114], [Sym("generator"), "weedfarm-generate"],
           [Sym("generator_version"), "1.0"], [Sym("uuid"), ROOT_UUID], [Sym("paper"), "A3"],
           [Sym("title_block"), [Sym("title"), "weedfarm controller (sample)"],
            [Sym("comment"), 1, "Generated by pcb/tools/generate.py - edit design.py, not this file"]],
           [Sym("lib_symbols")] + [embedded(i) for i in lib_ids]]
    sch += items
    sch.append([Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]])
    with open(os.path.join(OUT_DIR, NAME + ".kicad_sch"), "w") as f:
        f.write(dump(sch) + "\n")


# --------------------------------------------------------------------- board
def build_board():
    import pcbnew

    mm = pcbnew.FromMM
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)

    nets = {}

    def net(name, local=True):
        if name not in nets:
            # Local labels give hierarchical names: "/NET".
            n = pcbnew.NETINFO_ITEM(board, "/" + name if local else name)
            board.Add(n)
            nets[name] = n
        return nets[name]

    for p in design.PARTS:
        if not p["pcb"]:
            continue
        lib, name = p["footprint"].split(":")
        fp = pcbnew.FootprintLoad(os.path.join(FP_DIR, lib + ".pretty"), name)
        if fp is None:
            sys.exit(f"{p['ref']}: footprint {p['footprint']} not found")
        fp.SetFPIDAsString(p["footprint"])
        fp.SetReference(p["ref"])
        fp.SetValue(p["value"])
        fp.SetPath(pcbnew.KIID_PATH("/" + uid("sym", p["ref"])))
        fp.SetSheetname("Root")
        fp.SetSheetfile(NAME + ".kicad_sch")
        if p["lcsc"]:
            fp.SetField("LCSC", p["lcsc"])
            fp.GetField("LCSC").SetVisible(False)
        x, y, rot = p["pcb"]
        board.Add(fp)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        fp.SetOrientationDegrees(rot)
        names = pin_names(p["lib_id"])
        for pad in fp.Pads():
            num = pad.GetNumber()
            if num in p["pins"]:
                pad.SetNet(net(p["pins"][num]))
            elif num in names:
                # Match the name eeschema gives a no-connect pin's net.
                label = "-".join(x for x in (p["ref"], names[num], "Pad" + num) if x)
                pad.SetNet(net(f"unconnected-({label})", local=False))

    # Board outline.
    w, h = design.BOARD_W, design.BOARD_H
    corners = [(0, 0), (w, 0), (w, h), (0, h)]
    for (x1, y1), (x2, y2) in zip(corners, corners[1:] + corners[:1]):
        seg = pcbnew.PCB_SHAPE(board)
        seg.SetShape(pcbnew.SHAPE_T_SEGMENT)
        seg.SetLayer(pcbnew.Edge_Cuts)
        seg.SetWidth(mm(0.1))
        seg.SetStart(pcbnew.VECTOR2I(mm(x1), mm(y1)))
        seg.SetEnd(pcbnew.VECTOR2I(mm(x2), mm(y2)))
        board.Add(seg)

    # GND pour on the bottom layer.
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.B_Cu)
    zone.SetNet(net(design.GND))
    zone.SetLocalClearance(mm(0.3))
    zone.SetMinThickness(mm(0.25))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    outline = zone.Outline()
    outline.NewOutline()
    m = 0.5
    for x, y in [(m, m), (w - m, m), (w - m, h - m), (m, h - m)]:
        outline.Append(mm(x), mm(y))
    board.Add(zone)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())

    path = os.path.join(OUT_DIR, NAME + ".kicad_pcb")
    pcbnew.SaveBoard(path, board)


def write_project():
    path = os.path.join(OUT_DIR, NAME + ".kicad_pro")
    if not os.path.exists(path):  # KiCad expands it with defaults on first open.
        with open(path, "w") as f:
            f.write('{"meta": {"filename": "%s.kicad_pro", "version": 3}}\n' % NAME)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    write_project()
    build_schematic()
    build_board()
    print("wrote", OUT_DIR)


if __name__ == "__main__":
    main()
