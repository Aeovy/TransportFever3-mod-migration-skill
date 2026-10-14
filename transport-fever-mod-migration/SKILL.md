---
name: transport-fever-mod-migration
description: "Migrate Transport Fever 2 asset or scripted mods to Transport Fever 3, diagnose vehicle, material, Lua/Teal, React GUI, and macOS/Windows compatibility issues, and assess migration feasibility."
---

# Transport Fever 2 to 3 Mod Migration

Produce an independent TF3 mod and an evidence-based migration report. Use the installed game version, official documentation, and the actual source package as the basis for every decision. For model migrations, open the final output in the target Model Editor and inspect the appearance with textures loaded. For script-only mods, inspect resource registration, callbacks, GUI, styles, and state; mark Model Editor validation as not applicable. Never describe offline success as game or Windows success.

## Getting Started

1. Confirm the source package, target game version, work directory, and the validation scope the user permits. Use information already provided; if the install path is missing, inspect the local machine first. If the user does not want the game opened, continue offline and record game validation as `not run`. Treat Model Editor and the main game as separate permissions.
2. Inventory `mod.lua`, `res/`, models, materials, meshes, textures, formations, and scripts. Decide whether the package is an asset mod or contains runtime logic. Preserve the original package and apply every fix in a copy.
3. For asset conversion, read [Migration Workflow](references/migration-workflow.md). For runtime logic, read [Script Responsibilities and Interface Migration](references/script-migration.md); for GUI registration, node, or layout problems, read [TF3 React GUI and Style Isolation](references/tf3-react-gui.md); for offline validation, regression, and packaging, read [Script Validation and Delivery](references/script-validation.md). Read only the references relevant to the issue so that a case-specific implementation is not mistaken for a universal conversion rule.
4. For unreadable files, incorrect textures, wheel or LOD errors, missing dependencies, misplaced dynamic text, or editor failures, read [Troubleshooting](references/troubleshooting.md). For frosted opaque surfaces, background visible through the body, or materials shared by opaque and glass regions, also read [Material Opacity and Classification](references/material-opacity.md). For similar protected scripts or CR200J assets, consult [the CR200J case study](references/cr200j-case-study.md); its fixes are not general conversion rules.

The included inventory script is read-only. Write its report outside the source package:

```sh
uv run --with 'pydantic>=2.11,<3' python \
  <skill directory>/scripts/inventory_mod.py /path/to/source_mod \
  --output /path/to/work/inventory.json --hash
```

The script checks directory layout, case and Unicode path collisions, duplicate DDS/TGA names, Lua bytecode, missing mesh companions, text encoding, and DDS headers. It does not execute Lua, decrypt data, modify the source package, or replace full asset or game validation. `--hash` is optional; when enabled it records SHA-256 snapshots of source files.

## Key Migration Constraints

- Prefer the target Model Editor's official TF2 conversion support, then compare the result with the source package to restore metadata and dependencies. Convert one representative model first, verify the output directory and current/target mod, and only then convert in bulk.
- Build an explicit old-path to new-path map for final assets. Detect converted filename collisions before renaming and updating references. Filename normalization must not change animation or wheel-node names.
- `.msh.blob` is a binary mesh container, not proof of encryption. Handle Lua bytecode and genuinely unreadable geometry separately. Replace constants computed by a protected helper only when the mesh layout proves the replacement; otherwise preserve the blocker and state which source assets are required.
- Same-named DDS and TGA files may be different liveries. Assign unique target names before conversion. Check orientation, normal encoding, alpha, and mipmaps according to the actual material and toolchain; do not apply one flip or compression policy to every image.
- TF3 mod cards read `_metadata/0.png`; TF2 `image_00.*` and `workshop_preview.*` need explicit migration. When the cover is missing, the card shows a question mark, or a package is being prepared, read [Mod Cover Migration](references/mod-cover.md), and distinguish the management-page cover from vehicle purchase icons.
- Preserve vehicle performance, formation length, and facing unless the user requests a change. Disclose substitutes for missing textures or sounds. Adapt simulation Lua to the TF3 interfaces; moving files or changing extensions is insufficient.
- Destination displays may combine livery textures with dynamic destinations. Do not delete `metadata.labelList` merely because a scrolling display mesh or texture exists. Preserve and adapt `NEXT_STOP`, and remove `NAME` or other labels only when their role is confirmed. For blank, misplaced, or vehicle-name text, read [Dynamic Destination Labels](references/destination-labels.md) and inspect the final package, native layout dimensions, node binding, and actual mesh.
- Teal type names are not runtime module variables. Handle ordinary React recipe roots and native window wrappers separately. TF3 style class selectors use `!`. Lua syntax checks cannot find host-contract or style-scope errors; see the GUI reference for concrete failures.
- A pure asset package produced on macOS may work on Windows, but editor validation cannot prove Windows runtime behavior. Check case, package paths, version dependencies, and platform-specific programs or plugins, and clearly mark unrun platforms.
- TF3 night lighting is a native feature. A TF2 lamp cover, emissive texture, or `emissive` material only makes the lamp appear to glow; it does not create a beam on the ground. Treat night lighting as a separate migration item and do not count material conversion as lighting migration.
- After changing materials or textures, reopen the final models from the output directory in Model Editor and inspect the loaded appearance of the body, interior, glass, lights, and representative near/far LODs. Cover every formation and each distinct material or livery, or inspect every model when the set is small. Reading `.mdl` files, checking paths, or seeing a conversion log is not a visual inspection.

## TF3 Night-Light Adaptation

For TF2 vehicles with lamps, complete these steps separately and record the coverage:

1. Find the actual powered cab, headlight mesh nodes, and existing on/off animations. Attach lights at the real lamp positions and bind them to the existing forward-light state; do not add an unrelated light to the body root.
2. Add TF3 native `SPOT` / `LIGHT` sources to the final `.mdl`, with plausible direction, range, intensity, cone, and bounds. Use TF3 night or bad-weather conditions and synchronize with `front_forward_parts_on/off` or the equivalent animation. Tune values to vehicle size in Model Editor rather than copying numbers from another vehicle.
3. Open the final output in both night-on and night-off states. Confirm a forward beam appears and disappears, and check the lamp material, body opacity, and near/far LODs for regressions. Cover each powered cab, livery, or distinct light definition; record `not run` when the editor cannot be opened.
4. In the report, distinguish an emissive material from actual illumination. List adapted models and light sources, animation bindings, key parameters, on/off screenshots or logs, and whether the main game and Windows were tested. Without beam evidence, do not call night lighting complete.

## Validation and Delivery

Record each permitted layer as `passed / failed / not run`, and state partial coverage separately:

| Layer | Required evidence |
| --- | --- |
| Mod presentation | Decoded final `_metadata/0.png`, package path, and a main-game mod-card screenshot; record separately when the main game was not run |
| Static checks | Definitions and encoding, resource references, mesh indices, texture formats, formations, and required script checks |
| Dynamic labels and displays | Source/final `NEXT_STOP` counts, dimensions, transforms, node bindings, and display rectangles; preserve livery textures and animation. Check placement in the editor and station-name updates on a line with a next stop; geometry checks do not replace rendering |
| Offline script checks | Actual Lua/Teal scope, resource entry points, constrained host callbacks, node structure, and style parsing; these do not replace native GUI rendering |
| Editor checks | Inspect final models with textures loaded from the output directory; cover formations, distinct materials/liveries, body, interior, glass, lights, and representative LODs; save paths, version, screenshots, or logs. Mark script-only mods not applicable |
| Game checks | Actual enablement, purchase/run, interaction, saves, and script lifecycle |
| Windows checks | Actual loading and runtime behavior on the target version |

Do not add runtime scripts to a pure asset package. Preserve valid module dependencies in scripted mods. LOD performance errors are validation failures; hiding logs or deleting distant levels does not make them pass.

Deliver the independent mod directory, installable ZIP, CRC/SHA-256 checks, and migration report. The report must state what happened to the original package, dependencies and substitutes, applicable Model Editor evidence, tested scope, unresolved issues, and next steps. If model migration could not be rendered or the editor was disallowed, mark it `not run` rather than complete. Keep native GUI and lifecycle work pending when it was not tested in game. In Git projects, commit substantive tool and text-definition stages; follow project conventions for binaries. A migration request does not authorize publishing to Mod Hub, mod.io, or another platform.

Read supporting references only when their issue applies. References were last checked on 2026-10-04; verify the local version when using them, especially editor output locations, script signatures, and validation thresholds.
