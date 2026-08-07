# Audio Rearrangement

Audio rearrangement is a modular pipeline controlled by a set of **settings**
(`AudioSettings`). The same knobs are exposed in two places:

- the TUI **Advanced Audio Options** screen ([tui.md](tui.md)), and
- the `aud2aud` CLI flags ([cli.md](cli.md)).

The output is always written as a **WAV** file at the target's sample rate.

> **No FFmpeg required.** Input is decoded with the libsndfile library bundled inside
> `soundfile`, which reads WAV, FLAC, OGG, AIFF, **and MP3** natively.

---

## The default: spectral cross-synthesis

With no tuning, the pipeline does **spectral magnitude remapping**:

1. Load the source and target; resample the source to the target's sample rate.
2. Compute an STFT of both (FFT 2048, hop 512).
3. Rank-order the source magnitudes and the target magnitudes, then pair them
   (rank `i` of source → rank `i` of target) — a 1-D optimal-transport remap.
4. Resynthesise using the **source's** phases (`--phase source`).
5. Write the result.

The familiar result: the *energy/shape* of the source is reshaped toward the target,
but the source's own pitch and timbre are preserved.

### Why these defaults

| Setting | Default | Meaning |
|---|---|---|
| `remap_spectrum` | `true` | do the spectral remap |
| `reorder_time` | `false` | don't additionally slice/reorder in time |
| `normalize` | `false` | write the raw resynthesis (matches the original algorithm exactly) |
| `phase_mode` | `source` | keep the source's phase |
| `fft_size` / `hop_length` | `2048` / `512` | STFT windowing |

> These defaults reproduce behaviour identical to the classic (pre-refactor) version.

---

## The settings, explained

### "What we allow the rearrangement to change"

| Setting | TUI | CLI | Effect |
|---|---|---|---|
| Reorder time segments | on/off | `--time` / `--no-time` | Cut the source into uniform segments and place them into the order defined below. Segments keep their own pitch and frequency content — this is the "pure cut and splice" mode. |
| Remap frequency spectrum | on/off | `--spectral` / `--no-spectral` | Do the STFT magnitude remap (the default). |
| Shift pitch | on/off | `--pitch N` | Enable pitch shifting by `N` semitones. |
| Remap loudness / energy | on/off | `--energy` | Scale each output segment's RMS toward the target's per-segment RMS. |
| Normalize output | on/off | `--no-normalize` | Peak-normalize the final mix to 0.95. Off by default. |

### Segmentation / DSP

| Setting | TUI | CLI | Default | Effect |
|---|---|---|---|---|
| Segment size | number | `--chunk-ms` | `60` ms | Length of each slice for `reorder_time`. Smaller → more granular splicing. |
| Crossfade | number | `--crossfade` | `0` ms | Crossfade the joins. `0` = hard cuts (exact length); larger values smooth joins but shorten the output slightly. |
| FFT size | number | `--fft` | `2048` | Window size for the spectral mode. Powers of two; larger = better frequency resolution. |
| Hop length | number | `--hop` | `512` | STFT step between windows. |

### Sorting / variation

For `reorder_time = true`, segments are ordered by a **sort key**. The pipeline ranks the
source segments and the target segments and maps rank-for-rank, exactly like the image
algorithm maps pixels.

| Setting | TUI | CLI | Default | Effect |
|---|---|---|---|---|
| Sort key | choice | `--sort-key` | `energy` | Feature used to order segments: `energy`, `amplitude`, `zcr` (zero-crossing rate), `centroid`, or `none` (keep source order). |
| Randomize order | on/off | `--randomize` | off | Shuffle segments randomly instead of sorting. |
| Random seed | number | `--seed` | `0` | Seed for the shuffle. |
| Reverse order | on/off | `--reverse` | off | Reverse the resulting order. |

### Pitch

| Setting | TUI | CLI | Default | Effect |
|---|---|---|---|---|
| Pitch shift (semitones) | number | `--pitch` | `0` | Shift pitch by semitones (`-12` = an octave down, `+7` = a fifth up). |
| Keep duration | on/off | `--no-keep-duration` | on | Time-stretch back to the original length after a pitch shift. Off → the pitch shift also changes the duration. |

### Spectral phase

| Setting | TUI | CLI | Default | Effect |
|---|---|---|---|---|
| Spectral phase | choice | `--phase` | `source` | Which phase to resynthesise with: `source` (original timbre), `target` (target's phase), or `random` (noise-like). Only relevant when the spectral remap is enabled. |

### Output

| Setting | TUI | CLI | Default | Effect |
|---|---|---|---|---|
| Dry/wet mix | number | `--dry-wet` | `0` | Blend the result with the dry source. `0.0` = full effect, `1.0` = original source. |

---

## Suggested presets

**Classic (default)** — spectral cross-synthesis:
```
aud2aud vocal.wav pad.flac            # audio.flac decides structure, vocal keeps timbre
```

**Pure cut & reorder** — splice source segments onto the target's energy profile:
```
--time --no-spectral
```

**Splice + spectral + pitch**:
```
--time --pitch 7
```

**Glitch (random segmentation)**:
```
--time --no-spectral --randomize --seed 42
```

**Lo-fi blend**:
```
--spectral --phase random --energy --dry-wet 0.4
```

---

## The pipeline order

When multiple transforms are enabled they run in this order:

1. `reorder_time` — slice and reorder the source.
2. `shape_pitch` — pitch shift (with optional time-stretch).
3. `remap_spectrum` — STFT magnitude remap + phase selection.
4. `remap_energy` — per-segment loudness matching.
5. `dry_wet` — mix with the original source.
6. `normalize` — optional peak normalization.

The result is written as WAV at the target sample rate.