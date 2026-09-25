# 🎙️ Video Voiceover Tool

![version](https://img.shields.io/badge/version-1.0.0-blue)
![python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![ffmpeg](https://img.shields.io/badge/ffmpeg-required-007808)
![license](https://img.shields.io/badge/license-MIT-green)

> Put a **voiceover track** on any video, burn in a **custom watermark**,
> and export with **100% of metadata stripped**.

## 📖 What is this?

A command-line tool for creators who record a voiceover separately and want
it married to their video — with their brand watermarked on top and every
trace of metadata (camera model, GPS, software tags, …) removed from the
export.

**Deliberately simple:** no clip slicing, no re-arranging of content.
The video keeps its original order; only its length is matched to the audio.

## ✨ Features

- 🎤 **Voiceover muxing** — replaces the video's original audio track
- ⏱️ **Duration matching** — output is exactly as long as the voiceover
  (video trimmed if longer, seamlessly looped if shorter)
- 💧 **Text watermark** — your brand, with position / opacity / size controls
- 🧹 **Metadata scrub** — `ffmpeg -map_metadata -1` on every export,
  plus an ExifTool `-all=` deep-scrub pass when `exiftool` is installed
  (the same approach as exifremover.com)
- 📊 **Report** — prints durations and remaining tag count after each run

## 🛠️ How it works

```
video.mp4 (10s) + voiceover.mp3 (6s)
        │
        ▼
  1. Probe both durations (ffprobe)
  2. Video longer  → trim to audio length   (-t)
     Video shorter → loop to audio length   (-stream_loop)
  3. Map video stream + voiceover audio     (-map 0:v -map 1:a)
  4. Burn watermark via drawtext filter
  5. Encode H.264 + AAC, strip metadata     (-map_metadata -1)
  6. Optional ExifTool -all= deep scrub
        │
        ▼
  final.mp4 (6s, watermarked, zero metadata)
```

## 📦 Requirements

- Python 3.8+
- `ffmpeg` + `ffprobe` on PATH
- `exiftool` — optional, for the extra deep-scrub pass

## 🚀 Usage

```bash
# Basic: voiceover + watermark
python voiceover.py input.mp4 voiceover.mp3 -o final.mp4 -w "@mybrand"

# Custom watermark style
python voiceover.py input.mp4 voiceover.mp3 -o final.mp4 \
  -w "My Brand" --position bottomleft --opacity 0.4 --fontsize 28

# Check version
python voiceover.py --version
```

### Options

| Option | Default | Description |
|---|---|---|
| `-o / --output` | *(required)* | Output MP4 file |
| `-w / --watermark` | *(none)* | Watermark text (empty = no watermark) |
| `--position` | `bottomright` | `topleft`, `topright`, `bottomleft`, `bottomright`, `center` |
| `--opacity` | `0.55` | Watermark opacity, 0.0–1.0 |
| `--fontsize` | `32` | Watermark font size |
| `--fontfile` | auto-detected | Path to a TTF font |
| `--crf` | `20` | x264 quality (lower = better quality) |
| `--version` | | Print version and exit |

## 💡 Example

```bash
# 10s clip + 6s narration -> 6s watermarked video, metadata-free
$ python voiceover.py clip.mp4 narration.mp3 -o final.mp4 -w "@mybrand"
Video duration: 10.00s | Voiceover duration: 6.00s
Video longer than voiceover -> trimming to 6.00s
Watermark: '@mybrand' at bottomright
Rendering...
Done: final.mp4
  Duration: 6.00s (target was 6.00s)
  Remaining metadata tags: 4   # structural MP4 container tags only
```

## 📄 Version

**v1.0.0** — initial release: duration matching (trim/loop), voiceover
replacement, drawtext watermark, metadata strip + ExifTool pass.

## 📝 License

MIT — see [LICENSE](LICENSE).
