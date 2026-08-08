# 📐 FORGE PRO — Deep Technical Architecture

This document provides a complete technical walkthrough of the core systems powering **FORGE PRO**. Anyone looking to contribute, refactor, or build upon this project can use this guide as a blueprint.

---

## 📑 Table of Contents
1. [Core Philosophy](#1-core-philosophy)
2. [State Engine & Precision Timing](#2-state-engine--precision-timing)
3. [Circular Gauge & Chronograph Dial Mathematics](#3-circular-gauge--chronograph-dial-mathematics)
4. [Mathematical Web Audio Synthesizer](#4-mathematical-web-audio-synthesizer)
5. [PWA Offline Architecture & Service Worker](#5-pwa-offline-architecture--service-worker)
6. [Dynamic Theme Engine (CSS Custom Properties)](#6-dynamic-theme-engine-css-custom-properties)
7. [Screen WakeLock Integration](#7-screen-wakelock-integration)

---

## 1. Core Philosophy
- **Zero External Dependencies**: Pure vanilla HTML5, CSS3, and JavaScript ES6+. No frameworks, bundlers, or heavy npm node_modules.
- **Client-Side Synthesis**: Zero external audio assets (MP3/WAV/OGG). All sounds are generated via the Web Audio API synthesizer.
- **Mobile-First Progressive Web App**: Fully functional offline without network requests once loaded.
- **Zero Layout Shifts**: Dial readout, fractional timers, and round dots are mathematically pinned to avoid shifting elements during rapid ticking.

---

## 2. State Engine & Precision Timing

### 2.1 The Problem with `setInterval`
Traditional web timers use `setInterval(fn, 1000)`. However, `setInterval` drifts over time due to JavaScript event loop lag, CPU throttling, and background tab downclocking.

### 2.2 FORGE PRO's Solution: `requestAnimationFrame` + `performance.now()`
We use `requestAnimationFrame` with high-resolution timestamps:

```javascript
function tick(timestamp) {
  if (!STATE.isRunning) return;
  
  // 1. Calculate actual elapsed time between frames
  const delta = timestamp - STATE.lastTimestamp;
  STATE.lastTimestamp = timestamp;
  
  // 2. Decrement remaining time
  STATE.remainingMs -= delta;
  STATE.elapsedMs += delta;
  
  // 3. Precise second-boundary audio cues
  const currentSec = Math.ceil(STATE.remainingMs / 1000);
  if (currentSec <= 3 && currentSec > 0 && currentSec !== STATE.lastTriggeredSec) {
    STATE.lastTriggeredSec = currentSec;
    SoundEffects.countdownTick(currentSec);
  }
  
  // 4. Phase transition on completion
  if (STATE.remainingMs <= 0) {
    transitionPhase();
  }
  
  renderUI();
  STATE.rafId = requestAnimationFrame(tick);
}
```

---

## 3. Circular Gauge & Chronograph Dial Mathematics

The circular progress bar is built with SVG vector paths and calibrated using trigonometry:

- **Radius ($r$)**: `114px`
- **Circumference ($C$)**:
  $$C = 2 \times \pi \times 114 \approx 716.28318\text{px}$$
- **CSS Stroke Dashoffset Formula**:
  $$\text{offset} = C \times \left(1 - \frac{\text{remainingMs}}{\text{totalPhaseMs}}\right)$$

```javascript
const CIRCUMFERENCE = 2 * Math.PI * 114;

function updateDialProgress(remainingMs, totalMs) {
  const progress = Math.max(0, Math.min(1, remainingMs / totalMs));
  const offset = CIRCUMFERENCE * (1 - progress);
  
  DOM.dialBar.style.strokeDasharray = `${CIRCUMFERENCE}`;
  DOM.dialBar.style.strokeDashoffset = `${offset}`;
  DOM.dialGlow.style.strokeDashoffset = `${offset}`;
}
```

---

## 4. Mathematical Web Audio Synthesizer

Rather than fetching bulky audio files over the network, FORGE PRO synthesizes sounds natively on the user's audio device:

```
[AudioContext] ──► [OscillatorNode(s)] ──► [GainNode (ADSR Envelope)] ──► [Destination / Speakers]
```

### Sound Pack Architectures:
1. **Synth Pack**: Pure sine wave frequencies ($880\text{Hz} \rightarrow 1760\text{Hz}$) with exponential decay envelopes for electronic cues.
2. **Boxing Bell**: 4 harmonically tuned oscillators ($600\text{Hz}, 750\text{Hz}, 900\text{Hz}, 1150\text{Hz}$) routed through a metal resonance filter to emulate a ringside bell.
3. **Chrono Pack**: High-frequency click bursts ($1200\text{Hz} \rightarrow 2400\text{Hz}$) simulating Swiss timing watches.
4. **Cyber Pack**: Frequency modulation sweeps ($1600\text{Hz} \rightarrow 400\text{Hz}$) for futuristic tactical workouts.

---

## 5. PWA Offline Architecture & Service Worker

The application uses a **Cache-First** strategy implemented in `sw.js`:

```javascript
const CACHE_NAME = 'forge-pro-v1';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.svg',
  './icon-512.svg'
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then(res => res || fetch(e.request))
  );
});
```

---

## 6. Dynamic Theme Engine (CSS Custom Properties)

All visual elements consume centralized CSS design tokens defined on `html[data-theme="..."]`:

| Token | Purpose | Example (`jet-black`) |
|---|---|---|
| `--bg-page` | Background canvas | `#000000` (OLED True Black) |
| `--work-primary` | Active work phase color | `#FF5A26` (Electric Orange) |
| `--rest-primary` | Rest phase color | `#38BDF8` (Sky Blue) |
| `--font-mono` | Dial numerals font | `'JetBrains Mono', monospace` |
| `--shadow-deck` | Glassmorphic blur & glow | `0 24px 48px rgba(0,0,0,0.8)` |

Switching themes takes a single line:
```javascript
document.documentElement.setAttribute('data-theme', themeName);
```

---

## 7. Screen WakeLock Integration

To prevent mobile phone screens from turning off mid-exercise, the app requests a screen wake lock when the timer starts:

```javascript
let wakeLock = null;

async function requestWakeLock() {
  try {
    if ('wakeLock' in navigator) {
      wakeLock = await navigator.wakeLock.request('screen');
    }
  } catch (err) {
    console.warn('WakeLock not supported or denied');
  }
}

function releaseWakeLock() {
  if (wakeLock) {
    wakeLock.release();
    wakeLock = null;
  }
}
```

---

## 🤝 Contributing & Extension Ideas

Here are great features you can build on top of FORGE PRO:
1. **Heart Rate Monitor Support**: Connect Bluetooth Heart Rate straps (Web Bluetooth API) to show live BPM on the dial.
2. **Audio Voice Announcer**: Use `window.speechSynthesis` to speak out round names and exercise movements.
3. **Workout History & Heatmap**: Store completed workout logs in IndexedDB with weekly streak heatmaps.
