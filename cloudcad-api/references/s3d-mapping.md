# CloudCAD and S3D

There are two directions. Only one of them has any API support.

| Direction | How |
|---|---|
| **S3D model → drawing** | **No API function exists.** Generate the geometry yourself from the `s3d_model` (procedure below). Both prototypes in this repo do exactly this. |
| **Drawing → S3D model** | The editor does it (its `S3D` button), driven by the root `cad_data.s3d` block below. There's no API call to trigger it; `cloudcad.model.toS3D` and similar return *"could not be found"*. |

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

Worked implementations: `prototypes/truss-designer/server/cadDrawing.js` and
`prototypes/glass-balustrade-configurator/server/cadDrawing.js`.

## Inside the SkyCiv platform

Code running on platform.skyciv.com (S3D Apps, see [`s3d-apps`](../../s3d-apps/SKILL.md)) can open
a drawing directly in CloudCAD with `SKYCIV_UTILS.exportToCad(cad_data)`. There's no API call and
no save step. This isn't available to standalone prototypes.

## The root `s3d` block (CAD → S3D metadata) [export]

Optional. It only matters if the user will press **S3D** in the editor to build a structural
model from the drawing. It's written by the editor, so treat it as descriptive; none of it has
been exercised through the API.

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
| `settings.units` | Units of the generated model |
| `settings.connect_floors_by_columns`, `connect_floors_section_id` | Join the floors (canvases) with columns of that section |
| `settings.structural_defaults` | Default section, material, support fixity and plate thickness for generated members |
| `sections`, `materials` | Keyed by id, in the `s3d_model` section/material shape (see [`s3d-api`](../../s3d-api/SKILL.md)). Exports embed a full library here (≈200 KB), so leave it `{}` unless you need it |
| `elevations` | Maps each canvas index to its storey elevation. Multi-storey models use one canvas per floor |

Exports also carry `roundtrip` (id counters, fingerprints) and a per-canvas `s3d` of UI flags
such as `auto_schedule_table_dismissed`. Both are editor state, so omit them.
