# Troubleshooting

Common issues and their fixes.

---

## "MP3 is not supported / requires FFmpeg"

**Fix:** Pixelification does **not** need FFmpeg. The `soundfile` dependency bundles
libsndfile 1.2.x, which decodes MP3 natively. Make sure you have a recent `soundfile`
installed:

```bash
uv tool install --upgrade pixelification   # or
pip install --upgrade soundfile
```

If you still see a decoding error, the file may be corrupt or use an unusual MP3
encoding — try a standard CBR/VBR MP3, or convert with any audio editor.

---

## "I selected an audio file but nothing happens / it says select source first"

The audio file picker filters to `.wav .flac .ogg .aiff .aif .mp3`. If the dialog
shows images instead, you may be running an older build — update the package.

---

## The video result has black bars on the sides

That is intentional. When the source and target aspect ratios differ, the narrower
input is **letterboxed** with black bars so content is never stretched or cropped.

---

## No GPU acceleration / "Hardware acceleration: No"

- The `[cuda]` extra is optional and must be requested at install time:
  `pip install -e ".[cuda]"` or `uv sync --extra cuda`.
- Without it (or without an NVIDIA GPU), everything still runs on NumPy — slower for
  large images/videos, but identical results.
- To force CPU even when CuPy is installed, pass `--cpu` to any CLI command.

---

## File dialog does not open on Linux

The TUI uses a PowerShell dialog on Windows; elsewhere it falls back to Tk. If the
dialog doesn't appear, install Tk support for your distribution, e.g.:

```bash
sudo apt install python3-tk
```

If that's not possible, run the corresponding CLI command instead
(`pixelification img2img a.png b.png`, etc.).

---

## Video output won't open in some players

Output videos use the `mp4v` codec in an `.mp4` container, which is broadly
compatible but occasionally not with very old players. Use a modern player
(VLC, Windows Media Player, MPV), or re-mux/transcode if needed.

---

## `Ctrl+C` does not stop a running video / app freezes

The video loop checks a `_RUNNING` flag once per frame and the app calls
`os._exit` on `KeyboardInterrupt` for immediate termination. If a frame is slow, it
may take a moment. As a last resort, close the terminal.

---

## "Error: source must be an image/video/audio"

The CLI validates extensions against the expected sets:

- image: `.png .jpg .jpeg .bmp .tiff .gif .webp`
- video: `.mp4 .avi .mov .mkv .webm`
- audio: `.wav .flac .ogg .aiff .aif .mp3`

Check your file's actual extension (case-insensitive).

---

## Audio output is shorter than the input

With `--time` (segment reordering) enabled and a non-zero `--crossfade`, crossfading
overlaps the joins and trims a little length per join. Set `--crossfade 0`
(the default) to keep the length exact.

---

## My advanced audio settings vanished

Settings are persisted in `runtime-config.json` (see [installation.md](installation.md)
for the path). If the file is unreadable or the environment changed, settings fall back
to defaults. Corrupted JSON is ignored and recreated.

---

## `pixelification` command not found

The console script may not be on your `PATH`. Reinstall, or run via:

```bash
python -m pixelification.main --version   # from the repo root
```

## Large images/videos use a lot of memory

The whole frame is loaded and sorted. For very large media, consider:

- resizing inputs first, or
- processing with `--cpu` disabled GPU path only if relevant; memory use is similar.
