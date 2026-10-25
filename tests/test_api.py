"""Integration tests for HarmonicSpectra FastAPI application."""

from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["system"] == "HarmonicSpectra"


def test_analyze_synthetic_endpoint():
    payload = {
        "wave_type": "square",
        "frequency_hz": 440.0,
        "duration_sec": 0.5,
        "n_fft": 2048,
        "window_type": "hann",
    }
    res = client.post("/api/analyze-synthetic", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["wave_type"] == "square"
    assert "fft_analysis" in data
    assert "spectrogram" in data
    assert "oscilloscope_samples" in data
    assert "audio_base64_wav" in data
