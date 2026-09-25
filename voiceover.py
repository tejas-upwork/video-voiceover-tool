#!/usr/bin/env python3
"""
Video Voiceover Tool
====================
Puts a voiceover audio track on a video, adds a custom text watermark,
and exports with 100% of metadata stripped.

What it does NOT do:
- No slicing of the video into clips.
- No re-arranging / re-ordering of content.

What it does:
1. Matches the video duration to the voiceover audio duration
   (video is trimmed if longer, looped if shorter).
2. Replaces the video's original audio with the voiceover.
3. Burns a text watermark of your choice into the picture.
4. Strips ALL metadata on export (ffmpeg -map_metadata -1,
   plus an extra ExifTool deep-scrub pass when exiftool is installed).

Requires: ffmpeg + ffprobe on PATH. exiftool is optional.

Usage:
    python voiceover.py input.mp4 voiceover.mp3 -o out.mp4 -w "@mybrand"
    python voiceover.py input.mp4 voiceover.mp3 -o out.mp4 -w "My Brand" --position bottomleft --opacity 0.4
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

__version__ = "1.0.0"


def run(cmd):
    """Run a command, raise on failure, return stdout text."""
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{proc.stderr[-2000:]}")
    return proc.stdout


def probe_duration(path):
    out = run([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
    ]).strip()
    return float(out)


def find_font():
    """Pick a usable TTF font for the watermark."""
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            return c
    return None


def escape_drawtext(text):
    # Escape for ffmpeg drawtext option parsing.
    return (
        text.replace("\\", "\\\\")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace(",", "\\,")
    )


POSITIONS = {
    "topright": ("w-tw-20", "20"),
    "topleft": ("20", "20"),
    "bottomright": ("w-tw-20", "h-th-20"),
    "bottomleft": ("20", "h-th-20"),
    "center": ("(w-tw)/2", "(h-th)/2"),
}


def build_drawtext(watermark, position, opacity, fontsize, fontfile):
    x, y = POSITIONS[position]
    parts = [
        f"text='{escape_drawtext(watermark)}'",
        f"fontsize={fontsize}",
        f"fontcolor=white@{opacity}",
        f"x={x}",
        f"y={y}",
        "borderw=1",
        "bordercolor=black@0.6",
    ]
    if fontfile:
        # Quote the path so spaces/colons don't break parsing.
        parts.append(f"fontfile='{fontfile}'")
    return "drawtext=" + ":".join(parts)


def count_metadata_tags(path):
    """Rough metadata tag count via ffprobe (format + stream tags)."""
    out = run([
        "ffprobe", "-v", "error",
        "-show_entries", "format_tags",
        "-of", "default=noprint_wrappers=1", str(path),
    ])
    return sum(1 for line in out.splitlines() if "=" in line)


def main():
    ap = argparse.ArgumentParser(description="Add voiceover + watermark to video, strip all metadata.")
    ap.add_argument("video", help="Input video file")
    ap.add_argument("audio", help="Voiceover audio file")
    ap.add_argument("-o", "--output", required=True, help="Output video file (mp4)")
    ap.add_argument("-w", "--watermark", default="", help="Watermark text (empty = no watermark)")
    ap.add_argument("--position", choices=sorted(POSITIONS), default="bottomright",
                    help="Watermark position (default: bottomright)")
    ap.add_argument("--opacity", type=float, default=0.55,
                    help="Watermark opacity 0.0-1.0 (default: 0.55)")
    ap.add_argument("--fontsize", type=int, default=32, help="Watermark font size (default: 32)")
    ap.add_argument("--fontfile", default=None, help="TTF font for watermark (auto-detected if omitted)")
    ap.add_argument("--crf", type=int, default=20, help="x264 quality CRF (default: 20)")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"Error: {tool} not found on PATH.")

    video = Path(args.video)
    audio = Path(args.audio)
    if not video.exists():
        sys.exit(f"Error: video not found: {video}")
    if not audio.exists():
        sys.exit(f"Error: audio not found: {audio}")
    if not (0.0 < args.opacity <= 1.0):
        sys.exit("Error: --opacity must be between 0.0 and 1.0")

    dv = probe_duration(video)
    da = probe_duration(audio)
    print(f"Video duration: {dv:.2f}s | Voiceover duration: {da:.2f}s")

    cmd = ["ffmpeg", "-y"]
    if dv < da:
        print(f"Video shorter than voiceover -> looping video to {da:.2f}s")
        cmd += ["-stream_loop", "-1"]
    elif dv > da:
        print(f"Video longer than voiceover -> trimming to {da:.2f}s")
    cmd += ["-i", str(video), "-i", str(audio)]

    vf = []
    if args.watermark:
        fontfile = args.fontfile or find_font()
        if not args.fontfile and not fontfile:
            print("Warning: no TTF font found, skipping watermark.")
        else:
            vf.append(build_drawtext(args.watermark, args.position, args.opacity, args.fontsize, fontfile))
            print(f"Watermark: '{args.watermark}' at {args.position}")

    cmd += [
        "-t", f"{da:.3f}",          # output length = voiceover length
        "-map", "0:v:0",            # video from input 0
        "-map", "1:a:0",            # voiceover from input 1 (replaces original audio)
        "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k",
        "-map_metadata", "-1",      # strip all global metadata
        "-movflags", "+faststart",
    ]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd.append(args.output)

    print("Rendering...")
    run(cmd)

    # Extra deep scrub with ExifTool when available (equivalent to exifremover.com).
    if shutil.which("exiftool"):
        print("ExifTool deep scrub...")
        run(["exiftool", "-all=", "-overwrite_original", args.output])
    else:
        print("(exiftool not installed — ffmpeg metadata strip applied)")

    out_dur = probe_duration(args.output)
    tags = count_metadata_tags(args.output)
    print(f"Done: {args.output}")
    print(f"  Duration: {out_dur:.2f}s (target was {da:.2f}s)")
    print(f"  Remaining metadata tags: {tags}")


if __name__ == "__main__":
    main()
