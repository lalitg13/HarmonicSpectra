"""Unit tests for procedural audio synthesizer."""

import numpy as np
import pytest
from src.synthesizer import AudioSynthesizer


@pytest.fixture
def synth():
    return AudioSynthesizer(sample_rate=44100)


def test_generate_waveforms(synth: AudioSynthesizer):
    for wave in ["sawtooth", "square", "triangle", "sine", "organ", "chirp"]:
        signal = synth.generate_waveform(wave_type=wave, freq=300.0, duration=0.5)
        assert isinstance(signal, np.ndarray)
        assert len(signal) == int(44100 * 0.5)
        assert np.max(np.abs(signal)) <= 1.0


def test_to_wav_bytes(synth: AudioSynthesizer):
    signal = synth.generate_sine(freq=440.0, duration=0.2)
    wav_bytes = synth.to_wav_bytes(signal)
    assert isinstance(wav_bytes, bytes)
    assert len(wav_bytes) > 44  # Valid RIFF header + payload
    assert wav_bytes[:4] == b"RIFF"
