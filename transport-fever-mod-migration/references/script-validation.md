# 脚本迁移的离线验证、回归与交付

适用于 [脚本迁移](script-migration.md) 与 [React GUI](tf3-react-gui.md)。最后核对：2026-10-04。命令中的路径由当前安装和工作目录确定，不把本案例的主机路径作为其他机器的默认值。

## 1. 明确每层检查能证明什么

| 检查层 | 能发现 | 不能据此证明 |
| --- | --- | --- |
| JSON、路径、导出核对 | manifest、资源入口、编码、大小写、重复 ID、缺失依赖 | 引擎成功加载资源 |
| Lua `loadfile` / `luac -p` | 被检查 `.lua` 的语法 | `.tl` 合法、回调运行、GUI 契约 |
| Teal 解析与生成 Lua | Teal 语法与指定目标 Lua 转译 | 完整类型通过、TF3 全部 API 可用 |
| 配置完整定义的 Teal 类型检查 | 类型、未定义变量、签名等静态问题 | 原生节点类别、渲染效果、存档行为 |
| 限定宿主回调检查 | 所建模的导入、入口、布局约束、打开/刷新/关闭 | 真正 engine userdata、C++ 变换器、完整模拟端 |
| 目标游戏的样式解析器 | 选择器实际被怎样解析、是否失去类/ID 过滤 | 原生匹配、布局和屏幕效果 |
| 获准的实际游戏操作 | 被实际覆盖的加载、原界面、窗口、数据与存档行为 | 未测版本/系统/场景的行为 |
| ZIP CRC 和 SHA-256 | 文件传输完整性及包身份 | 模组功能正确 |

Model Editor 能验证模型资源，不执行这类主游戏 React GUI。纯脚本模组标记“不适用”，不要把 Model Editor 能启动当作 GUI 已测试。

用户禁止打开游戏时不通过后台进程、Steam URI、热重载或其他途径绕过。继续可进行的离线检查；游戏栏写“未运行”，并提供具体待测操作。

## 2. 固定检查输入与工具来源

保留原模组，以只读盘点工具的 `--hash` 生成迁移前快照；修改全部在独立副本。需要证明原包未变时，另生成迁移后快照并比较文件列表与散列，不能把原包与自身同一份报告比较。

记录目标 API 来源、插件虚拟入口、revision、被测试模块/样式的散列和实际运行命令。小工具输出也写明“未测原生渲染”。依赖可从本机读取，技能包不携带游戏原生源码或下载的第三方编译器副本。

使用 Teal 时记录实际编译器版本和散列。这不是 TF3 内置编译器版本声明；不要把下载失败的 HTML/部分文件当作编译器，其他版本应另记版本和散列。

以下示例只准备离线工作区，三个变量均为任务路径：

```sh
skill_root='/Users/aeovy/.codex/skills/transport-fever-mod-migration'
tf3_root='/path/to/Transport Fever 3'
probe_dir='/path/to/work/script-probes'
mkdir -p "$probe_dir"
unzip -p "$tf3_root/base/content/gui.zip" gui/main/stylesheetutil.lua \
  > "$probe_dir/stylesheetutil.lua"
```

如果缺少编译器，可从官方仓库取得并核对散列；运行前确认输出是 Lua 源码：

```sh
curl --fail --location --connect-timeout 5 --max-time 30 \
  --header 'Accept: application/vnd.github.raw+json' \
  'https://api.github.com/repos/teal-language/tl/contents/tl.lua?ref=v0.24.8' \
  -o "$probe_dir/tl.lua"
shasum -a 256 "$probe_dir/tl.lua" "$probe_dir/stylesheetutil.lua"
```

本案例解析器来自本机 `gui.zip`，当次散列为 `411a00603da7bcd11b242395e615129109e4ff64237bd903b6cf7f3c22026a23`。该值仅标识当次版本，不要求其他游戏版本一致。

`.lua` 描述符另做语法检查，`.tl` 不能交给 `luac -p`。对有 GUI 或脚本入口的迁移，编写只覆盖实际资源入口和宿主契约的限定检查；不要用“任何方法都返回成功”的假宿主。

## 3. 针对性回归与实际 GUI 测试

先用历史错误或最小临时副本证明新检查器能捕获目标缺陷，核实错误内容后再运行修复版本。缺失文件、工具下载失败或任意非零退出都不能算作成功捕获缺陷。

按实际功能选择游戏测试顺序：

1. 完整替换旧模组，确认实际 `modId`、revision、资源散列；排除同 ID 的另一路径遮蔽。
2. 启用后观察原主界面、窗口尺寸、位置和鼠标焦点，确认自有样式没有泄漏到基础界面。
3. 操作目标功能的打开、关闭、重开、刷新、缩放和错误路径；只记录实际覆盖的场景。
4. 如果新增持久状态或模拟逻辑，再测试暂停/继续、新建、保存/加载、切图、事件去重与状态升级。
5. 在目标 Windows 版本分别验证，不把 macOS 离线或编辑器结果代替 Windows 游戏结果。

出现重载次数限制时先修复根因，再由获准的测试者重启。保留真实错误栈、版本和截图；不要清日志或忽略异常后宣称通过。纯信息窗口没有保存状态时无需强行增加模拟生命周期实现或测试。

## 6. 从被测试源目录生成包

使用 [打包工具](../scripts/package_mod.py)，明确指定源目录和外部输出位置：

```sh
uv run --with 'pydantic>=2.11,<3' --with 'pillow>=11,<13' python \
  "$skill_root/scripts/package_mod.py" \
  --mod /path/to/work/my_mod \
  --archive /path/to/dist/my_mod.zip
```

工具要求 `mod.json`、`content/`；可见模组还需可解码的 `_metadata/0.png`，封面迁移或明确例外见 [封面说明](mod-cover.md)。它生成一个模组根目录，检查 ZIP CRC，旁写 `.zip.sha256` 与 `.package.json`。它排除 `.DS_Store` / `__MACOSX`，拒绝文件符号链接和隐藏文件；并不自动识别所有开发日志、缓存或错误资源。先整理交付源目录，包内不得混入无关文件。

修改逻辑或样式后按项目规则更新 revision，重新运行受影响的检查，从同一个目录打包。解压到新工作目录，比较文件列表与源散列，检查没有多层错误目录，必要时对解压内容重跑入口/样式测试。安装副本与被测内容必须一致。

ZIP 已存在不代表它已更新；最终报告给出包 SHA-256。禁止把旧 ZIP、后来修改的源和过时验证报告组合交付。不要恢复用户明确删除的生成目录，除非本任务确实需要且已说明。

## 7. 报告字段与状态用法

区分 agent 离线结果、用户实际反馈和未覆盖功能。可以按下面结构记录，实际替换字段值，不生成假的证据：

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

每项通过对应命令或实际操作证据，失败保留原因，未运行写明范围。在 Git 项目中按实质阶段提交工具、模板和文档，使用具体路径，保留其他任务的变更。向平台发布不属于一般迁移授权。
