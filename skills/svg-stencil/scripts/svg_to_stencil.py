#!/usr/bin/env python3
"""SVG icon -> recolorable draw.io custom shape stencil.

Usage: python3 svg_to_stencil.py in.svg --name workers-unbound [--fill-color #0051c3]

Recolorable by default: no <fillcolor>/<strokecolor>, so the Style panel
controls color. Pass --fill-color only for a fixed-brand stencil.
Warns on <arc> usage and evenodd fill rules (holes render filled).
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET


def f(v):
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def parse_d(d):
    toks = re.findall(
        r"[MmLlHhVvCcSsQqTtAaZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?", d
    )
    out = []
    i = 0
    cx = cy = sx = sy = 0.0
    pcx = pcy = pqx = pqy = None
    cmd = None
    nargs = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2}

    def is_cmd(t):
        return len(t) == 1 and t.isalpha()

    def pop_tok():
        nonlocal i
        t = toks[i]
        i += 1
        return t

    while i < len(toks):
        if is_cmd(toks[i]):
            cmd = toks[i]
            i += 1
        if cmd is None:
            i += 1
            continue
        if cmd in ("Z", "z"):
            out.append("      <close/>")
            cx, cy = sx, sy
            pcx = pcy = pqx = pqy = None
            cmd = None
            continue
        rel = cmd.islower()
        C = cmd.upper()
        if C == "A":
            # flags may concatenate to x (e.g. '002.526' -> 0,0,2.526)
            def push(t):
                nonlocal i
                toks.insert(i, t)

            try:
                rx = float(pop_tok())
                ry = float(pop_tok())
                rot = float(pop_tok())
                flags = []
                while len(flags) < 2:
                    t = pop_tok()
                    if t in ("0", "1"):
                        flags.append(int(t))
                    else:
                        k = 0
                        while len(flags) < 2 and k < len(t) and t[k] in "01":
                            flags.append(int(t[k]))
                            k += 1
                        if k == 0:
                            raise ValueError("bad arc flag " + t)
                        if t[k:]:
                            push(t[k:])
                x = float(pop_tok())
                y = float(pop_tok())
                if rel:
                    x += cx
                    y += cy
                out.append(
                    f'<arc rx="{f(rx)}" ry="{f(ry)}"'
                    f' x-axis-rotation="{f(rot)}"'
                    f' large-arc-flag="{flags[0]}" sweep-flag="{flags[1]}"'
                    f' x="{f(x)}" y="{f(y)}"/>'
                )
                cx, cy = x, y
                pcx = pcy = pqx = pqy = None
            except (IndexError, ValueError):
                cmd = None
            continue
        need = nargs[C]
        if i + need > len(toks) or is_cmd(toks[i]):
            cmd = None
            continue
        vals = [float(toks[i + k]) for k in range(need)]
        i += need
        if C == "M":
            x = vals[0] + (cx if rel else 0)
            y = vals[1] + (cy if rel else 0)
            out.append(f'<move x="{f(x)}" y="{f(y)}"/>')
            cx, cy, sx, sy = x, y, x, y
            pcx = pcy = pqx = pqy = None
            cmd = "l" if rel else "L"
        elif C == "L":
            x = vals[0] + (cx if rel else 0)
            y = vals[1] + (cy if rel else 0)
            out.append(f'<line x="{f(x)}" y="{f(y)}"/>')
            cx, cy = x, y
            pcx = pcy = pqx = pqy = None
        elif C == "H":
            x = vals[0] + (cx if rel else 0)
            out.append(f'<line x="{f(x)}" y="{f(cy)}"/>')
            cx = x
            pcx = pcy = pqx = pqy = None
        elif C == "V":
            y = vals[0] + (cy if rel else 0)
            out.append(f'<line x="{f(cx)}" y="{f(y)}"/>')
            cy = y
            pcx = pcy = pqx = pqy = None
        elif C == "C":
            if rel:
                x1, y1 = cx + vals[0], cy + vals[1]
                x2, y2 = cx + vals[2], cy + vals[3]
                x3, y3 = cx + vals[4], cy + vals[5]
            else:
                x1, y1, x2, y2, x3, y3 = vals
            out.append(
                f'<curve x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}"'
                f' x3="{f(x3)}" y3="{f(y3)}"/>'
            )
            pcx, pcy = x2, y2
            pqx = pqy = None
            cx, cy = x3, y3
        elif C == "S":
            if rel:
                x2, y2, x3, y3 = cx + vals[0], cy + vals[1], cx + vals[2], cy + vals[3]
            else:
                x2, y2, x3, y3 = vals
            x1 = 2 * cx - pcx if pcx is not None else cx
            y1 = 2 * cy - pcy if pcy is not None else cy
            out.append(
                f'<curve x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}"'
                f' x3="{f(x3)}" y3="{f(y3)}"/>'
            )
            pcx, pcy = x2, y2
            pqx = pqy = None
            cx, cy = x3, y3
        elif C == "Q":
            if rel:
                x1, y1, x2, y2 = cx + vals[0], cy + vals[1], cx + vals[2], cy + vals[3]
            else:
                x1, y1, x2, y2 = vals
            out.append(f'<quad x1="{f(x1)}" y1="{f(y1)}" x2="{f(x2)}" y2="{f(y2)}"/>')
            pqx, pqy = x1, y1
            pcx = pcy = None
            cx, cy = x2, y2
        elif C == "T":
            if rel:
                x, y = cx + vals[0], cy + vals[1]
            else:
                x, y = vals
            x1 = 2 * cx - pqx if pqx is not None else cx
            y1 = 2 * cy - pqy if pqy is not None else cy
            out.append(f'<quad x1="{f(x1)}" y1="{f(y1)}" x2="{f(x)}" y2="{f(y)}"/>')
            pqx, pqy = x1, y1
            pcx = pcy = None
            cx, cy = x, y
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("svg")
    ap.add_argument("--name", required=True)
    ap.add_argument("--fill-color", default=None)
    ap.add_argument("-o", "--out", default=None)
    a = ap.parse_args()
    svg = open(a.svg).read()
    m = re.search(r'viewBox="([\d.\-+\s]+)"', svg)
    if not m:
        sys.exit("no viewBox found")
    _, _, vw, vh = m.group(1).split()
    ds = re.findall(r'<path[^>]*d="([^"]+)"', svg)
    if not ds:
        sys.exit("no <path d> found")
    if "fill-rule" in svg or "clip-rule" in svg:
        print("warning: fill/clip rule present; holes render filled", file=sys.stderr)
    paths = []
    narcs = 0
    for d in ds:
        els = parse_d(d)
        narcs += sum(1 for e in els if "<arc" in e)
        paths.append("    <path>\n" + "\n".join(els) + "\n    </path>\n    <fillstroke/>")
    if narcs:
        print(f"warning: {narcs} <arc> ops; check Preview", file=sys.stderr)
    color = (
        f"    <fillcolor color=\"{a.fill_color}\"/>\n"
        f"    <strokecolor color=\"{a.fill_color}\"/>\n"
        if a.fill_color
        else ""
    )
    xml = f"""<shape name="{a.name}" h="{vh}" w="{vw}" aspect="variable" strokewidth="inherit">
  <connections>
    <constraint x="0.5" y="0"/>
    <constraint x="0.5" y="1"/>
    <constraint x="0" y="0.5"/>
    <constraint x="1" y="0.5"/>
  </connections>
  <background>
{color}{chr(10).join(paths)}
  </background>
  <foreground>
    <fillstroke/>
  </foreground>
</shape>"""
    ET.fromstring(xml)
    out = a.out or f"{a.name}.xml"
    open(out, "w").write(xml)
    print(f"wrote {out} ({len(xml)} chars, {len(ds)} paths)")


if __name__ == "__main__":
    main()
