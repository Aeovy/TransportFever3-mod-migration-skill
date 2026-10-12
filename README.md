# Transport Fever Mod Migration Skill

[English](README.en.md) | 中文

这是一个面向 Transport Fever 2 到 Transport Fever 3 模组迁移的 Codex skill。它用于把真实的车辆、材质、贴图、音效和脚本模组迁移到 TF3，并以可核查的离线检查、Model Editor 证据和游戏验证范围生成迁移报告。

## 功能

- 盘点原始模组，保留原包，并在独立副本中执行迁移。
- 使用目标版本的官方 Model Editor 转换模型、材质和元数据。
- 处理 Lua/Teal 脚本、资源入口、React GUI、动态目的地标签、车辆灯光和跨平台路径问题。
- 检查 DDS/TGA、网格、LOD、编组、封面和依赖关系。
- 生成 ZIP、CRC/SHA-256 校验和分层验证报告。
- 明确区分离线检查、编辑器检查、主游戏检查和 Windows 检查，避免把未运行的测试写成通过。

## 目录

```text
transport-fever-mod-migration-skill/
├── transport-fever-mod-migration/
│   ├── SKILL.md
│   ├── agents/openai.yaml
│   ├── references/
│   └── scripts/
├── README.md
└── README.en.md
```

`SKILL.md` 是入口。`references/` 按问题提供迁移流程、脚本接口、React GUI、材质、封面、动态目的地和故障排查资料。`scripts/` 提供只读盘点、封面转换和打包校验工具。

## 安装

将 `transport-fever-mod-migration` 目录复制到 Codex skill 目录：

```sh
cp -R transport-fever-mod-migration "$CODEX_HOME/skills/"
```

如果使用 Codex Desktop，默认目录通常是 `~/.codex/skills`。安装后可在任务中使用 `$transport-fever-mod-migration`。

## 使用

在任务中说明源模组位置、目标 TF3 版本、允许的验证范围和期望输出。例如：

```text
Use $transport-fever-mod-migration to migrate /path/to/source_mod to TF3.
Keep the source package unchanged, produce an installable ZIP, and report
editor, game, and Windows validation separately.
```

技能不会替用户授权打开游戏、Model Editor 或发布平台。未实际运行的检查必须在报告中标记为 `not run`。

## 运行环境

- Python 命令使用 `uv run python`。
- 盘点和打包工具依赖 Pydantic 2，封面工具还依赖 Pillow。
- 目标游戏和 Model Editor 的版本会影响资源 schema、脚本签名、样式解析和验证阈值；使用前请以本机安装为准。

## 许可证

本仓库只提供迁移流程、检查脚本和参考资料。原始 Transport Fever 模组、模型、纹理、音频、游戏资源和第三方依赖仍归各自作者或权利人所有。重新分发迁移产物前，请分别确认原模组许可证和相关授权。

## 语言

英文版本：[README.en.md](README.en.md)。
