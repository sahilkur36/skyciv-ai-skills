# `design_code: "American"` — AISC 360-22 / ACI 318-19

Values the `baseplate` skill's shared schema leaves code-specific. Load this once `design_code` is
`American`. Starting template: [`sample-api/america/input.js`](../sample-api/america/input.js)
(fixed base, `Mz = 10 kN-m`, metric).

An unrecognised string in any list below is **not rejected** — the calculator silently substitutes a
default and returns `status: 0`. Copy values exactly, including spaces and case.

## Units

Metric or imperial are both supported (verified live). Imperial: set `units: "imperial"`,
`units_length: "in"`, `axial_f_units: "kips"`, `units_strength: "psi"`, `units_strength_steel: "ksi"`,
`bending_f_units: "kip-ft"`, `project_details.project_units: "imperial"`, and give every length in
inches, loads in kips / kip-ft. The conversion-factor keys can stay as in the sample.

## Materials

| Field | Accepted values |
|---|---|
| `steel-column-material` | `A36`, `A53 grB`, `A500 grB`, `A500 grC`, `A501 grA`, `A501 grB`, `A529 gr50`, `A529 gr55`, `A709 gr36`, `A709 gr50`, `A709 gr50S`, `A709 gr50W`, `A1043 gr36`, `A1043 gr50`, `A1085 grA`, `A572 gr42`, `A572 gr50`, `A572 gr55`, `A572 gr60`, `A572 gr65`, `A618 grI`, `A618 grII`, `A618 grIII`, `A913 gr50`, `A913 gr60`, `A913 gr65`, `A913 gr70`, `A992`, `A1065 gr50`, `A1065 gr50W`, `A242 gr42`, `A242 gr46`, `A242 gr50`, `A588`, `A847`, `Custom` |
| `steel-baseplate-material` | `A36`, `A283 grC`, `A283 grD`, `A529 gr50`, `A529 gr55`, `A709 gr36`, `A709 gr50`, `A709 gr50W`, `A709 grHPS 50W`, `A709 grHPS 70W`, `A709 grHPS 100W`, `A572 gr42`…`gr65`, `A1043 gr36`, `A1043 gr50`, `A1066 gr50`…`gr80`, `A242 gr42/46/50`, `A588 gr42/46/50`, `A514 gr90`, `A514 gr100`, `A852`, `Custom` |
| `steel-foundation-material` | metric (MPa): `20.68`, `27.68`, `31.03`, `34.47`, `41.36`, `Custom` · imperial (psi): `3000`, `4000`, `4500`, `5000`, `6000`, `Custom` |
| `welds-column-mat` | `E60xx`, `E70xx`, `E80xx`, `E90xx`, `E100xx`, `E110xx`, `E120xx`, `Custom` |

## Anchors

| Field | Accepted values |
|---|---|
| `anchor-prop-diam` | metric (mm): `10`, `12`, `16`, `20`, `22`, `24`, `27`, `30`, `33`, `36` · imperial (in): `3/8`, `1/2`, `5/8`, `3/4`, `7/8`, `1`, `1-1/8`, `1-1/4`, `1-3/8`, `1-1/2` |
| `anchor-prop-material` | `A307`, `A325`, `A490`, `A36`, `A193 Gr.B7 (105/95/75)`, `A354 Gr.BC (109/99)`, `A354 Gr.BD (130/115)`, `A449 Gr.92/81/58`, `A572 Gr.42/50/55/60/65`, `A588 Gr.50/46/42`, `F1554 Gr.36`, `F1554 Gr.55`, `F1554 Gr.105`, `Custom` |
| `anchor-prop-ending` | `straight`, `rectangle`, `circular`, `hook` |
| `anchor-thread-included` | `included` (sample value) |

## `factors` (LRFD)

| Key | Default | Reference |
|---|---|---|
| `concrete_bearing_factor` | `0.65` | AISC 360 |
| `steel_bearing_factor` | `0.75` | AISC 360 |
| `steel_flexure_factor` | `0.90` | AISC 360 |
| `weld_factor` | `0.75` | AISC 360 |
| `steel_tension_factor` | `0.90` | AISC 360 |
| `steel_shear_rupture_factor` | `0.75` | AISC 360 |
| `anchor_tension_factor` | `0.75` | ACI 318 |
| `anchor_shear_factor` | `0.65` | ACI 318 |
| `anchor_bolts_factor` | `0.75` | AISC 360 |
| `concrete_tension_factor` | `0.70` | ACI 318 |
| `concrete_shear_factor` | `0.65` | ACI 318 |
| `concrete_normal_weight_factor` | `1` | ACI 318 (λ) |

## Code-specific settings

- `design_settings.distribute_shear_to_all` and `simplified_approach_shear` (simplified ACI grout-pad
  approach vs. combined shear + axial stress) apply here.
- With shear applied, the response adds `Concrete Breakout Capacity (Vy Shear)`, `Concrete Pryout
  Capacity`, `Anchor Rod Shear Capacity`, `Anchor Rod Capacity (AISC Tension and Shear)` and
  `Interaction Check (ACI)` — the last has `capacity: 1.2` and `units_on_UI: ""` (a unitless
  interaction sum; its `ratio` is already sum ÷ 1.2).
