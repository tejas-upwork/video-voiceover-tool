# Video Voiceover Tool

Put a voiceover track on any video, burn in a custom text watermark, and export
with **100% of metadata stripped**.

## What it does

1. **Voiceover** — replaces the video's original audio with your voiceover file.
2. **Duration match** — the output is exactly as long as the voiceover
   (video is trimmed if longer, looped if shorter). No slicing, no re-arranging.
3. **Watermark** — your custom text, with position / opacity / size options.
4. **Metadata scrub** — every export strips all metadata
   (`ffmpeg -map_metadata -1`, plus an ExifTool `-all=` deep-scrub pass
   when `exiftool` is installed).

## Requirements

- `ffmpeg` + `ffprobe` on PATH
- `exiftool` (optional, for the extra deep-scrub pass)
- Python 3.8+

## Usage

```bash
python voiceover.py input.mp4 voiceover.mp3 -o out.mp4 -w "@mybrand"
```

More options:

```bash
python voiceover.py input.mp4 voiceover.mp3 -o out.mp4 \
  -w "My Brand" --position bottomleft --opacity 0.4 --fontsize 28
```

| Option | Default | Description |
|---|---|---|
| `-w / --watermark` | (none) | Watermark text |
| `--position` | `bottomright` | `topleft`, `topright`, `bottomleft`, `bottomright`, `center` |
| `--opacity` | `0.55` | 0.0–1.0 |
| `--fontsize` | `32` | Watermark font size |
| `--fontfile` | auto | Path to a TTF font |
| `--crf` | `20` | x264 quality (lower = better) |

## Example

```bash
# 10s video + 6s voiceover -> 6s watermarked output, no metadata
python voiceover.py clip.mp4 narration.mp3 -o final.mp4 -w "@mybrand"
```

## Note

Sample / spec work created for portfolio purposes.
