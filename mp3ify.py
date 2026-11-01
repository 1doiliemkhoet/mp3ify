#!/usr/bin/env python3
"""mp3ify: A small, offline MP4-to-MP3 command-line tool (Python stdlib + FFmpeg)."""

from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

VERSION = "1.0.1"


def parse_bitrate(value: str) -> int:
    normalized = value.strip().lower().removesuffix("k")
    try:
        bitrate = int(normalized)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("bitrate must be 64-320 (e.g. 192 or 320k)") from exc
    if bitrate not in (64, 96, 128, 160, 192, 224, 256, 320):
        raise argparse.ArgumentTypeError("choose one of 64, 96, 128, 160, 192, 224, 256, 320")
    return bitrate


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mp3ify",
        description="Convert MP4 to MP3 locally with FFmpeg. Never uploads anything.",
        epilog=(
            'Examples:\n'
            '  mp3ify "my video.mp4"\n'
            '  mp3ify "video.mp4" -o "song.mp3"\n'
            '  mp3ify *.mp4 -b 320\n'
            '  mp3ify "D:\\Videos" -r -d "D:\\MP3"\n'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("inputs", nargs="+", metavar="INPUT", help="MP4 files, *.mp4 patterns, and/or directories")
    parser.add_argument("-o", "--output", metavar="FILE.mp3", help="output filename (exactly one input file)")
    parser.add_argument("-d", "--out-dir", metavar="DIR", help="directory for converted MP3s")
    parser.add_argument("-r", "--recursive", action="store_true", help="scan subdirectories too")
    parser.add_argument("-q", "--quality", type=int, choices=range(10), default=2,
                        metavar="0-9", help="VBR quality: 0 best, 9 smallest (default: 2)")
    parser.add_argument("-b", "--bitrate", type=parse_bitrate, metavar="KBPS",
                        help="constant bitrate e.g. 128, 192, 320; overrides -q")
    parser.add_argument("--track", type=int, default=0, metavar="N", help="audio track, zero based (default: 0)")
    parser.add_argument("-y", "--overwrite", action="store_true", help="replace existing MP3 files")
    parser.add_argument("--dry-run", action="store_true", help="show planned conversions without converting")
    parser.add_argument("--version", action="version", version=f"mp3ify {VERSION}")
    return parser


def collect_files(raw_inputs: list[str], recursive: bool) -> tuple[list[tuple[Path, Path]], list[str]]:
    """Return [(source, relative source path)] and problems. Relative path is used with -d."""
    collected: list[tuple[Path, Path]] = []
    errors: list[str] = []
    seen: set[str] = set()

    for raw in raw_inputs:
        expanded = os.path.expandvars(os.path.expanduser(raw))
        # An existing path is always literal. Windows video names commonly
        # contain square brackets (e.g. "clip [12345].mp4"), which glob would
        # otherwise misinterpret as a character class.
        # Only expand wildcard patterns when that exact path does not exist.
        if Path(expanded).exists():
            candidates = [expanded]
        elif glob.has_magic(expanded):
            candidates = glob.glob(expanded, recursive=recursive)
        else:
            candidates = [expanded]
        if not candidates:
            errors.append(f"No matches: {raw}")
        for candidate in candidates:
            path = Path(candidate)
            if path.is_file():
                if path.suffix.lower() != ".mp4":
                    errors.append(f"Not an MP4: {path}")
                    continue
                sources = [(path, Path(path.name))]
            elif path.is_dir():
                iterator = path.rglob("*") if recursive else path.iterdir()
                sources = [
                    (child, child.relative_to(path))
                    for child in sorted(iterator, key=lambda p: str(p).lower())
                    if child.is_file() and child.suffix.lower() == ".mp4"
                ]
                if not sources:
                    errors.append(f"No MP4 files found: {path}")
            else:
                errors.append(f"Not found: {path}")
                continue

            for source, relative in sources:
                key = os.path.normcase(os.path.abspath(source))
                if key not in seen:
                    collected.append((source, relative))
                    seen.add(key)

    return collected, errors


def find_ffmpeg() -> str | None:
    """Prefer ffmpeg.exe bundled alongside the script, otherwise use PATH."""
    bases = [Path(__file__).resolve().parent]
    if getattr(sys, "frozen", False):  # PyInstaller standalone .exe
        bases.insert(0, Path(sys.executable).resolve().parent)
    for candidate in (base / name for base in bases for name in ("ffmpeg.exe", "ffmpeg")):
        if candidate.is_file():
            return str(candidate)
    return shutil.which("ffmpeg")


def convert(ffmpeg: str, source: Path, destination: Path, args: argparse.Namespace) -> tuple[str, str]:
    if destination.exists() and not args.overwrite:
        return "skipped", f"Already exists: {destination} (use -y to overwrite)"
    if args.dry_run:
        return "ok", f"WOULD CREATE: {destination}"

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return "failed", f"Cannot create output directory: {exc}"

    # Encode to a unique temporary MP3, so a failed conversion doesn't leave
    # behind a broken final output or destroy an existing MP3.
    temporary = destination.with_name(f".{destination.stem}.{uuid.uuid4().hex}.part.mp3")
    command = [
        ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source), "-map", f"0:a:{args.track}", "-vn",
        "-map_metadata", "0", "-c:a", "libmp3lame",
    ]
    if args.bitrate is None:
        command += ["-q:a", str(args.quality)]
    else:
        command += ["-b:a", f"{args.bitrate}k"]
    command += ["-id3v2_version", "3", str(temporary)]

    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding="utf-8", errors="replace", check=False)
        if result.returncode != 0:
            message = (result.stderr or result.stdout).strip().splitlines()
            return "failed", message[-1] if message else f"FFmpeg exit code {result.returncode}"
        if not temporary.is_file() or temporary.stat().st_size == 0:
            return "failed", "FFmpeg did not produce a valid MP3 file"
        if destination.exists() and not args.overwrite:
            return "skipped", f"Already exists: {destination}"
        os.replace(temporary, destination)
        return "ok", f"CREATED: {destination} ({destination.stat().st_size / 1024 / 1024:.2f} MB)"
    except (OSError, subprocess.SubprocessError) as exc:
        return "failed", str(exc)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.track < 0:
        parser.error("--track must be >= 0")
    if args.output and args.out_dir:
        parser.error("-o and -d cannot be used together")
    if args.output and Path(args.output).suffix.lower() != ".mp3":
        parser.error("-o output filename must end in .mp3")

    files, problems = collect_files(args.inputs, args.recursive)
    if args.output and len(files) != 1:
        parser.error("-o requires exactly one MP4 file")
    if not files:
        for problem in problems:
            print(f"[WARN] {problem}", file=sys.stderr)
        print("No MP4 files to convert.", file=sys.stderr)
        return 1

    ffmpeg = find_ffmpeg()
    if not ffmpeg and not args.dry_run:
        print("[ERROR] FFmpeg not found. Install it with: winget install -e --id Gyan.FFmpeg", file=sys.stderr)
        print("Then open a NEW CMD window and run: ffmpeg -version", file=sys.stderr)
        return 2

    destination_dir = Path(args.out_dir).expanduser() if args.out_dir else None
    output_file = Path(args.output).expanduser() if args.output else None
    succeeded = skipped = failed = 0
    for index, (source, relpath) in enumerate(files, start=1):
        destination = (output_file if output_file else
                       destination_dir / relpath.with_suffix(".mp3") if destination_dir else
                       source.with_suffix(".mp3"))
        print(f"[{index}/{len(files)}] {source}", flush=True)
        status, message = convert(ffmpeg or "ffmpeg", source, destination, args)
        print(f"  [{status.upper()}] {message}", flush=True)
        succeeded += status == "ok"
        skipped += status == "skipped"
        failed += status == "failed"

    for problem in problems:
        print(f"[WARN] {problem}", file=sys.stderr)
    print(f"Done: {succeeded} created, {skipped} skipped, {failed} failed.")
    return 1 if problems or failed else 0


if __name__ == "__main__":
    sys.exit(main())
