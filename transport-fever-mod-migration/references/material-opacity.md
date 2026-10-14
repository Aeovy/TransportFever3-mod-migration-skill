# Opacity and Material Classification

Use this reference when nominally solid bodies look frosted, background shows through the model, or glass/windows render incorrectly. Inspect material type, alpha, map/sampler bindings, and depth/sorting together. Changing only `sorted` or the material type rarely isolates the problem.

## Diagnosis

1. Follow each model/LOD mesh reference to the exact affected `.mtl`. Narrow the problem by viewpoint and livery rather than editing every similarly named material.
2. Compare TF2 and TF3 `type`, `map_albedo`/`map_albedo_opacity`, samplers, `alpha_test`, `sorted`, depth/normal-write settings, and normal/MGA references.
3. Inspect the alpha of the referenced texture, including UV islands and atlas regions. Whole-image min/max values cannot classify a face when an atlas mixes solid panels and windows.
4. Classify actual surfaces as solid shells, separate transparent glass, or shared solid/glass atlases. Filenames are clues, not substitutes for model and UV evidence.
5. Apply the smallest repair in a copy, check fields/references, package, and retest on the platform where the user reported the issue. Record revision, material coverage, and results. Editor preview cannot replace in-game sorting/occlusion checks.

## Conversion Rules

| Surface | Typical settings | Verify |
| --- | --- | --- |
| Fully opaque | `PHYSICAL` or normal-mapped `PHYSICAL_NRML_MAP`; `map_albedo` + `albedoTex` | Faces need no alpha cutouts; retain required normals, MGA, two-sided and lighting parameters |
| Transparent glass | `PHYS_TRANSPARENT` or its normal-mapped variant; `map_albedo_opacity` + `albedoOpacityTex` | Set alpha, sorting, and depth/normal writes according to the target definition and actual appearance |
| Shared solid/glass atlas | Choose from UVs and shader alpha/cutout semantics | Prefer splitting materials in the source project; forced opacity may seal windows, while cutout replaces continuous transparency with coverage |

When changing `PHYS_TRANSPARENT*` to `PHYSICAL*`, also migrate `map_albedo_opacity` to `map_albedo` and `albedoOpacityTex` to `albedoTex`. Changing `type` alone leaves incompatible bindings. Retain required `map_normal`, `map_metal_gloss_ao`, and other references; do not extend an opacity repair into unrelated lighting, normal, two-sided, or texture edits.

`sorted` controls transparent draw order, not whether a material is solid. Enabling it everywhere can place entire bodies on the transparent path; disabling it blindly for glass can break occlusion. `cutout` provides threshold coverage, not continuous semitransparent glass.

## Verified Case: CR200J Frosted Bodies on Windows

The first migration loaded on Windows but bodies looked frosted and exposed the background. Many solid parts retained `PHYS_TRANSPARENT*`; some atlases had alpha 125–255 and separate glass was semitransparent. Static data alone did not identify a unique shader cause.

The first repair moved mostly solid materials to opaque shaders, used cutout for mixed atlases, and retained transparent glass. User screenshots still showed small see-through areas. The final repair changed six main body-atlas materials to `PHYSICAL` / `PHYSICAL_NRML_MAP` with matching `map_albedo` + `albedoTex`, retaining separate glass and cutout on other mixed parts. Textures, UVs, and models were unchanged. The user confirmed that this revision completely resolved the reported body transparency in the Windows game.

That result applies to these six CR200J materials and their model/UV combinations. Neither `_body_` filenames, alpha ranges, nor shader replacements are automatic rules for other mods. Some models genuinely render windows through the same atlas alpha. Locate mesh references and UVs first, then select shaders and verify glass in the target game.

## Sources

- [TF3 material resource type](https://wiki.transportfever3.com/doku.php?id=modding:general:resourcetypes:mtl)
- [CR200J case history](cr200j-case-study.md)
