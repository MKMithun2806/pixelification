# Terminal UI (TUI) Guide

Run `pixelification` with no arguments to open the interactive, keyboard-navigated
terminal UI:

```
  ■ Pixel Rearrangement Tool

  ● Rearrange Images     sort pixels between two images
  ○ Rearrange Videos     sort frames between two videos
  ○ Rearrange Audio      spectral cross-synthesis between two audio clips
  ○ ASCII                convert images to ASCII art
  ○ Quit                 exit the application
```

---

## Keyboard controls (all modes)

| Key | Action |
|---|---|
| `↑` `↓` | Move the cursor |
| `Enter` | Select / confirm / open |
| `1`–`N` | Jump directly to menu item *N* |
| `q` / `Esc` | Quit (or go back on the settings screen) |
| `Ctrl+C` | Quit |

### ASCII mode only
| Key | Action |
|---|---|
| `Shift`+`↑` `↓` | Scroll the art vertically |
| `Shift`+`←` `→` | Scroll the art horizontally |
| `PgUp` / `PgDn` | Jump one page |

---

## File dialogs

Selecting a source/target opens a **native file dialog**; its filter is based on the
current mode:

| Mode | Filter |
|---|---|
| Image | images (`.png .jpg .jpeg .bmp .tiff .gif .webp`) |
| Video | videos (`.mp4 .avi .mov .mkv .webm`) |
| Audio | audio (`.wav .flac .ogg .aiff .aif .mp3`) |

On Windows this uses a PowerShell `OpenFileDialog`; if unavailable it falls back to a
Tk file dialog.

---

## Image Mode

Menu:

```
● Select Source Image     choose the image whose pixels will be rearranged
○ Select Target Image     choose the image whose layout will be approximated
○ Run Rearrangement       execute the sort-based pixel-matching algorithm
○ Save Result Image       save the reconstructed image to disk
○ Back to Main Menu
○ Quit
```

1. Select a **source** image and a **target** image.
2. **Run Rearrangement** — an OpenCV window opens with three panels
   (`Source · Target · Reconstruction`) and animates the pixels sliding into place
   over ~60 frames.
3. Press `Esc` or `q` to close the animation.
4. **Save Result Image** writes `reconstructed_{src}_from_{tgt}.png`.

---

## Video Mode

```
0. Select Source Video
1. Select Target Video
2. Run Video Rearrangement
3. Save Result Video
4. Back to Main Menu
5. Quit
```

1. Select a **source** video (or a still image, which is looped) and a **target** video.
2. **Run Video Rearrangement** processes every frame, showing a progress bar.
3. The result plays in an OpenCV window and loops until closed.
4. **Save Result Video** writes `rearranged_{src}_from_{tgt}.mp4`.

---

## Audio Mode

```
0. Select Source Audio
1. Select Target Audio
2. Advanced Audio Options     ← tune what the rearrangement may change
3. Run Audio Rearrangement
4. Play Result Audio          ← preview with your system player
5. Save Result Audio          writes morphed_{src}_from_{tgt}.wav
6. Back to Main Menu
7. Quit
```

1. Select a **source** and a **target** audio file.
2. Optionally open **Advanced Audio Options** to configure the pipeline (see below).
3. **Run Audio Rearrangement** (defaults = spectral cross-synthesis).
4. **Play Result Audio** previews the temp result with your default system audio player.
5. **Save Result Audio** copies the result to `morphed_{src}_from_{tgt}.wav`.

### Advanced Audio Options screen

Opens a grouped form of every tunable setting. It is also reflected in the
`aud2aud` CLI flags.

| Section | Setting | Type | Default |
|---|---|---|---|
| What may change | Reorder time segments | on/off | off |
| | Remap frequency spectrum | on/off | on |
| | Shift pitch | on/off | off |
| | Remap loudness / energy | on/off | off |
| | Normalize output | on/off | off |
| Segmentation / DSP | Segment size (ms) | number | 60 |
| | Crossfade (ms) | number | 0 |
| | FFT size | number | 2048 |
| | Hop length | number | 512 |
| Sorting | Sort key | choice | energy |
| | Randomize order | on/off | off |
| | Random seed | number | 0 |
| | Reverse order | on/off | off |
| Pitch | Pitch shift (semitones) | number | 0 |
| | Keep duration after pitch | on/off | on |
| Spectral phase | Spectral phase | choice | source |
| Output | Dry/wet mix | number | 0 |
| — | **Reset to default settings** | action | — |

**Editing controls on this screen:**

| Key | Action |
|---|---|
| `↑` `↓` | Move between settings |
| `Enter` | Toggle an on/off, cycle a choice, or open a numeric field for typing |
| `←` `→` | Step a number / cycle a choice |
| `0`–`9`, `-`, `.` | Type into an open numeric field |
| `Backspace` | Delete last typed character |
| `Enter` (while typing) | Commit the value |
| `Esc` | Cancel typing, or return to Audio Mode |
| `Reset to default settings` row | Restore all defaults |

Every change is saved automatically to the runtime config and restored next launch.
See [audio.md](audio.md) for what each setting does.

---

## ASCII Mode

```
0. Select Image
1. Run ASCII Conversion
2. Copy to Clipboard
3. Save Result
4. Back to Main Menu
5. Quit
```

1. **Select Image**, then **Run ASCII Conversion** — the art renders in place.
2. Scroll with `Shift+arrows`, jump with `PgUp`/`PgDn`.
3. **Copy to Clipboard** pipes the art to `clip.exe` (Windows).
4. **Save Result** writes `{stem}_ascii.txt`.