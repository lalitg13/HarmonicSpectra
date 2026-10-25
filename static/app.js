/* HarmonicSpectra DSP Deck Client Engine */

document.addEventListener("DOMContentLoaded", () => {
  // Elements
  const timbreBtns = document.querySelectorAll(".timbre-btn");
  const freqSlider = document.getElementById("freq-slider");
  const freqReadout = document.getElementById("freq-readout");
  const fftSizeSelect = document.getElementById("fft-size-select");
  const windowSelect = document.getElementById("window-select");
  const generateBtn = document.getElementById("generate-btn");
  const playToneBtn = document.getElementById("play-tone-btn");
  const micToggleBtn = document.getElementById("mic-toggle-btn");

  const dispF0 = document.getElementById("disp-f0");
  const dispNote = document.getElementById("disp-note");
  const dispCentroid = document.getElementById("disp-centroid");
  const dispRolloff = document.getElementById("disp-rolloff");
  const dispFlatness = document.getElementById("disp-flatness");
  const dispNoisiness = document.getElementById("disp-noisiness");

  const vuFillL = document.getElementById("vu-fill-l");
  const vuFillR = document.getElementById("vu-fill-r");
  const vuPeakL = document.getElementById("vu-peak-l");
  const vuPeakR = document.getElementById("vu-peak-r");

  const harmonicTableBody = document.getElementById("harmonic-table-body");
  const dspConsole = document.getElementById("dsp-console");

  const fftCanvas = document.getElementById("fft-canvas");
  const oscCanvas = document.getElementById("osc-canvas");
  const specCanvas = document.getElementById("spectrogram-canvas");

  // State
  let currentWave = "sawtooth";
  let audioContext = null;
  let activeAudioBuffer = null;
  let activeSource = null;
  let isPlaying = false;
  let isMicActive = false;
  let micStream = null;
  let micAnalyser = null;

  // Logging
  function log(msg, type = "event") {
    const time = new Date().toISOString().slice(11, 19);
    const line = document.createElement("div");
    line.className = `log-line ${type}`;
    line.textContent = `[${time}] ${msg}`;
    dspConsole.appendChild(line);
    dspConsole.scrollTop = dspConsole.scrollHeight;
  }

  // Pitch to Note Converter
  function freqToNote(freq) {
    if (!freq || freq <= 0) return { note: "--", cents: 0 };
    const a4 = 440.0;
    const notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    const semitones = 12 * Math.log2(freq / a4);
    const midi = Math.round(semitones) + 69;
    const noteName = notes[((midi % 12) + 12) % 12];
    const octave = Math.floor(midi / 12) - 1;
    const cents = Math.round((semitones - (midi - 69)) * 100);
    const centsStr = cents >= 0 ? `+${cents}.0c` : `${cents}.0c`;
    return { note: `${noteName}${octave}`, cents: centsStr };
  }

  // Timbre selection
  timbreBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      timbreBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      currentWave = btn.dataset.wave;
      triggerSynthesis();
    });
  });

  // Frequency slider
  freqSlider.addEventListener("input", (e) => {
    const val = parseFloat(e.target.value);
    freqReadout.textContent = `${val.toFixed(1)} Hz`;
  });

  freqSlider.addEventListener("change", () => {
    triggerSynthesis();
  });

  generateBtn.addEventListener("click", () => {
    triggerSynthesis();
  });

  // Canvas helper
  function setupCanvas(canvas) {
    const rect = canvas.parentElement.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    return { width: rect.width, height: rect.height, ctx };
  }

  // Draw FFT Spectrum Plot
  function drawFFTSpectrum(spectrum, harmonics, centroid, rolloff) {
    if (!spectrum || spectrum.length === 0) return;
    const { width, height, ctx } = setupCanvas(fftCanvas);

    ctx.clearRect(0, 0, width, height);

    const padLeft = 45;
    const padRight = 15;
    const padTop = 15;
    const padBottom = 25;
    const w = width - padLeft - padRight;
    const h = height - padTop - padBottom;

    // Grid (dBFS from -100 to 0)
    ctx.strokeStyle = "#1b1b22";
    ctx.lineWidth = 1;
    for (let db = 0; db >= -100; db -= 20) {
      const y = padTop + (Math.abs(db) / 100) * h;
      ctx.beginPath();
      ctx.moveTo(padLeft, y);
      ctx.lineTo(width - padRight, y);
      ctx.stroke();

      ctx.fillStyle = "#555866";
      ctx.font = "9px 'Share Tech Mono', monospace";
      ctx.textAlign = "right";
      ctx.fillText(`${db}dB`, padLeft - 6, y + 3);
    }

    // Freq Log Grid markers (100Hz, 500Hz, 1kHz, 5kHz, 10kHz, 20kHz)
    const markerFreqs = [100, 500, 1000, 5000, 10000, 20000];
    const minF = 20;
    const maxF = 22050;
    const logMin = Math.log10(minF);
    const logMax = Math.log10(maxF);

    markerFreqs.forEach((freq) => {
      const ratio = (Math.log10(freq) - logMin) / (logMax - logMin);
      const x = padLeft + ratio * w;
      ctx.beginPath();
      ctx.moveTo(x, padTop);
      ctx.lineTo(x, height - padBottom);
      ctx.stroke();

      ctx.fillStyle = "#555866";
      ctx.font = "9px 'Share Tech Mono', monospace";
      ctx.textAlign = "center";
      const lbl = freq >= 1000 ? `${freq / 1000}k` : `${freq}`;
      ctx.fillText(lbl, x, height - 8);
    });

    // Draw Spectrum Path
    ctx.beginPath();
    ctx.moveTo(padLeft, height - padBottom);

    spectrum.forEach((point, i) => {
      const freq = Math.max(minF, point.freq_hz);
      const ratio = Math.min(1, Math.max(0, (Math.log10(freq) - logMin) / (logMax - logMin)));
      const x = padLeft + ratio * w;
      const magClamped = Math.max(-100, Math.min(0, point.magnitude_db));
      const y = padTop + (Math.abs(magClamped) / 100) * h;

      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    // Fill under curve
    ctx.lineTo(width - padRight, height - padBottom);
    ctx.lineTo(padLeft, height - padBottom);
    ctx.closePath();

    const grad = ctx.createLinearGradient(0, padTop, 0, height - padBottom);
    grad.addColorStop(0, "rgba(0, 243, 255, 0.35)");
    grad.addColorStop(0.6, "rgba(188, 19, 254, 0.15)");
    grad.addColorStop(1, "rgba(10, 10, 15, 0.0)");
    ctx.fillStyle = grad;
    ctx.fill();

    // Trace line stroke
    ctx.strokeStyle = "#00f3ff";
    ctx.lineWidth = 1.8;
    ctx.stroke();

    // Draw Centroid Marker (Vertical Cyan Dash)
    if (centroid && centroid > minF) {
      const cRatio = (Math.log10(centroid) - logMin) / (logMax - logMin);
      const cx = padLeft + cRatio * w;
      ctx.strokeStyle = "#00f3ff";
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(cx, padTop);
      ctx.lineTo(cx, height - padBottom);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = "#00f3ff";
      ctx.fillText(`CENTROID ${centroid.toFixed(0)}Hz`, cx, padTop + 12);
    }

    // Draw Rolloff Marker (Vertical Violet Dash)
    if (rolloff && rolloff > minF) {
      const rRatio = (Math.log10(rolloff) - logMin) / (logMax - logMin);
      const rx = padLeft + rRatio * w;
      ctx.strokeStyle = "#bc13fe";
      ctx.setLineDash([3, 3]);
      ctx.beginPath();
      ctx.moveTo(rx, padTop);
      ctx.lineTo(rx, height - padBottom);
      ctx.stroke();
      ctx.setLineDash([]);

      ctx.fillStyle = "#bc13fe";
      ctx.fillText(`ROLLOFF ${rolloff.toFixed(0)}Hz`, rx, padTop + 24);
    }

    // Mark Detected Harmonics
    if (harmonics && harmonics.length > 0) {
      harmonics.forEach((hItem) => {
        const hFreq = Math.max(minF, hItem.actual_hz);
        const hRatio = (Math.log10(hFreq) - logMin) / (logMax - logMin);
        const hx = padLeft + hRatio * w;
        const hy = padTop + (Math.abs(Math.max(-100, hItem.relative_amplitude_db)) / 100) * h;

        ctx.fillStyle = "#bc13fe";
        ctx.beginPath();
        ctx.arc(hx, hy, 3.5, 0, Math.PI * 2);
        ctx.fill();

        ctx.font = "8px 'Share Tech Mono', monospace";
        ctx.fillText(`H${hItem.harmonic_number}`, hx, hy - 6);
      });
    }
  }

  // Draw Oscilloscope
  function drawOscilloscope(samples) {
    if (!samples || samples.length === 0) return;
    const { width, height, ctx } = setupCanvas(oscCanvas);

    ctx.clearRect(0, 0, width, height);

    const midY = height / 2;

    // Center Zero Line
    ctx.strokeStyle = "#1b1b22";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, midY);
    ctx.lineTo(width, midY);
    ctx.stroke();

    // Waveform Trace
    ctx.strokeStyle = "#bc13fe";
    ctx.lineWidth = 2;
    ctx.shadowColor = "rgba(188, 19, 254, 0.6)";
    ctx.shadowBlur = 8;
    ctx.beginPath();

    const n = samples.length;
    const step = width / (n - 1);

    samples.forEach((val, i) => {
      const x = i * step;
      const y = midY - val * (height * 0.45);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });

    ctx.stroke();
    ctx.shadowBlur = 0;
  }

  // Draw Spectrogram Heatmap
  function drawSpectrogram(specData) {
    if (!specData || !specData.spectrogram_matrix_db) return;
    const { width, height, ctx } = setupCanvas(specCanvas);

    ctx.clearRect(0, 0, width, height);

    const matrix = specData.spectrogram_matrix_db;
    const rows = matrix.length; // Frequency bins
    const cols = matrix[0].length; // Time bins

    const cellW = width / cols;
    const cellH = height / rows;

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const dbVal = matrix[r][c]; // -90 to 0
        const norm = Math.max(0, Math.min(1, (dbVal + 90) / 90));

        // Color mapping: Black -> Violet -> Cyan -> White
        let rCol, gCol, bCol;
        if (norm < 0.4) {
          const t = norm / 0.4;
          rCol = Math.round(188 * t * 0.5);
          gCol = Math.round(19 * t * 0.5);
          bCol = Math.round(254 * t);
        } else if (norm < 0.8) {
          const t = (norm - 0.4) / 0.4;
          rCol = Math.round(94 * (1 - t));
          gCol = Math.round(243 * t);
          bCol = 255;
        } else {
          const t = (norm - 0.8) / 0.2;
          rCol = Math.round(255 * t);
          gCol = 255;
          bCol = 255;
        }

        ctx.fillStyle = `rgb(${rCol}, ${gCol}, ${bCol})`;
        // Invert Y so low frequencies are at bottom
        ctx.fillRect(c * cellW, height - (r + 1) * cellH, cellW + 0.5, cellH + 0.5);
      }
    }
  }

  // Populate UI
  function updateUI(data) {
    const fft = data.fft_analysis;
    const f0 = fft.fundamental_frequency_hz;

    dispF0.textContent = f0 ? `${f0.toFixed(2)} Hz` : "INHARMONIC";
    const noteInfo = freqToNote(f0);
    dispNote.textContent = f0 ? `NOTE: ${noteInfo.note} (${noteInfo.cents})` : "NO PITCH LOCK";

    dispCentroid.textContent = `${fft.spectral_centroid_hz.toFixed(1)} Hz`;
    dispRolloff.textContent = `${fft.spectral_rolloff_85_hz.toFixed(1)} Hz`;
    dispFlatness.textContent = fft.spectral_flatness.toFixed(4);
    dispNoisiness.textContent = fft.spectral_flatness > 0.3 ? "NOISY / ATYPICAL" : "TONAL / HARMONIC PROMINENT";

    // Populate Harmonics Table
    harmonicTableBody.innerHTML = "";
    if (fft.harmonics && fft.harmonics.length > 0) {
      fft.harmonics.forEach((h) => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td style="color: #bc13fe; font-weight: 700;">H${h.harmonic_number}</td>
          <td>${h.harmonic_ratio}</td>
          <td>${h.target_hz.toFixed(1)}</td>
          <td style="color: #00f3ff;">${h.actual_hz.toFixed(1)}</td>
          <td>${h.relative_amplitude_db.toFixed(1)} dB</td>
        `;
        harmonicTableBody.appendChild(tr);
      });
    } else {
      harmonicTableBody.innerHTML = '<tr><td colspan="5" class="table-empty">NO HARMONICS DETECTED</td></tr>';
    }

    // Decode WAV audio for audition playback
    if (data.audio_base64_wav) {
      const binaryString = window.atob(data.audio_base64_wav);
      const len = binaryString.length;
      const bytes = new Uint8Array(len);
      for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }

      if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
      }

      audioContext.decodeAudioData(
        bytes.buffer,
        (buffer) => {
          activeAudioBuffer = buffer;
          animateVUMeters(0.85);
        },
        (err) => console.error("Audio decode error:", err)
      );
    }

    // Render Canvas Visualizations
    drawFFTSpectrum(fft.spectrum, fft.harmonics, fft.spectral_centroid_hz, fft.spectral_rolloff_85_hz);
    drawOscilloscope(data.oscilloscope_samples);
    drawSpectrogram(data.spectrogram);
  }

  // VU Meter Animator
  function animateVUMeters(peakFactor) {
    const pct = Math.min(100, peakFactor * 90);
    vuFillL.style.width = `${pct}%`;
    vuFillR.style.width = `${pct * 0.96}%`;

    const db = (20 * Math.log10(peakFactor)).toFixed(1);
    vuPeakL.textContent = `${db} dB`;
    vuPeakR.textContent = `${db} dB`;

    setTimeout(() => {
      vuFillL.style.width = "0%";
      vuFillR.style.width = "0%";
      vuPeakL.textContent = "-inf dB";
      vuPeakR.textContent = "-inf dB";
    }, 1200);
  }

  // Audition playback
  playToneBtn.addEventListener("click", () => {
    if (!audioContext) {
      audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioContext.state === "suspended") {
      audioContext.resume();
    }

    if (isPlaying && activeSource) {
      activeSource.stop();
      isPlaying = false;
      playToneBtn.textContent = "AUDITION_SIGNAL";
      return;
    }

    if (activeAudioBuffer) {
      activeSource = audioContext.createBufferSource();
      activeSource.buffer = activeAudioBuffer;
      activeSource.connect(audioContext.destination);
      activeSource.start();
      isPlaying = true;
      playToneBtn.textContent = "STOP_SIGNAL";
      animateVUMeters(0.92);

      activeSource.onended = () => {
        isPlaying = false;
        playToneBtn.textContent = "AUDITION_SIGNAL";
      };
      log(`Auditioning ${currentWave.toUpperCase()} signal output.`, "event");
    }
  });

  // Microphone Input Mode
  micToggleBtn.addEventListener("click", async () => {
    if (!isMicActive) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
        micStream = stream;
        if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
        if (audioContext.state === "suspended") await audioContext.resume();

        micAnalyser = audioContext.createAnalyser();
        micAnalyser.fftSize = 2048;
        const micSource = audioContext.createMediaStreamSource(stream);
        micSource.connect(micAnalyser);

        isMicActive = true;
        micToggleBtn.textContent = "MICROPHONE_INPUT [ACTIVE]";
        micToggleBtn.classList.add("active");
        log("Microphone live feed connected to DSP pipeline.", "system");

        renderMicLoop();
      } catch (err) {
        log(`Microphone access error: ${err.message}`, "warn");
      }
    } else {
      if (micStream) {
        micStream.getTracks().forEach((track) => track.stop());
      }
      isMicActive = false;
      micToggleBtn.textContent = "MICROPHONE_INPUT [OFF]";
      micToggleBtn.classList.remove("active");
      log("Microphone feed disconnected.", "event");
    }
  });

  function renderMicLoop() {
    if (!isMicActive || !micAnalyser) return;

    const timeBuffer = new Float32Array(micAnalyser.fftSize);
    micAnalyser.getFloatTimeDomainData(timeBuffer);

    // Compute basic peak
    let peak = 0;
    for (let i = 0; i < timeBuffer.length; i++) {
      const a = Math.abs(timeBuffer[i]);
      if (a > peak) peak = a;
    }
    const pct = Math.min(100, peak * 100);
    vuFillL.style.width = `${pct}%`;
    vuFillR.style.width = `${pct}%`;
    vuPeakL.textContent = peak > 0.001 ? `${(20 * Math.log10(peak)).toFixed(1)} dB` : "-inf dB";
    vuPeakR.textContent = peak > 0.001 ? `${(20 * Math.log10(peak)).toFixed(1)} dB` : "-inf dB";

    // Downsample for oscilloscope
    const oscSamples = [];
    const step = Math.floor(timeBuffer.length / 400);
    for (let i = 0; i < timeBuffer.length; i += step) {
      oscSamples.push(timeBuffer[i]);
    }
    drawOscilloscope(oscSamples);

    requestAnimationFrame(renderMicLoop);
  }

  // Trigger backend analysis
  async function triggerSynthesis() {
    const freq = parseFloat(freqSlider.value);
    const nFft = parseInt(fftSizeSelect.value, 10);
    const windowType = windowSelect.value;

    generateBtn.disabled = true;
    generateBtn.textContent = "COMPUTING_FFT...";

    try {
      const res = await fetch("/api/analyze-synthetic", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          wave_type: currentWave,
          frequency_hz: freq,
          duration_sec: 1.2,
          n_fft: nFft,
          window_type: windowType,
        }),
      });

      if (!res.ok) throw new Error("Synthesis API call failed");
      const data = await res.json();
      updateUI(data);

      log(`FFT Analysis complete: ${currentWave} at ${freq}Hz. Centroid: ${data.fft_analysis.spectral_centroid_hz}Hz.`, "system");
    } catch (err) {
      log(`DSP Execution failed: ${err.message}`, "warn");
    } finally {
      generateBtn.disabled = false;
      generateBtn.textContent = "CALCULATE_FFT_DECOMPOSITION";
    }
  }

  // Initial trigger
  triggerSynthesis();
});
