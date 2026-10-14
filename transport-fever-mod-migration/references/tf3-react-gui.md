# TF3 React GUI: Registration, Node Structure, and Style Isolation

Last checked: 2026-10-04. Use this reference when rewriting TF2 `api.gui.comp` / `api.gui.layout` code or diagnosing migrated Lua, layout, and base-interface failures. Read [Script Responsibilities](script-migration.md) first; see [Script Validation](script-validation.md) for tests.

## 1. Import Modules: Type Names Are Not Runtime Names

Local GUI examples use `ug_require` and Teal assertions:

```teal
local react = ug_require "::/gui/main/react.lua" as React
local builtin = ug_require "::/gui/main/builtin.lua" as Builtin
local main_mod_button_area = ug_require "::/gui/main/main_mod_button_area.tl" as MainModButtonArea
local game_react_globals = ug_require "::/gui/main/game_react_globals.tl" as GameReactGlobals
```

Call `react.RegisterPluginRecipe` and `builtin.BoxLayout`, not `React.RegisterPluginRecipe` or `Builtin.BoxLayout`. `as React` annotates the type and does not create a global `React`.

Confusing the type with a runtime global produces a nil `React`. Running `loadfile` only on `.lua` files does not check `.script.tl`. Parse Teal, inspect generated Lua bindings, and execute the actual module entry under a constrained host. Unknown-global checks in a complete type environment are also useful; keep their coverage distinct.

## 2. Register Through Extension Points

The installed `gui/main/main_mod_button_area.tl` provides `MainModButtonAreaExtension`. Example plugin descriptor:

```lua
function data()
  return {
    type = "react-plugin ::MainModButtonAreaExtension",
    data = {
      filePath = "my_mod::/gui/main/example.script@ExampleButton",
      order = 0,
    },
  }
end
```

Register with `react.RegisterPluginRecipe(main_mod_button_area.MainModButtonAreaExtension, recipeName, fn)` and return `{ ExampleButton = registeredRecipe }` directly. The descriptor path, exported key, and actual recipe must agree. The installed `react.getPlugins` sorts by `desc.order`; do not substitute an unused `priority` field.

Choose an appropriate extension point from installed definitions and its parent layout. Adding a button should not replace `GameUIRoot`, alter all base windows, or copy an entire native GUI file.

## 3. Node Categories: Ordinary Recipes Return Layouts

TF3 `TreeNodeId` cannot statically express all native node-category constraints. The native transformer still validates relationships among recipes, layouts, and widgets. Static typing alone does not prove those contracts.

Use a layout as an ordinary plugin recipe's root:

```teal
return builtin.BoxLayout{
  orientation = builtin.type.Orientation.Horizontal,
  children = {
    builtin.Button{
      content = builtin.TextView{ text = _("Example") },
      onClick = handleClick,
    },
  },
}
```

`builtin.Component.layout` also requires a layout. Wrap widgets in `BoxLayout` or another suitable layout before passing them to `Component`. Use an explicit vertical layout to contain a window's components.

These are observed contracts for these recipes and slots, not proof that every extension returns `BoxLayout`. Check definitions, native examples, and callers for another extension point. A constrained host validates only modeled contracts and cannot replace the C++ transformer.

## 4. Windows: Native Wrappers and Containers

Installed examples such as `DialogWindow` wrap `builtin.Window` with `RegisterWrapperRecipe`. This structural fragment still requires feature-specific parameters and event logic:

```teal
local ExampleWindow = react.RegisterWrapperRecipe(
  "ExampleWindow", builtin.Window,
  function(param : ExampleWindowParam) : TreeNodeId
    return builtin.Window{
      meta = { class = "example-window" },
      id = "example.window",
      title = _("Example"),
      onClose = param.onClose,
      content = builtin.BoxLayout{
        orientation = builtin.type.Orientation.Vertical,
        children = {},
      },
    }
  end
)
```

On open, obtain `game_react_globals.getDefaultWindowContainer()`, check `nil` and `hasExpired()`, then access `get():getApi()`. Use `addSingletonWindow` for repeated clicks and the same API to remove that recipe's window on close.

Installed API comments state that an existing singleton does not automatically replace parameters or change visibility. If refresh needs either, verify the API and choose between updating the existing window and removing/re-adding it. Do not assume singleton calls refresh data.

Fetch business data on open or explicit refresh rather than scanning on every recipe rebuild. The container controls closure lifetime; do not reuse expired references after closing or changing context. Recheck validity when asynchronous results arrive.

## 5. Style Classes Use `!`

TF3 `.css.lua` uses `stylesheetutil`, whose selectors are not browser CSS. The current parser recognizes `!class`, not `.class`:

| Target | Supported form |
| --- | --- |
| Recipe itself | `R::ExampleButton` |
| This mod's window | `Window!example-window` |
| This mod's action bar | `BoxLayout!example-actions` |
| Owned component ID | `#example-preview` |
| Action bar within window | `Window!example-window BoxLayout!example-actions` |

Components still use `meta = { class = "example-window" }`, without `!` in the value. Selectors and metadata use different syntax.

`Window.example-window` may parse without an error but lose its class filter, becoming plain `Window`. Size, spacing, and alignment then leak to other interfaces. `.class` can likewise degrade to an unfiltered layout selector.

Repair ownership constraints on every rule. Do not compensate with base-interface resizing, offsets, or more global rules. Geometry properties especially need scope checks.

The current class pattern is `[%a%d%-]`; use ASCII letters, digits, and hyphens. Do not assume underscores or other characters work. ID parsing differs and may discard the element before `#id`. A regex showing that a selector appears prefixed is insufficient.

## 6. Inspect Actual Parser Output

Read `gui/main/stylesheetutil.lua` from the target's `base/content/gui.zip` and use it to execute the mod's `.css.lua` `data()`. Inspect every returned rule's `levels`: were class, ID, and recipe conditions retained, or did a level become just `Window` / `BoxLayout`?

An owned-window condition should resemble `{ element = "Window", classList = { "example-window" } }`. Incorrect `.class` syntax loses `classList`. Descendant rules must retain the intended ancestor or target constraints. Judge each rule's semantics; valid rules need not share one fixed prefix.

Run the real target parser in a minimal supporting environment and verify intended class/ID/recipe ownership for each rule. This does not implement full layout or rendering and cannot replace native GUI validation.

## 7. Diagnose by Failure Layer

| Symptom | First checks | After repair |
| --- | --- | --- |
| Nil `React` / `Builtin` | Imported locals, generated Lua, exports | Execute plugin loading and callbacks |
| `Recipe child must be a layout` | Root, wrapper, layout slots | Contract tests and native game transformation |
| Misplaced base UI or enlarged windows | Parsed styles, broad geometry rules | Inspect base interface before opening the mod window |
| Slow open/refresh | Scan frequency, asynchronous requests | Sampling counts and actual refresh time |
| No new window or stale data | Container validity, singleton parameters/visibility, closures | Open, close, reopen, refresh, context switch |

`Already automatically reloaded 3 times...` suppresses reloads after earlier failures; it is not the root cause. For `Failed during startup, don't try automatic reload`, inspect the following actual error. Fix the source, verify revision/package, and have an authorized tester fully replace and restart it. Do not trigger reloads or background game launches when the user prohibits game startup.

Do not hide registration failures with broad `pcall` blocks or immediately blame cache for layout problems. Record stack virtual paths, functions, recipes, and package versions, then investigate each layer.
