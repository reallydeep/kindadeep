# 🌊 Deep Patel — Portfolio

> **Interactive deep-ocean themed personal portfolio** — a single HTML file featuring GPU-accelerated ocean visuals, live data widgets, pixel art, and a full section-based navigation experience.

[![Live Site](https://img.shields.io/badge/🌊_Live_Site-reallydeep.github.io-4fc3f7?style=for-the-badge)](https://reallydeep.github.io)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-dspatel00-0077B5?style=for-the-badge&logo=linkedin)](https://linkedin.com/in/dspatel00)
[![GitHub](https://img.shields.io/badge/GitHub-reallydeep-181717?style=for-the-badge&logo=github)](https://github.com/reallydeep)

---

## ✨ Features

### 🎨 Visual Design
- **Deep ocean aesthetic** — bioluminescent particle system, animated coral, jellyfish, fish, and pixel art sea life
- **GPU-accelerated animations** — all motion uses `transform` and `opacity` with `will-change` hints; zero `top`/`left` animation
- **Pixel art assets** — custom SVG Statue of Liberty, PERSEVERANCIA sailing ship, XRP token rain, treasure chest
- **Press Start 2P** typography throughout for a consistent retro-digital identity
- **Custom pixel cursor** — cyan crosshair replacing the default OS pointer

### 🧭 Navigation & Layout
- **Section-based scroll** — 8 sections: Surface · About · Skills · Experience · Projects · Hobbies · Photos · Contact
- **Desktop minimap** (top-left HUD) — depth meter with section labels and live position indicator
- **Mobile toolbar** (bottom bar) — fixed pixel-art nav with section jumping and widget drawers
- **Smooth scroll** — `scrollTo` with `behavior: smooth` across all navigation paths
- **Intro splash screen** — animated wave entrance gate before the main portfolio loads

### 📡 Live Data Widgets
| Widget | Platform | Requires HTTPS |
|--------|----------|---------------|
| 🎵 Spotify | Embedded playlist | No (works on file://) |
| 📺 Live News | YouTube iframes (13 channels) | Yes |
| 🔎 OSINT Feed | Twitter/X List embed | Yes |

### 📱 Mobile Experience
- Responsive breakpoints at `768px` (mobile) and `769px–1024px` (tablet)
- Slide-up drawer panels for News, OSINT, and Spotify widgets
- Scroll snap disabled on mobile — single scroll context prevents iOS nested-scroll conflicts
- `storage-access` permission on Spotify iframe handles iOS WebKit ITP
- Touch-optimized tap targets throughout

### 🪟 Modals & Interactive Overlays
- Experience modal — SML Group Limited 3-tier career timeline
- Education modal — Rutgers University, GPA 3.70, EGA 3K+
- Skills Reef — 14-chip interactive tag cloud
- Project cards — Bergen Logistics WMS Portfolio, Telegram Clip Bot
- Photo lightbox — full-screen polaroid viewer with ESC support
- Photos grid modal — gallery overview of all photos

---

## 🗂️ Project Structure

```
/
├── index.html          ← Entire portfolio (single file — HTML + CSS + JS + assets)
├── preview.png         ← OG social preview image (1200×630px, add manually)
├── README.md           ← This file
└── .gitignore
```

No build step. No node_modules. No framework. Everything is self-contained in `index.html`.

---

## 🚀 Deployment (GitHub Pages)

### One-time setup

```bash
# 1. Clone your GitHub Pages repo
git clone https://github.com/reallydeep/reallydeep.github.io
cd reallydeep.github.io

# 2. Place the portfolio file as index.html
cp deep-patel-pixel-v11.html index.html

# 3. (Optional) Add a 1200×630px screenshot as the OG preview image
# Save it as preview.png in the repo root

# 4. Commit and push
git add index.html preview.png README.md .gitignore
git commit -m "feat: deploy portfolio v11"
git push origin main
```

### Enable GitHub Pages

1. Repo → **Settings** → **Pages**
2. Source: `Deploy from a branch`
3. Branch: `main` / Folder: `/ (root)`
4. Save — live at `https://reallydeep.github.io` within ~2 minutes

---

## 📎 Adding Your Resume PDF

The Resume button currently links to your GitHub profile. To point it at a real PDF:

1. Add `deep-patel-resume.pdf` to the repo root
2. In `index.html`, find the Resume anchor and update:
```html
<a href="deep-patel-resume.pdf" target="_blank" rel="noopener noreferrer" ...>
```
3. Commit and push.

---

## 🎵 Spotify Widget Notes

- `allow="storage-access"` is set on all Spotify iframes to handle iOS WebKit ITP
- First load on iOS Safari may prompt: *"Allow spotify.com to use cookies?"* — tap **Allow**
- Desktop widget lazy-loads on first click (preserves render performance)
- Mobile drawer uses `loading="eager"` — necessary because `visibility:hidden` prevents lazy load thresholds from firing

---

## 📺 Why Twitter & YouTube Require HTTPS

- **YouTube** — Its embed runs authenticated JS that makes CORS-checked API calls back to `youtube.com`. Those calls require an `https://` origin; `file://` has no origin, so Chrome rejects them as mixed content.
- **Twitter/X** — `widgets.js` reads `document.referrer` and validates the embedding page's domain. `file://` produces an empty domain string and the script fails silently.
- **Spotify** — Its embed player has no origin validation on initial render; it only needs to load an audio player URL. That's why it works on `file://` while the others don't.

When testing locally via `file://`, both YouTube and Twitter widgets show an "HTTPS Required" notice. They activate fully once deployed to GitHub Pages.

---

## 🛠️ Tech Stack

| Layer | Tech |
|-------|------|
| Structure | HTML5 |
| Styling | Vanilla CSS3 (custom properties, keyframe animations, media queries) |
| Logic | Vanilla JavaScript (ES5 syntax, no frameworks) |
| Font | Press Start 2P — Google Fonts |
| Embeds | Spotify Embed API · YouTube iframes · Twitter widgets.js |
| Hosting | GitHub Pages |

---

## 🧪 Local Testing

```bash
# Spotify works; YouTube + Twitter show HTTPS notice
open index.html

# Better: serve over HTTP so relative paths resolve cleanly
python3 -m http.server 8080
# → http://localhost:8080

# VS Code users: right-click index.html → "Open with Live Server"
```

---

## 📐 Browser Support

| Browser | Desktop | Mobile |
|---------|---------|--------|
| Chrome 90+ | ✅ | ✅ |
| Safari 15+ | ✅ | ✅ (ITP handled) |
| Firefox 88+ | ✅ | ✅ |
| Edge 90+ | ✅ | ✅ |
| Samsung Internet | — | ✅ |

---

## 📬 Contact

**Deep Snehal Patel** — Technical Business Analyst · WMS/EDI · Bergen Logistics / Cloud X Systems

- 📧 deeppatell20005@yahoo.com
- 🔗 [linkedin.com/in/dspatel00](https://linkedin.com/in/dspatel00)
- 🐙 [github.com/reallydeep](https://github.com/reallydeep)
- 📍 Morris Plains, NJ · US Citizen · CSM · CSPO · No H-1B Required

---

<p align="center">Built with 🌊 and zero frameworks · 2025</p>
