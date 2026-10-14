# Script Migration: Responsibilities, Registration, and State

Last checked: 2026-10-04. Determine interfaces from the target installation's definitions, actual callers, and official examples together. See [React GUI](tf3-react-gui.md) for implementation and [Script Validation](script-validation.md) for checks and delivery.

## 1. Inventory Behavior Before Choosing a Route

Read the original `mod.lua`, `res/config/game_script`, helper scripts, styles, imports, and event entry points. Record user actions, defaults, outcomes, refresh rates, saved state, resource modifications, and third-party dependencies. Split large scripts by responsibility instead of translating line by line along old file boundaries.

| TF2 responsibility | TF3 entry point | Behavior to preserve or explicitly mark unmigrated |
| --- | --- | --- |
| Load parameters, filtering, configuration changes | Script references in `mod.json` and the appropriate load stage | Default switches, resource visibility, modification order |
| Simulation updates, entity operations, runtime events | `.gs.lua` descriptors and `.script.lua` / `.script.tl` callbacks | Frequency, commands, deduplication, saved state |
| Information display or GUI operations | React extension points and GUI modules | Buttons, windows, clicks, closing, refresh |
| Simulation/GUI coordination | `GameScriptWithGui` state and event channels | Cross-context permissions, serializable data, asynchronous results |
| Descriptor generation and fixed constants | Verifiable static definitions or generators | Source-equivalent values and references |

Mark each feature `implemented / partial / not implemented`; successful loading does not pass the whole inventory. Reconstructing CR200J helper constants does not constitute a general complex-Lua converter.

## 2. Collect Local Evidence

Prefer `rg` for definitions, `unzip -Z1` for member listings, and `unzip -p` for read-only extraction. Save extracted data in the work directory; do not modify shipped archives.

| Target installation location | Purpose |
| --- | --- |
| `api/tealdef/api/{engine,res,gui,type}.d.tl` | Queries, resources, camera, descriptors, ScriptRef |
| `base/tealdef/scripts/gamescript.d.tl` | Actual lifecycle and state permissions |
| `base/tealdef/scripts/{react,builtin}.d.tl` | Recipes, native components, window APIs |
| `gui/main/main_mod_button_area.tl` in `base/content/gui.zip` | GUI extension point and parent layout |
| `gui/main/{react,builtin,stylesheetutil}.lua` in the same ZIP | Registration, plugin ordering, style parsing |
| `arrivaltracker.gs.lua` and its module in `base/content/game_mechanics.zip` | Official simulation, initialization, and event examples |

Recheck signatures and callers after version changes. When documentation summaries disagree with implementation, record the discrepancy and follow the actual call chain rather than selecting the source that favors existing code.

## 3. Physical Paths, Virtual References, and Exports

For physical file `content/gui/main/example.script.tl` in `my_mod`, a function reference is:

```text
my_mod::/gui/main/example.script@ExampleButton
```

The virtual path omits `content/` and `.tl`. The name after `@` must exist in the returned module table. `::/` refers to the base game and `my_mod::/` to the named mod. Case must match.

Resource descriptors such as `.res.lua` and `.gs.lua` return definitions through `data()`. Ordinary script modules return their module table directly; do not wrap every TF3 file in `data()`:

```teal
local mod = {}
-- Define the functions actually referenced by the current descriptor here.
return mod
```

An ordinary module has no automatically invoked lifecycle of its own. A descriptor or another module must reference specific exported functions. Map `mod.json`, directory names, virtual resources, plugin exports, recipe names, and window IDs as separate identifier layers.

## 4. Mod Load Stages

`mod.json` can reference load functions in `.script` modules. This is a field fragment, not a complete manifest:

```json
{
  "preRunScript": {"fileName": "my_mod::/mod.script@preRunFn"}
}
```

The [official load-script documentation](https://wiki.transportfever3.com/doku.php?id=modding:general:modscripts) lists these business parameters:

| Function | Documented business parameters |
| --- | --- |
| `preRunFn` | `configDict, allModParams, baseConfig` |
| `runFn` / `postRunFn` | `configDict, allModParams` |

**These lists alone do not establish argument positions.** The shipped `urbangames_no_costs/content/mod.script.tl` has `captureParams` before these `preRunFn` arguments. Inspect `ScriptRef`, the caller, and same-version examples to determine how captured parameters are supplied. Do not remove the first argument based on a summary or assume captures are always appended.

Resource availability differs by stage. For TF2 modifiers such as `loadConstruction`, verify TF3 registration, schema, and execution order rather than moving the old modifier unchanged.

Option `defaultIndex` is zero-based while Lua arrays usually start at 1. Convert option indices where required, not numeric values in general. Check defaults, user choices, saved parameters, and combinations; never globally add one to all numbers.

## 5. Runtime Game Scripts

The current `GameScriptDesc` references module functions with `updateScript`, `postUpdateScript`, `handleEventScript`, `guiUpdateScript`, and `guiHandleEventScript`:

```lua
function data()
  return {
    updateScript = { fileName = "my_mod::/example.script@update" },
    handleEventScript = { fileName = "my_mod::/example.script@handleEvent" },
  }
end
```

Parameters in the local definitions and [official GameScript interface](https://wiki.transportfever3.com/script-doc/content/scripts/gamescript.html):

| Callback | Argument order | Context and state |
| --- | --- | --- |
| `update` | `userParams, state, dt` | Simulation state |
| `postUpdate` | `userParams, state, dt, updateResult` | After simulation update |
| `handleEvent` | `userParams, state, src, id, name, param` | Simulation event |
| `guiUpdate` | `userParams, readonlySimState, guiState` | Read-only simulation state; no `dt` |
| `guiHandleEvent` | `userParams, readonlySimState, guiState, src, id, name, param` | GUI event |

An older reference incorrectly listed `loadGame`, `init`, `updateSimulation`, `updateGui`, `saveState`, and `viewState` as members of this interface. Current definitions do not support that list. Do not mechanically map TF2 `load/save/update` using those names.

Use current `GameScriptState.get/set`, corresponding native methods, and actual event APIs. Design each concern explicitly:

- Initialization: follow official `initStateIfEmpty` examples; handle empty state, new maps, and old saves separately. Record the state schema version and required upgrades.
- Permissions: GUI reads simulation state without writing read-only objects. Use supported commands/events for game-data changes.
- Data: save serializable business values; do not persist native window references, closures, or transient GUI objects directly.
- Events: verify subscription and exit conditions so hot reloads or reopened windows do not duplicate subscriptions, entities, or commands.
- Timing: asynchronous results can outlive windows or maps; verify validity before executing callbacks.

Syntax checks cannot prove lifecycle behavior. Actual new-game, save, load, event, and reload tests are required. If game launch is disallowed, deliver lifecycle work as pending verification.

## 6. Implement GUI and Data in Verifiable Stages

Start with one button in a valid extension point, then an empty window, followed by data, refresh, styles, and additional views. At each step, check registration, returned node category, arguments, and scope so startup failures remain diagnosable.

If an overlay or click API has not been confirmed, mark it `not implemented / suitable interface not yet found` and continue investigating supported approaches. This does not establish that TF3 cannot implement it. Do not keep a superficially working UI through unrelated global styles or swallowed exceptions.

## 7. Unreadable Scripts and Platform Dependencies

Lua header `1b 4c 75 61` identifies standard bytecode; the next byte, such as `0x52`, indicates Lua 5.2. Bytecode is not plaintext source, and version, ABI, or host-API differences can break compatibility. Read-only inventory must not execute unknown bytecode.

For modules supplying only provable constants, see [CR200J](cr200j-case-study.md). Irreplaceable algorithms require authorized source or an author-provided version. Verify native DLLs, plugins, and binary modules per platform. Pure Lua/Teal source is usually portable, but Windows cannot be marked passed without testing the target Windows game.

## Official Sources

- [Load scripts and parameters](https://wiki.transportfever3.com/doku.php?id=modding:general:modscripts)
- [Resource syntax and imports](https://wiki.transportfever3.com/doku.php?id=modding:general:syntax)
- [GameScript interface](https://wiki.transportfever3.com/script-doc/content/scripts/gamescript.html); check actual calls against installed definitions too.
