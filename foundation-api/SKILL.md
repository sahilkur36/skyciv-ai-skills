---
name: foundation-api
description: "Use when designing or checking a reinforced concrete pile through the SkyCiv API with standalone.foundation.start and standalone.foundation.check, for ACI 318-14, AS 3600-2018 and EN 1992 (Eurocode). Covers the pile object (settings.type, settings.code, settings.units), load case keys per code (DL/LL/W/E/LR/RL/SL, G/Q/Wu/Eu/Su, G/Ql/Qw/Qe/Qs/Qt), custom factored/service loads, geometry, pile_details, materials, long_rebar, shear_rebar, soils, layers and parameters. Also use for questions like 'design a pile', 'check this pile for these column loads', 'can the API design a pad or combined footing' (not at the moment) or 'why does my foundation API call hang'."
---

# Foundation Design API (piles)

Design and check reinforced concrete piles with the SkyCiv Foundation module via the `standalone.foundation` API.

> **Prerequisite:** start the session with `standalone.foundation.start`, not `S3D.session.start`. See the
> [`skyciv-api-v3`](../skyciv-api-v3/SKILL.md) skill for auth, `options` and the request/response envelope.
> If you also need an S3D model (e.g. to get column reactions), run that in a separate session.

**Only piles are supported through the API at the moment.** Pad footings (`isolated_foundation`) and combined
footings (`combined_foundation`) are not: don't send them; tell the user instead.

## Request

```json
{
  "auth": { "username": "...", "key": "..." },
  "options": { "validate_input": true },
  "functions": [
    { "function": "standalone.foundation.start", "arguments": { "keep_open": false } },
    { "function": "standalone.foundation.check", "arguments": { "1": { "settings": { "...": "..." } } } }
  ]
}
```

`arguments` holds the foundations keyed by ID (`"1"`, `"2"`, ...).

**Use the input format of the samples in [`assets/`](assets/).** Don't add `settings.version`, and don't send a
file exported from the current Foundation Designer as it is: those calls time out or never return.

Set `options.validate_input: true` so bad keys and values come back as clear error messages before the design runs.

### Supported piles

| `settings.type` | `settings.code` | `settings.units` |
|---|---|---|
| `piles_foundation` | `ACI_318_2014` | `metric`, `imperial` |
| | `AS_3600_2018`, `EN` | `metric` |

## Loads

`loads` is keyed by column ID (`"1"`). It holds the load cases for the code, each with `axial`, `shear_x`,
`shear_z` (kN / kip) and `moment_x`, `moment_z` (kN-m / kip-ft):

| Code | Load case keys |
|---|---|
| ACI | `DL`, `LL`, `W`, `E`, `LR`, `RL`, `SL` |
| AS 3600 | `G`, `Q`, `Wu`, `Eu`, `Su` |
| EN | `G`, `Ql`, `Qw`, `Qe`, `Qs`, `Qt` |

### Custom loads

To give factored and service loads directly, set `parameters.others.custom_load: true` and use:

```json
"loads": {
  "factored": { "P": 600, "Vx": 20, "Vz": 10, "Mx": 40, "Mz": 20 },
  "service": { "P": 420, "Vx": 14, "Vz": 7, "Mx": 28, "Mz": 14 }
}
```

## Units

`settings.units` (`metric` or `imperial`) sets the unit system for every value in the pile. The units of each field
are in [`references/fields.md`](references/fields.md) where they're confirmed, e.g. pile length in m / ft, pile size
and cover in mm / in, strengths in MPa / psi. Don't mix systems inside one pile.

## Building a pile

Start from the sample for your code and change values; don't build the object from scratch. Every sample has been
run successfully against the live API. Every key is described in [`references/fields.md`](references/fields.md);
load it when you need the allowed values for a field.

| Sample | Code | Units |
|---|---|---|
| [`aci-318-14-pile-imperial.json`](assets/aci-318-14-pile-imperial.json) | ACI 318-14 | imperial |
| [`as-3600-pile-metric.json`](assets/as-3600-pile-metric.json) | AS 3600-2018 | metric |
| [`en-pile-metric.json`](assets/en-pile-metric.json) | EN | metric |

## Gotchas

- **Piles use their own top-level keys:** `materials` (not `material`), `pile_details`, `long_rebar`, `shear_rebar`,
  `soils`, `layer`. `long_rebar` lists every bar, one entry each.
- **AS and EN pile parameters** go in `parameters.AS` and `parameters.EN`; ACI piles have neither.
- **A call that "times out" or never returns** is almost always an unsupported input (a pad or combined footing,
  `settings.version`, or a v4 export), not a slow design. Supported calls finish in about 10 seconds.

## Related skills

- [`skyciv-api-v3`](../skyciv-api-v3/SKILL.md): auth, sessions, request envelope.
- [`s3d-api`](../s3d-api/SKILL.md) and [`analysis-results`](../analysis-results/SKILL.md): get column reactions to use as pile loads.
- [`run-quick-design`](../run-quick-design/SKILL.md): other foundation calculators.
