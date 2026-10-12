"""Convert an original mod preview into TF3's _metadata/0.png grid cover."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

from PIL import Image, ImageOps
from pydantic import BaseModel


class CoverResult(BaseModel):
    """Record the original image, resulting cover, and independent decode check."""

    source: str
    source_sha256: str
    source_size: tuple[int, int]
    target: str
    target_sha256: str
    target_size: tuple[int, int]
    png_verified: bool


class ModCoverInstaller:
    """Preserve an existing cover's content while adapting its file format/layout."""

    def __init__(self, image: Path, mod: Path) -> None:
        """Store the original preview image and explicitly selected output mod."""
        self.image = image.resolve()
        self.mod = mod.resolve()

    def run(self) -> CoverResult:
        """Decode the source, fit it without cropping, and verify the saved PNG."""
        if not (self.mod / "mod.json").is_file():
            raise ValueError(f"Missing target mod manifest: {self.mod}")
        target = self.mod / "_metadata/0.png"
        if self.image == target:
            raise ValueError("Source image must be separate from the target cover.")
        with Image.open(self.image) as original:
            image = ImageOps.exif_transpose(original).convert("RGBA")
            source_size = image.size
            # TF3 recommends 1920x1080. Contain keeps logos/text and aspect ratio;
            # square legacy previews receive padding instead of a destructive crop.
            fitted = ImageOps.contain(image, (1920, 1080), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (1920, 1080), (25, 32, 36))
            offset = ((1920 - fitted.width) // 2, (1080 - fitted.height) // 2)
            canvas.paste(fitted, offset, fitted)
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(".tmp")
            canvas.save(temporary, format="PNG")
        with Image.open(temporary) as decoded:
            decoded.load()
            if decoded.format != "PNG" or decoded.size != (1920, 1080):
                raise ValueError("Generated TF3 cover failed the PNG decode check.")
        temporary.replace(target)
        return CoverResult(
            source=str(self.image),
            source_sha256=hashlib.sha256(self.image.read_bytes()).hexdigest(),
            source_size=source_size,
            target=str(target),
            target_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
            target_size=(1920, 1080),
            png_verified=True,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mod", type=Path, required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--image", type=Path, help="Explicit existing preview image.")
    source.add_argument("--source", type=Path, help="Original TF2 mod directory.")
    parser.add_argument("--report", type=Path)
    arguments = parser.parse_args()
    image_path: Path | None = arguments.image
    if image_path is None:
        # Prefer the in-game cover over a Workshop-only marketing image.
        image_path = next(
            (
                arguments.source / name
                for name in (
                    "image_00.tga", "image_00.png", "image_00.jpg",
                    "workshop_preview.jpg", "workshop_preview.png",
                )
                if (arguments.source / name).is_file()
            ),
            None,
        )
    if image_path is None:
        parser.error("No original cover found; select an existing image with --image.")
    result = ModCoverInstaller(image_path, arguments.mod).run()
    if arguments.report is not None:
        arguments.report.parent.mkdir(parents=True, exist_ok=True)
        arguments.report.write_text(result.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(result.model_dump_json())
