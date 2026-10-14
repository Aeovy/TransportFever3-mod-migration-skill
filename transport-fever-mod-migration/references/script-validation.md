# Offline Script Validation, Regression, and Delivery

Use with [Script Migration](script-migration.md) and [React GUI](tf3-react-gui.md). Last checked: 2026-10-04. Resolve command paths from the current installation and work directory rather than copying a case study's machine paths.

## 1. Define What Each Check Proves

| Layer | Detects | Does not prove |
| --- | --- | --- |
| JSON, paths, exports | Manifest, entry points, encoding, case, duplicate IDs, missing dependencies | Successful engine loading |
| Lua `loadfile` / `luac -p` | Syntax of checked `.lua` files | Valid Teal, working callbacks, GUI contracts |
| Teal parsing and Lua generation | Teal syntax and transpilation to the selected Lua target | Complete type correctness or all TF3 APIs |
| Teal checking with complete definitions | Types, undefined variables, signatures | Native node categories, rendering, save behavior |
| Constrained host callbacks | Modeled imports, entries, layout rules, open/refresh/close | Real engine userdata, C++ transformer, complete simulation |
| Target game's style parser | Actual selector parsing and lost class/ID filters | Native matching, layout, screen appearance |
| Authorized game operation | Actually covered loading, base UI, windows, data, saves | Untested versions, systems, or scenarios |
| ZIP CRC and SHA-256 | Transfer integrity and package identity | Correct mod behavior |

Model Editor validates model assets, not this main-game React GUI. Mark script-only mods `not applicable`; starting Model Editor is not GUI testing.

When game launch is prohibited, do not bypass the restriction with background processes, Steam URIs, hot reloads, or other routes. Continue offline checks, record game results as `not run`, and provide concrete remaining test steps.

## 2. Fix Inputs and Tool Provenance

Preserve the source and use read-only inventory with `--hash` for a before snapshot. Edit independent copies. To prove preservation, create an after snapshot and compare file lists and hashes; comparing a report with itself proves nothing.

Record API provenance, plugin virtual entry, revision, tested module/style hashes, and actual commands. Helper output must also state that native rendering was not tested. Read dependencies locally; do not bundle native game source or downloaded third-party compiler copies in the skill.

Record the actual Teal compiler version and hash. This does not establish TF3's bundled compiler version. Verify downloads are Lua source rather than an HTML error or partial file; record other versions separately.

Prepare the offline workspace using task-specific paths:

```sh
skill_root='/path/to/transport-fever-mod-migration'
tf3_root='/path/to/Transport Fever 3'
probe_dir='/path/to/work/script-probes'
mkdir -p "$probe_dir"
unzip -p "$tf3_root/base/content/gui.zip" gui/main/stylesheetutil.lua \
  > "$probe_dir/stylesheetutil.lua"
```

If the compiler is missing, obtain it from the official repository and check its hash and source before execution:

```sh
curl --fail --location --connect-timeout 5 --max-time 30 \
  --header 'Accept: application/vnd.github.raw+json' \
  'https://api.github.com/repos/teal-language/tl/contents/tl.lua?ref=v0.24.8' \
  -o "$probe_dir/tl.lua"
shasum -a 256 "$probe_dir/tl.lua" "$probe_dir/stylesheetutil.lua"
```

The parser extracted from the case study's local `gui.zip` had SHA-256 `411a00603da7bcd11b242395e615129109e4ff64237bd903b6cf7f3c22026a23`. It identifies that version only; other game versions need not match.

Check `.lua` descriptor syntax separately; do not pass `.tl` to `luac -p`. For GUI/script migrations, build constrained checks around actual resource entries and host contracts. Do not use a mock host where every method returns success.

## 3. Targeted Regression and Native GUI Tests

First demonstrate that a new checker detects its intended defect using a historical failure or minimal temporary faulty copy. Verify the actual error before testing the repair. Missing files, failed downloads, or arbitrary nonzero exits do not count as successful defect detection.

Choose game tests based on implemented features:

1. Fully replace the old mod, confirm actual `modId`, revision, and resource hashes, and rule out same-ID shadow copies.
2. After enabling, inspect the original interface, window size/position, and mouse focus for leaked styles.
3. Exercise open, close, reopen, refresh, zoom, and error paths. Report only covered scenarios.
4. When persistent state or simulation logic was added, test pause/resume, new game, save/load, map changes, event deduplication, and state upgrades.
5. Verify separately on the target Windows version; macOS offline/editor results do not substitute for Windows game results.

For reload limits, repair the cause before an authorized tester restarts. Keep real stacks, versions, and screenshots; do not clear logs or suppress exceptions and claim success. A purely informational window with no persisted state does not need an invented simulation lifecycle or its tests.

## 4. Package the Tested Source Directory

Use the [packaging helper](../scripts/package_mod.py) with an explicit source and external output:

```sh
uv run --with 'pydantic>=2.11,<3' --with 'pillow>=11,<13' python \
  "$skill_root/scripts/package_mod.py" \
  --mod /path/to/work/my_mod \
  --archive /path/to/dist/my_mod.zip
```

The helper requires `mod.json` and `content/`; visible mods also require a decodable `_metadata/0.png`. See [Cover Migration](mod-cover.md) for conversion and explicit exceptions. It writes a single mod root, verifies ZIP CRCs, and creates `.zip.sha256` and `.package.json` sidecars. It excludes `.DS_Store` / `__MACOSX` and rejects file symlinks and hidden files. It cannot identify every development log, cache, or incorrect asset; clean the delivery source first.

After logic/style changes, increment revision according to project rules, rerun affected checks, and package that same directory. Extract into a fresh directory, compare file lists and hashes, check root nesting, and rerun entry/style checks on extracted content when needed. The installed copy must match the tested files.

An existing ZIP is not evidence that it was rebuilt. Report its final SHA-256. Never combine an old ZIP, later source edits, and stale validation results. Do not recreate generated directories explicitly deleted by the user unless the current task needs them and this has been explained.

## 5. Report Fields and Statuses

Distinguish agent offline results, user-reported observations, and uncovered features. Replace the example values with actual evidence:

```json
{
  "revision": 4,
  "api_source": "target installation definitions and shipped GUI",
  "script_sha256": "record actual digest",
  "checks": {
    "teal_parse_and_generate": "passed",
    "full_teal_typecheck": "not_run",
    "host_contract_subset": "passed",
    "shipped_style_parser": "passed",
    "native_gui": "not_run",
    "model_editor": "not_applicable",
    "windows_game": "not_run"
  },
  "user_reported": [],
  "implemented": [],
  "partial": [],
  "not_implemented": [],
  "package": {"path": "actual path", "sha256": "actual digest"}
}
```

Every pass requires command or observed-operation evidence. Retain failure reasons and state unrun coverage. Commit substantive tool/template/documentation stages using explicit paths in Git projects and preserve unrelated changes. Publishing is outside ordinary migration authorization.
