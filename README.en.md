# Transport Fever Mod Migration Skill

English | [中文](README.md)

This repository contains a Codex skill for migrating mods from Transport Fever 2 to Transport Fever 3. It covers real vehicle, material, texture, audio, and script migrations and produces evidence-based reports that separate offline checks, Model Editor checks, game checks, and Windows checks.

## Features

- Inventory the source mod, preserve the original package, and work in an independent copy.
- Use the target version's official Model Editor conversion for models, materials, and metadata.
- Handle Lua/Teal scripts, resource entry points, React GUI, dynamic destination labels, vehicle lighting, and cross-platform path issues.
- Check DDS/TGA files, meshes, LODs, formations, covers, and dependencies.
- Produce an installable ZIP, CRC/SHA-256 evidence, and a layered validation report.
- Keep offline, editor, main-game, and Windows results separate so unrun tests are never reported as passed.

## Layout

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

`SKILL.md` is the entry point. `references/` contains focused guidance for the migration workflow, script interfaces, React GUI, materials, covers, dynamic destinations, and troubleshooting. `scripts/` provides read-only inventory, cover conversion, and package verification tools.

## Installation

Copy `transport-fever-mod-migration` into the Codex skills directory:

```sh
cp -R transport-fever-mod-migration "$CODEX_HOME/skills/"
```

For Codex Desktop, the default directory is commonly `~/.codex/skills`. After installation, invoke the skill with `$transport-fever-mod-migration`.

## Usage

Describe the source mod, target TF3 version, permitted validation scope, and expected outputs. For example:

```text
Use $transport-fever-mod-migration to migrate /path/to/source_mod to TF3.
Keep the source package unchanged, produce an installable ZIP, and report
editor, game, and Windows validation separately.
```

The skill does not grant permission to open the game, Model Editor, or publishing platforms. Any check that was not actually run must be recorded as `not run`.

## Requirements

- Run Python commands with `uv run python`.
- Inventory and packaging tools require Pydantic 2; the cover tool also requires Pillow.
- The installed game and Model Editor version controls resource schemas, script signatures, style parsing, and validation thresholds. Verify the local installation before use.

## License

This repository provides migration workflows, checking scripts, and reference material. Original Transport Fever mods, models, textures, audio, game assets, and third-party dependencies remain the property of their respective authors or rights holders. Confirm the original mod license and all required permissions before redistributing migrated output.

## Language

Chinese version: [README.md](README.md).
