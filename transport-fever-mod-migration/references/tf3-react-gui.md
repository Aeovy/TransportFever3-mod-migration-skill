# 三代 React GUI：注册、节点结构与样式隔离

最后核对：2026-10-04。本参考适用于 TF2 `api.gui.comp` / `api.gui.layout` 向 TF3 GUI 的重写，以及迁移后 Lua 错误、布局错误和主界面被影响的诊断。先读 [脚本职责](script-migration.md)，测试方法见 [脚本验证](script-validation.md)。

## 1. 导入模块：类型名称不是运行时名称

本机 GUI 示例采用 `ug_require` 与 Teal 类型断言：

```teal
local react = ug_require "::/gui/main/react.lua" as React
local builtin = ug_require "::/gui/main/builtin.lua" as Builtin
local main_mod_button_area = ug_require "::/gui/main/main_mod_button_area.tl" as MainModButtonArea
local game_react_globals = ug_require "::/gui/main/game_react_globals.tl" as GameReactGlobals
```

后续调用 `react.RegisterPluginRecipe`、`builtin.BoxLayout`，不能改用 `React.RegisterPluginRecipe` 或 `Builtin.BoxLayout`。`as React` 是类型标注，不会创建全局 `React`。

把 Teal 的 `as React` 当成运行时全局会导致 `React` 为 nil。只对 `.lua` 执行 `loadfile` 不能检查 `.script.tl`；必须解析 Teal、查看生成 Lua 的变量绑定，并在限定宿主里执行实际模块入口。完整类型环境下的未知全局检查也有价值，见验证参考中的覆盖区分。

## 2. 用扩展点注册插件，不替换根界面

本机 `gui/main/main_mod_button_area.tl` 提供 `MainModButtonAreaExtension`。插件资源描述符示例：

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

脚本用 `react.RegisterPluginRecipe(main_mod_button_area.MainModButtonAreaExtension, recipeName, fn)` 注册，并直接 `return { ExampleButton = registeredRecipe }`。资源的 `filePath`、导出表键与实际 recipe 必须对应。当前原生 `react.getPlugins` 按 `desc.order` 排序，不能凭习惯使用未读取的 `priority`。

从本机定义和父布局选择实际适合的扩展点。不要为了添加按钮覆盖 `GameUIRoot`、修改所有基础窗口或复制整个原生 GUI 文件。

## 3. 节点类别：普通 recipe 返回布局

TF3 的 `TreeNodeId` 类型不足以静态表达所有原生节点类别约束。原生变换器仍会检查 recipe、布局和 widget 的关系；静态类型通过不等于原生节点契约通过。

普通插件 recipe 的根节点应使用布局：

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

`builtin.Component.layout` 同样必须接布局。widget 要放进 `BoxLayout` 等布局后再交给 `Component`，不能直接把 widget 当作 layout。窗口内容用明确的纵向布局承载各个子组件。

这是本机这类 recipe 和 slot 的实际约束，不是所有扩展点统一返回 `BoxLayout` 的证明。移植到其他扩展点时查看其定义、原生示例和调用方。限定宿主测试也只能检查主动写入的契约，不能代替 C++ 变换器。

## 4. 窗口：使用原生 wrapper 与窗口容器

本机 `DialogWindow` 等实例以 `RegisterWrapperRecipe` 包装原生 `builtin.Window`。下面只是结构片段，参数和事件逻辑按目标功能的实际 API 设计：

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

打开时获取 `game_react_globals.getDefaultWindowContainer()`，先检查 `nil` 与 `hasExpired()`，再取 `get():getApi()`。使用 `addSingletonWindow` 管理重复点击，关闭通过该 API 删除这个 recipe 的窗口。

本机 API 注释指出，单例已存在时不会自动替换参数或改变可见性。若刷新需要替换参数或恢复可见性，先核实 API，再决定是更新现有窗口还是移除后重新添加；不可依赖单例自动更新数据。

业务数据在打开或显式刷新时获取，避免 recipe 每次重建都执行昂贵扫描。窗口闭包的寿命由窗口容器决定；关闭或上下文变化后不复用过期引用。对异步流程，在结果到达时再次核实有效性。

## 5. 样式：TF3 的类选择器使用 `!`

TF3 `.css.lua` 使用游戏的 `stylesheetutil`，其选择器不是浏览器 CSS。当前解析器识别 `!class`，没有将 `.class` 识别为类条件：

| 意图 | 当前可用形式 |
| --- | --- |
| recipe 本身 | `R::ExampleButton` |
| 本模组的窗口 | `Window!example-window` |
| 本模组操作栏 | `BoxLayout!example-actions` |
| 自有组件 ID | `#example-preview` |
| 窗口里的操作栏 | `Window!example-window BoxLayout!example-actions` |

组件仍写 `meta = { class = "example-window" }`，值里面没有 `!`。样式选择器与 meta 值是两种语法。

如果把类选择器写成 `Window.example-window`，解析器可能不报错，却会把它解析为不带类条件的 `Window`；本应只作用于自有窗口的尺寸、间距和对齐就会泄漏到其他界面。`.class` 也可能退化为无类过滤的布局选择器。

修复必须恢复所有规则的所有权约束。不能以修改主界面尺寸、增加偏移或更多全局规则来补偿。尺寸、间距、对齐等几何属性尤其需要检查作用域。

当前解析器的类名模式使用 `[%a%d%-]`，自有类名采用 ASCII 字母、数字和连字符；下划线等字符不要未经核实直接使用。ID 的解析规则不同，当前实现还可能去掉 `#id` 前的元素部分。不能仅用正则检查选择器字符串“看起来有前缀”。

## 6. 实际解析样式，检查解析结果

读取目标版本 `base/content/gui.zip` 的 `gui/main/stylesheetutil.lua`，用它执行模组 `.css.lua` 的 `data()`。核对每条返回规则的 `levels`：类、ID、recipe 条件是否实际保留下来，是否某一层仅剩 `Window` / `BoxLayout`。

正确的单窗口条件应解析为类似 `{ element = "Window", classList = { "example-window" } }`。错误 `.class` 形式会丢失 `classList` 的内容。后代规则应保留自有祖先或目标的条件；规则语义必须逐条判断，不能要求所有合法样式都有相同固定前缀。

应加载目标版本的真实解析器，用最小辅助环境执行当前模组的 `.css.lua`，检查每条规则是否保留预期的类/ID/recipe 所有权。检查器没有实现完整布局计算或渲染，不能代替原生 GUI 验证。

## 7. 按错误层级定位

| 症状 | 先查什么 | 修复后验证 |
| --- | --- | --- |
| `React` / `Builtin` 为 nil | 导入局部变量、Teal 生成代码、模块导出 | 执行插件加载和回调 |
| `Recipe child must be a layout` | recipe 根节点、wrapper、各个 layout slot | 契约测试与游戏原生变换 |
| 主界面错位、所有窗口变大 | 实际解析的样式、广域几何属性 | 启用后先检查原界面，再打开自有窗口 |
| 打开/刷新卡顿 | 业务数据扫描频率和异步请求 | 采样计数、实际刷新耗时 |
| 点击按钮无新窗口/数据陈旧 | 容器有效性、单例参数/可见性、闭包寿命 | 打开、关闭、重开、刷新、上下文切换 |

`Already automatically reloaded 3 times...` 是前面反复失败后的重载抑制，不是根因。`Failed during startup, don't try automatic reload` 同样优先看后续实际错误。修复源文件、确认 revision 和安装包，再由获准的测试者完整替换和重启；用户禁止启动游戏时 agent 不触发重载或后台启动。

不要用大范围 `pcall` 忽略注册错误，或把 UI 错位直接归因于安装缓存。记录错误栈指向的虚拟路径、函数、recipe 和实际包版本，逐层排除。
