# `design_code: "Canadian"` — CSA S16:19 / CSA A23.3:19

Values the `baseplate` skill's shared schema leaves code-specific. Load this once `design_code` is
`Canadian`. Starting template: [`sample-api/canada/input.js`](../sample-api/canada/input.js)
(fixed base, `Mz = 10 kN-m`, square HSS column, `All Sides` anchors, metric).

An unrecognised string in any list below is **not rejected** — the calculator silently substitutes a
default and returns `status: 0`. Copy values exactly, including spaces and case.

## Units

Metric: `mm`, `kN`, `kN-m`, `MPa`.

## Anchor diameters are imperial sizes written in mm

The live docs list `12, 16, 20, 22, 24, 27, 30, 36`. **Those values are silently ignored** — verified
live, `12`, `16`, `20` and `22` all return results identical to `12.7`, the default. The values the
calculator actually recognises are inch rod sizes converted to mm:

| `anchor-prop-diam` | Rod size | Verified live |
|---|---|---|
| `12.7` | 1/2" | yes (sample value) |
| `15.9` | 5/8" | yes |
| `19.1` | 3/4" | yes |
| `22.2` | 7/8" | yes |
| `25.4` | 1" | accepted (reached geometry validation) |

Larger sizes presumably follow the same pattern (`28.6`, `31.8`, `34.9`, `38.1`) but have not been
verified — confirm the capacity changes before relying on one.

## Materials

| Field | Accepted values |
|---|---|
| `steel-column-material` / `steel-baseplate-material` | `230G`, `350G`, `400G`, `260W`, `300W`, `350W`, `380W`, `400W`, `480W`, `550W`, `260WT`, `300WT`, `350WT`, `380WT`, `400WT`, `480WT`, `550WT`, `350R`, `350A`, `400A`, `480A`, `550A`, `350AT`, `400AT`, `480AT`, `550AT`, `700Q`, `700QT`, `Custom` |
| `steel-foundation-material` | `20.68`, `27.68`, `31.03`, `34.47`, `41.36`, `Custom` (MPa) |
| `welds-column-mat` | `E43XX`, `E49XX(-X)`, `E55XX-X`, `E62XX-X`, `E69XX-X`, `E76XX-X`, `E83XX-X`, `Custom` |
| `anchor-prop-material` | `ASTM F1554 G36`, `ASTM F1554 G55`, `ASTM F1554 G105`, `ASTM A193`, `Custom` |
| `anchor-prop-ending` | `straight`, `rectangle`, `circular`, `hook` |

## Extra `steel_parts.data` keys in the sample

`grout-material-selected` (`less-than-30` / `greater-than-30`), `steel-grouting-material` (grout
grade, `20.68` in the sample), `steel-column-height` (`0`) and `steel-column-rot` (`0`, column
rotation — undocumented; leave at `0` since only concentric layouts are supported).

## `factors` (resistance φ)

| Key | Default | Reference |
|---|---|---|
| `concrete_factor` | `0.65` | CSA A23.3:19 |
| `steel_factor` | `0.90` | CSA S16:19 |
| `steel_ultimate_factor` | `0.75` | CSA S16:19 |
| `weld_factor` | `0.67` | CSA S16:19 |
| `anchor_rod_factor` | `0.85` | CSA A23.3:19 |
| `anchor_rod_s16_factor` | `0.67` | CSA S16:19 |
| `concrete_normal_weight_factor` | `1` | CSA A23.3:19 (λ) |
| `anchors_in_tension_factor` | `0.8` | CSA A23.3:19 — follows `r_factor_steel` unless that is `custom` |
| `anchors_in_shear_factor` | `0.75` | CSA A23.3:19 — same |
| `anchors_in_concrete_failures_factor_tension` / `_shear` | `1` | CSA A23.3:19 — follows `r_factor_concrete` unless that is `custom` |
| `r_factor_steel` | `"ductile"` | `ductile`, `brittle`, `custom` |
| `r_factor_concrete` | `"condition_b"` | `condition_a`, `condition_b`, `custom` |

## Code-specific settings

`design_settings.distribute_shear_to_all`, `simplified_approach_shear` (CSA A23.3 method ignoring
grout-pad thickness, plus a shear-strength reduction), `consider_both_directions` and
`include_embedded_head_radius` all apply here.
