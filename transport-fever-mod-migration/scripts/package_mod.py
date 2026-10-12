"""Package an explicit TF3 mod directory and verify ZIP CRCs and SHA-256."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from pydantic import BaseModel
from PIL import Image


class PackageResult(BaseModel):
    """Portable archive identity and integrity evidence written beside the ZIP."""

    archive: str
    files: int
    size_bytes: int
    sha256: str
    crc_verified: bool


class ModPackager:
    """Archive a mod directory without platform launchers or development files."""

    def __init__(self, mod: Path, archive: Path, allow_missing_cover: bool = False) -> None:
        """Store the assembled mod directory and destination archive path."""
        self.mod = mod.resolve()
        self.archive = archive.resolve()
        self.allow_missing_cover = allow_missing_cover

    def run(self) -> None:
        """Write the ZIP, check all CRCs, and save SHA-256 and package metadata."""
        assert (self.mod / "mod.json").is_file(), "Assembled mod manifest is missing."
        assert (self.mod / "content").is_dir(), (
            "Assembled content directory is missing."
        )
        assert not self.archive.is_relative_to(self.mod), (
            "Archive must be outside the mod."
        )
        manifest = json.loads((self.mod / "mod.json").read_text(encoding="utf-8"))
        cover = self.mod / "_metadata/0.png"
        if cover.is_file():
            with Image.open(cover) as decoded:
                decoded.load()
                assert decoded.format == "PNG", "TF3 cover must contain actual PNG data."
        elif manifest.get("visible", True) and not self.allow_missing_cover:
            raise ValueError(
                "Visible mod is missing _metadata/0.png. Run migrate_cover.py first; "
                "use --allow-missing-cover only for an explicitly documented exception."
            )
        files = sorted(
            path
            for path in self.mod.rglob("*")
            if path.is_file()
            and not {".DS_Store", "__MACOSX"}.intersection(
                path.relative_to(self.mod).parts
            )
        )
        self.archive.parent.mkdir(parents=True, exist_ok=True)
        with ZipFile(self.archive, "w", ZIP_DEFLATED, compresslevel=6) as package:
            for path in files:
                assert not path.is_symlink(), f"Unexpected symlink: {path}"
                assert not path.name.startswith("."), f"Unexpected hidden file: {path}"
                # Include a single root directory so extraction yields an installable mod.
                package.write(path, path.relative_to(self.mod.parent).as_posix())
        with ZipFile(self.archive) as package:
            assert package.testzip() is None, "Archive CRC validation failed."
        with self.archive.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        result = PackageResult(
            archive=self.archive.name,
            files=len(files),
            size_bytes=self.archive.stat().st_size,
            sha256=digest,
            crc_verified=True,
        )
        self.archive.with_suffix(".zip.sha256").write_text(
            f"{digest}  {self.archive.name}\n", encoding="utf-8"
        )
        self.archive.with_suffix(".package.json").write_text(
            result.model_dump_json(indent=2) + "\n", encoding="utf-8"
        )
        print(result.model_dump_json())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mod", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--allow-missing-cover", action="store_true")
    arguments = parser.parse_args()
    ModPackager(arguments.mod, arguments.archive, arguments.allow_missing_cover).run()
