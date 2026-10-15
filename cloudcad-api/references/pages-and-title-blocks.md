# Pages, title blocks and blocks

**Default behaviour:** wrap every generated drawing in the A2 page + title block below, unless the
user asked for bare geometry. It's easy to remove afterwards: delete `pdfExport`,
`blockReferences` and the title-block entry in `block_instances`.

## The default template: `assets/title-block-a2.json`

This is an A2-landscape sheet at **plot scale 1:100** (1 printed mm = 100 canvas mm), derived from
a real platform export. The out-of-page instruction notes the export carried have been removed.
Verified by live render on 2026-09-22. Load it **in code**; it's about 50 KB, so don't paste it
into a prompt.

| Key | Copy to |
|---|---|
| `pdfExport` | `cad_data.pdfExport` |
| `attributeStyles` | `cad_data.attributeStyles` (the 1:100 style, id `as-default`) |
| `blockReferences` | `cad_data.blockReferences` (the title-block definition) |
| `block_instance` | push onto the canvas's `block_instances` |
| `zones` | measured rectangles in canvas mm, at 1:100 (below) |

`scripts/cad_helpers.js` → `wrapInTitleBlock({ canvas })` does all of this. It translates your
true-size content so its bounding box is centred in the safe zone, and **throws if the content
doesn't fit** rather than shrinking it.

### Zones (canvas mm; y more negative = higher on the sheet)

| Zone | minX | maxX | minY | maxY | Notes |
|---|---|---|---|---|---|
| `page_frame` | 67000 | 126400 | -105000 | -63000 | The printed page, 594 × 420 mm × 100 |
| `border` | 68000 | 125400 | -104000 | -64000 | The drawn border line |
| `title_table` | 110400 | 125400 | -74500 | -64000 | Bottom-right info table (top line measured at -74150) |
| `safe_zone` | 69000 | 109400 | -103000 | -65000 | **Default.** Full height, left of the table: 40.4 × 38 m of real space |
| `safe_zone_wide` | 69000 | 124400 | -103000 | -75500 | Full width, above the table: 55.4 × 27.5 m |

The old guidance (safe zone out to `x: 114000`) **overlapped the title table** by 3.6 m at the
bottom right. That was confirmed by rendering it; use the values above.

### Content that's too small or too big

At 1:100 a 7 m truss is small on an A2 sheet. **That is correct and not a bug.** If it needs to
fill more of the sheet, that's a plot-scale choice, never a reason to scale the geometry:

- **Finer scale (e.g. 1:50): `wrapInTitleBlock({ canvas, plotScale: 50 })`** [verified]. It
  multiplies the page frame, the title-block instance (`scale` and its offset from
  `frame.start`) and the zones by `plotScale / 100` about `frame.start`, sets
  `pdfExport.pdfPages[0].scale`, and swaps in `attributeStyle(plotScale)`. The printed sheet
  looks the same while the geometry stays true size. The title block's own text scales with the
  block instance. At 1:50 the default safe zone holds 20.2 × 19 m; at 1:20 it holds 8.1 × 7.6 m.
- **Other ISO A sizes in landscape** (A0–A4) share A2's √2 : 1 aspect ratio. Rescale
  `pdfExport.frame`, the instance `position` offset and `scale` together by the paper ratio.
- **Portrait, or ANSI sizes:** the title block's artwork is fixed geometry, so it can't be
  stretched non-uniformly. These need their own template.

## `pdfExport`

```json
{ "pdfPages": [ { "frame": { "start": { "x": 67000, "y": -105000 }, "end": { "x": 126400, "y": -63000 } },
  "orientation": "landscape", "format": "A2", "printPage": true,
  "offset": { "top": 0, "right": 0, "bottom": 0, "left": 0 }, "scale": 100, "canvasIndex": 0 } ] }
```

| Key | Type | Description |
|---|---|---|
| `frame.start` / `frame.end` | `{x,y}` | The page rectangle in canvas mm. **This is the page**; keep `format`/`orientation` consistent with it |
| `orientation` | `string` | `"landscape"`, `"portrait"` |
| `format` | `string` | Paper label, `"A0"`–`"A4"` |
| `printPage` | `bool` | Include the page in PDF export |
| `offset` | `{top,right,bottom,left}` | Print margins |
| `scale` | `number` | Plot-scale denominator (100 = 1:100); the editor shows `Page 1 · 1:100` |
| `canvasIndex` | `int` | Which `canvases[]` entry the page belongs to |

Frame size = paper mm × scale. For example, A2 landscape at 1:100 is 59400 × 42000. The
`savedSettings` sibling that exports carry is editor dialog state, so omit it.

## Blocks

### Definitions: `cad_data.blockReferences` (top-level, camelCase)

```json
{ "id": "block-1", "name": "Detail A", "basePoint": { "x": 0, "y": 0 },
  "items": [ { "type": "line", "data": { "p1": { "x": 0, "y": 0 }, "p2": { "x": 100, "y": 0 } } } ] }
```

Each item is `{ "type", "data" }`, where `data` is the same object the element would have on a
canvas.

| Item `type` | Renders inside a block |
|---|---|
| `line`, `text`, `table`, `axes`, `dimension`, `radiusDimension` | yes [verified] |
| `arc`, `circle`, `point`, `hatch`, `leaderText`, `multiLeaderText` | yes [in the working title block / exports] |
| `image` | **no** [verified]. Put images on the canvas `images` array |

A per-canvas `"block_references"` (snake_case) array appears in exports as a denormalised copy.
It isn't authoritative, so leave it out.

### Instances: `canvas.block_instances`

![Block placement transform](../assets/images/block-transform.svg)

```json
{ "blockId": "block-1", "position": { "x": 0, "y": 0 }, "rotation": 0, "scale": { "x": 1, "y": 1 } }
```

For each local point in the definition [translate, scale and rotation each verified separately]:

```
dx = local.x - basePoint.x ;  dy = local.y - basePoint.y
world.x = position.x + scale.x * (dx*cos(r) - dy*sin(r))
world.y = position.y + scale.y * (dx*sin(r) + dy*cos(r))
```

- `basePoint` is the local point that lands on `position`. It isn't necessarily a corner.
- `rotation` `r` is in **radians**, and positive turns clockwise on screen (because y points down
  the screen). `rotation: 90` means 90 rad (about 116.6°), not a quarter turn: use `Math.PI / 2`.

## A logo in the title block

The template's logo slot is a `"LOGO PLACEHOLDER"` text item, because images don't render inside
blocks. For a real logo, push an entry onto the canvas's own `images` array whose `x`/`y`
(top-left corner) and `width`/`height` cover the placeholder. The placeholder text sits at about
`(115246, -73535)` inside the `title_table` zone.
