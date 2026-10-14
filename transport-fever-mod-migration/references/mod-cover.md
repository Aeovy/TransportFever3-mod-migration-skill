# Mod Management Cover Migration

Last checked: 2026-10-06, against official Mod Definition documentation and locally installed TF3 mods.

TF3 grid cards use `_metadata/0.png` under the mod root. Detail pages can use numbered images such as `1.png` and `2.png`. The recommended size is 1920×1080. TF2 root images such as `image_00.tga`, `image_00.jpg`, and `workshop_preview.jpg` do not automatically replace this TF3 presentation asset. A card may show a question mark even when models, purchase icons, and `_metadata/modinfo.json` are valid.

## Repair and Migration

1. Find `image_00.*` in the source, then `workshop_preview.*` if missing. Inspect the image and choose one representative of the final contents for merged packages. Preserve author text and marks; do not generate a replacement for an existing cover. If the source has no image, use an authorized screenshot of the actual model or report the missing source.
2. Decode and save the image as `_metadata/0.png`; changing the extension is insufficient, and `content/_metadata/` is the wrong location. Preserve aspect ratio and pad non-16:9 images instead of cropping text or stretching vehicles. The helper converts format and size without generating new imagery:

   ```sh
   uv run --with 'pydantic>=2.11,<3' --with 'pillow>=11,<13' python \
     "$skill_root/scripts/migrate_cover.py" \
     --source /path/to/original_tf2_mod --mod /path/to/final_tf3_mod \
     --report /path/to/work/cover.json
   ```

   Set `skill_root` to this skill's directory. To choose a specific source image, replace `--source` with `--image /path/to/existing/image`.
3. Decode the final PNG again and verify dimensions, SHA-256, and ZIP member path. Increment the output revision when updating the cover, preserving `modId` and vehicle/script assets. `package_mod.py` blocks missing covers for visible mods by default; use `--allow-missing-cover` only for an explained exception. Hidden helper mods do not need an unnecessary cover.
4. Within the permitted scope, inspect the real main-game mod grid and relevant detail pages. Model Editor purchase icons do not prove management-card rendering. Record screenshots/version, or `not run`. For stale question marks, restart and check same-ID `staging_area` copies, actual load location, and filename case. Do not begin by deleting saves or all caches.

For a package missing only its cover, a merge patch containing `modId/_metadata/0.png` is acceptable if clearly labeled as incomplete and not independently enableable. Update the full ZIP, CRC/SHA-256, and report too, and confirm other files are unchanged apart from revision metadata.

Official source: [Mod Definition](https://wiki.transportfever3.com/doku.php?id=modding:general:moddefinition).
