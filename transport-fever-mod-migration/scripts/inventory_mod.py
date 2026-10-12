"""Read-only TF2/TF3 asset inventory; never import or execute mod code."""

from __future__ import annotations

import argparse
import hashlib
import re
import struct
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class PathCollision(BaseModel):
    """Paths that collide after Unicode NFC normalization and case folding."""

    normalized_path: str
    paths: list[str]


class TexturePair(BaseModel):
    """Same-stem DDS/TGA inputs that need distinct conversion destinations."""

    normalized_stem: str
    paths: list[str]


class BytecodeInfo(BaseModel):
    """Standard Lua bytecode signature and its encoded version byte."""

    path: str
    lua_version: str


class MeshCompanion(BaseModel):
    """Missing exact mesh companion and possible names to investigate."""

    mesh: str
    expected_blob: str
    alternative_candidates: list[str]


class DdsInfo(BaseModel):
    """DDS header facts, without claiming payload or shader validity."""

    path: str
    width: int
    height: int
    mip_count: int
    expected_full_mip_count: int
    fourcc: str
    dxgi_format: int | None


class InspectionIssue(BaseModel):
    """Unreadable files or inconsistent headers requiring further inspection."""

    path: str
    message: str


class InventoryReport(BaseModel):
    """Portable typed report of observations, not a migration pass/fail result."""

    source_root: str
    layout: Literal["tf2-res", "tf3-content", "legacy-in-content", "mixed", "unknown"]
    file_count: int
    resource_counts: dict[str, int]
    nonlowercase_paths: list[str] = Field(default_factory=list)
    space_or_nonascii_paths: list[str] = Field(default_factory=list)
    path_collisions: list[PathCollision] = Field(default_factory=list)
    dds_tga_pairs: list[TexturePair] = Field(default_factory=list)
    lua_bytecode: list[BytecodeInfo] = Field(default_factory=list)
    utf8_bom_files: list[str] = Field(default_factory=list)
    missing_mesh_companions: list[MeshCompanion] = Field(default_factory=list)
    dds_headers: list[DdsInfo] = Field(default_factory=list)
    incomplete_mip_chains: list[str] = Field(default_factory=list)
    script_import_hints: dict[str, list[str]] = Field(default_factory=dict)
    symlinks: list[str] = Field(default_factory=list)
    issues: list[InspectionIssue] = Field(default_factory=list)
    sha256: dict[str, str] = Field(default_factory=dict)
    limitations: list[str] = Field(
        default_factory=lambda: [
            "No Lua execution, decryption, conversion, or source writes.",
            "Imports are text hints and may include comments or inactive code.",
            "DDS checks cover headers and mip counts, not payloads or shader roles.",
            "No full resource graph, mesh-index, editor, game, or Windows validation.",
            "Symlinks and macOS packaging metadata are excluded from file counts/hashes.",
        ]
    )


class ModInventory:
    """Collect resource hazards from an unchanged source directory."""

    TEXT_SUFFIXES = {".lua", ".tl", ".mdl", ".msh", ".mtl", ".ani", ".json"}
    COMPOUND_SUFFIXES = (
        ".msh.blob",
        ".mu.lua",
        ".snd.lua",
        ".gs.lua",
        ".script.lua",
        ".script.tl",
        ".con.lua",
        ".cargo.lua",
        ".trf.lua",
    )
    IMPORT_PATTERN = re.compile(r"\b(?:ug_require|require)\s*\(\s*['\"]([^'\"]+)['\"]")

    def __init__(self, root: Path, hash_files: bool) -> None:
        """Set the source root and whether to hash every regular source file."""
        self.root = root.resolve()
        self.hash_files = hash_files

    def run(self) -> InventoryReport:
        """Scan self.root and return observations without executing source files."""
        has_res = (self.root / "res").is_dir()
        has_content = (self.root / "content").is_dir()
        layout: Literal[
            "tf2-res", "tf3-content", "legacy-in-content", "mixed", "unknown"
        ] = "unknown"
        if has_res and has_content:
            layout = "mixed"
        elif has_res:
            layout = "tf2-res"
        elif (self.root / "content/res").is_dir():
            layout = "legacy-in-content"
        elif has_content:
            layout = "tf3-content"

        report = InventoryReport(
            source_root=str(self.root), layout=layout, file_count=0, resource_counts={}
        )
        files: dict[str, Path] = {}
        folded_paths: defaultdict[str, list[str]] = defaultdict(list)
        textures: defaultdict[str, list[str]] = defaultdict(list)
        counts: Counter[str] = Counter()

        # Include directory collisions too: renaming colliding folders can merge assets.
        for path in sorted(self.root.rglob("*")):
            relative = path.relative_to(self.root)
            if ".DS_Store" in relative.parts or "__MACOSX" in relative.parts:
                continue
            name = relative.as_posix()
            if path.is_symlink():
                report.symlinks.append(name)
                continue
            key = unicodedata.normalize("NFC", name).casefold()
            folded_paths[key].append(name)
            if relative.parts[0] in {"res", "content"}:
                if name != name.lower():
                    report.nonlowercase_paths.append(name)
                if any(
                    character.isspace() or not character.isascii() for character in name
                ):
                    report.space_or_nonascii_paths.append(name)
            if not path.is_file():
                continue
            files[name] = path
            suffix = path.suffix.lower()
            resource_type = next(
                (
                    item
                    for item in self.COMPOUND_SUFFIXES
                    if name.lower().endswith(item)
                ),
                suffix or "<no-extension>",
            )
            counts[resource_type] += 1
            if suffix in {".dds", ".tga"}:
                stem = unicodedata.normalize(
                    "NFC", str(relative.with_suffix(""))
                ).casefold()
                textures[stem].append(name)

        report.file_count = len(files)
        report.resource_counts = dict(sorted(counts.items()))
        report.path_collisions = [
            PathCollision(normalized_path=key, paths=paths)
            for key, paths in sorted(folded_paths.items())
            if len(paths) > 1
        ]
        report.dds_tga_pairs = [
            TexturePair(normalized_stem=stem, paths=paths)
            for stem, paths in sorted(textures.items())
            if {Path(name).suffix.lower() for name in paths} == {".dds", ".tga"}
        ]

        for name, path in files.items():
            try:
                with path.open("rb") as stream:
                    header = stream.read(148)
                    if self.hash_files:
                        stream.seek(0)
                        report.sha256[name] = hashlib.file_digest(
                            stream, "sha256"
                        ).hexdigest()
                if header.startswith(b"\x1bLua"):
                    version = (
                        f"{header[4] >> 4}.{header[4] & 15}"
                        if len(header) > 4
                        else "unknown-truncated"
                    )
                    report.lua_bytecode.append(
                        BytecodeInfo(path=name, lua_version=version)
                    )
                    continue
                if path.suffix.lower() == ".dds":
                    self.inspect_dds(name, header, report)
                elif path.suffix.lower() in self.TEXT_SUFFIXES:
                    self.inspect_text(name, path, report)
            except OSError as error:
                report.issues.append(InspectionIssue(path=name, message=str(error)))

            if path.suffix.lower() == ".msh":
                expected = name + ".blob"
                if expected not in files:
                    # Candidates are clues only; never copy or select them automatically.
                    candidates = set(
                        folded_paths.get(
                            unicodedata.normalize("NFC", expected).casefold(), []
                        )
                    )
                    alternative = str(Path(name).with_suffix(".blob"))
                    candidates.update(
                        folded_paths.get(
                            unicodedata.normalize("NFC", alternative).casefold(), []
                        )
                    )
                    report.missing_mesh_companions.append(
                        MeshCompanion(
                            mesh=name,
                            expected_blob=expected,
                            alternative_candidates=sorted(
                                candidate
                                for candidate in candidates
                                if candidate in files
                            ),
                        )
                    )
        return report

    def inspect_text(self, name: str, path: Path, report: InventoryReport) -> None:
        """Decode a text candidate at path; append BOM/import/error observations."""
        content = path.read_bytes()
        if content.startswith(b"\xef\xbb\xbf"):
            report.utf8_bom_files.append(name)
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            report.issues.append(
                InspectionIssue(
                    path=name, message="Not valid UTF-8 text; inspect format/encoding."
                )
            )
            return
        imports = sorted(set(self.IMPORT_PATTERN.findall(text)))
        if imports:
            report.script_import_hints[name] = imports

    def inspect_dds(self, name: str, header: bytes, report: InventoryReport) -> None:
        """Read DDS header bytes; report dimensions/mips without validating payloads."""
        if len(header) < 128 or header[:4] != b"DDS ":
            report.issues.append(
                InspectionIssue(path=name, message="Missing/truncated DDS header.")
            )
            return
        if struct.unpack_from("<I", header, 4)[0] != 124:
            report.issues.append(
                InspectionIssue(path=name, message="DDS header size is not 124.")
            )
            return
        height, width = struct.unpack_from("<II", header, 12)
        if width == 0 or height == 0:
            report.issues.append(
                InspectionIssue(path=name, message="DDS dimensions must be positive.")
            )
            return
        mip_count = struct.unpack_from("<I", header, 28)[0] or 1
        fourcc_bytes = header[84:88]
        fourcc = fourcc_bytes.decode("ascii", errors="replace").rstrip("\x00")
        dxgi_format: int | None = None
        if fourcc_bytes == b"DX10":
            if len(header) < 148:
                report.issues.append(
                    InspectionIssue(path=name, message="Truncated DDS DX10 header.")
                )
                return
            dxgi_format = struct.unpack_from("<I", header, 128)[0]
        expected_mips = max(width, height).bit_length()
        report.dds_headers.append(
            DdsInfo(
                path=name,
                width=width,
                height=height,
                mip_count=mip_count,
                expected_full_mip_count=expected_mips,
                fourcc=fourcc,
                dxgi_format=dxgi_format,
            )
        )
        if mip_count < expected_mips:
            report.incomplete_mip_chains.append(name)
        elif mip_count > expected_mips:
            report.issues.append(
                InspectionIssue(
                    path=name, message="Mip count exceeds full 2D chain length."
                )
            )


class InventoryArguments(argparse.Namespace):
    """Typed arguments for the read-only inventory command."""

    source: str
    output: str
    hash: bool


def main() -> None:
    """Parse CLI paths and write a report outside the source tree; takes no inputs."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="Original mod directory (read only).")
    parser.add_argument(
        "--output", required=True, help="JSON report outside the source directory."
    )
    parser.add_argument(
        "--hash", action="store_true", help="Hash all regular source files."
    )
    arguments = parser.parse_args(namespace=InventoryArguments())
    source = Path(arguments.source).expanduser().resolve()
    output = Path(arguments.output).expanduser().resolve()
    if not source.is_dir():
        parser.error(f"Source is not a directory: {source}")
    if output == source or output.is_relative_to(source):
        parser.error(
            "Report must be outside the source directory; source writes are forbidden."
        )
    report = ModInventory(source, arguments.hash).run()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(
        f"Inventoried {report.file_count} files ({report.layout}); "
        f"{len(report.issues)} inspection issues. Report: {output}"
    )


if __name__ == "__main__":
    main()
