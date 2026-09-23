# `design_code: "Australian"` — AS 4100:2020 / AS 3600:2018 / AS 5216:2021

Values the `baseplate` skill's shared schema leaves code-specific. Load this once `design_code` is
`Australian`. Starting template: [`sample-api/australia/input.js`](../sample-api/australia/input.js)
(pinned base, `Nx = 100 kN`, CHS column, metric).

An unrecognised string in any list below is **not rejected** — the calculator silently substitutes a
default and returns `status: 0`. Copy values exactly, including spaces and case.

## Units

Metric only: `mm`, `kN`, `kN-m`, `MPa`.

## Materials

The column and base plate lists are **different** — base plates are plate/strip standards, columns are
section standards. A column grade used as a base plate grade silently falls back to a default.

| Field | Accepted values |
|---|---|
| `steel-column-material` | I-sections: `AS/NZS 3679.1 Gr. 350`, `AS/NZS 3679.1 Gr. 300` · welded sections: `AS/NZS 3679.2 Gr. 400`, `Gr. 350`, `Gr. 300` · hollow sections: `AS/NZS 1163 Gr. C450`, `AS/NZS 1163 Gr. C350`, `AS/NZS 1163 Gr. C250` · `Custom` |
| `steel-baseplate-material` | `AS/NZS 3678 Gr. 450`, `Gr. 400`, `Gr. 350`, `Gr. WR350`, `Gr. 300`, `Gr. 250`, `Gr. 200` · `AS/NZS 1594 Gr. HA400`, `HW350`, `HA350`, `HA300/1`, `HU300/1`, `HA300`, `HU300`, `HA250`, `HU250`, `HA200`, `XF500`, `XF400`, `XF300` · `AS/NZS 3597 Gr. 500`, `Gr. 600`, `Gr. 700` · `Custom` (write the full prefix each time, e.g. `AS/NZS 3678 Gr. 250`) |
| `steel-foundation-material` | `N20`, `N25`, `N32`, `N40`, `N50`, `N65`, `N80`, `N100`, `S28`, `S65`, `Custom` |
| `welds-column-mat` | `430`, `490`, `550`, `620`, `690`, `760`, `830`, `Custom` |

## Anchors

| Field | Accepted values |
|---|---|
| `anchor-prop-diam` | `M10`, `M12`, `M16`, `M20`, `M22`, `M24`, `M27`, `M30`, `M36`, `M39`, `M42`, `M48`, `M52` |
| `anchor-prop-material` | `4.6`, `8.8`, `HR8.8`, `HR10.9`, `Custom` |
| `anchor-prop-ending` | `straight`, `rectangle`, `circular` — **no `hook`** |

## Welds

`welds.data['as-weld-category']`: `sp` (Structural Purpose, default) or `gp` (General Purpose) — AS 4100:2020 Cl. 9.6.1.3.

## `factors` (capacity reduction φ)

| Key | Default | Reference |
|---|---|---|
| `concrete_compression_factor` | `0.60` | AS 3600:2018 |
| `steel_bending_factor` | `0.90` | AS 4100:2020 |
| `steel_tension_factor` | `0.90` | AS 4100:2020 |
| `steel_shear_factor` | `0.90` | AS 4100:2020 |
| `weld_factor` | `0.80` | AS 4100:2020 (SP welds) |
| `bolt_in_tension_factor` | `0.80` | AS 5216:2021 |
| `concrete_failure_factor` | `0.6667` | AS 5216:2021 |
| `prying_factor` | `1` | AS 5216:2021 |
| `custom_lever_arm` | `0` | AS 5216:2021 Cl. 4.2.2.4 — `0` = auto-calculate |
| `k7_factor` | `"ductile"` | AS 5216:2021 Cl. 7.2.2.2 — `ductile` (k7 = 1.0) or `non-ductile` (k7 = 0.8) |
| `restraint_factor` | `"no-restraint"` | AS 5216:2021 Cl. 4.2.2.4 — `no-restraint` or `full-restraint` |

## Code-specific behaviour

- `detailing.concrete_splitting` is not applied for this code.
- `design_settings.include_embedded_head_radius` applies here.
- On a pinned, axial-only base the response returns `Concrete Bearing Capacity` (in `force`),
  `Weld Capacity` (`0 / 0` — not evaluated) and `Base Plate Yield Capacity (Compression Load)`.
  Put tension (`Nx < 0`) on the same base and the anchor checks appear instead, including
  `Base Plate Yield Capacity (Tension Load)` in `units_on_UI: "moment"`.
