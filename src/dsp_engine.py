"""Digital signal processing engine for audio spectrogram and harmonic analysis.

Provides high-resolution Fast Fourier Transforms, spectral centroid computation,
Wiener spectral flatness, harmonic overtone extraction, and pitch detection.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import scipy.fft
import scipy.signal


class DSPEngine:
    """High-performance audio digital signal processing engine."""

    def __init__(self, default_sample_rate: int = 44100) -> None:
        self.default_sample_rate = default_sample_rate

    @staticmethod
    def get_window(window_type: str, n_points: int) -> np.ndarray:
        """Generate specified analysis window function."""
        win_map = {
            "hann": np.hanning(n_points),
            "hamming": np.hamming(n_points),
            "blackman": np.blackman(n_points),
            "rectangular": np.ones(n_points),
        }
        return win_map.get(window_type.lower(), np.hanning(n_points))

    def compute_fft(
        self,
        audio_signal: np.ndarray,
        sample_rate: Optional[int] = None,
        n_fft: int = 2048,
        window_type: str = "hann",
    ) -> Dict[str, Any]:
        """Compute real Fast Fourier Transform on an audio segment.

        Args:
            audio_signal: 1D floating point audio sample array.
            sample_rate: Sampling frequency in Hertz.
            n_fft: FFT window size.
            window_type: Analysis window ('hann', 'hamming', 'blackman', 'rectangular').

        Returns:
            Dictionary containing frequencies, magnitudes (linear & dB), and peak harmonics.
        """
        sr = sample_rate or self.default_sample_rate
        if len(audio_signal) < n_fft:
            audio_signal = np.pad(audio_signal, (0, n_fft - len(audio_signal)))
        else:
            audio_signal = audio_signal[:n_fft]

        # Windowing to mitigate spectral leakage
        window = self.get_window(window_type, n_fft)
        windowed = audio_signal * window

        # Real FFT calculation
        fft_complex = scipy.fft.rfft(windowed, n=n_fft)
        magnitudes_linear = np.abs(fft_complex) / (n_fft / 2.0)
        frequencies = scipy.fft.rfftfreq(n_fft, d=1.0 / sr)

        # Decibel scale normalized to 0 dBFS peak
        eps = 1e-12
        mags_db = 20.0 * np.log10(np.maximum(magnitudes_linear, eps))
        peak_db = np.max(mags_db)
        mags_db_norm = np.clip(mags_db - peak_db, -100.0, 0.0)

        # Spectral Centroid
        centroid = self.compute_spectral_centroid(magnitudes_linear, frequencies)

        # Spectral Flatness (Wiener entropy)
        flatness = self.compute_spectral_flatness(magnitudes_linear)

        # Spectral Roll-off (85%)
        rolloff = self.compute_spectral_rolloff(magnitudes_linear, frequencies, 0.85)

        # Fundamental pitch detection
        f0 = self.detect_pitch_autocorrelation(audio_signal, sr)

        # Extract harmonics if fundamental detected
        harmonics = self.extract_harmonics(frequencies, magnitudes_linear, f0, n_harmonics=8)

        # Downsample for network payload efficiency (e.g. 256 spectrum bins)
        step = max(1, len(frequencies) // 256)
        spectrum_payload = [
            {
                "freq_hz": round(float(frequencies[i]), 1),
                "magnitude_linear": round(float(magnitudes_linear[i]), 6),
                "magnitude_db": round(float(mags_db_norm[i]), 2),
            }
            for i in range(0, len(frequencies), step)
        ]

        return {
            "sample_rate": sr,
            "n_fft": n_fft,
            "fundamental_frequency_hz": round(float(f0), 2) if f0 > 0 else None,
            "spectral_centroid_hz": round(float(centroid), 2),
            "spectral_rolloff_85_hz": round(float(rolloff), 2),
            "spectral_flatness": round(float(flatness), 4),
            "harmonics": harmonics,
            "spectrum": spectrum_payload,
        }

    @staticmethod
    def compute_spectral_centroid(magnitudes: np.ndarray, frequencies: np.ndarray) -> float:
        """Compute center of mass of the spectrum.

        Centroid = sum(f_k * |X_k|) / sum(|X_k|)
        """
        mag_sum = np.sum(magnitudes)
        if mag_sum < 1e-12:
            return 0.0
        return float(np.sum(frequencies * magnitudes) / mag_sum)

    @staticmethod
    def compute_spectral_rolloff(
        magnitudes: np.ndarray, frequencies: np.ndarray, roll_percent: float = 0.85
    ) -> float:
        """Compute frequency below which roll_percent of total spectral energy lies."""
        energy = np.cumsum(magnitudes**2)
        total_energy = energy[-1]
        if total_energy < 1e-12:
            return 0.0
        threshold = roll_percent * total_energy
        idx = np.searchsorted(energy, threshold)
        return float(frequencies[min(idx, len(frequencies) - 1)])

    @staticmethod
    def compute_spectral_flatness(magnitudes: np.ndarray) -> float:
        """Compute Wiener entropy: geometric mean / arithmetic mean of power spectrum."""
        power = magnitudes**2 + 1e-12
        geom_mean = np.exp(np.mean(np.log(power)))
        arith_mean = np.mean(power)
        if arith_mean < 1e-12:
            return 0.0
        return float(np.clip(geom_mean / arith_mean, 0.0, 1.0))

    @staticmethod
    def detect_pitch_autocorrelation(
        audio_signal: np.ndarray,
        sample_rate: int,
        min_freq: float = 40.0,
        max_freq: float = 2400.0,
    ) -> float:
        """Estimate fundamental pitch (f0) using normalized autocorrelation method."""
        sig = audio_signal - np.mean(audio_signal)
        if np.std(sig) < 1e-5:
            return 0.0

        corr = np.correlate(sig, sig, mode="full")
        corr = corr[len(corr) // 2 :]

        min_lag = int(sample_rate / max_freq)
        max_lag = int(sample_rate / min_freq)

        if max_lag >= len(corr):
            max_lag = len(corr) - 1

        search_slice = corr[min_lag:max_lag]
        if len(search_slice) == 0:
            return 0.0

        peak_idx = int(np.argmax(search_slice)) + min_lag

        # Quadratic parabolic interpolation for sub-bin precision
        if 0 < peak_idx < len(corr) - 1:
            alpha = corr[peak_idx - 1]
            beta = corr[peak_idx]
            gamma = corr[peak_idx + 1]
            denom = 2 * (2 * beta - alpha - gamma)
            delta = (alpha - gamma) / denom if denom != 0 else 0.0
            peak_lag = peak_idx + delta
        else:
            peak_lag = peak_idx

        if peak_lag <= 0 or corr[peak_idx] / (corr[0] + 1e-12) < 0.25:
            return 0.0

        return float(sample_rate / peak_lag)

    @staticmethod
    def extract_harmonics(
        frequencies: np.ndarray,
        magnitudes: np.ndarray,
        f0: float,
        n_harmonics: int = 8,
    ) -> List[Dict[str, Any]]:
        """Identify harmonic overtone peaks and ratios relative to f0."""
        if f0 <= 0 or len(frequencies) == 0:
            return []

        harmonics: List[Dict[str, Any]] = []
        max_mag = np.max(magnitudes) if np.max(magnitudes) > 0 else 1.0

        for h in range(1, n_harmonics + 1):
            target_freq = f0 * h
            if target_freq > frequencies[-1]:
                break

            # Search in a narrow window (+/- 5% of target frequency)
            win_hz = max(15.0, target_freq * 0.05)
            mask = (frequencies >= target_freq - win_hz) & (frequencies <= target_freq + win_hz)
            if not np.any(mask):
                continue

            sub_mags = magnitudes[mask]
            sub_freqs = frequencies[mask]
            best_idx = np.argmax(sub_mags)
            peak_hz = float(sub_freqs[best_idx])
            peak_mag = float(sub_mags[best_idx])
            rel_db = 20.0 * np.log10(max(1e-12, peak_mag / max_mag))

            harmonics.append(
                {
                    "harmonic_number": h,
                    "target_hz": round(target_freq, 1),
                    "actual_hz": round(peak_hz, 1),
                    "magnitude_linear": round(peak_mag, 6),
                    "relative_amplitude_db": round(rel_db, 2),
                    "harmonic_ratio": f"{h}:1",
                }
            )

        return harmonics

    def compute_spectrogram(
        self,
        audio_signal: np.ndarray,
        sample_rate: Optional[int] = None,
        n_fft: int = 1024,
        hop_length: int = 512,
    ) -> Dict[str, Any]:
        """Compute Short-Time Fourier Transform (STFT) for time-frequency waterfall representation."""
        sr = sample_rate or self.default_sample_rate
        f, t, zxx = scipy.signal.stft(
            audio_signal,
            fs=sr,
            window="hann",
            nperseg=n_fft,
            noverlap=n_fft - hop_length,
        )

        magnitude = np.abs(zxx)
        eps = 1e-12
        mag_db = 20.0 * np.log10(np.maximum(magnitude, eps))
        mag_db_norm = np.clip(mag_db - np.max(mag_db), -90.0, 0.0)

        # Downsample dimensions for JSON transport if large
        max_t = 64
        max_f = 64
        t_step = max(1, len(t) // max_t)
        f_step = max(1, len(f) // max_f)

        sampled_matrix = mag_db_norm[::f_step, ::t_step]
        sampled_t = t[::t_step]
        sampled_f = f[::f_step]

        return {
            "time_bins": [round(float(val), 3) for val in sampled_t],
            "frequency_bins": [round(float(val), 1) for val in sampled_f],
            "spectrogram_matrix_db": np.round(sampled_matrix, 1).tolist(),
        }
