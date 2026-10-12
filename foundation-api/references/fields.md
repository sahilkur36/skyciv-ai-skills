# Pile field reference

Every key in the working `standalone.foundation.check` pile samples. Load this when building or checking a pile object field by field. Supported codes, load cases and custom loads are in [SKILL.md](../SKILL.md).

## Piles

These keys apply when `settings.type` is `piles_foundation`. Units are given as metric / imperial where confirmed.

### `geometry`

| Key | Type | Description |
| :--- | :--- | :--- |
| `shape` | `string` | Pile shape. Options: `round`, `rectangular`. |
| `diameter` | `number` | Pile diameter (mm / in). Used when `shape` is `round`. |
| `width` | `number` | Pile width (mm / in). Used when `shape` is `rectangular`. |
| `depth` | `number` | Pile depth (mm / in). Used when `shape` is `rectangular`. |

### `pile_details`

| Key | Type | Description |
| :--- | :--- | :--- |
| `length` | `number` | Pile length (m / ft). |
| `H_exposed` | `number` | Exposed length (m / ft). |
| `construction_type` | `string` | Pile construction type. Options: `cast_in_place`, `prestressed`, `precast`. |
| `type` | `string` | `bored` for `cast_in_place`, `driven` for `precast`. |
| `head_fixity` | `string` | Fixity at the pile head. Options: `free`, `pinned`, `fixed`. |
| `tip_fixity` | `string` | Fixity at the pile tip. Options: `free`, `pinned`, `fixed`. |
| `concrete_cover` | `number` | Concrete cover (mm / in). |

### `materials`

| Key | Type | Description |
| :--- | :--- | :--- |
| `properties` | `string` | Pile material, e.g. `reinforced_concrete`. |
| `concrete_strength` | `number` | Concrete compressive strength (MPa / psi). |
| `pile_modulus` | `number` | Pile modulus of elasticity (MPa / psi). |
| `rebar_strength` | `number` | Longitudinal bar yield strength (MPa / psi). |
| `steel_modulus` | `number` | Steel modulus of elasticity (MPa / psi). |
| `shear_rebar_strength` | `number` | Shear bar yield strength (MPa / psi). |
| `shear_rebar_type` | `string` | Shear bar type, e.g. `ties`. |

### `long_rebar` and `shear_rebar`

`long_rebar` lists the longitudinal bars, keyed by ID. `shear_rebar` holds one set of shear bars, keyed `"1"`.

| Key | Type | Description |
| :--- | :--- | :--- |
| `long_rebar.<id>.number` | `number` | `number` value of the bar entry (`1` in the samples). |
| `long_rebar.<id>.diameter` | `number` | Bar diameter. |
| `long_rebar.<id>.y` | `number` | Depth of the bar from the pile face. |
| `shear_rebar.1.number` | `number` | Shear bar `number` value. |
| `shear_rebar.1.diameter` | `number` | Bar diameter. |
| `shear_rebar.1.spacing` | `number` | Shear bar spacing (mm / in). |

### `soils` and `layer`

`soils` lists the soil types, keyed by ID. `layer` lists the soil layers, keyed by ID, and refers to a soil type by `soil_id`.

| Key | Type | Description |
| :--- | :--- | :--- |
| `soils.<id>.type` | `string` | Soil type. Options: `granular`, `cohesive`. |
| `soils.<id>.label` | `string` | Soil name. |
| `soils.<id>.soil_weight` | `number` | Soil unit weight. |
| `soils.<id>.friction_angle` | `number` | Angle of internal friction. |
| `soils.<id>.cohesion` | `number` | Cohesion. |
| `soils.<id>.subgrade_modulus` | `number` | Modulus of subgrade reaction. |
| `layer.<id>.thickness` | `number` | Layer thickness. |
| `layer.<id>.start` | `number` | Start of the layer. |
| `layer.<id>.end` | `number` | End of the layer. |
| `layer.<id>.soil_id` | `integer` | ID of the soil type in `soils`. |

### `parameters`

| Key | Type | Description |
| :--- | :--- | :--- |
| `others.n_segment` | `integer` | Number of pile segments for the analysis of lateral geotechnical capacity. |
| `others.factor_of_safety` | `number` | Factor of safety. |
| `others.ground_water_level` | `number`, `string` | Ground water level, or `"N/A"` for no ground water. |
| `others.water_density` | `number` | Water density. |
| `others.custom_load` | `boolean` | See [Custom loads (piles)](../SKILL.md#custom-loads). |
| `AS` | `object` | **AS 3600.** See below. |
| `EN` | `object` | **EN.** See below. |

**`parameters.AS`**

| Key | Type | Description |
| :--- | :--- | :--- |
| `psic`, `psil` | `number` | Factors ψ<sub>c</sub> and ψ<sub>l</sub>. |
| `design_life` | `number` | Design life in years. Options: `50`, `100`. |
| `exposure_classification` | `string` | Concrete exposure classification (AS 2159 Section 6.4.2). Options: `non_aggressive`, `mild`, `moderate`, `severe`, `very_severe`. |
| `average_risk_rating` | `number` | Overall design Average Risk Rating (ARR): the product of all the risk weighing factors and the relevant Individual Risk Ratings (AS 2159 Section 4.3). |
| `intrinsic_test` | `number` | Intrinsic test value. |
| `concrete_placement_factor` | `number` | Concrete placement factor k. For concrete and grout piles, between 0.75 and 1.0. |

**`parameters.EN`**

| Key | Type | Description |
| :--- | :--- | :--- |
| `psi_factor` | `number` | Factor ψ. |
| `shaft` | `number` | Partial factor for shaft resistance of a pile. |
| `base` | `number` | Partial factor for the base resistance of a pile. |
| `model` | `number` | Partial factor for uncertainty in a resistance model. |
| `concrete` | `number` | Concrete partial factor. |
| `steel` | `number` | Steel partial factor. |
| `foundation` | `number` | Foundation material factor k<sub>f</sub>: partial factor for materials for foundations. |
| `long_term_effect_factor` | `number` | Long-term effect factor. |
