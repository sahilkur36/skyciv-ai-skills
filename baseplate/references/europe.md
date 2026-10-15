# `design_code: "Europe"` — EN 1993-1-8:2005 / EN 1992-1-1:2004 / EN 1992-4:2018

Values the `baseplate` skill's shared schema leaves code-specific. Load this once `design_code` is
`Europe` (not `European` — the value is `Europe`). Starting template:
[`sample-api/europe/input.js`](../sample-api/europe/input.js) (pinned base, `Nx = 100 kN`, HE 200 B
column, metric).

An unrecognised string in any list below is **not rejected** — the calculator silently substitutes a
default and returns `status: 0`. Copy values exactly, including spaces and case.

## Units

Metric: `mm`, `kN`, `kN-m`, `MPa`.

## Sections

Both the `European` and `British` section-library databases are usable, e.g.
`steel-column-database: "Wide flange HE HL beams"`, `steel-column-profile: "HE 200 B"`.

## Materials

| Field | Accepted values |
|---|---|
| `steel-column-material` / `steel-baseplate-material` | `S235`, `S275`, `S355`, `S460`, `S275N`, `S355N`, `S420N`, `S460N`, `S275M`, `S355M`, `S420M`, `S460M`, `Custom` |
| `steel-foundation-material` | `C12/15`, `C16/20`, `C20/25`, `C25/30`, `C30/37`, `C35/45`, `C40/50`, `C45/55`, `C50/60`, `C60/75`, `C70/85`, `C80/95`, `C90/105`, `Custom` |
| `welds-column-mat` | `E35`, `E38`, `E42`, `E46`, `E50`, `Custom` |

## Anchors

| Field | Accepted values |
|---|---|
| `anchor-prop-diam` | `M6`, `M8`, `M10`, `M12`, `M16`, `M20`, `M24`, `M27`, `M30`, `M36`, `M39`, `M42`, `M45`, `M52` |
| `anchor-prop-material` | `4.6`, `4.8`, `5.6`, `6.8`, `8.8`, `10.8`, `12.9`, `Custom` |
| `anchor-prop-ending` | `straight`, `rectangle`, `circular` — **no `hook`** |
| `anchor-hole-clearance` | `no-clearance`, `compliant`, `large` (Europe only) |

`anchor-web-bending`, `use-welded-plate-washers` and `anchor-plate-washer-thickness` are not used
for this code (the sample omits the washer keys).

## Extra `steel_parts.data` keys

`steel-column-height` (used only in this workflow — for the rotational-stiffness `EI/L` bounds) and
`grout-material-selected` (`less-than-30` / `greater-than-30`).

## `factors` (partial factors γ — these divide, unlike the φ factors of the other codes)

| Key | Default | Reference |
|---|---|---|
| `concrete_factor` | `1.5` | EN 1992-1-1 Table 2.1N — changes with `design_situation` |
| `bending_factor` | `1.0` | EN 1993-1-8 Table 2.1 |
| `anchor_shear_factor` | `1.5` | EN 1992-4 Table 4.1 |
| `weld_factor` | `1.25` | EN 1993-1-8 Table 2.1 |
| `custom_lever_arm` | `0` | EN 1992-4 Cl. 6.2.2.3(3) — `0` = auto-calculate |
| `concrete_alpha_factor` | `1.5` | SCI P358 p.241 |
| `concrete_beta_factor` | `0.66667` | EN 1993-1-8 Cl. 6.2.5(7) |
| `concrete_alpha_cc_factor` | `1.0` | EN 1992-1-1 Cl. 3.1.6 |
| `concrete_theta_factor` | `90` | user assumption, max 180° |
| `exposure_class` | `"xc4"` | `x0`, `xc1`, `xc2_xc3`, `xc4`, `xd1_xs1`, `xd2_xs2`, `xd3_xs3` |
| `structural_class` | `"s4"` | `s1` … `s6` |
| `countersunk` | `"no"` | `yes` / `no` |
| `cut_threads` | `"no"` | EN 1090 compliance, `yes` / `no` |
| `k7_factor` | `"ductile"` | `ductile` / `non-ductile` |
| `k8_factor` | `2` | EN 1992-4 Cl. 7.2.2.4(2) — pryout |
| `restraint_factor` | `"no-restraint"` | `no-restraint` / `full-restraint` |
| `design_situation` | `"permanent"` | `permanent` / `accidental` |
| `elastic_modulus_steel` | `210000` | MPa |
| `elastic_modulus_concrete` | `33000` | MPa |
| `rotational_stiffness_lower` / `_upper` | `2` / `30` | multipliers on `EI/L` |

## Code-specific response shape

- Bearing and plate yield are combined into one key: `Concrete Bearing Capacity and Base Plate Yield
  Capacity (Compression Load)` (`units_on_UI: "force"`). `Weld Capacity` reports `units_on_UI: "stress"`.
- The response adds a non-check key, `rotational_stiffness: { stiffness_array, upper_bound_array,
  lower_bound_array, remarks_array }` — one entry per load case. Every case tested returned `"N/A"`,
  including a fixed base under moment (`steel-column-height: 0`); treat it as optional output. Skip it
  when scanning for ratios.
- Concrete bearing is **not** pinned at `ratio: 1` here, unlike the American and Canadian moment
  method — a fixed base with `Nx = 50`, `Mz = 10` returned `0.167`.
- `design_settings.use_sci_for_welds`: `true` = SCI P398 approach for moment-loaded welds, `false` =
  EN 1993 approach.
- A fixed base under moment needs anchors in the tension zone — the `Web Only` pattern from the
  sample returns a `conflicts` entry ("no anchors are configured to resist the tension load") as soon
  as `Mz` is applied. `Flange Only` (verified live) puts anchors in the tension zone.
