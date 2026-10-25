# HarmonicSpectra

[![Python](https://img.shields.io/badge/Python-3.9%20|%203.10%20|%203.11%20|%203.12%20|%203.15-3776ab.svg?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![SciPy](https://img.shields.io/badge/SciPy-1.10+-8caae6.svg?style=flat-square&logo=scipy&logoColor=white)](https://scipy.org/)
[![NumPy](https://img.shields.io/badge/NumPy-1.24+-013243.svg?style=flat-square&logo=numpy&logoColor=white)](https://numpy.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square)](LICENSE)
[![Status: Production](https://img.shields.io/badge/Status-Production--Grade-00f3ff.svg?style=flat-square)](#)

> [!NOTE]
> High-precision acoustic signal processing pipeline and studio audio engineering deck. Calculates discrete Fast Fourier Transforms (FFT), Short-Time Fourier Transforms (STFT), harmonic overtone ratios, spectral centroid shifts, and normalized autocorrelation pitch tracking.

---

## Technical Architecture

```
+-------------------------------------------------------------------------------------------------+
|                                 HARMONIC SPECTRA DSP PIPELINE                                   |
+-------------------------------------------------------------------------------------------------+
|                                                                                                 |
|   +-----------------------+      +-----------------------+      +---------------------------+   |
|   |  Audio Ingestion      | ---> |  Window Function      | ---> |  Real-Valued FFT / STFT   |   |
|   |  (Microphone / Synth) |      |  (Hann/Hamming/Black) |      |  (Cooley-Tukey Algorithm) |   |
|   +-----------------------+      +-----------------------+      +---------------------------+   |
|                                                                               |                 |
|                                                                               v                 |
|   +-----------------------+      +-----------------------+      +---------------------------+   |
|   |  Harmonic Ratio       | <--- |  Sub-Bin Peak Quad    | <--- |  Magnitude Normalization  |   |
|   |  Extraction [1f..8f]  |      |  Interpolation (f0)   |      |  (0 to -100 dBFS Scale)   |   |
|   +-----------------------+      +-----------------------+      +---------------------------+   |
|               |                              |                                                  |
|               v                              v                                                  |
|   +-----------------------------------------------------------------------------------------+   |
|   |  Timbral Descriptors (Spectral Centroid, 85% Roll-off, Wiener Spectral Flatness)        |   |
|   +-----------------------------------------------------------------------------------------+   |
|                                              |                                                  |
|                                              v                                                  |
|   +-----------------------------------------------------------------------------------------+   |
|   |  Dark-Mode Studio Deck UI (#121215 Slate, #00f3ff Cyan / #bc13fe Violet Visualizers)     |   |
|   +-----------------------------------------------------------------------------------------+   |
+-------------------------------------------------------------------------------------------------+
```

---

## Signal Processing Specifications

| Parameter | Specification | Functional Description |
|---|---|---|
| **Sampling Frequency ($f_s$)** | 44,100 Hz | Standard professional audio sampling rate |
| **Nyquist Limit ($f_N$)** | 22,050 Hz | Upper frequency boundary for unaliased signal representation |
| **FFT Windows** | 1024, 2048, 4096 pts | Configurable frequency vs temporal resolution tradeoff |
| **Windowing Types** | Hann, Hamming, Blackman | Sidelobe suppression and spectral leakage attenuation |
| **Decibel Dynamic Range** | -100.0 dBFS to 0.0 dBFS | Normalized log magnitude scale |
| **Pitch Detection Method** | Autocorrelation with Quadratic Peak Fit | Precision sub-bin pitch frequency estimation |

---

## Mathematical Formulation

### 1. Discrete Fast Fourier Transform
For a windowed time series $x[n] \cdot w[n]$ of length $N$:

$$X[k] = \sum_{n=0}^{N-1} x[n] w[n] e^{-j 2\pi k n / N}, \quad k = 0, 1, \dots, \frac{N}{2}$$

The physical frequency corresponding to bin index $k$ is $f_k = \frac{k \cdot f_s}{N}$.

### 2. Spectral Centroid
Quantifies the brightness of a sound by computing the weighted center of mass of the spectrum:

$$\text{Centroid} = \frac{\sum_{k=0}^{N/2} f_k |X[k]|}{\sum_{k=0}^{N/2} |X[k]|}$$

### 3. Spectral Roll-off (85%)
The boundary frequency $f_R$ below which 85% of total spectral power resides:

$$\sum_{k=0}^{R} |X[k]|^2 = 0.85 \sum_{k=0}^{N/2} |X[k]|^2$$

### 4. Wiener Spectral Flatness
Measures the tone-to-noise ratio via the quotient of geometric and arithmetic spectral means:

$$\text{Flatness} = \frac{\exp\left( \frac{1}{M} \sum_{k=0}^{M-1} \ln |X[k]|^2 \right)}{\frac{1}{M} \sum_{k=0}^{M-1} |X[k]|^2}$$

Where $\text{Flatness} \approx 0$ indicates a pure harmonic tone and $\text{Flatness} \approx 1$ indicates white noise.

---

## REST API Specification

### Endpoint: `POST /api/analyze-synthetic`
Generates an audio waveform and outputs complete DSP analysis metrics and spectrogram matrices.

**Request Payload:**
```json
{
  "wave_type": "sawtooth",
  "frequency_hz": 440.0,
  "duration_sec": 1.2,
  "n_fft": 2048,
  "window_type": "hann"
}
```

**Response Payload Sample:**
```json
{
  "wave_type": "sawtooth",
  "input_frequency_hz": 440.0,
  "duration_sec": 1.2,
  "fft_analysis": {
    "fundamental_frequency_hz": 440.0,
    "spectral_centroid_hz": 1284.2,
    "spectral_rolloff_85_hz": 3520.0,
    "spectral_flatness": 0.0182,
    "harmonics": [
      {
        "harmonic_number": 1,
        "harmonic_ratio": "1:1",
        "target_hz": 440.0,
        "actual_hz": 440.0,
        "relative_amplitude_db": 0.0
      },
      {
        "harmonic_number": 2,
        "harmonic_ratio": "2:1",
        "target_hz": 880.0,
        "actual_hz": 880.0,
        "relative_amplitude_db": -6.02
      }
    ]
  }
}
```

---

## Installation & Execution

### 1. Requirements
Ensure Python 3.9+ is installed:
```bash
python3 --version
```

### 2. Dependency Installation
```bash
pip install -r requirements.txt
```

### 3. Run Test Suite
```bash
pytest -v tests/
```

### 4. Launch Studio Server
```bash
uvicorn src.app:app --host 0.0.0.0 --port 8001 --reload
```
Navigate to `http://localhost:8001` in any modern web browser.

---

## License

This software is released under the MIT License. Refer to the LICENSE file for details.
