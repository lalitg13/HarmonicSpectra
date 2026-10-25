"""Procedural audio waveform synthesizer for testing and demonstration.

Generates mathematically defined acoustic waveforms, harmonic series, frequency sweeps,
and filtered noise profiles, exporting directly to raw audio arrays or WAV format.
"""

from __future__ import annotations

import io
from typing import List, Optional
import numpy as np
import scipy.io.wavfile
import scipy.signal


class AudioSynthesizer:
    """Procedural audio generator supporting multi-timbre additive synthesis."""

    def __init__(self, sample_rate: int = 44100) -> None:
        self.sample_rate = sample_rate

    def generate_sine(self, freq: float = 440.0, duration: float = 1.0, amplitude: float = 0.8) -> np.ndarray:
        """Generate pure sinusoidal waveform."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        return (amplitude * np.sin(2.0 * np.pi * freq * t)).astype(np.float32)

    def generate_harmonic_series(
        self,
        fundamental: float = 220.0,
        harmonic_weights: Optional[List[float]] = None,
        duration: float = 1.0,
    ) -> np.ndarray:
        """Additive harmonic synthesis combining fundamental and overtones.

        Args:
            fundamental: Fundamental frequency in Hz (e.g. A3 = 220Hz).
            harmonic_weights: Amplitude coefficients for [1f, 2f, 3f, 4f, ...].
            duration: Duration in seconds.

        Returns:
            Normalized 1D floating point audio sample array.
        """
        weights = harmonic_weights or [1.0, 0.5, 0.25, 0.12, 0.06, 0.03, 0.015, 0.008]
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        signal = np.zeros_like(t)

        for harmonic_idx, weight in enumerate(weights, start=1):
            f = fundamental * harmonic_idx
            if f >= self.sample_rate / 2.0:
                break
            signal += weight * np.sin(2.0 * np.pi * f * t)

        # Normalize to prevent digital clipping
        peak = np.max(np.abs(signal))
        if peak > 0:
            signal = (signal / peak) * 0.85

        return signal.astype(np.float32)

    def generate_waveform(self, wave_type: str, freq: float = 440.0, duration: float = 1.0) -> np.ndarray:
        """Generate classic analog synthesizer wave shapes."""
        t = np.linspace(0, duration, int(self.sample_rate * duration), endpoint=False)
        wave = wave_type.lower()

        if wave == "sawtooth":
            signal = scipy.signal.sawtooth(2.0 * np.pi * freq * t)
        elif wave == "square":
            signal = scipy.signal.square(2.0 * np.pi * freq * t)
        elif wave == "triangle":
            signal = scipy.signal.sawtooth(2.0 * np.pi * freq * t, width=0.5)
        elif wave == "chirp":
            signal = scipy.signal.chirp(t, f0=100.0, t1=duration, f1=4000.0, method="logarithmic")
        elif wave == "organ":
            # Odd & even church organ overtone mixture
            signal = (
                1.0 * np.sin(2 * np.pi * freq * t)
                + 0.8 * np.sin(2 * np.pi * freq * 2 * t)
                + 0.4 * np.sin(2 * np.pi * freq * 3 * t)
                + 0.5 * np.sin(2 * np.pi * freq * 4 * t)
                + 0.3 * np.sin(2 * np.pi * freq * 8 * t)
            )
        else:
            signal = np.sin(2.0 * np.pi * freq * t)

        peak = np.max(np.abs(signal))
        if peak > 0:
            signal = (signal / peak) * 0.85

        return signal.astype(np.float32)

    def to_wav_bytes(self, signal: np.ndarray) -> bytes:
        """Encode float audio array into standard 16-bit PCM WAV byte buffer."""
        # Clip and convert float [-1.0, 1.0] to int16 [-32767, 32767]
        clipped = np.clip(signal, -1.0, 1.0)
        int16_samples = (clipped * 32767.0).astype(np.int16)

        buffer = io.BytesIO()
        scipy.io.wavfile.write(buffer, self.sample_rate, int16_samples)
        return buffer.getvalue()
