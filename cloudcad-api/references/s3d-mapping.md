# CloudCAD and S3D

There are two directions. Only one of them has any API support.

| Direction | How |
|---|---|
| **S3D model → drawing** | **No API function exists.** Generate the geometry yourself from the `s3d_model` (procedure below). Both prototypes in this repo do exactly this. |
| **Drawing → S3D model** | The editor does it (its `S3D` button), driven by per-element `s3d` data plus the root `cad_data.s3d` block (below). The API can **carry** that data, since it survives `create` + `save`, but it can't trigger the conversion: `cloudcad.model.toS3D` and similar return *"could not be found"*. Opt-in only. |

## Drawing an elevation or plan from an `s3d_model`

1. Choose the view plane. For a planar truss or frame in X–Y, an elevation uses `(x, y)`; a plan
   uses `(x, z)`. For a 3D frame, filter members to one gridline or plane first. Don't draw a
   silhouette of every member.
2. Convert units to **mm** if the model isn't in metric mm (e.g. ft × 304.8). The CAD canvas is
   always mm internally; set `settings.canvasLengthUnits` only for the label unit.
3. **Flip y:** `y_cad = -y_model`. S3D is y-up; CloudCAD is y-negative-up.
4. For each member, add a `lines` entry from `nodes[node_A]` to `nodes[node_B]`.
5. Add dimensions for the governing extents (overall span, height, bay widths), with
   `projectionType` `"horizontal"` / `"vertical"`, plus text for the title or section labels.
6. `wrapInTitleBlock({ canvas })`, which translates everything into the page. Never scale.

```js
const cad = require('./scripts/cad_helpers');
const MM = 304.8; // model in ft
const pt = (n) => ({ x: n.x * MM, y: -n.y * MM });
const canvas = cad.emptyCanvas('Truss Elevation', { drawing_type: 'Elevation' });
for (const m of Object.values(s3d_model.members)) {
  canvas.lines.push({ p1: pt(s3d_model.nodes[m.node_A]), p2: pt(s3d_model.nodes[m.node_B]) });
}
const cad_data = cad.wrapInTitleBlock({ canvas, settings: { canvasLengthUnits: 'ft' } });
```

This gives a plain drawing, which is the default. **Only if the user explicitly asks** for the
structural data to come through, tag each element as well:
`{ p1, p2, s3d: cad.s3dMember({ section: m.section_id }) }`, add
`{ ...pt(node), s3d: cad.s3dSupport(restraint_code) }` to `points` for each support, and pass
`s3d: cad.s3dRoot()` to `wrapInTitleBlock`. See
[Structural data](#structural-s3d-data-opt-in-only).

Worked implementations: `prototypes/truss-designer/server/cadDrawing.js` and
`prototypes/glass-balustrade-configurator/server/cadDrawing.js`.

## Inside the SkyCiv platform

Code running on platform.skyciv.com (S3D Apps, see [`s3d-apps`](../../s3d-apps/SKILL.md)) can open
a drawing directly in CloudCAD with `SKYCIV_UTILS.exportToCad(cad_data)`. There's no API call and
no save step. This isn't available to standalone prototypes.

## Structural (`s3d`) data: opt-in only

**Don't add any `s3d` data unless the user explicitly asks** for a drawing that can become an S3D
model (they might say "structural", "so I can press S3D", "carry the members/supports/plates
through", or "round-trip to S3D"). A plain drawing leaves out the root `s3d` block and every
per-element `s3d`.

When it *is* asked for, it takes **two levels**, and both are needed:

1. **Per-element `s3d`** on each point, line or hatch that is structural. This is what carries
   the data. **A line without `s3d` is only a drawn line.** The converter skips it, even when the
   editor's "Structural" toggle is on, because that toggle only tags lines the user draws in the UI.
2. **Root `cad_data.s3d`** holding the settings. Without `s3d.settings.normal_axis`, the
   editor's CAD → S3D converter throws *"Missing or invalid normal_axis in s3d.settings"*.

Verified live on 2026-09-25: a payload built from the shapes below was sent with
`cloudcad.model.create` + `cloudcad.file.save`, then reopened in the editor. Every per-element
`s3d` survived unchanged, and the editor's converter turned it into 1 member, 2 supports and a
4-node plate. The element shapes are exactly what the editor writes when you use its
right-click *Assign …* actions.

### Per-element shapes

| Element | `s3d` value | Becomes in S3D | Editor action |
|---|---|---|---|
| `lines[]` | `{ "member": MEMBER }` | a member from `p1` to `p2` | Assign Section to Line |
| `lines[]` | `{ "plate": PLATE }` | a wall plate extruded from the line between floors. Nothing on a single canvas | Assign Plate Properties to Line |
| `points[]` | `{ "support": { "restraint_code": "FFFFFF" } }` | a node support | Assign Support Fixity |
| `points[]` | `{ "column": MEMBER }` | a column projected to the next floor (`column_projection_direction`). Nothing on a single canvas | Assign Section to Point |
| `hatches[]` | `PLATE` (flat, **not** wrapped in `{plate: …}`) | a plate over the hatch loop's corner nodes | (hatch properties) |

A point can carry both `support` and `column`. `restraint_code` is the `s3d_model` 6-character
code (`F` fixed, `R` released, order Tx Ty Tz Rx Ry Rz). The editor's full default support object
also has `direction_code: "BBBBBB"`, `tx…rz: 0` and `original_support_id: null`. All of these are
optional.

`MEMBER` (the editor's default: change `section` and the fixities, keep the rest):

```json
{ "section": 1, "type": "normal_continuous", "rotation_angle": 0, "mirror": "no",
  "disable_non_linear_effects": "no", "fixity_A": "FFFFFF", "fixity_B": "FFFFFF",
  "offset_Ax": "0", "offset_Ay": "0", "offset_Az": "0", "offset_Bx": "0", "offset_By": "0", "offset_Bz": "0" }
```

`PLATE` (`thickness` is **mm**, `material_id` is a key of the root `s3d.materials`):

```json
{ "material_id": 1, "thickness": 200, "membrane_thickness": null, "bending_thickness": null,
  "shear_thickness": null, "rotZ": 0, "structure_type": "plate", "type": "auto", "diaphragm": "no",
  "offset": 0, "state": "stress", "drilling_stiffness_factor": 1 }
```

In Node: `cad.s3dMember({ section: 2 })`, `cad.s3dSupport('FFFRRR')`, `cad.s3dColumn()`,
`cad.s3dPlate({ thickness: 150 })` and `cad.s3dRoot()` build these.
`wrapInTitleBlock({ canvas, s3d: cad.s3dRoot() })` passes the root block through. Without the
`s3d` argument it's dropped, which is intended for plain drawings.

**Mapping** (with `normal_axis: "Y"`): canvas `(x, y)` becomes S3D `(x, elevation, z = y)`, in
mm. A canvas point at `y: -4000` becomes `z: -4000`. Because `wrapInTitleBlock` **translates**
the content, the S3D model is built at the translated coordinates. That's harmless for analysis,
but the origin won't be at a support.

**Sections:** `section` is an id. `1` is the editor's built-in *Default Section* placeholder.
Other ids refer to keys of the root `s3d.sections`. The converter only carries the section's id
and `material_id`: it renames the section to `"Section <id>"` and nulls its properties (verified
with a `load_section` entry). So assign the real sections in S3D, or with
[`section-selector`](../../section-selector/SKILL.md) on the resulting `s3d_model`, rather than
relying on the CAD file to carry them.

**Multi-storey** (`column`, `lines[].s3d.plate`, `elevations`): the shapes above are the ones the
editor writes. Projecting them between canvases happens in the editor's S3D button flow, which
hasn't been exercised end to end. A single-canvas conversion ignores them.

### The root `s3d` block

```json
"s3d": {
  "settings": {
    "units": "mm", "tolerance": 0.0001, "normal_axis": "Y", "column_projection_direction": "down",
    "connect_floors_by_columns": false, "connect_floors_section_id": null,
    "remove_duplicate_members": true, "supports_only_base": true, "ignore_unassigned_sections": false,
    "structural_defaults": { "defaultLineSectionId": 1, "defaultColumnSectionId": 1,
      "defaultSupportFixity": "FFFFFF", "defaultPlateMaterialId": 1, "defaultPlateThickness": 200 }
  },
  "sections": { },
  "materials": { },
  "elevations": [ { "canvas_id": 0, "elevation": 0 } ]
}
```

| Key | Meaning |
|---|---|
| `settings.normal_axis` | **Required** (`"X"`/`"Y"`/`"Z"`). This is the S3D axis the drawing plane is normal to. Use `"Y"` for a plan |
| `settings.units` | Units of the generated model |
| `settings.connect_floors_by_columns`, `connect_floors_section_id` | Join the floors (canvases) with columns of that section |
| `settings.structural_defaults` | Default section, material, support fixity and plate thickness the editor applies to *newly drawn* elements. It doesn't fill elements you send without `s3d` |
| `sections`, `materials` | Keyed by id, in the `s3d_model` shape (see [`s3d-api`](../../s3d-api/SKILL.md)). When `materials` is `{}`, the converter supplies its default library (1 = Structural Steel … 4 = Concrete). Exports embed a full section library here (≈200 KB), so leave `sections` as `{}` |
| `elevations` | Maps each canvas index to its storey elevation. Multi-storey models use one canvas per floor |

Exports also carry `roundtrip` (id counters, fingerprints) and a per-canvas `s3d` of UI flags
such as `auto_schedule_table_dismissed`. Both are editor state, so leave them out.
