# Destination Displays: Service Type Visible, Destination Blank or Misplaced

## Identify the Text Source

Display meshes, scrolling animations, and textures do not prove that destinations are baked into textures. E2 / E5 / E6 / H5 `roll*empty*` textures provide service types such as HAYATE and a blank display region. Station names come from `NEXT_STOP` in `metadata.labelList.labels`. Deleting all of `labelList` preserves the service type but removes station names.

An older skill advised deleting `labelList` when original display assets existed. That advice is withdrawn: it confused complementary content with duplicates. For regressions, recheck source assets, final packages, and the target version instead of relying on that old conclusion.

| Symptom | First checks |
| --- | --- |
| Service type visible, adjacent station blank | Source/final `NEXT_STOP` counts, build-time label deletion, assigned line and next stop |
| Station text on the body or facing incorrectly | `size`, transform basis scaling, `childId`, root/body transforms, display mesh position |
| Vehicle-name text such as “Train” on glass | Whether the source author used `NAME` for vehicle numbering; remove only confirmed unwanted labels |
| Entire display or lamp surface disappears by time of day | Shader time conditions, animation, LOD; investigate separately |

`NEXT_STOP` retains next-stop semantics and is not automatically the route terminus. Do not fake a restored dynamic feature with a fixed name such as Tokyo.

## Adapt Against Current Native Vehicles

Local TF3 Model Editor v13 resources inspected on 2026-10-07:

- `tgv_duplex/tgv_middle1.mdl` in `base/content/vehicle/train/tgv_duplex.zip`: destination `size = {39.8, 12.4}`, transform basis scale `0.01`, bound to `middle1_body`.
- `re_450/re_450_back.mdl` in `re_450.zip`: destination `size = {97.5, 12.6}`, basis scale `0.01`, bound to `back_body`.
- `model_editor/meta_metadata.lua` in `model_editor.zip` still declares `NEXT_STOP`, `childId`, `size`, `transf`, `fitting`, and `renderMode`.
- In this case, official legacy conversion retained source `size = {0.4, 0.14}` and identity transforms instead of adopting these native layout conventions.

Regenerate this case's labels from unmodified TF2 data: multiply both `size` dimensions by 100 and the first three transform columns by 0.01; preserve translation and the final homogeneous element. Layout dimensions become `{40,14}` while physical dimensions remain `0.4 × 0.14` meters. Preserve `fitting = "SCALE"`, original color, alignment, and render mode. Some E2 labels were originally `STD`; do not change all labels to emissive rendering.

This is a native-resource convention used for this case, not a universal schema requirement to multiply by 100. Check whether final models are already converted and rebuild from the source on repeat runs to prevent accumulated scaling. Other scale choices must also preserve physical rectangles and undergo rendering checks.

## Coordinates and Body Binding

Every near-LOD model in this case had one `body` node with an identity local transform. Destination coordinates were in body-local space, so `childId = "body"` was appropriate. Fifteen vehicle models had 180-degree root rotations; binding put text, body, and display on the same transform chain.

Do not assume another vehicle uses `body`. Verify its actual node name, local transform, hierarchy, and coordinate space. Convert text into target-node local space when transforms are nonidentity to avoid duplicate rotation or translation. Do not bind to scrolling or visibility-animated display children, which would animate the text too.

Source coordinates can also be wrong. In `e2_0_as/01.mdl` and `ba.mdl`, source label X was approximately `-7` while the display's local center was `2.805`. Mesh vertices and equivalent `fr/08` layouts supported correcting the two sides to X `2.71/2.89`. These numbers apply only to those two models, not every E2.

## Separate Offline Geometry from Runtime Validation

At minimum, verify:

1. Source/final destination counts match. Remove `NAME` or other labels only with explicit evidence; absence of `labelList` is not a pass condition.
2. Original and converted physical rectangle corners agree, with explicit exceptions for repaired source errors.
3. Accumulate root/body transforms and compare text corners with actual `.msh.blob` display vertices. Cover both sides and rotated cars; text must stay inside the display.
4. Preserve scrolling textures, materials, animations, and physical bounds. Inspect labels inside the final ZIP, not only the work directory.
5. Repeated runs do not keep changing assets. Fault cases must detect deleted labels, retained old dimensions, removed body bindings, and off-screen placement.
6. Inspect font position and clipping in Model Editor, then station names and updates in game on a line with a next stop. Editor blankness without a route context alone does not prove runtime failure.

The case's E2 set covered 74 models / 148 destinations; E5/E6/H5 covered 21 models / 42 destinations. Offline geometry and resource checks passed and all four fault categories were rejected. Screenshots were available, but computer-use clicks failed with `windowNotFoundAtPosition`, preventing final rendering validation. Repaired-package game and Windows results still required retesting. Do not label this method runtime-verified.

Project-local helpers were `tools/vehicle_destination_labels.py` for restoration and `tools/check_destination_labels.py` for independent geometry checks. They depend on that project's asset/mesh utilities and are not standalone bundled skill scripts.

## Whole-Display Disappearance: Check Material Time Gates

The installed `rendering/programs/shaders/mat/fs/normal/emissive.fs` discards entire emissive surfaces outside a time range. `properties/emissive_scale.prop.lua` in `rendering/properties.zip` defaults `fromTime/toTime` to `-1/-1`, interpreted by the shader as 20:00–06:00. For displays intended to remain visible all day with state controlled by geometry animation, explicitly set `params.emissive_scale.fragmentProperties[1].fromTime = 0` and `toTime = 24`, then verify day/night and animation switches.

Do not edit materials based only on blank destinations. When the service-type texture is visible but station text is missing, check labels first. Do not force ground-illuminating TF3 SPOT lights on all day because of this display issue. The user later attributed this case's lamp anomaly to game loading, so “all lamps disappeared” is not a reproduced material-defect result.
