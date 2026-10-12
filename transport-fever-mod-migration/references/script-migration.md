# 脚本模组迁移：职责、资源注册与状态

最后核对：2026-10-04。以目标安装中的定义、实际调用方和官方实例共同确定接口。GUI 实现另读 [React GUI](tf3-react-gui.md)，检查与交付另读 [脚本验证](script-validation.md)。

## 1. 建立行为清单，再选择迁移路线

读取原 `mod.lua`、`res/config/game_script`、辅助脚本、样式、模块导入与事件入口。记录用户操作、默认参数、结果、刷新频率、保存状态、资源修改和第三方依赖。大型脚本按职责拆分，避免只按原文件边界逐行翻译。

| 二代职责 | 三代迁移入口 | 必须保留或明确未迁移的行为 |
| --- | --- | --- |
| 装载参数、过滤、配置修改 | `mod.json` 的脚本引用和适当装载阶段 | 默认开关、资源可见性、修改顺序 |
| 模拟更新、实体操作、运行事件 | `.gs.lua` 描述符及 `.script.lua` / `.script.tl` 回调模块 | 频率、命令、去重、存档状态 |
| 仅显示信息或操作 GUI | React 扩展点与 GUI 模块 | 按钮、窗口、点击、关闭、刷新 |
| 模拟与 GUI 联动 | `GameScriptWithGui` 状态及事件通道 | 端间权限、可序列化数据、异步结果 |
| 描述符生成、固定资源常量 | 可核实的静态定义或生成工具 | 与原包相同的值与引用 |

逐项标记“已实现 / 部分实现 / 未实现”，不要把“能加载”作为功能清单全部通过。CR200J 重建保护辅助脚本常量的经验不能推广为复杂 Lua 脚本转换器。

## 2. 收集本机证据

优先用 `rg` 查找定义，用 `unzip -Z1` 列表、`unzip -p` 只读提取 ZIP 成员。读取输出存到工作目录，不能修改游戏自带 ZIP。

| 目标安装中的位置 | 用途 |
| --- | --- |
| `api/tealdef/api/{engine,res,gui,type}.d.tl` | 数据查询、资源、相机、描述符与 ScriptRef |
| `base/tealdef/scripts/gamescript.d.tl` | 实际生命周期和状态权限 |
| `base/tealdef/scripts/{react,builtin}.d.tl` | recipe、原生组件及窗口 API |
| `base/content/gui.zip` 内 `gui/main/main_mod_button_area.tl` | GUI 扩展点及父布局 |
| 同 ZIP 内 `gui/main/{react,builtin,stylesheetutil}.lua` | 注册实现、插件排序、样式解析 |
| `base/content/game_mechanics.zip` 内 `arrivaltracker.gs.lua` 及对应模块 | 官方模拟脚本、初始化、事件实例 |

安装版本更新后重新核对函数签名与调用者。文档摘要和本机实现不一致时，写明差异并从实际调用链确定行为；不要只选择有利于现有代码的一份材料。

## 3. 分清物理路径、虚拟资源引用与模块导出

例如物理文件 `content/gui/main/example.script.tl`，在模组 `my_mod` 中的函数引用是：

```text
my_mod::/gui/main/example.script@ExampleButton
```

虚拟路径不包含物理 `content/` 前缀或 `.tl` 后缀。`@` 后的名称必须真实存在于模块返回表；`::/` 引用基础游戏，`my_mod::/` 引用指定模组。大小写必须一致。

`.res.lua`、`.gs.lua` 等资源描述符以 `data()` 返回定义；普通脚本模块直接返回模块表，不能把所有三代文件都包成 `data()`：

```teal
local mod = {}
-- 这里定义当前描述符实际引用的函数。
return mod
```

普通模块自身没有被自动调用的生命周期。描述符或其他模块必须引用导出的具体函数。`mod.json`、模组目录、虚拟资源、插件导出、recipe 名和窗口 ID 是不同层级，全部纳入路径映射。

## 4. 迁移模组装载阶段

`mod.json` 可引用 `.script` 模块中的装载函数。下面是字段片段，不能作为完整 manifest：

```json
{
  "preRunScript": {"fileName": "my_mod::/mod.script@preRunFn"}
}
```

[官方装载说明](https://wiki.transportfever3.com/doku.php?id=modding:general:modscripts) 列出的业务参数如下：

| 函数 | 文档中的业务参数 |
| --- | --- |
| `preRunFn` | `configDict, allModParams, baseConfig` |
| `runFn` / `postRunFn` | `configDict, allModParams` |

**这些列表不能单独确定实际函数参数位置。** 本机自带 `urbangames_no_costs/content/mod.script.tl` 的 `preRunFn` 在上述参数之前还有 `captureParams`。同时查 `ScriptRef`、实际调用方和同版本示例，确认捕获参数怎样传入；不能根据文档摘要删除第一个参数，也不能猜测它统一追加在末尾。

各阶段资源可用性不同。二代 `loadConstruction` modifier 等逻辑需要核对三代注册方式、资源 schema 和执行顺序，不能仅移动旧 modifier。

选项 `defaultIndex` 为零基，Lua 数组通常从 1 开始；只对选项索引做必要换算。实际数值参数不是数组索引。核实默认行为、用户选项、参数保存与开关组合，不全局替换“所有数字加一”。

## 5. 迁移游戏运行脚本

当前 `GameScriptDesc` 使用 `updateScript`、`postUpdateScript`、`handleEventScript`、`guiUpdateScript`、`guiHandleEventScript` 指向模块函数，例如：

```lua
function data()
  return {
    updateScript = { fileName = "my_mod::/example.script@update" },
    handleEventScript = { fileName = "my_mod::/example.script@handleEvent" },
  }
end
```

当前本机定义与 [官方 GameScript 接口](https://wiki.transportfever3.com/script-doc/content/scripts/gamescript.html) 对应的参数：

| 回调 | 参数顺序 | 端与状态 |
| --- | --- | --- |
| `update` | `userParams, state, dt` | 模拟端状态 |
| `postUpdate` | `userParams, state, dt, updateResult` | 模拟更新后 |
| `handleEvent` | `userParams, state, src, id, name, param` | 模拟事件 |
| `guiUpdate` | `userParams, readonlySimState, guiState` | 模拟状态只读；无 `dt` 参数 |
| `guiHandleEvent` | `userParams, readonlySimState, guiState, src, id, name, param` | GUI 事件 |

旧版参考曾把 `loadGame`、`init`、`updateSimulation`、`updateGui`、`saveState`、`viewState` 列为本接口成员；当前定义不支持该列表。不要据这些名字机械映射二代 `load/save/update`。

采用当前 `GameScriptState` 的 `get/set`、对应 native 方法及实际事件 API。逐项设计：

- 初始化：参考官方 `initStateIfEmpty` 实例，空状态、新地图与旧存档分别处理；记录状态 schema 版本及必要升级。
- 权限：GUI 读取模拟状态，不直接写只读对象；改变游戏数据经当前支持的命令或事件通道。
- 数据：保存可序列化业务值；原生窗口引用、闭包、瞬态 GUI 对象不直接作为存档数据。
- 事件：核实订阅和退出条件，避免热重载或重新打开界面导致重复订阅、重复实体或命令。
- 时序：异步结果可能晚于窗口关闭或地图切换，回调执行前检查有效状态。

这种设计不能单靠语法测试证明。只有实际新建、保存、载入、事件操作和重载测试才能确认生命周期结果；不允许开游戏时明确交付为待测。

## 6. 按可验证的阶段实现 GUI 与数据

先做合法扩展点上的一个按钮，再做空窗口，然后接业务数据、刷新、样式和附加视图。每一步检查注册、返回节点类别、调用参数和作用域，避免同时引入所有二代行为而无法定位启动错误。

若叠加层或点击 API 尚未确认，标为“尚未实现 / 尚未找到适用接口”，继续调查支持方案；这不足以宣布 TF3 全局不可能实现。不要用无关全局样式或吞掉异常维持表面可用。

## 7. 不可读脚本与跨平台依赖

Lua 头 `1b 4c 75 61` 是标准字节码，下一字节如 `0x52` 表示 Lua 5.2。字节码不是明文源码；版本、ABI、宿主 API 不同会破坏兼容。只读盘点不执行不明字节码。

只提供可证明资源常量的模块可参考 [CR200J](cr200j-case-study.md) 重建必要值；不可替代的算法需要授权源码或作者版本。原生 DLL、插件和二进制模块分别核实平台支持。纯 Lua/Teal 源码通常可跨平台，但未在目标 Windows 游戏实测不能写“Windows 已通过”。

## 官方依据

- [装载脚本与参数](https://wiki.transportfever3.com/doku.php?id=modding:general:modscripts)：装载阶段与业务参数。
- [资源语法及导入](https://wiki.transportfever3.com/doku.php?id=modding:general:syntax)：虚拟资源路径、导出函数与模块。
- [GameScript 接口](https://wiki.transportfever3.com/script-doc/content/scripts/gamescript.html)：生命周期与状态；具体调用同时核对本机定义。
