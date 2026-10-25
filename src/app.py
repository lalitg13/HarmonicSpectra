"""FastAPI application for Audio Spectrogram & Harmonic Frequency Analyzer.

Exposes REST endpoints for real-time DSP analysis, Fast Fourier Transform computation,
spectral centroid tracking, and procedural audio synthesis.
"""

from __future__ import annotations

import base64
import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.dsp_engine import DSPEngine
from src.synthesizer import AudioSynthesizer

app = FastAPI(
    title="HarmonicSpectra Audio DSP API",
    description="High-precision audio spectral analysis, FFT decomposition, and harmonic overtone tracking engine.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")
dsp = DSPEngine(default_sample_rate=44100)
synth = AudioSynthesizer(sample_rate=44100)


class SynthesisRequest(BaseModel):
    wave_type: str = Field(default="sawtooth", description="Waveform type: sine, sawtooth, square, triangle, organ, chirp")
    frequency_hz: float = Field(default=440.0, ge=20.0, le=10000.0, description="Base pitch frequency in Hz")
    duration_sec: float = Field(default=1.5, ge=0.1, le=5.0, description="Signal duration in seconds")
    n_fft: int = Field(default=2048, description="FFT window size")
    window_type: str = Field(default="hann", description="Windowing function")


class RawSignalRequest(BaseModel):
    samples: List[float] = Field(..., description="Array of normalized audio samples [-1.0, 1.0]")
    sample_rate: int = Field(default=44100, ge=8000, le=96000)
    n_fft: int = Field(default=2048)
    window_type: str = Field(default="hann")


@app.get("/api/health")
def health_check() -> Dict[str, str]:
    return {"status": "HEALTHY", "system": "HarmonicSpectra", "version": "1.0.0"}


@app.post("/api/analyze-synthetic")
def analyze_synthetic(req: SynthesisRequest) -> Dict[str, Any]:
    """Generate waveform and execute comprehensive FFT and harmonic decomposition."""
    signal = synth.generate_waveform(wave_type=req.wave_type, freq=req.frequency_hz, duration=req.duration_sec)
    wav_bytes = synth.to_wav_bytes(signal)
    wav_b64 = base64.b64encode(wav_bytes).decode("ascii")

    fft_results = dsp.compute_fft(
        audio_signal=signal,
        sample_rate=44100,
        n_fft=req.n_fft,
        window_type=req.window_type,
    )

    spectrogram_results = dsp.compute_spectrogram(
        audio_signal=signal,
        sample_rate=44100,
        n_fft=1024,
        hop_length=512,
    )

    # Subsample waveform points for visual oscilloscope
    n_pts = min(len(signal), 600)
    step = len(signal) // n_pts
    oscilloscope_pts = [round(float(signal[i]), 4) for i in range(0, len(signal), step)][:n_pts]

    return {
        "wave_type": req.wave_type,
        "input_frequency_hz": req.frequency_hz,
        "duration_sec": req.duration_sec,
        "fft_analysis": fft_results,
        "spectrogram": spectrogram_results,
        "oscilloscope_samples": oscilloscope_pts,
        "audio_base64_wav": wav_b64,
    }


@app.post("/api/analyze-raw")
def analyze_raw(req: RawSignalRequest) -> Dict[str, Any]:
    """Analyze client-provided raw audio sample buffer."""
    import numpy as np

    arr = np.array(req.samples, dtype=np.float32)
    fft_results = dsp.compute_fft(
        audio_signal=arr,
        sample_rate=req.sample_rate,
        n_fft=req.n_fft,
        window_type=req.window_type,
    )
    return fft_results


if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index() -> FileResponse:
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="Static assets missing")
