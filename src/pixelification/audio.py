"""
Audio rearrangement via a modular transform chain.

By default the source audio is cut into segments and rearranged in time
(segments keep their frequency and pitch intact).  Advanced settings can
additionally remap the spectrum, shift pitch, remap loudness and more.
"""

from dataclasses import asdict, dataclass, fields

import numpy as np
import soundfile as sf

SORT_KEYS = ("energy", "amplitude", "zcr", "centroid", "none")
PHASE_MODES = ("source", "target", "random")


@dataclass
class AudioSettings:
    # ── what we allow the rearrangement to change ──────────────────
    reorder_time: bool = True        # cut into segments and reorder them
    remap_spectrum: bool = False     # spectral magnitude remapping (STFT)
    shape_pitch: bool = False        # pitch shift (semitones)
    remap_energy: bool = False       # per-segment loudness matching to target
    normalize: bool = True           # peak-normalize the output

    # ── segmentation / dsp ─────────────────────────────────────────
    segment_ms: float = 60.0         # segment length for time reorder
    crossfade_ms: float = 0.0        # crossfade length between segments
    fft_size: int = 2048             # only used when remap_spectrum
    hop_length: int = 512            # only used when remap_spectrum

    # ── sorting / variation ────────────────────────────────────────
    sort_key: str = "energy"         # energy|amplitude|zcr|centroid|none
    randomize: bool = False
    seed: int = 0
    reverse: bool = False

    # ── pitch ──────────────────────────────────────────────────────
    pitch_shift_semitones: float = 0.0
    keep_duration: bool = True       # time-stretch back to original length

    # ── spectral phase (only when remap_spectrum) ──────────────────
    phase_mode: str = "source"       # source|target|random

    # ── output ─────────────────────────────────────────────────────
    dry_wet: float = 0.0             # 0.0 = full effect, 1.0 = original

    @staticmethod
    def default() -> "AudioSettings":
        return AudioSettings()

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(data) -> "AudioSettings":
        known = {f.name for f in fields(AudioSettings)}
        clean = {k: v for k, v in (data or {}).items() if k in known}
        s = AudioSettings()
        for k, v in clean.items():
            setattr(s, k, v)
        if s.sort_key not in SORT_KEYS:
            s.sort_key = "energy"
        if s.phase_mode not in PHASE_MODES:
            s.phase_mode = "source"
        return s


def read_audio(path):
    data, sr = sf.read(path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data.astype(np.float32), sr


def write_audio(path, samples, sr):
    sf.write(path, samples, sr)


def _resample(samples, src_sr, tgt_sr):
    if src_sr == tgt_sr:
        return samples
    ratio = tgt_sr / src_sr
    out_len = int(len(samples) * ratio)
    indices = np.arange(out_len, dtype=np.float64) / ratio
    return np.interp(
        indices, np.arange(len(samples), dtype=np.float64), samples
    ).astype(np.float32)


def _segment_sort_key(segment, key):
    n = len(segment)
    if n == 0:
        return 0.0
    if key == "amplitude":
        return float(np.mean(np.abs(segment)))
    if key == "zcr":
        return float(np.mean(np.abs(np.signbit(segment[1:]) != np.signbit(segment[:-1]))))
    if key == "centroid":
        mag = np.abs(np.fft.rfft(segment))
        freqs = np.arange(len(mag))
        total = mag.sum()
        return float(freqs @ mag / total) if total > 0 else 0.0
    # default: energy (mean squared amplitude)
    return float(np.mean(segment ** 2))


def _rank_map(src_keys, tgt_keys, rng=None):
    """Order source items by key and map them onto target positions."""
    src_order = np.argsort(src_keys, kind="stable")
    tgt_order = np.argsort(tgt_keys, kind="stable")
    out = np.empty(len(src_keys), dtype=int)
    out[tgt_order] = src_order
    return out


def _segments_to_samples(segments, sample_rate, crossfade_seconds):
    if len(segments) == 0:
        return np.zeros(0, dtype=np.float32)
    if len(segments) == 1:
        return segments[0]
    fade_len = int(crossfade_seconds * sample_rate)
    if fade_len <= 0:
        return np.concatenate(segments)
    fade = np.minimum(fade_len, min(len(s) for s in segments))
    if fade <= 1:
        return np.concatenate(segments)
    ramp = np.linspace(0.0, 1.0, fade, dtype=np.float64)
    out = np.array(segments[0], dtype=np.float64)
    for seg in segments[1:]:
        seg = np.array(seg, dtype=np.float64)
        tail = out[-fade:]
        head = seg[:fade]
        blended = tail * (1.0 - ramp) + head * ramp
        out = np.concatenate([out[:-fade], blended, seg[fade:]])
    return out.astype(np.float32)


def _reorder_time(samples, sort_key, segment_ms, sample_rate, crossfade_ms,
                  randomize, seed, reverse):
    seg_len = max(1, int(segment_ms / 1000.0 * sample_rate))
    n_seg = max(1, int(np.ceil(len(samples) / seg_len)))
    segments = [
        samples[i * seg_len:(i + 1) * seg_len]
        for i in range(n_seg)
    ]
    if randomize:
        rng = np.random.default_rng(seed)
        order = rng.permutation(n_seg)
    elif sort_key == "none":
        order = np.arange(n_seg)
    else:
        keys = [_segment_sort_key(s, sort_key) for s in segments]
        order = np.argsort(keys, kind="stable")
    if reverse:
        order = order[::-1]
    ordered = [segments[i] for i in order]
    return _segments_to_samples(ordered, sample_rate, crossfade_ms / 1000.0)


def stft(samples, fft_size=2048, hop_length=512):
    window = np.hanning(fft_size).astype(np.float32)
    n_frames = max(1, 1 + (len(samples) - fft_size) // hop_length)
    out = np.zeros((fft_size // 2 + 1, n_frames), dtype=np.complex64)
    for i in range(n_frames):
        start = i * hop_length
        frame = samples[start : start + fft_size]
        if len(frame) < fft_size:
            frame = np.pad(frame, (0, fft_size - len(frame)))
        out[:, i] = np.fft.rfft(frame * window)
    return out


def istft(spectrogram, hop_length=512):
    n_frames = spectrogram.shape[1]
    fft_size = 2 * (spectrogram.shape[0] - 1)
    window = np.hanning(fft_size).astype(np.float32)
    out_len = (n_frames - 1) * hop_length + fft_size
    out = np.zeros(out_len, dtype=np.float64)
    for i in range(n_frames):
        frame = np.fft.irfft(spectrogram[:, i]).real.astype(np.float64)
        start = i * hop_length
        out[start : start + fft_size] += frame * window
    return out.astype(np.float32)


def _rearrange_spectrogram(src_mag, tgt_mag):
    s_order = np.argsort(src_mag.ravel())
    t_order = np.argsort(tgt_mag.ravel())
    out = np.empty_like(src_mag.ravel())
    out[t_order] = src_mag.ravel()[s_order]
    return out.reshape(src_mag.shape)


def _rearrange_spectral(samples, target_samples, fft_size, hop_length, phase_mode):
    src_spec = stft(samples, fft_size, hop_length)
    tgt_spec = stft(target_samples, fft_size, hop_length)

    n_frames = min(src_spec.shape[1], tgt_spec.shape[1])
    src_spec = src_spec[:, :n_frames]
    tgt_spec = tgt_spec[:, :n_frames]

    src_mag = np.abs(src_spec)
    src_phase = np.angle(src_spec)
    tgt_mag = np.abs(tgt_spec)

    new_mag = _rearrange_spectrogram(src_mag, tgt_mag)
    if phase_mode == "target":
        phase = np.angle(tgt_spec)
    elif phase_mode == "random":
        rng = np.random.default_rng(0)
        phase = rng.uniform(-np.pi, np.pi, size=src_spec.shape).astype(np.float32)
    else:
        phase = src_phase
    new_spec = new_mag * np.exp(1j * phase)

    return istft(new_spec, hop_length)


def _shift_pitch(samples, semitones, keep_duration, sample_rate):
    if semitones == 0.0:
        return samples
    ratio = 2.0 ** (semitones / 12.0)
    if not keep_duration:
        return _resample(samples, sample_rate, int(sample_rate * ratio))
    stretched = _resample(samples, sample_rate, int(sample_rate * ratio))
    return _resample(stretched, int(sample_rate * ratio), sample_rate)


def _remap_energy(samples, target, n_segments, sample_rate):
    """Scale each output segment's RMS toward the target's per-segment RMS."""
    if len(samples) == 0 or len(target) == 0:
        return samples
    seg_len = max(1, int(len(samples) / n_segments))
    out = np.array(samples, dtype=np.float64)
    t_seg_len = max(1, int(len(target) / n_segments))
    for i in range(n_segments):
        src = out[i * seg_len:(i + 1) * seg_len]
        if len(src) == 0:
            continue
        rms_src = np.sqrt(np.mean(src ** 2))
        tgt = target[i * t_seg_len:(i + 1) * t_seg_len]
        rms_tgt = np.sqrt(np.mean(tgt ** 2)) if len(tgt) else 0.0
        if rms_src > 1e-9 and rms_tgt > 1e-9:
            out[i * seg_len:(i + 1) * seg_len] *= rms_tgt / rms_src
    return out.astype(np.float32)


def _peak_normalize(samples):
    peak = np.max(np.abs(samples)) if len(samples) else 0.0
    if peak > 1e-9:
        return (samples / peak * 0.95).astype(np.float32)
    return samples


def _mix_dry_wet(dry, wet, amount):
    if amount <= 0.0:
        return wet
    if amount >= 1.0:
        return dry
    n = min(len(dry), len(wet))
    if n <= 0:
        return wet
    dry = dry[:n]
    wet = wet[:n]
    return (dry * amount + wet * (1.0 - amount)).astype(np.float32)


def rearrange_audio(source_path, target_path, output_path,
                    settings: AudioSettings | None = None):
    if settings is None:
        settings = AudioSettings.default()

    src, src_sr = read_audio(source_path)
    tgt, tgt_sr = read_audio(target_path)

    target_sr = tgt_sr
    src = _resample(src, src_sr, target_sr)
    tgt = tgt if tgt_sr == target_sr else tgt

    out = src
    dry = src

    if settings.reorder_time:
        out = _reorder_time(
            src,
            sort_key=settings.sort_key,
            segment_ms=settings.segment_ms,
            sample_rate=target_sr,
            crossfade_ms=settings.crossfade_ms,
            randomize=settings.randomize,
            seed=settings.seed,
            reverse=settings.reverse,
        )

    if settings.shape_pitch:
        out = _shift_pitch(
            out,
            settings.pitch_shift_semitones,
            settings.keep_duration,
            target_sr,
        )

    if settings.remap_spectrum:
        out = _rearrange_spectral(
            out, tgt, settings.fft_size, settings.hop_length, settings.phase_mode
        )

    if settings.remap_energy:
        n_seg = max(1, int(len(src) / max(1, int(settings.segment_ms / 1000.0 * target_sr))))
        out = _remap_energy(out, tgt, n_seg, target_sr)

    if settings.dry_wet > 0.0:
        out = _mix_dry_wet(dry, out, settings.dry_wet)

    if settings.normalize:
        out = _peak_normalize(out)

    write_audio(output_path, out, target_sr)
