# Meshing plates inside S3D

Read this before writing code that runs inside S3D (an S3D App, a Left Menu panel, or any
in-app script) and meshes, re-meshes or un-meshes plates. A plate only takes part in the
analysis once it is meshed: `plates[id].isMeshed` is `true` and its elements are in the
`meshedPlates` array. Meshing goes to the SkyCiv server, so treat every mesher call as
**asynchronous**.

## Which function to call

| | `S3D.mesher.autoMesher(options)` | `S3D.mesher.meshPlates(options)` | `S3D.mesher.autoMeshAll(size, unmesh)` |
|---|---|---|---|
| Mesh style | Unstructured | Structured (regular grid) | Unstructured |
| Scope | The plate IDs you pass, or all non-diaphragm plates | The plate IDs you pass | Every plate in the model |
| Plate shape | Any polygon, holes allowed | 4-node plates without holes (3-node plates are forced to triangles) | Any polygon |
| Control | Coarseness 1–6, or a target element size | Exact divisions, e.g. 4 × 6 | Coarseness 1–6 |
| Tells you when it's done | `options.callback`, but see the gotchas | Calls `S3D.UI.update` itself when it finishes | Nothing |
| Free accounts | Unstructured quads are disabled | Works | Unstructured quads are disabled |

- **`autoMeshAll(coarseness, unmesh)`** is the default for meshing the whole model. It's the
  same as the Auto-Mesh All Plates button and the most reliable mesher, including on plates
  with holes and members along hole edges. **Always pass `coarseness` (1–6).** Without it,
  the function opens a confirmation dialog instead of meshing.
- **`autoMesher`** is for a specific set of plates.
- **`meshPlates`** is for when the user gives the grid ("4 × 6") or a target size, and for free accounts.

All mesher calls drive the mesher's UI panel, so they need S3D's UI to be loaded. They do
nothing in guest mode.

## `autoMesher(options)`

| Key | Default | Notes |
|---|---|---|
| `plate_ids` | Every non-diaphragm plate | Array of plate IDs. Rigid-diaphragm plates (`diaphragm !== "no"`) are skipped. |
| `method` | `"frontal_quads"` | `"frontal_quads"` \| `"frontal"` \| `"adapt"` \| `"packing_parallelograms"` \| `"delaunay"` |
| `granularity` | `1` | 1 (coarse) … 6 (fine), clamped. **Always pass it**: leaving it out gives the coarsest mesh. The UI default is 3. |
| `physical_size` | From `granularity` | Documented as a target element size that overrides `granularity`, but in testing a size in model length units had no effect. For an exact size, use `meshPlates` with divisions. |
| `callback` | No-op | Called with `{ status, msg }`. |

```javascript
const slabIds = [1, 2];  // plates that share an edge go in the same call
S3D.mesher.autoMesher({
  plate_ids: slabIds,
  method: "frontal_quads",
  granularity: 5,
  callback: function (res) {
    const model = S3D.structure.get();
    const failed = slabIds.filter((id) => !(model.plates[id] && model.plates[id].isMeshed));
    SKYCIV_UTILS.alert.sideNotify({
      title: "Mesh",
      content: failed.length ? "Plates " + failed.join(", ") + " did not mesh: " + res.msg : "Plates meshed.",
      theme: failed.length ? "warning" : "success",
    });
    S3D.UI.update({ redraw: true, update_undo: true });
  },
});
```

## `meshPlates(options)`

| Key | Notes |
|---|---|
| `plateIDs` | Array of plate IDs. **Required**: leaving it out throws. |
| `b_nDivisions` | Divisions along the plate's node 0 → node 1 edge. |
| `h_nDivisions` | Divisions along node 0 → node 3. Falls back to `b_nDivisions` when empty. Ignored for triangles. |
| `structuredMeshMethod` | `0` = quads (the UI option). `1` and `2` are triangle patterns, not offered in the UI. |

```javascript
S3D.mesher.meshPlates({ plateIDs: [4], b_nDivisions: 4, h_nDivisions: 6, structuredMeshMethod: 0 });
```

For a target size, work the divisions out per direction:
`Math.max(2, Math.ceil(edgeLength / size))`.

The whole call is one undo step. Corner nodes are reused, and new mesh nodes reuse any
existing node at the same coordinates.

## `unMeshPlates(plateIDs, update_ui)`

```javascript
S3D.mesher.unMeshPlates([1, 2], false);  // false: no redraw; update once yourself at the end
```

This removes the mesh and the nodes it created. It keeps any node still used by a member,
another plate, a support, a point load or a moment. IDs that don't exist or aren't meshed
are skipped.

## Rules that are easy to miss

- **Mesh plates that must connect in one call.** Plates connect only through shared mesh
  nodes. Mesh two slab bays, or a wall and the slab it meets, separately and their meshes
  won't line up along the shared edge.
- **Mesh after the geometry that sits on the plate.** The mesher puts mesh nodes on the
  members, supports and point loads on a plate. If you add a beam after meshing, it isn't
  connected. Un-mesh and mesh again.
- **Re-meshing:** un-mesh first, then mesh.
- **`autoMesher`'s callback stops waiting after 10 seconds.** A slower mesh still finishes,
  but the callback never runs. For a large model, don't rely on it alone: watch
  `plates[id].isMeshed`, or the `meshedPlates` count settling, before moving on.
- **`meshPlates` with `b_nDivisions: 1, h_nDivisions: 1` does nothing** and returns silently.
- **Don't skip plates on a geometry guess.** Holes, members along hole edges and members
  crossing a plate are handled by the mesher. If a plate really fails, `isMeshed` stays
  `false`. Report that plate.
- **`meshPlates` ignores holes.** It doesn't check for them, so a plate with holes gets a mesh
  that covers them. Use `autoMesher` for those.
- **Never write `meshedPlates` or `isMeshed` yourself.** Each `meshedPlates` row is
  `[n1, n2, n3, n4 (null for a triangle), parentPlateId, rotZ]`. Read it, don't hand-build it.
- **Check the result before reporting it**: `plates[id].isMeshed` for each plate you meshed.
- **For "finer" or "coarser"**, measure the current element size from the mesh (the mean edge
  length of the plate's `meshedPlates` elements), scale it, and apply it with `meshPlates`
  divisions on 4-node plates. With `autoMesher`, change `granularity` instead. Afterwards,
  check that the element count moved the right way (up for finer, down for coarser).

## Units

Work out division counts from lengths in the model's length units (`settings.units.length`).
If the user gives a size in other units, convert it first with
`SKYCIV_UTILS.units.convert(value, from, to)`.
