#!/usr/bin/env python3
"""
Convert PDF figures to high-resolution PNGs.

Usage:
    python pdf_to_png.py figure1.pdf figure2.pdf          # specific files
    python pdf_to_png.py Figures/                          # all PDFs in a directory
    python pdf_to_png.py Figures/ -o static/images/ -s 3000  # custom output dir & size

The output PNGs are named after the input PDFs (e.g., my_figure.pdf -> my_figure.png).
"""

import argparse
import subprocess
import os
import sys
import shutil
import tempfile
from pathlib import Path


def convert_pdf_to_png(pdf_path: Path, output_dir: Path, size: int) -> Path:
    """Convert a single PDF to PNG using macOS qlmanage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        result = subprocess.run(
            ["qlmanage", "-t", "-s", str(size), "-o", tmpdir, str(pdf_path)],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"  ERROR: qlmanage failed for {pdf_path.name}")
            print(f"  stderr: {result.stderr.strip()}")
            return None

        # qlmanage outputs <filename>.pdf.png
        tmp_png = Path(tmpdir) / f"{pdf_path.name}.png"
        if not tmp_png.exists():
            print(f"  ERROR: expected output not found: {tmp_png}")
            return None

        output_path = output_dir / f"{pdf_path.stem}.png"
        shutil.move(str(tmp_png), str(output_path))
        return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF figures to high-resolution PNGs (macOS)."
    )
    parser.add_argument(
        "inputs", nargs="+",
        help="PDF file(s) or directory containing PDFs."
    )
    parser.add_argument(
        "-o", "--output-dir", default=None,
        help="Output directory for PNGs. Defaults to same directory as each input PDF."
    )
    parser.add_argument(
        "-s", "--size", type=int, default=2400,
        help="Max dimension in pixels (default: 2400)."
    )
    args = parser.parse_args()

    # Collect all PDF paths
    pdf_files = []
    for inp in args.inputs:
        p = Path(inp)
        if p.is_dir():
            pdf_files.extend(sorted(p.glob("*.pdf")))
        elif p.is_file() and p.suffix.lower() == ".pdf":
            pdf_files.append(p)
        else:
            print(f"Skipping: {inp} (not a PDF file or directory)")

    if not pdf_files:
        print("No PDF files found.")
        sys.exit(1)

    print(f"Found {len(pdf_files)} PDF(s) to convert (max size: {args.size}px)\n")

    for pdf in pdf_files:
        out_dir = Path(args.output_dir) if args.output_dir else pdf.parent
        out_dir.mkdir(parents=True, exist_ok=True)

        print(f"  {pdf.name} -> ", end="", flush=True)
        result = convert_pdf_to_png(pdf, out_dir, args.size)
        if result:
            # Get dimensions via sips
            sips_out = subprocess.run(
                ["sips", "--getProperty", "pixelWidth", "--getProperty", "pixelHeight", str(result)],
                capture_output=True, text=True
            )
            dims = ""
            for line in sips_out.stdout.splitlines():
                if "pixelWidth" in line or "pixelHeight" in line:
                    dims += line.strip() + "  "
            print(f"{result.name}  ({dims.strip()})")

    print("\nDone.")


if __name__ == "__main__":
    main()
