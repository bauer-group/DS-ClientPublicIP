#!/usr/bin/env python3
"""Generate PNG icons from SVG favicon for PWA and Apple Touch Icon."""

import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
STATIC_DIR = SCRIPT_DIR.parent / "src" / "static"
SVG_PATH = STATIC_DIR / "favicon.svg"

ICONS = [
    ("icon-192.png", 192),
    ("icon-512.png", 512),
    ("apple-touch-icon.png", 180),
]


def generate_with_cairosvg():
    """Generate PNGs using cairosvg (pip install cairosvg)."""
    try:
        import cairosvg
        for filename, size in ICONS:
            output_path = STATIC_DIR / filename
            cairosvg.svg2png(
                url=str(SVG_PATH),
                write_to=str(output_path),
                output_width=size,
                output_height=size
            )
            print(f"Created: {filename} ({size}x{size})")
        return True
    except ImportError:
        return False


def generate_with_inkscape():
    """Generate PNGs using Inkscape CLI."""
    try:
        for filename, size in ICONS:
            output_path = STATIC_DIR / filename
            subprocess.run([
                "inkscape",
                str(SVG_PATH),
                "--export-type=png",
                f"--export-filename={output_path}",
                f"--export-width={size}",
                f"--export-height={size}"
            ], check=True, capture_output=True)
            print(f"Created: {filename} ({size}x{size})")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def generate_with_imagemagick():
    """Generate PNGs using ImageMagick."""
    try:
        for filename, size in ICONS:
            output_path = STATIC_DIR / filename
            subprocess.run([
                "magick", "convert",
                "-background", "none",
                "-density", "300",
                str(SVG_PATH),
                "-resize", f"{size}x{size}",
                str(output_path)
            ], check=True, capture_output=True)
            print(f"Created: {filename} ({size}x{size})")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def main():
    print("Generating PWA icons from favicon.svg...\n")

    if not SVG_PATH.exists():
        print(f"Error: {SVG_PATH} not found")
        sys.exit(1)

    # Try different methods
    if generate_with_cairosvg():
        print("\nDone! Icons generated using cairosvg.")
    elif generate_with_inkscape():
        print("\nDone! Icons generated using Inkscape.")
    elif generate_with_imagemagick():
        print("\nDone! Icons generated using ImageMagick.")
    else:
        print("\nNo suitable tool found. Please install one of:")
        print("  - cairosvg: pip install cairosvg")
        print("  - Inkscape: https://inkscape.org/")
        print("  - ImageMagick: https://imagemagick.org/")
        print("\nAlternatively, use an online SVG to PNG converter:")
        print(f"  1. Open {SVG_PATH}")
        print("  2. Export as PNG in sizes: 180x180, 192x192, 512x512")
        print("  3. Save as: apple-touch-icon.png, icon-192.png, icon-512.png")
        sys.exit(1)


if __name__ == "__main__":
    main()
