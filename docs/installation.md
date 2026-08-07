# Installation

Pixelification requires **Python ≥ 3.10** and runs on Windows, macOS, and Linux.

---

## Option 1 — `uv` (recommended)

Install as a global tool:

```bash
uv tool install pixelification
```

Run it from anywhere:

```bash
pixelification
```

## Option 2 — `pip`

```bash
pip install pixelification
```

## Option 3 — `pipx`

No persistent installation needed:

```bash
pipx run pixelification
```

## From source (development)

```bash
git clone <repo>
cd pixelification
uv sync                # or: pip install -e .
uv run pixelification --version
```

---

## Requirements

| Package | Notes |
|---|---|
| `prompt-toolkit >= 3.0` | terminal UI |
| `opencv-python >= 4.0` | image / video I/O and rendering |
| `numpy >= 1.20` | array math |
| `soundfile >= 0.12` | audio I/O (bundles libsndfile — decodes WAV, FLAC, OGG, AIFF **and MP3**) |

There are **no system-level requirements** — no FFmpeg, no external audio decoders.
MP3 decoding is handled by the libsndfile binary bundled inside `soundfile`.

---

## Optional — NVIDIA GPU acceleration (CUDA)

CuPy is **not** installed by default. To enable GPU acceleration for the image and
video rearrangements:

```bash
pip install -e ".[cuda]"        # or with uv:
uv sync --extra cuda            # or: uv sync --all-extras
```

This installs `cupy-cuda13x[ctk]`. Only use it if you have a compatible NVIDIA GPU.
On CPUs (or when CuPy is absent), Pixelification automatically falls back to NumPy —
you never need to configure anything.

> On first launch the tool probes for a CUDA device and writes the result to the
> runtime config (see below). The TUI status line shows
> `Hardware acceleration: Yes (CuPy, N CUDA devices)` or `No`.

---

## Runtime configuration file

On first run, Pixelification creates a small JSON config at an OS-specific location:

| OS | Path |
|---|---|
| Windows | `%APPDATA%\pixelification\runtime-config.json` |
| macOS | `~/Library/Application Support/pixelification/runtime-config.json` |
| Linux | `~/.config/pixelification/runtime-config.json` (or `$XDG_CONFIG_HOME`) |

Example contents:

```json
{
  "audio_settings": {
    "reorder_time": false,
    "remap_spectrum": true,
    ...
  },
  "backend": "cpu",
  "hardware_acceleration_available": false,
  "host_os": "Windows"
}
```

Fields:

| Field | Meaning |
|---|---|
| `host_os` | OS detected at first run |
| `hardware_acceleration_available` | whether a CUDA device was detected |
| `backend` | `"cupy"` if acceleration is available, else `"cpu"` |
| `audio_settings` | your persisted **Advanced Audio Options** (see [audio.md](audio.md)) |

You can edit this file by hand; invalid values are ignored and reset to defaults.
