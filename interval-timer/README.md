# ⚡ FORGE PRO — High Performance Interval Trainer

> **A zero-dependency, standalone Progressive Web App (PWA) interval timer designed with luxury chronograph aesthetics, mathematical precision, studio audio synthesis, and 100% offline capability.**

[![Live Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-FF5A26?style=for-the-badge&logo=github)](https://adarsh-tripathi7.github.io/forge/)
[![PWA Ready](https://img.shields.io/badge/PWA-100%25%20Offline-38BDF8?style=for-the-badge&logo=pwa)](https://adarsh-tripathi7.github.io/forge/)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20(Pure%20HTML%2FCSS%2FJS)-34D399?style=for-the-badge)](https://adarsh-tripathi7.github.io/forge/)

---

## 📸 Live Preview & Architecture

- **Live Web App:** [https://adarsh-tripathi7.github.io/forge/](https://adarsh-tripathi7.github.io/forge/)
- **Repository:** [https://github.com/Adarsh-Tripathi7/forge](https://github.com/Adarsh-Tripathi7/forge)

```
interval-timer/
├── index.html            # Core application (Semantic HTML, CSS Tokens, State Engine)
├── sw.js                 # Service Worker (Cache-First offline strategy)
├── manifest.json         # PWA Manifest (Standalone display, theme colors, icons)
├── icon-192.svg          # High-resolution vector PWA home screen icon (192x192)
├── icon-512.svg          # Vector splash icon for Android/iOS (512x512)
├── .nojekyll             # Bypasses Jekyll on GitHub Pages for instant static delivery
├── .github/workflows/
│   └── deploy.yml        # Zero-config GitHub Actions deployment pipeline
├── README.md             # Developer documentation and modification guide
└── ARCHITECTURE.md       # In-depth technical guide (Audio synthesis, Dial Math, State)
```

---

## ✨ Key Technical Features

### 1. ⏱️ Chronograph Dial Math & Optical Alignment
- Built with an SVG circular gauge (`r = 114`, circumference $C = 2\pi r \approx 716.28\text{px}$).
- Uses `stroke-dashoffset` calculated via `circumference * (1 - progress)` for sub-millisecond fluid animations.
- Time readout uses `font-variant-numeric: tabular-nums` to guarantee zero horizontal layout shift as numbers change.

### 2. 🎵 Real-Time Web Audio API Synthesis (Zero MP3/WAV files)
All sound effects are synthesized mathematically in real-time on the client's audio hardware:
- **Synth Pulse:** High-resonance sine wave beeps ($880\text{Hz} \rightarrow 1760\text{Hz}$) with exponential gain decays.
- **Boxing Bell:** 4-operator additive oscillator cluster ($600, 750, 900, 1150\text{Hz}$) with metal clang resonance.
- **Chrono Beep:** Crisp square/triangle wave clicks ($1200\text{Hz} \rightarrow 2400\text{Hz}$).
- **Cyber Laser:** High-to-low FM frequency sweep ($1600\text{Hz} \rightarrow 400\text{Hz}$) for futuristic cues.

### 3. 📱 Automatic Device Detection & Offline PWA Installation
- **Smart Detection:** Automatically detects whether the app is on Android (Chrome/Edge) or iOS (Safari).
- **Zero Header Clutter:** No static install buttons cluttering the navigation. The app automatically triggers a non-intrusive floating installation card at the bottom.
- **Standalone Guard:** If already running as an installed standalone app (`display-mode: standalone`), installation prompts are completely suppressed.
- **Screen Wake Lock API:** Automatically acquires a `wakeLock` when workouts start to keep the phone screen awake during high-intensity intervals.

### 4. 🎨 5 Handcrafted Theme Color Systems
Curated CSS variables with dynamic background glow and contrast:
- **Jet Black:** Pure OLED `#000000` with high-contrast electric orange accents.
- **Peach White:** Warm luxury porcelain cream with coral ember accents.
- **Cyber Neon:** High-contrast matrix green on pitch black.
- **Nebula Violet:** Deep cosmic violet with vibrant ultraviolet cues.
- **Titanium Raw:** Aerospace brushed metal monochrome.

---

## 🚀 Getting Started (Quick Run)

Because FORGE PRO is built with zero external dependencies and zero build tools, you can run and edit it immediately:

### Option A: Open directly in Browser
Double-click `index.html` in your file explorer.

### Option B: Local HTTP Server (Recommended for PWA testing)
Run with Python or Node:
```bash
# Using Python 3:
python -m http.server 8000

# OR using npx:
npx serve .
```
Then visit `http://localhost:8000`.

---

## 🛠️ How to Edit and Improve the Codebase

### 1. How to Add a New Sound Profile
Open `index.html` and locate the `SoundEffects` object (around line 1750):
```javascript
const SoundEffects = {
  // Add a new sound profile here:
  myCustomSound(freq, duration) {
    if (!isAudioEnabled) return;
    const ctx = getAudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(freq, ctx.currentTime);
    
    gain.gain.setValueAtTime(0.2, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
    
    osc.connect(gain);
    gain.connect(ctx.destination);
    
    osc.start();
    osc.stop(ctx.currentTime + duration);
  }
};
```

### 2. How to Add a New Theme
1. In `index.html`, add your CSS theme variables under `<style>`:
```css
html[data-theme="emerald-pro"] {
  --bg-page: #021a12;
  --bg-deck: rgba(2, 26, 18, 0.88);
  --text-1: #E6FBF2;
  --text-2: #A3E4D7;
  --work-primary: #00F5A0;
  --work-glow: rgba(0, 245, 160, 0.45);
  --rest-primary: #00D9F5;
  --rest-glow: rgba(0, 217, 245, 0.45);
  /* ... */
}
```
2. In the `#themeDrawer` container in `index.html`, add a new theme button:
```html
<button class="theme-opt" onclick="selectTheme('emerald-pro')">
  <span>Emerald Pro</span>
  <div class="theme-preview-chips">
    <div class="swatch" style="background:#021a12;"></div>
    <div class="swatch" style="background:#00F5A0;"></div>
  </div>
</button>
```

### 3. How to Add New Interval Presets
In `index.html`, find the `DEFAULT_PRESETS` array (around line 2040) and add your routine:
```javascript
const DEFAULT_PRESETS = [
  { id: 'tabata', name: 'Tabata Protocol', wMin: 0, wSec: 20, rMin: 0, rSec: 10, rounds: 8, prepSec: 3 },
  { id: 'hiit',   name: 'HIIT Classic',    wMin: 0, wSec: 45, rMin: 0, rSec: 15, rounds: 10, prepSec: 5 },
  // Add your new preset:
  { id: 'boxing', name: 'Boxing Rounds',   wMin: 3, wSec: 0,  rMin: 1, rSec: 0,  rounds: 12, prepSec: 5 },
];
```

---

## 🔄 Timer State Machine

The core state machine is managed by the `STATE` object:

```
           [handleTogglePlay()]
   [IDLE] ─────────────────────► [COUNTDOWN (3s)]
     ▲                                 │
     │ (Reset)                         │ (Prep finished)
     │                                 ▼
   [DONE] ◄────────────────────── [WORK PHASE]
     ▲      (All rounds done)          │
     │                                 │ (Work timer = 0)
     │                                 ▼
     └─────────────────────────── [REST PHASE]
            (Round < Total)
```

- **`requestAnimationFrame`**: Precision delta time tracking using `performance.now()` ensures timer never drifts when the device undergoes background throttling.
- **Audio Cue Triggers**: 3-2-1 warning beeps automatically trigger when `remainingMs <= 3000` with deduplicated second thresholds (`lastTriggeredSec`).

---

## 🚢 Deployment to GitHub Pages

This project is set up with GitHub Actions for instant CI/CD:
1. Push your commits to branch `main`.
2. `.github/workflows/deploy.yml` will automatically build and publish the site.
3. Access your live app at `https://<username>.github.io/<repo-name>/`.

---

## 📄 License
MIT License — Feel free to use, modify, and distribute for personal or commercial projects!
