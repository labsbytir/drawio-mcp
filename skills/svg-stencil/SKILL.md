---
name: svg-stencil
description: Use when converting an SVG icon into a recolorable draw.io custom shape stencil, or fixing a stencil that won't recolor. Covers SVG path to stencil ops, the recolor rule, and validation. For generating diagram files, use the drawio skill in plugins/ instead.
---

# SVG to draw.io Stencil

## 1. Recolor rule (read first)

A stencil that hardcodes `<fillcolor color="#..."/>` / `<strokecolor color="#..."/>`
locks the shape color: the Style panel can no longer recolor it.

- Recolorable stencil: NO `<fillcolor>`/`<strokecolor>` elements. End each
  `<path>` with `<fillstroke/>` and leave colors to the Style panel.
- Fixed-brand stencil: add both elements once at the top of `<background>`.
  Only on explicit request.

## 2. SVG to stencil conversion

Stencil coordinates are absolute in the `viewBox`: top-left `(0,0)`,
bottom-right `(w,h)`. Set `<shape h height w width>` from the viewBox.

| SVG path cmd | Stencil element |
|---|---|
| `M x y` | `<move x y/>` (later pairs in same `M` = implicit lineto) |
| `L x y`, `H x`, `V y` | `<line x y/>` (resolve H/V against current point) |
| `C x1 y1 x2 y2 x y` | `<curve x1 y1 x2 y2 x3 y3/>` (`x3,y3` = endpoint) |
| `S`, `Q`, `T` | reflect previous control point, emit `curve` / `quad` |
| `A rx ry rot laf sf x y` | `<arc rx ry x-axis-rotation large-arc-flag sweep-flag x y/>` |
| `Z` | `<close/>` |
| relative (lowercase) | add current point before emitting |

Arc-flag trap: flags concatenate to the next number (`0 002.526` means
flags `0,0` then `x=2.526`). Split leading `0`/`1` chars before parsing `x,y`.

Template (recolorable):

```xml
<shape name="NAME" h="VH" w="VW" aspect="variable" strokewidth="inherit">
  <connections>
    <constraint x="0.5" y="0"/>
    <constraint x="0.5" y="1"/>
    <constraint x="0" y="0.5"/>
    <constraint x="1" y="0.5"/>
  </connections>
  <background>
    <path>
      <!-- converted ops -->
    </path>
    <fillstroke/>
  </background>
  <foreground>
    <fillstroke/>
  </foreground>
</shape>
```

Insert via `Arrange > Insert > Shape`, paste, Preview. Multi-subpath `d`
(`...Z M...`) maps to multiple `<move>` groups inside one `<path>`.
SVG `evenodd` holes render as filled under draw.io's nonzero rule; for icons
with punch-out holes, ship an SVG-image library entry instead.

Run `python3 scripts/svg_to_stencil.py in.svg --name NAME` (writes
`NAME.xml`, validates XML, warns on arcs/evenodd). Never hand-convert.

## 3. Validation and references

- Stencil must parse as XML; recolor works (no hardcoded colors unless asked).
- Diagram generation rules: `shared/xml-reference.md`, style keys:
  `shared/style-reference.md`, XSD: `shared/mxfile.xsd`.
- Custom shapes tutorial: https://www.drawio.com/docs/tutorials/custom-shapes/
