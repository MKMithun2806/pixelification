"""
Audio rearrangement via spectral cross-synthesis.

Converts audio → spectrogram → rearrange magnitudes → inverse → audio.
"""

import numpy as np
import soundfile as sf


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


def rearrange_audio(source_path, target_path, output_path,
                    fft_size=2048, hop_length=512):
    src, src_sr = read_audio(source_path)
    tgt, tgt_sr = read_audio(target_path)

    src = _resample(src, src_sr, tgt_sr)

    src_spec = stft(src, fft_size, hop_length)
    tgt_spec = stft(tgt, fft_size, hop_length)

    n_frames = min(src_spec.shape[1], tgt_spec.shape[1])
    src_spec = src_spec[:, :n_frames]
    tgt_spec = tgt_spec[:, :n_frames]

    src_mag = np.abs(src_spec)
    src_phase = np.angle(src_spec)
    tgt_mag = np.abs(tgt_spec)

    new_mag = _rearrange_spectrogram(src_mag, tgt_mag)
    new_spec = new_mag * np.exp(1j * src_phase)

    out_samples = istft(new_spec, hop_length)
    write_audio(output_path, out_samples, tgt_sr)
