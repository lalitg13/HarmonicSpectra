"""Unit tests for digital signal processing functions."""

import numpy as np
import pytest
from src.dsp_engine import DSPEngine
from src.synthesizer import AudioSynthesizer


@pytest.fixture
def dsp():
    return DSPEngine(default_sample_rate=44100)


@pytest.fixture
def synth():
    return AudioSynthesizer(sample_rate=44100)


def test_fft_frequency_peak_accuracy(dsp: DSPEngine, synth: AudioSynthesizer):
    target_freq = 440.0
    signal = synth.generate_sine(freq=target_freq, duration=1.0)
    result = dsp.compute_fft(signal, sample_rate=44100, n_fft=4096)

    assert result["fundamental_frequency_hz"] is not None
    assert abs(result["fundamental_frequency_hz"] - target_freq) < 5.0
    assert abs(result["spectral_centroid_hz"] - target_freq) < 25.0


def test_harmonic_series_extraction(dsp: DSPEngine, synth: AudioSynthesizer):
    fundamental = 200.0
    signal = synth.generate_harmonic_series(fundamental=fundamental, duration=1.0)
    result = dsp.compute_fft(signal, sample_rate=44100, n_fft=4096)

    harmonics = result["harmonics"]
    assert len(harmonics) >= 4

    h1 = harmonics[0]
    assert h1["harmonic_number"] == 1
    assert abs(h1["actual_hz"] - 200.0) < 15.0


def test_spectral_flatness_bounds(dsp: DSPEngine):
    mags = np.ones(100)
    flatness = dsp.compute_spectral_flatness(mags)
    assert np.isclose(flatness, 1.0, atol=1e-3)

    sparse_mags = np.zeros(100)
    sparse_mags[10] = 100.0
    flatness_tone = dsp.compute_spectral_flatness(sparse_mags)
    assert flatness_tone < 0.1
