---
name: baseplate
description: "Use when designing or checking a steel column base plate connection through the SkyCiv API — base plate thickness and bearing, anchor bolts / anchor rods / holding-down bolts (tension, shear, pullout, concrete breakout, pryout, side-face blowout), column-to-plate welds, and the supporting concrete footing or pedestal. Covers the standalone.baseplate.start and standalone.baseplate.check calls, the full design_obj input (units_data, steel_parts, anchors, welds, loads, factors, detailing, design_settings) and how to read the per-check demand/capacity/ratio response, for AISC 360 / ACI 318 (American), AS 4100 / AS 3600 / AS 5216 (Australian), CSA S16 / A23.3 (Canadian) and EN 1993-1-8 / EN 1992-4 (Europe). Trigger even without the word SkyCiv, e.g. 'size a base plate for this column', 'check my anchor bolts', 'column footing connection', 'feed these support reactions into a base plate check'. Not for general member design (use run-quick-design) or for solving the frame itself (use s3d-api)."
---

# Base Plate Design

Design and check a steel column base plate connection — base plate, anchor bolts, welds and the
concrete below — with the SkyCiv `standalone.baseplate` API.

> **Prerequisite:** open the session with **`standalone.baseplate.start`**, not `S3D.session.start`
> (verified: a check after `S3D.session.start` returns *"Session has not been started. Please call
> standalone.baseplate.start first."*). Auth, `options` and the `{ auth, options, functions }` envelope
> are in [`skyciv-api-v3`](../skyciv-api-v3/SKILL.md).

Only **concentric** column / plate / foundation layouts with **symmetric** anchors are supported.

## Workflow

1. Choose `design_code` and **load its reference file** — it holds every accepted material, grade,
   diameter, electrode and the `factors` block for that code:
   [`American`](references/american.md) · [`Australian`](references/australian.md) ·
   [`Canadian`](references/canadian.md) · [`Europe`](references/europe.md).
2. Start from that code's `sample-api/<country>/input.js` (see Worked examples) and change only
   what you need. Every key must be present, even unused ones.
3. Send `standalone.baseplate.start` then `standalone.baseplate.check` in one request. `design_obj`
   **is** the `arguments` object — not nested under another key.
4. Check `response.status`. On `1`, read `errors` / `warnings` / `conflicts` (below) and fix the input.
5. Scan every check for its `ratio` (see Reading the response).

```json
"functions": [
  { "function": "standalone.baseplate.start", "arguments": { "keep_open": true } },
  { "function": "standalone.baseplate.check", "arguments": { "design_code": "American", "...": "..." } }
]
```

Several checks can follow one `start` in a request (verified; top-level `response` is the last).
Each check takes **about 11–20 s** and uses one API credit.

## Gotchas

- **Invalid strings are silently replaced, not rejected.** An unknown material, concrete grade or
  anchor diameter returns `status: 0` with results computed on a default value (verified for column,
  base plate, anchor and concrete grades, and Canadian diameters). Copy values exactly from the
  reference file, and confirm the relevant capacity moved when you change one.
- **Canadian anchor diameters are imperial sizes in mm** (`12.7`, `15.9`, `19.1`, `22.2` …). The
  `12, 16, 20…` list in the live docs is silently ignored — see [`canadian.md`](references/canadian.md).
- **A failing `detailing` check hangs the call instead of erroring.** Verified with `embed_plate`
  (embedded plate side < 4 × anchor diameter): no `conflicts` are returned — the call runs until the
  server timeout (~45 s) and returns *"standalone.baseplate.check timed out"*. `options.timeout` does
  not extend it. Treat any timeout as an input problem: check the detailing rules below against your
  geometry before retrying.
- **`My` must be `"0"`.** It is reserved for future weak-axis support; any non-zero value (`"1"`,
  `"10"`) hangs the call until timeout.
- **A `fixed` base needs a non-zero `Mz` in every load case.** Otherwise `status: 1` with the
  conflict *"configured as a fixed support, but the load combination does not include a moment"*.
  Axial-only or axial + shear cases go on a `pinned` base.
- **A wrong section name fails fast with an unhelpful message** — *"could not be completed for an
  unknown reason"* in ~5 s. `steel-column-database` is the **third** level of the section library
  path and `steel-column-profile` the fourth (e.g. `American › AISC › Pipes › Pipe6STD` →
  `"Pipes"`, `"Pipe6STD"`). Resolve both with [`section-selector`](../section-selector/SKILL.md).
- **`status: 0` does not mean the design passes** — a run returned a breakout `ratio: 1.248` with
  `status: 0`. Derive pass/fail from the ratios.
- **`capacity: 0` with `ratio: 0` means "not evaluated"**, not a pass with infinite margin — e.g.
  `Weld Capacity` on an axial-only pinned base, `Side-Face Blowout (Y-Direction)` when no anchor is
  near that edge. Report these as N/A.
- **`Concrete Bearing Capacity` sits at `ratio: 1` for American/Canadian fixed bases under large
  moment.** Ratio 1 = demand equals capacity (limit reached). This method takes bearing stress at its
  limit and solves for the bearing length, so the ratio stayed `1.000` when the plate grew 400 → 500 mm
  and the footing 450 → 900 mm. Report it as at-limit, but size the connection on the other checks —
  enlarging the plate won't move it. Small eccentricity (`Nx = 200`, `Mz = 2`) gave `0.102`.
- **Load values are strings** (`"Mz": "10"`) in every sample; keep them strings.
- **Report URLs are temporary** (`solver.skyciv.com/temp/...`).
- **Strip `screenshot` before logging a failure** — `status: 1` responses carry a 60–200 KB base64
  PNG of the calculator UI. Decode it only when diagnosing.

## `design_obj` — top level

| Key | Type | Description |
|---|---|---|
| `design_code` | `string` | `American`, `Australian`, `Canadian` or `Europe` (not `European`). |
| `support_type` | `string` | `fixed` (needs `Mz ≠ 0` in every case) or `pinned`. |
| `units_data` | `object` | Unit system — see below. |
| `project_details` | `object` | `project_units` (`metric`/`imperial`) plus optional strings `company`, `designer`, `project_name`, `project_id`, `project_notes`, `client` (`""` if unused). |
| `steel_parts` | `object` | `{ data: {...} }` — column, base plate, foundation. |
| `anchors` | `object` | `{ data: {...} }` — anchor layout, size, material, end type. |
| `welds` | `object` | `{ data: {...} }` — column-to-plate welds. |
| `loads` | `array` | Load cases — see below. |
| `factors` | `object` | Resistance / partial factors. **Keys differ per code** — copy the block from the code's reference file. |
| `detailing` | `object` | Detailing check flags — see below. |
| `design_settings` | `object` | Method options — see below. |
| `version` | `integer` | `2`. |

## Units

`units_data.units` (`metric` / `imperial`) and `project_details.project_units` control the unit
system. **Imperial is American-only**; the other three codes are metric.

| Key | Metric | Imperial |
|---|---|---|
| `units` | `metric` | `imperial` |
| `units_length` | `mm` | `in` |
| `axial_f_units` (axial and shear) | `kN` | `kips` |
| `bending_f_units` | `kN-m` | `kip-ft` |
| `units_strength` (concrete) | `MPa` | `psi` |
| `units_strength_steel` | `MPa` | `ksi` |

All request values and all response `demand`/`capacity` values use these units. Copy the remaining
`units_data` keys (`first_init`, `length_factor`, `strength_factor`, `strength_factor_steel`, `to_mm`,
`to_in`, `kNm_Kipft`, `kN_Kip`) from the sample unchanged — verified to have no effect on results in
either unit system (the American sample's `length_factor: 25.4` is harmless).

## `steel_parts.data`

| Key | Type | Description |
|---|---|---|
| `steel-column-shape` | `string` | `i-shape`, `rectangular` or `pipe`. Sets the allowed `anchor-pattern`s. |
| `steel-column-database` / `steel-column-profile` | `string` | Section library level 3 / level 4 names (see Gotchas). |
| `steel-column-material` | `string` | Column grade — per-code list. |
| `steel-baseplate-width` / `-height` / `-thickness` | `number` | Plate size (length units). |
| `steel-baseplate-material` | `string` | Plate grade — per-code list (differs from the column list). |
| `steel-baseplate-grouting-thickness` | `number` | Grout pad thickness. |
| `steel-foundation-width` / `-height` / `-thickness` | `number` | Concrete pedestal / footing size. |
| `steel-foundation-material` | `string` | Concrete grade — per-code list. |
| `use-cracked-concrete` | `boolean` | Assume cracked concrete. |
| `custom-column-fy`, `-fu`, `custom-bp-fy`, `-fu`, `custom-conc-fc` | `number` | Always present; read only for a `Custom` material. |

Code-only keys (`steel-column-height`, `grout-material-selected`, `steel-grouting-material`,
`steel-column-rot`) are listed in the Canadian and Europe reference files.

## `anchors.data`

| Key | Type | Description |
|---|---|---|
| `anchor-pattern` | `string` | See pattern table below. |
| `anchor-prop-diam` | `string` | Diameter — per-code list (`"12"`, `"M12"`, `"1/2"`, `"12.7"` …). |
| `anchor-prop-material` | `string` | Anchor grade — per-code list. |
| `anchor-prop-length` | `number` | Embedment length. Must fit inside `steel-foundation-thickness` (else a conflict). |
| `anchor-prop-ending` | `string` | `straight`, `rectangle`, `circular`, `hook` (`hook` American/Canadian only). |
| `anchor-prop-side-dim` / `anchor-prop-thk-dim` | `number` | Embedded plate side (or diameter) and thickness — `rectangle`/`circular` ends. Side ≥ 4 × diameter or the call hangs. Plates must not overlap at the chosen spacing. |
| `hook-direction` / `anchor-prop-hook-length` | `string` / `number` | `hook` end only. |
| `anchor-numbers` | `number` | Anchors per side for the pattern. |
| `anchor-numbers-z` / `-y` | `number` | Anchor count per direction (`All Sides`-type patterns). |
| `anchor-spacing-z` / `-y` | `number` | Anchor spacing per direction. |
| `anchor-edge-distance-z` / `-y` | `number` | Anchor to plate edge. |
| `line-anchor-edge-distance-z` / `-y` | `number` | Edge distance for line anchors. |
| `anchor-thread-included` | `string` | `included` in every sample. |
| `anchor-web-bending` | `string` | `web-bending` or `flange-bending` (I-sections; not used by Europe). |
| `use-welded-plate-washers` / `anchor-plate-washer-thickness` | `boolean` / `number` | Not used by Europe. |
| `anchor-hole-clearance` | `string` | Europe only. |
| `custom-anchor-fy` / `-fu` | `number` | Always present; read only for a `Custom` material. |

| `steel-column-shape` | Allowed `anchor-pattern` |
|---|---|
| `i-shape` | `Four Corners`, `Flange Only`, `Web Only` |
| `rectangular` | `Four Corners`, `Top/Bottom Only`, `Left/Right Only`, `All Sides` |
| `pipe` | `Four Corners` |

For a fixed base the anchors must sit in the tension zone — `Web Only` under moment returns a
conflict.

## `welds.data`

| Key | Type | Description |
|---|---|---|
| `weld-type` | `string` | `fillet` or `cjp`. |
| `welds-column-mat` | `string` | Electrode — per-code list. `Custom` uses `custom-weld-fexx`. |
| `box-weld-size` | `number` | Weld size for `pipe` / `rectangular` columns. |
| `input_table_col_weld_size` | `array` | I-sections: rows `[rowId, element, side, size]`, e.g. `[[1,"Top Flange","Both",9],[2,"Bottom Flange","Both",9],[3,"Web","Both",9]]`. Use one size for all three rows. `[]` for other shapes. |
| `use_welds_for_comp` | `string` | `"true"` / `"false"` (a string) — compression through the welds instead of direct bearing. |
| `weld-setback` | `number` | Setback near I-section fillet radii. |
| `as-weld-category` | `string` | Australian only. |

## `loads`

An array of load cases. Give **factored** (ULS / LRFD) combinations — the factors in `factors` are
resistance factors only.

| Key | Type | Description |
|---|---|---|
| `lc` | `string` | Case label. Each check's `lc_number` is the 1-based **position** in this array of its governing case, not the label (verified). |
| `Nx` | `string` | Axial — **positive = compression**, negative = tension. Force units. |
| `Mz` | `string` | Strong-axis moment. Moment units. Required non-zero for `fixed`. |
| `My` | `string` | Always `"0"` (see Gotchas). |
| `Vy` | `string` | Strong-axis shear. Force units. |
| `Vz` | `string` | Weak-axis shear. Force units. |
| `moment_label` | `string` | `""` — auto-determined. |

## `detailing` and `design_settings`

`detailing` flags (`true` enables the check; a **failed** enabled check hangs the call):

| Key | Check |
|---|---|
| `weld_size` | Weld size within code min/max. |
| `anchor_clearance` | Room for washers / nut tightening near welds and the column. |
| `bp_edge_distance` | Minimum anchor-to-plate-edge distance. |
| `embed_plate` | Embedded plate side ≥ 4 × anchor diameter (`rectangle`/`circular`). |
| `concrete_splitting` | Minimum spacing / cover against splitting (not applied for Australian). |
| `min_anchors` | At least 4 anchors. |

`design_settings` change the method — **only change them with review by a suitably qualified
engineer**; keep the sample values otherwise. Which ones apply to which code is in the reference files.

| Key | Effect |
|---|---|
| `neglect_concrete_breakout_for_tension` / `_shear` | Skip breakout — only if separately-checked reinforcement carries the load. |
| `neglect_concrete_pryout` | Skip pryout (slender anchors, h_ef > 12d). |
| `distribute_shear_to_all` | `false` = only edge anchors take shear (conservative). |
| `simplified_approach_shear`, `consider_both_directions`, `include_embedded_head_radius`, `use_sci_for_welds` | Code-specific method switches — see the reference file. |

## Reading the response

`response.data` holds one key per applicable check, e.g.
`"Concrete Breakout Capacity (Tension Load)": { "demand": 27.511, "capacity": 33.143, "ratio": 0.83, "units_on_UI": "force", "lc_number": 1 }`,
plus the non-check keys `version`, `file_name`, `reports` (`html_view_link`, `html_download_link`,
`pdf_download_link`) and, for Europe, `rotational_stiffness`.

There is **no pass/fail or governing-ratio field**, and the set of check keys depends on code,
support type and which load components are non-zero (shear adds five shear checks, tension adds
the anchor checks). Never look up a fixed key name — scan:

```js
const data = res.response.data;
const checks = Object.entries(data)
  .filter(([, v]) => v && typeof v === 'object' && typeof v.ratio === 'number')
  .map(([name, v]) => ({ name, ...v, evaluated: v.capacity !== 0 }));
const evaluated = checks.filter(c => c.evaluated);
const governing = evaluated.reduce((a, c) => (!a || c.ratio > a.ratio ? c : a), null);
const passes = evaluated.every(c => c.ratio <= 1);
```

`units_on_UI` is the *kind* of quantity (`force`, `stress`, `length`, `moment`,
`force_per_unit_length`, …, `""` = unitless) in your units — it varies per code for the same check.

On `status: 1` the reason is in arrays next to `msg` (HTML strings — strip tags before showing):

| Field | Seen for |
|---|---|
| `conflicts` | Fixed base without `Mz`; no anchors in the tension zone; embedded plates overlapping; anchor longer than the foundation; welds overlapping. |
| `errors` / `warnings` | Empty in every failure observed so far — still read them. |
| *(all empty)* | Bad section name ("unknown reason") or a timeout — see Gotchas. |

## Minimal working example

Verified live: American, metric, pinned pipe column, 100 kN compression (governing ratio 0.17).

```json
{
  "design_code": "American",
  "support_type": "pinned",
  "units_data": {
    "first_init": true, "units": "metric", "units_length": "mm", "axial_f_units": "kN",
    "units_strength": "MPa", "units_strength_steel": "MPa", "bending_f_units": "kN-m",
    "length_factor": 1, "strength_factor": 0.00689476, "strength_factor_steel": 6.89476,
    "to_mm": 1, "to_in": 1, "kNm_Kipft": 1, "kN_Kip": 1
  },
  "project_details": { "project_units": "metric", "company": "", "designer": "", "project_name": "", "project_id": "", "project_notes": "", "client": "" },
  "steel_parts": { "data": {
    "custom-column-fy": 240, "custom-column-fu": 400, "custom-bp-fy": 240, "custom-bp-fu": 400,
    "custom-conc-fc": 20, "use-cracked-concrete": true,
    "steel-column-shape": "pipe", "steel-column-database": "Pipes", "steel-column-profile": "Pipe6STD",
    "steel-column-material": "A53 grB",
    "steel-baseplate-width": 300, "steel-baseplate-height": 300, "steel-baseplate-thickness": 20,
    "steel-baseplate-material": "A36", "steel-baseplate-grouting-thickness": 0,
    "steel-foundation-material": "20.68", "steel-foundation-width": 450, "steel-foundation-height": 450, "steel-foundation-thickness": 380
  } },
  "anchors": { "data": {
    "custom-anchor-fy": 240, "custom-anchor-fu": 400,
    "anchor-pattern": "Four Corners", "anchor-prop-diam": "16", "anchor-prop-material": "F1554 Gr.36",
    "anchor-thread-included": "included", "anchor-web-bending": "web-bending",
    "use-welded-plate-washers": false, "anchor-plate-washer-thickness": 0,
    "anchor-prop-length": 250, "anchor-prop-ending": "straight",
    "anchor-numbers": 1, "anchor-numbers-z": 2, "anchor-numbers-y": 2,
    "anchor-spacing-z": 200, "anchor-spacing-y": 200,
    "anchor-edge-distance-z": 50, "anchor-edge-distance-y": 50,
    "line-anchor-edge-distance-z": 50, "line-anchor-edge-distance-y": 50
  } },
  "welds": { "data": {
    "box-weld-size": 8, "input_table_col_weld_size": [], "custom-weld-fexx": 482,
    "use_welds_for_comp": "false", "weld-type": "fillet", "weld-setback": 0, "welds-column-mat": "E70xx"
  } },
  "loads": [ { "lc": "1", "Mz": "0", "My": "0", "Nx": "100", "Vz": "0", "Vy": "0", "moment_label": "" } ],
  "factors": {
    "concrete_bearing_factor": 0.65, "steel_bearing_factor": 0.75, "steel_flexure_factor": 0.9,
    "weld_factor": 0.75, "steel_tension_factor": 0.9, "steel_shear_rupture_factor": 0.75,
    "anchor_tension_factor": 0.75, "anchor_shear_factor": 0.65, "anchor_bolts_factor": 0.75,
    "concrete_tension_factor": 0.7, "concrete_shear_factor": 0.65, "concrete_normal_weight_factor": 1
  },
  "detailing": { "weld_size": true, "anchor_clearance": true, "bp_edge_distance": true, "embed_plate": true, "concrete_splitting": true, "min_anchors": true },
  "design_settings": {
    "neglect_concrete_breakout_for_tension": false, "neglect_concrete_breakout_for_shear": false,
    "neglect_concrete_pryout": true, "distribute_shear_to_all": true, "simplified_approach_shear": true,
    "consider_both_directions": false, "include_embedded_head_radius": false, "use_sci_for_welds": false
  },
  "version": 2
}
```

## Feeding S3D results into a base plate check

1. Solve the frame in [`s3d-api`](../s3d-api/SKILL.md) (its own `S3D.session.start` session — a
   separate request from the base plate one). Don't use `result_filter` to fetch reactions; read
   them from the full results as described in [`analysis-results`](../analysis-results/SKILL.md).
2. For each **factored** load combination, take the column's member forces at its base station
   (local axes; `bending_moment_z` = strong axis) and write one `loads` entry: `Nx` ← axial, `Mz` ← strong-axis moment,
   `Vy` ← `shear_force_y`, `Vz` ← `shear_force_z`, `My` ← `"0"`. Convert to the base plate's units.
3. **Confirm the sign before trusting it**: `Nx` is positive for compression here, and the S3D sign
   convention is not documented in these skills. Run one gravity-only combination — the column must
   come out with `Nx > 0`. If it doesn't, negate axial for every case.
4. `My` is unsupported — flag a significant weak-axis moment to the user rather than dropping it.
   A `fixed` base needs `Mz ≠ 0` in every case; never invent a nominal moment to get past that.
5. Use [`section-selector`](../section-selector/SKILL.md) to get the column's database/profile names,
   and hand the finished results to [`qa-engineer`](../qa-engineer/SKILL.md) for review.

## Worked examples

Verified request/response pairs (re-run live 2026-09-22, results unchanged):

| Code | Support | Load | Files |
|---|---|---|---|
| American | fixed | `Mz = 10 kN-m` — full tension-side check set | [`input.js`](sample-api/america/input.js), [`response.json`](sample-api/america/response.json) |
| Australian | pinned | `Nx = 100 kN` — compression-only set | [`input.js`](sample-api/australia/input.js), [`response.json`](sample-api/australia/response.json) |
| Canadian | fixed | `Mz = 10 kN-m` — full tension-side check set | [`input.js`](sample-api/canada/input.js), [`response.json`](sample-api/canada/response.json) |
| Europe | pinned | `Nx = 100 kN` — compression set + `rotational_stiffness` | [`input.js`](sample-api/europe/input.js), [`response.json`](sample-api/europe/response.json) |

Copy the `design_obj` literal from each `input.js`. The American and Canadian samples have breakout
ratios of 0.83 / 0.976 — little margin if you only raise the loads.
