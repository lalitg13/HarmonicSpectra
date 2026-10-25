# HarmonicSpectra

[![Python](https://img.shields.io/badge/Python-3.9%20|%203.10%20|%203.11%20|%203.12%20|%203.15-3776ab.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SciPy](https://img.shields.io/badge/SciPy-1.10+-8caae6.svg?style=flat-square&logo=scipy&logoColor=white)](https://scipy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Status: Production](https://img.shields.io/badge/Status-Production--Grade-00f3ff.svg?style=flat-square)](#)

> [!NOTE]
> A real-time audio analysis and spectrogram studio. Computes Fast Fourier Transforms (FFT), identifies musical pitch, and displays live frequency readouts on an audio engineering deck.

---

## Overview

HarmonicSpectra converts audio waveforms into their component frequencies. It allows you to synthesize tones or use your microphone, detecting fundamental pitch (F0), overtone harmonics, and spectral brightness in real time.

```
+-----------------------------------------------------------------------+
| Audio Input  -->  FFT Engine  -->  Pitch Detection  -->  Studio Deck  |
| (Synth / Mic)     (Fast Fourier)   (Harmonic Overtones)   (Spectrogram)|
+-----------------------------------------------------------------------+
```

---

## Key Features

- **Live Frequency Spectrum**: Interactive canvas chart displaying frequency distribution from 20 Hz to 20 kHz.
- **Harmonics Table**: Identifies fundamental frequency and calculates overtone ratios (1f, 2f, 3f, up to 8f).
- **Pitch Detection**: Matches detected frequency to the nearest musical note and cents deviation (e.g. A4 +0.0c).
- **Built-in Synthesizer**: Generates Sawtooth, Square, Triangle, Sine, Organ, and Frequency Sweep waveforms.
- **Time-Domain Oscilloscope**: Visualizes raw audio wave shape with peak stereo VU meters.
- **Microphone Support**: Stream live audio directly from your input device with a single click.

---

## Supported Waveforms

| Waveform | Tone Quality | Harmonic Content |
|---|---|---|
| **Sine** | Pure, smooth | Fundamental only (1f) |
| **Sawtooth** | Bright, buzzy, sharp | All integer harmonics (1f, 2f, 3f, 4f...) |
| **Square** | Hollow, woody, digital | Odd harmonics only (1f, 3f, 5f, 7f...) |
| **Triangle** | Mellow, flute-like | Odd harmonics with rapid high-frequency decay |
| **Organ** | Rich, complex, acoustic | Multi-octave harmonic blend |
| **Chirp** | Sweeping, dynamic | Frequency sweep from 100 Hz to 4 kHz |

---

## Quickstart

### 1. Installation

```bash
cd ~/Desktop/Workspace/harmonic-spectra
pip install -r requirements.txt
```

### 2. Run the Application

```bash
uvicorn src.app:app --host 127.0.0.1 --port 8001 --reload
```

Open your browser and navigate to: **http://localhost:8001**

### 3. Run Tests

```bash
pytest -v tests/
```

---

## API Summary

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check and DSP status |
| `POST` | `/api/analyze-synthetic` | Generates a waveform and returns full FFT analysis, harmonics, and audio buffer |
| `POST` | `/api/analyze-raw` | Analyzes a client-provided raw audio sample array |

---

## License

Released under the MIT License.
