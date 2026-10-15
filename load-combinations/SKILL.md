---
name: load-combinations
description: "Use when adding load cases and load combinations to a SkyCiv S3D model (s3d_model) — tagging loads with load_group, writing load_combinations, load_cases and load_combination_settings, or factoring dead, live, roof live, snow, wind and seismic loads to ASCE 7-22 (LRFD or ASD), AS/NZS 1170.0, NBCC 2020, EN 1990 or IS 800. Includes the generator's own factor tables for each code, the rules that make combos solve and display correctly, and how to call and convert the 7000-load-combination-generator Quick Design calculator. Trigger even without the word SkyCiv, e.g. 'add the load combos', 'factor the loads', 'ULS / SLS combinations', '1.2D + 1.6L', 'strength and serviceability cases', 'why does every load group show as Dead'. Not for deriving wind/snow/seismic magnitudes (use load-gen-api) or reading solved results (use analysis-results)."
---

# Load Combinations

How to put **load groups, load cases and load combinations** on an `s3d_model` so that
`S3D.model.solve` gives code-correct results and the S3D UI classifies every group correctly.

> **Prerequisite:** these objects live inside the `s3d_model` passed to `S3D.model.set` — see
> [`s3d-api`](../s3d-api/SKILL.md) for the full model schema and solve flow, and
> [`skyciv-api-v3`](../skyciv-api-v3/SKILL.md) for auth and the `{ auth, options, functions }`
> envelope. The load magnitudes come from you or [`load-gen-api`](../load-gen-api/SKILL.md);
> reading the solved combinations is [`analysis-results`](../analysis-results/SKILL.md).

**Units:** factors are dimensionless. Load magnitudes carry the units set by
`s3d_model.settings.units` (`"metric"` or `"imperial"`); combinations never change them.

## How the pieces fit

Every load (`point_loads`, `distributed_loads`, `moments`, `pressures`, `area_loads`,
`self_weight`, …) carries a `load_group` string. A combination is a factor per group; the solver
sums group × factor.

| Object | What it does (verified live) |
|---|---|
| `load_combinations` | **Required** for combination results. Integer-keyed; each entry is `name`, `criteria`, and one numeric key per load group. |
| `load_cases` | `{ "<code id>": { "<group>": "<case symbol>" } }`. Tells the S3D UI what type each group is. **Also changes the solve output:** it adds one `type: "load_case"` result per symbol (all groups with that symbol summed), which shifts the ids of every later `load_group` and `envelope` result. |
| `load_combination_settings` | `country` + `code` choose which standard the S3D UI's Load Group & Cases manager opens on. This is **not inert**: if it's missing, the UI assumes `ASCE-7-2022-LRFD`, and any symbol that isn't an ASCE symbol shows as Dead. The other keys (`criteria`, `filters`, `patterns`, …) only record generator settings. |
| `permanent_load_groups` | Array of the group names the generator varied. Metadata only; the solver ignores it. |

## Minimal working example

```json
{
  "self_weight": { "1": { "enabled": true, "x": 0, "y": -1, "z": 0, "load_group": "SW1" } },
  "distributed_loads": {
    "1": { "member": 2, "x_mag_A": 0, "y_mag_A": -5,  "z_mag_A": 0, "x_mag_B": 0, "y_mag_B": -5,  "z_mag_B": 0, "position_A": 0, "position_B": 100, "axes": "global", "load_group": "D1" },
    "2": { "member": 2, "x_mag_A": 0, "y_mag_A": -10, "z_mag_A": 0, "x_mag_B": 0, "y_mag_B": -10, "z_mag_B": 0, "position_A": 0, "position_B": 100, "axes": "global", "load_group": "L1" }
  },
  "point_loads": {
    "1": { "type": "n", "node": 2, "x_mag": 10,  "y_mag": 0, "z_mag": 0, "load_group": "Wx+" },
    "2": { "type": "n", "node": 3, "x_mag": -10, "y_mag": 0, "z_mag": 0, "load_group": "Wx-" }
  },
  "load_combinations": {
    "1": { "name": "1: 1.40D", "criteria": "strength", "SW1": 1.4, "D1": 1.4 },
    "2": { "name": "2: 1.20D + 1.60L", "criteria": "strength", "SW1": 1.2, "D1": 1.2, "L1": 1.6 },
    "3": { "name": "3: 1.20D + 1.00L + 1.00W (+x)", "criteria": "strength", "SW1": 1.2, "D1": 1.2, "L1": 1.0, "Wx+": 1.0 },
    "4": { "name": "4: 1.20D + 1.00L + 1.00W (-x)", "criteria": "strength", "SW1": 1.2, "D1": 1.2, "L1": 1.0, "Wx-": 1.0 },
    "5": { "name": "5: 0.90D + 1.00W (+x)", "criteria": "strength", "SW1": 0.9, "D1": 0.9, "Wx+": 1.0 },
    "6": { "name": "6: 0.90D + 1.00W (-x)", "criteria": "strength", "SW1": 0.9, "D1": 0.9, "Wx-": 1.0 }
  },
  "load_cases": { "ASCE-7-2022-LRFD": { "SW1": "D", "D1": "D", "L1": "L", "Wx+": "W", "Wx-": "W" } },
  "load_combination_settings": { "country": "United States", "code": "ASCE-7-2022-LRFD", "criteria": "All" }
}
```

| `load_combinations` key | Type | Notes |
|---|---|---|
| `name` | string | Free text, shown in results as `name`. |
| `criteria` | string | Lowercase: `strength`, `serviceability` or `other` (the UI dropdown's values). Stored as given; **not** returned in solve results, so keep your own id → criteria map if you filter results by it. |
| *group name* | number | Factor for that `load_group`. May be negative (the generator emits `0.90D - 1.00Eh`). Omit groups that don't participate. |

## Gotchas (all verified against the live API and S3D UI)

- **`load_cases` values are the code's short symbols** (`D`, `L`, `W`, `G`, `Qdo`, `Wu`, …) from
  the tables below, keyed by the code id. The `"Dead: dead"` style shows **every group as
  Dead** in the UI. So does a symbol that doesn't belong to the code in
  `load_combination_settings.code`, or to the default ASCE code if that's missing.
- **Set `load_combination_settings.country` and `.code` for any code other than ASCE-7-2022-LRFD**,
  or the UI opens on ASCE and classifies Australian/European symbols as Dead.
- **One wind (or seismic) direction per combination.** Model each direction as its own group
  (`Wx+`, `Wx-`, `Wy+`, `Wy-`) and repeat the wind rows once per direction, as combos 3–6 above do.
  Putting `Wx+` and `Wx-` in the same combination largely cancels them out.
  The `simultaneous` generator pattern does exactly this, so use `independent` (see below). Even
  with separate combos, the automatic `load_case` result for `W` sums every `W` group, so it is
  meaningless when opposite directions share a symbol; read the combinations instead.
- **Leaving a group out = factor 0.** The results are identical, so don't pad every combination
  with zeros.
- **A combination with no self-weight key applies no self-weight.** Put the self-weight group
  in every combination, with the same factor as the dead load. Self-weight defaults to group
  `SW1`: a flat `self_weight: {enabled, x, y, z}` and keyed entries without `load_group` both
  behave as `SW1`.
- **Keys that match no group are silently ignored** (`"NOPE": 5` → no error, no effect). Group
  names are case-sensitive exact matches, so check them against your loads.
- **Identical combinations only trigger a warning** (`"Load Combination #1 and Load Combination #2
  are identical"`), but each one still costs solve time. The generator's own sets repeat some
  combos (below); delete them.
- **Results come back keyed by position, not by your ids.** User combos are `type: "user_defined"`,
  followed by `load_case`, `load_group` and `envelope` entries. Their ids depend on how many of
  each exist, so match results by `name`/`type`.
- **Solve time grows with the combination count.** Only include cases the model actually has.

## Building combinations from the tables

1. **Pick the code** and write its id into both `load_cases` and `load_combination_settings`.
2. **Map every load group to a symbol** from that code's list. Dead loads and `SW1` both get the
   dead symbol (`D` / `G`).
3. **For each table row, write one combination per direction group** (row × `Wx+`, `Wx-`, …). Where a
   row's case has several groups (e.g. `D1` + `SW1`), give each of them that row's factor.
4. **Drop rows whose cases the model doesn't have**, then drop any duplicates this creates.
5. **Name each combination** with the row formula, **set `criteria`** in lowercase, then solve.

Factors below are copied from the live `7000-load-combination-generator` output (2026-09-23,
`remove_unnecessary: true`, filter `",f,u"`). `u` rows treat dead load as unfavourable. `f` rows
treat it as favourable and use the reduced dead factor.

### United States — ASCE 7-22 LRFD (`ASCE-7-2022-LRFD`, country `United States`)

Symbols: `D` dead · `L` live · `Lr` roof live · `S` snow · `R` rain · `W` wind · `Wt` tornado ·
`Eh`/`Ev` seismic · `H`/`Hf` lateral earth · `T` · `Ak` · `N` notional.

| Set | Combinations |
|---|---|
| Strength `u` | `1.4D` · `1.2D + 1.6L` · `1.2D + 1.6L + 0.5Lr` · `1.2D + 1.6L + 0.3S` · `1.2D + 1.6Lr` · `1.2D + 1.6Lr + 1.0L` · `1.2D + 1.6Lr + 0.5W` · `1.2D + 1.0S` · `1.2D + 1.0S + 1.0L` · `1.2D + 1.0S + 0.5W` · `1.2D + 1.0L + 1.0W` · `1.2D + 1.0L + 1.0W + 0.5Lr` · `1.2D + 1.0L + 1.0W + 0.3S` · `1.2D + 1.0W` · `1.2D + 1.0Eh + 1.0L` · `1.2D + 1.0Eh + 0.15S` · `1.2D + 1.0Eh + 1.0L + 0.15S` |
| Strength `f` — in ASCE 7 | `0.9D + 1.0W` · `0.9D + 1.0Eh` · `0.9D - 1.0Eh` |
| Strength `f` — **generator variants, not in ASCE 7 §2.3** | Every other `u` row with `0.9D` in place of the dead factor, e.g. `0.9D` · `0.9D + 1.6L` · `0.9D + 1.6L + 0.3S` · `0.9D + 1.0S + 1.0L`. These are extra reduced-dead checks (uplift, overturning, stress reversal). Keep them, but label them in `name` (e.g. suffix `(f)`) so a reviewer can tell them apart from code combinations. |
| Serviceability | None generated; the US generator only offers `All` / `Strength`. Choose them per project. |

### United States — ASCE 7-22 ASD (`ASCE-7-2022-ASD`, country `United States`)

Same symbols as LRFD.

| Set | Combinations |
|---|---|
| Strength `u` | `1.0D` · `1.0D + 1.0L` · `1.0D + 1.0Lr` · `1.0D + 0.7S` · `1.0D + 0.75L + 0.75Lr` · `1.0D + 0.75L + 0.525S` · `1.0D + 0.6W` · `1.0D + 0.75L + 0.75Lr + 0.45W` · `1.0D + 0.75L + 0.525S + 0.45W` · `1.0D + 0.7Eh` · `1.0D + 0.525Eh + 0.75L` · `1.0D + 0.525Eh + 0.1S` · `1.0D + 0.525Eh + 0.75L + 0.1S` |
| Strength `f` — in ASCE 7 | `0.6D + 0.6W` · `0.6D + 0.7Eh` |
| Strength `f` — **generator variants, not in ASCE 7 §2.4** | The other `u` rows with `0.6D`, e.g. `0.6D + 1.0L` · `0.6D + 0.7S`. Keep them and label them as for LRFD. |

The generator also emits `1.0D + 0.6W` twice; delete the duplicate. Names round to 2 dp
(`0.53S`); the stored factor is 0.525.

### Australia / New Zealand — AS/NZS 1170.0 (`AS-1170.0-2002`, country `Australia`; `AS/NZS-1170.0-2002`, country `New Zealand`)

Both ids share the same symbols and factors; the UI lists them as separate standards.

Symbols: `G` dead · `Qd?`/`Qc?` live, where the letter after `d`/`c` is the occupancy:
`Qdd` domestic, `Qdo` offices, `Qdp` parking, `Qde` retail, `Qds` storage, `Qdx` other,
`Qdr`/`Qdy` roofs, `Qcb` balustrades, `Qcm` machinery · `Wu`/`Ws` wind ultimate/serviceability
· `Su` snow/liquid/rain · `Eu`/`Es` seismic · `Ld?`/`Lc?` long-term live · `N`.
Use ultimate symbols (`Wu`, `Eu`) and serviceability symbols (`Ws`, `Es`) as **separate groups**.

The table below is for `Qdo`. The combination factors depend on the Q type (ψc = 0.4, ψE = 0.3,
ψs = 0.7 for offices), so regenerate for other occupancies or look up Table 4.1.

| Set | Combinations |
|---|---|
| Strength `str` (cl 4.2.2) | `1.35G` · `1.2G + 1.5Q` · `1.2G + 1.0Wu` · `1.2G + 0.4Q + 1.0Wu` · `0.9G + 1.0Wu` · `1.0G + 1.0Eu` · `1.0G + 0.3Q + 1.0Eu` · `1.2G + 1.0Su` · `1.2G + 0.4Q + 1.0Su` |
| Stability `sta` `f` (cl 4.2.1, stabilising G) | `0.9G` · `0.9G + 1.5Q` · `0.9G + 1.0Wu` · `0.9G + 0.4Q + 1.0Wu` · `0.9G + 1.0Eu` · `0.9G + 0.4Q + 1.0Eu` · `0.9G + 1.0Su` · `0.9G + 0.4Q + 1.0Su` |
| Stability `sta` `u` | Identical to the `str` rows except for `0.9G + 1.0Wu`. Delete them as duplicates unless you report stability separately. |
| Serviceability `ser` | `1.0G` · `0.7Q` · `1.0Ws` · `1.0Es`. Each row is one component on its own (the generator doesn't add G to them); check each against its own deflection limit. |

### Canada — NBCC 2020 (`NBCC-2020`, country `Canada`)

Symbols: `D` · `L` · `Ls` sustained live · `S` · `W` · `E` · `H`/`Hf` · `T` · `N`.

| Set | Combinations |
|---|---|
| Strength `u` | `1.4D` · `1.25D + 1.5L` · `1.25D + 1.5L + 1.0S` · `1.25D + 1.5L + 0.4W` · `1.25D + 1.5S` · `1.25D + 1.0L + 1.5S` · `1.25D + 1.5S + 0.4W` · `1.25D + 1.4W` · `1.25D + 0.5L + 1.4W` · `1.25D + 0.5S + 1.4W` |
| Strength `f` | The same ten rows with `0.9D`. NBCC applies 0.9D wherever dead load resists, so these are code combinations. |
| Seismic | `1.0D + 1.0E` · `1.0D + 0.5L + 1.0E` · `1.0D + 0.25S + 1.0E` · `1.0D + 0.5L + 0.25S + 1.0E` |
| Serviceability | `1.0D` · `1.0D + 1.0L` · `1.0D + 1.0L + 0.35S` · `1.0D + 1.0L + 0.3W` · `1.0D + 1.0S` · `1.0D + 0.35L + 1.0S` · `1.0D + 1.0S + 0.3W` · `1.0D + 1.0W` · `1.0D + 0.35L + 1.0W` · `1.0D + 0.35S + 1.0W` |

### Europe — EN 1990 (`EN-1990-2002`, country `Europe`; no national annex)

Symbols: `G` · `Qa`–`Qh` imposed by category (`Qa` domestic, `Qb` office, `Qc` congregation,
`Qd` shopping, `Qe` storage, `Qf`/`Qg` traffic, `Qh` roofs) · `Sl`/`Sh` snow below/above 1000 m ·
`W` · `T` · `Ad`/`Ae` accidental/seismic · `N`. The UI also offers the `EN-1990-2002-NA-UK` and
`-NA-FR` annexes, whose factors differ; regenerate if you use one.

Each set is one pattern: a **leading** variable action × γQ, plus every **accompanying** one × γQ·ψ0.
The generator used ψ0 = 0.7 (`Qb`), 0.5 (`Sl`), 0.6 (`W`) and ψ1/ψ2 = 0.5/0.3 (`Qb`), 0.2/0 (`Sl`),
0.2/0 (`W`). ψ depends on the Q category.

| Set | Pattern (enumerate every lead × accompanying subset) | Use |
|---|---|---|
| STR `setB1` `u` | `1.35G + 1.5·lead + 1.5ψ0·others`, e.g. `1.35G + 1.5Qb + 0.75Sl + 0.9W`, `1.35G + 1.05Qb + 1.5Sl`, `1.35G + 0.75Sl + 1.5W` | **Member design** |
| STR `setB1` `f` | same with `1.0G` | Member design, favourable G |
| EQU `setA1` | `1.1G` (`u`) / `0.9G` (`f`) with the same Q pattern | Overall stability only |
| GEO `setC` | `1.0G + 1.3·lead + 1.3ψ0·others` | Foundations/geotechnical |
| SLS characteristic | `1.0G + 1.0·lead + ψ0·others` | Irreversible deflection |
| SLS frequent | `1.0G + ψ1·lead + ψ2·others`, e.g. `1.0G + 0.5Qb`, `1.0G + 0.3Qb + 0.2W` | Reversible deflection, vibration |
| SLS quasi-permanent | `1.0G + ψ2·Q`, e.g. `1.0G + 0.3Qb` | Long-term / creep |

Don't read EQU (`1.1G`) rows as the design set; STR is `1.35G`. The full generator run (G, Qb, Sl,
W) is 85 combinations. Filter `multi_dropdown_2` to the sets you need (see below).

### India — IS 800:2007 (`IS-800-2007`, country `India`)

Symbols: `D` · `L` · `W` · `E` · `A` accidental · `N` (`IS-456-2000` has no `A`).

| Set | Combinations |
|---|---|
| Strength `u` | `1.5D + 1.5L` · `1.2D + 1.2L + 1.2W` · `1.5D + 1.5W` · `1.2D + 1.2L + 1.2E` · `1.5D + 1.5E` |
| Strength `f` — in IS 800 Table 4 | `0.9D + 1.5W` · `0.9D + 1.5E` |
| Strength `f` — **generator variants** | `0.9D + 1.5L` · `0.9D + 1.2L + 1.2W` · `0.9D + 1.2L + 1.2E`. Keep them and label them as for ASCE. |
| Serviceability | `1.0D + 1.0L` · `1.0D + 0.8L + 0.8W` · `1.0D + 1.0W` |

## Generating a set — `7000-load-combination-generator` (optional)

Use this to regenerate the tables above for other occupancies, cases or national annexes. Call it
through [`run-quick-design`](../run-quick-design/SKILL.md) (`POST https://qd.skyciv.com/run`, own
auth, not the S3D envelope). The payload below mirrors the request the S3D UI's own Load
Combination Generator sends (captured from the live UI, 2026-09-23).

| Input | Value |
|---|---|
| `country_input` | `united-states` · `australia` · `canada` · `europe` · `india`. The UI sends this key; the schema's `region_input` is also accepted. |
| `standard_input` | The calculator's id for the code: the heading ids above, **except NZ, which is `AS-1170.0-2002`** (see below). **Never `"Please Select"`**; it crashes with `Cannot find module …Please Select_Schema.json`. |
| `criteria_input` | `All` or `Strength` (Europe also `Serviceability`) |
| `combination_naming_input` | `ID + Factor + Name` (UI default; names use your `col6` group names, e.g. `1.20D1 + 1.20SW1`) · `ID + Factor + Symbol` (uses internal ids like `D2`, `W1`) · `ID` · `ID + Criteria` · `Schema Row + Increment` |
| `multi_dropdown_1` | **Required** (without it: `Cannot read properties of undefined (reading 'split')`). Use `",f,u"`. |
| `multi_dropdown_2` | AS/NZS: `",sta,str"`. Europe: any of `setA1,setB1,setC,seis`. |
| `multi_dropdown_3` | Europe SLS: `",cha,fre,qua"` |
| `load_case_table` | One row per case: `col1` symbol, `col2` number of groups of that case, `col3` pattern, `col4` main ratio, `col5` alternate ratio (UI sends `1`), `col6` comma-separated **group names**, one per `col2` (e.g. `"D1,SW1"`), or `"auto"` for `D1`, `W1`, `W2`, … |
| `remove_unnecessary` | `true` removes redundant combos (57 of 69 in a D/L/W×2 test) |

Also send `"calcs_only": true` next to `input`, as the UI does.

**New Zealand.** The model and UI use code `AS/NZS-1170.0-2002` with country `New Zealand`, but the
calculator has one AS/NZS 1170.0 schema, filed under `AS-1170.0-2002`. The S3D UI itself sends
`country_input: "australia"`, `standard_input: "AS-1170.0-2002"` when New Zealand is selected. Do the
same: passing `AS/NZS-1170.0-2002` as `standard_input` fails. Then write `AS/NZS-1170.0-2002` /
`New Zealand` into `load_cases` and `load_combination_settings`, as the UI's import does. The factors
are the ones in the AS/NZS table above.

**Patterns (`col3`):** with `col2 > 1`, `independent` puts one group per combination, which is
correct for wind directions. `simultaneous` puts them all in every combination: right for the
dead groups (`D1`, `SW1`), wrong for directions (the cancelling bug above). `mirror`, `paired`,
`sweep` and `checker` exist but haven't been verified here.

```json
{ "uid": "7000-load-combination-generator", "auth": "you@example.com", "key": "YOUR_API_TOKEN",
  "pdf_report": false, "calcs_only": true,
  "input": { "country_input": "united-states", "standard_input": "ASCE-7-2022-LRFD", "criteria_input": "All",
    "combination_naming_input": "ID + Factor + Name", "multi_dropdown_1": ",f,u", "remove_unnecessary": true,
    "load_case_table": [
      { "col1": "D", "col2": 2, "col3": "simultaneous", "col4": 1, "col5": 1, "col6": "D1,SW1" },
      { "col1": "L", "col2": 1, "col3": "simultaneous", "col4": 1, "col5": 1, "col6": "L1" },
      { "col1": "W", "col2": 2, "col3": "independent",  "col4": 1, "col5": 1, "col6": "Wx+,Wx-" } ] } }
```

The output is **not** `load_combinations`. Read `data.results.combination_obj.value`:
`{ "3": { "name": "…", "criteria": "Strength", "schema_row": "4a-W1-u", "groups": [ { "id": "D1",
"label": "D1", "value": 1.2, "load_case": "D" }, … ] } }`. The group's name is in `label`: `id` is
internal (`G1`, `G2`) when you name the groups in `col6`. `criteria` is capitalised. If you used
`"auto"`, there is no self-weight group, so add it with the dead factor (as below).

```js
function toModel(combinationObj, code, country, { selfWeight = 'SW1' } = {}) {
  const load_combinations = {}, cases = {};
  Object.values(combinationObj).forEach((c, i) => {
    const combo = { name: c.name, criteria: c.criteria.toLowerCase() };
    for (const g of c.groups) { combo[g.label] = g.value; cases[g.label] = g.load_case; }
    const dead = c.groups.find(g => g.load_case === 'D' || g.load_case === 'G');
    if (dead && !(selfWeight in combo)) { combo[selfWeight] = dead.value; cases[selfWeight] = dead.load_case; }
    load_combinations[i + 1] = combo;
  });
  return { load_combinations, load_cases: { [code]: cases }, load_combination_settings: { country, code, criteria: 'All' } };
}
```

Pass the **model** code and country (`AS/NZS-1170.0-2002`, `New Zealand` for NZ), not the
calculator's. After converting, rename `f`-variant names as described in the tables and delete
duplicates.
