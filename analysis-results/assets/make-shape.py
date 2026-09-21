"""Regenerate example1-shape.md from example1-api-format.json.

The reference solve is ~5.6 MB (~1.37M tokens) - far too large for any agent to
read into context, and there is no slice of it that is safe to read whole: a
single load combination is ~57k tokens on its own.

So this emits a SHAPE MANIFEST instead: every key name, how each object is keyed,
and one real sample value per object, in ~1-2k tokens. It is orientation, not
data. Once you know the shape, query the source file for actual numbers - see the
probe recipe in ../SKILL.md.

Everything here is derived from the source file at generation time, so the
manifest cannot drift from it the way a hand-written summary would. A renamed or
added key raises KeyError below rather than being silently dropped.

Usage:  python make-shape.py
"""
import json
import os
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "example1-api-format.json")
TARGET = os.path.join(HERE, "example1-shape.md")
NL = chr(10)
Q = chr(34)

SCALAR = ("name", "type", "buckling")
# <result key> -> <element id> -> <station> -> value
BY_STATION = ("member_displacements", "member_forces", "member_stresses")
# <result key> -> <element id> -> value
BY_RESULT_THEN_ID = (
    "member_minimums", "member_maximums",
    "plate_displacements", "plate_forces", "plate_stresses",
    "plate_element_forces", "plate_element_stresses",
    "plate_minimums", "plate_maximums",
)
# <result key> -> {min, max}
PEAK = ("member_peak_results", "plate_peak_results")
# <element id> -> value
BY_ID = ("member_lengths", "member_stations", "member_discontinuities")

SHAPES = {
    "reactions": "node id -> {Fx, Fy, Fz, Mx, My, Mz}",
    "member_lengths": "member id -> float",
    "member_stations": "member id -> [float]",
    "member_discontinuities": "member id -> int",
}
for _k in BY_STATION:
    SHAPES[_k] = ("result key -> member id -> station (string) -> float"
                  " | [left, right] at a discontinuity")
for _k in BY_RESULT_THEN_ID:
    _noun = "member" if _k.startswith("member_") else "plate"
    _tail = ("float" if ("minimum" in _k or "maximum" in _k)
             else "[float] (one per corner node)")
    SHAPES[_k] = "result key -> %s id -> %s" % (_noun, _tail)
for _k in PEAK:
    SHAPES[_k] = "result key -> {min, max} across every %s" % (
        "member" if _k.startswith("member_") else "plate")


def nonzero(v):
    """Does this value carry a real number anywhere inside it?"""
    if isinstance(v, bool) or v is None:
        return False
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, list):
        return any(nonzero(x) for x in v)
    if isinstance(v, dict):
        return any(nonzero(x) for x in v.values())
    return False


def pick(d):
    """First key holding a non-zero value, else the first key.

    A sample of 0 tells the reader nothing about magnitude or sign, and most
    quantities are zero in most combinations, so prefer a live number. The path
    returned is still a genuine path into the source file.
    """
    for k, v in d.items():
        if nonzero(v):
            return k
    return next(iter(d))


def fmt(v, limit=4):
    if isinstance(v, list) and len(v) > limit:
        head = ", ".join(json.dumps(x) for x in v[:limit])
        return "[%s, ... %d total]" % (head, len(v))
    return json.dumps(v)


def sample(combo, key):
    """A real value from this object, plus the path fragment that reaches it."""
    obj = combo[key]
    if key in SCALAR:
        return None, json.dumps(obj)
    if not obj:
        return None, None
    if key == "reactions":
        nid = pick(obj)
        return ".%s%s%s.Fy" % (Q, nid, Q), fmt(obj[nid]["Fy"])
    if key in BY_ID:
        eid = pick(obj)
        return ".%s%s%s" % (Q, eid, Q), fmt(obj[eid])
    rk = pick(obj)
    inner = obj[rk]
    if key in PEAK:
        return "." + rk, fmt(inner)
    if not inner:
        return "." + rk, "{} (no elements)"
    eid = pick(inner)
    leaf = inner[eid]
    if key in BY_STATION:
        st = pick(leaf)
        return ".%s.%s%s%s.%s%s%s" % (rk, Q, eid, Q, Q, st, Q), fmt(leaf[st])
    return ".%s.%s%s%s" % (rk, Q, eid, Q), fmt(leaf)


def main():
    with open(SOURCE, encoding="utf-8") as fh:
        full = json.load(fh)

    known = (set(SCALAR) | set(BY_STATION) | set(BY_RESULT_THEN_ID)
             | set(PEAK) | set(BY_ID) | {"reactions"})
    seen = set()
    for combo in full.values():
        seen |= set(combo)
    if seen - known:
        raise KeyError(
            "Unhandled key(s) %s - the API shape has changed; update this script "
            "and ../SKILL.md together." % sorted(seen - known))

    always = sorted(k for k in seen if all(k in c for c in full.values()))
    sometimes = sorted(seen - set(always))

    # Reference combination for shapes and samples: it must carry every key, and
    # among those, carry the most live numbers - a combination whose results are
    # mostly zero produces samples that teach nothing.
    complete = [c for c in full if len(full[c]) == len(seen)] or list(full)
    ref_id = max(complete, key=lambda c: sum(
        1 for v in full[c]["member_peak_results"].values() if nonzero(v)))
    ref = full[ref_id]
    mb = os.path.getsize(SOURCE) / 1e6

    out = [
        "# `example1-api-format.json` - shape manifest",
        "",
        "Generated by `assets/make-shape.py`. **Do not edit by hand** - rerun the script",
        "after any refresh of the source asset.",
        "",
        "Source: `example1-api-format.json`, %.1f MB, %d load combinations, %d members, "
        "%d plates." % (mb, len(full), len(ref["member_lengths"]),
                        len(ref["plate_minimums"]["displacement_x"])),
        "",
        "**Shape only** - key names, how each object is keyed, one real sample value each.",
        "For actual numbers, query the source file; it is ~1.37M tokens and must never be",
        "read whole. Sample paths below are jq paths within one combination, e.g.",
        "`jq '.%s1%s.reactions.%s1%s.Fy' example1-api-format.json`." % (Q, Q, Q, Q),
        "",
        "## Load combinations",
        "",
        "Ids are the model's own and are **not sequential** - gaps are normal.",
        "",
        "| id | name | type | `plate_element_*` |",
        "|---|---|---|---|",
    ]
    for cid, combo in full.items():
        out.append("| `%s` | %s | `%s` | %s |" % (
            cid, combo["name"], combo["type"],
            "`{}`" if "plate_element_forces" in combo else "**absent**"))

    out += [
        "",
        "## Keys per combination",
        "",
        "Present on all %d combinations (%d keys):" % (len(full), len(always)),
        "",
        "```",
        ", ".join(always),
        "```",
        "",
    ]
    if sometimes:
        n_absent = sum(1 for c in full.values() if sometimes[0] not in c)
        out += [
            "Present on some only (%d keys) - **guard every access**:" % len(sometimes),
            "",
            "```",
            ", ".join(sometimes),
            "```",
            "",
            "Absent entirely (not `{}`) on %d of %d combinations here, so reading"
            % (n_absent, len(full)),
            "`combo.%s` without a guard throws rather than returning empty."
            % sometimes[0],
            "`result_filter` on `S3D.model.solve` can drop any other key the same way.",
            "",
        ]

    out += [
        "## Object shapes",
        "",
        "Sample values are real, and come from combination `%s` (%s)." % (
            ref_id, ref["name"]),
        "",
    ]
    for key in [k for k in ref if k not in SCALAR]:
        path, val = sample(ref, key)
        inner = ref[key]
        if not inner:
            out += [
                "### `%s` - empty" % key,
                "",
                "`{}` on every combination of this solve. Populates only once the plates",
                "have been meshed (`S3D.model.mesh`); shape is then " + SHAPES[key] + ",",
                "keyed per meshed element instead of per corner node.",
                "",
            ]
            continue
        keyed = key in BY_STATION or key in BY_RESULT_THEN_ID or key in PEAK
        count = " - %d result keys" % len(inner) if keyed else " - %d entries" % len(inner)
        out += ["### `%s`%s" % (key, count), "", "```", SHAPES[key]]
        if keyed:
            out.append("keys: " + ", ".join(inner))
        if path:
            out.append("e.g. %s%s = %s" % (key, path, val))
        out += ["```", ""]

    out += [
        "## Members: stations and discontinuities",
        "",
        "Station count is **not** `settings.evaluation_points` and is not constant across",
        "members - it rises with the member's discontinuity count. Read the count from",
        "`member_stations[\"<id>\"].length`; never derive or assume one.",
        "",
        "| member | stations | discontinuities | length |",
        "|---|---|---|---|",
    ]
    for m in sorted(ref["member_stations"], key=int):
        out.append("| `%s` | %d | %d | %s |" % (
            m, len(ref["member_stations"][m]),
            ref["member_discontinuities"][m], ref["member_lengths"][m]))

    # Station values are usually scalars but become [left, right] pairs at a
    # discontinuity, per result key. Report it with real counts and a real row.
    def count_pairs(combo):
        n, members, first = 0, set(), None
        for obj in BY_STATION:
            for rk, byid in combo[obj].items():
                for mid, stations in byid.items():
                    for stn, val in stations.items():
                        if isinstance(val, list):
                            n += 1
                            members.add(mid)
                            if first is None:
                                first = (obj, rk, mid, stn)
        return n, members, first

    per_combo = {c: count_pairs(full[c]) for c in full}
    pairs, pair_members, example = per_combo[ref_id]
    total_pairs = sum(n for n, _, _ in per_combo.values())
    nonzero_counts = [n for n, _, _ in per_combo.values() if n]
    empty_combos = [c for c in full if not per_combo[c][0]]
    pair_section = []
    if example:
        o, rk, mid, stn = example
        order = list(ref[o][rk][mid])
        i = order.index(stn)
        before, after = order[max(i - 1, 0)], order[min(i + 1, len(order) - 1)]
        para = (
            "At a discontinuity a station holds a **2-element `[left, right]` pair** - the "
            "value either side of the step - instead of a float. Across this solve %d "
            "station values are pairs (%d-%d per combination), always on %d of the %d "
            "members: those with `member_discontinuities > 0`. %sA quantity that stays "
            "continuous through the step keeps a scalar at that same station, so this "
            "varies per result key, not just per station - member `%s` of combination "
            "`%s` at station `%s`:" % (
                total_pairs, min(nonzero_counts), max(nonzero_counts),
                len(pair_members), len(ref["member_lengths"]),
                "" if not empty_combos else
                "Combination `%s` has none at all, so never feature-detect on a single "
                "combination. " % "`, `".join(empty_combos),
                mid, ref_id, stn))
        pair_section = [
            "## Station values are not always scalars",
            "",
            textwrap.fill(para, width=86),
            "",
            "```",
        ]
        width = max(len(k) for k in ref[o])
        for k in ref[o]:
            v = ref[o][k][mid]
            pair_section.append("%-*s  %s=%s   %s=%s   %s=%s" % (
                width, k, before, fmt(v[before]), stn, fmt(v[stn]),
                after, fmt(v[after])))
        pair_section += [
            "```",
            "",
            "So `Math.max(...Object.values(series))`, or any arithmetic run straight over a",
            "station series, will break. Flatten the pairs first, or read `member_minimums`",
            "/ `member_maximums`, which are always scalars.",
            "",
        ]

    st = ref["member_stations"]["1"]
    keys = list(ref["member_forces"]["axial_force"]["1"])
    out += [
        "",
        "Station *keys* are those positions rounded to 1 decimal, as strings, while",
        "`member_stations` holds the full-precision floats. Member `1` starts",
        "`%s ...` and the matching keys are" % ", ".join(str(x) for x in st[:3]),
        "`%s ...` - never match on float equality."
        % ", ".join("%s%s%s" % (Q, k, Q) for k in keys[:3]),
        "",
    ]
    out += pair_section

    with open(TARGET, "w", encoding="utf-8") as fh:
        fh.write(NL.join(out) + NL)

    size = os.path.getsize(TARGET)
    print("%s -> %s  (%.1f MB -> %.1f KB, ~%d tokens)" % (
        os.path.basename(SOURCE), os.path.basename(TARGET), mb,
        size / 1e3, size // 4))


if __name__ == "__main__":
    main()
