# CyberCrypt Pro ✦

CyberCrypt Pro is a premium, multi-layer secure text encryption and decryption application. It combines three classical cryptographic cipher layers into a unified processing pipeline, wrapped in a gorgeous dark-space glassmorphism UI designed for modern desktop and web experiences.

## Features

- **Multi-Layer Cryptographic Pipeline**: 
  1. **Caesar Cipher**: Shifts characters by a numeric offset ($1 - 127$).
  2. **Vigenere Cipher**: Applies polyalphabetic substitution based on a custom alphanumeric keyword.
  3. **Random XOR Layer**: XOR-encrypts text using a seeded pseudo-random keystream.
- **Staggered Step-by-Step Visualization**: Watch each cipher layer be applied or removed in real-time.
- **Responsive Theme Engine**: Supports both a Dark Palette (Deep Space Navy Glass) and a Light Palette (Crisp White Glass) with instant switching.
- **Cross-Platform Compatibility**: Fully compatible with Windows, macOS, and Linux out of the box.
- **Web UI & API Endpoints**: Run as a native desktop app or interact with the ciphers via a Vercel-deployed serverless web dashboard.

---

## Technical Architecture

CyberCrypt Pro runs on one shared cryptographic core with two frontends:

```
   DESKTOP (main.py)                      WEB (Vercel)
        │                                      │
 ┌──────▼───────────┐               ┌──────────▼──────────┐
 │  CustomTkinter   │               │    index.html       │
 │  Glass UI Layer  │               │  Glass Chat Web UI  │
 │  (cybercrypt.ui) │               │  (sidebar+composer) │
 └──────┬───────────┘               └──────────┬──────────┘
        │                            fetch /api/encrypt
        │                            fetch /api/decrypt
        │                          ┌────────────▼────────────┐
        │                          │  Serverless Functions   │
        │                          │  api/encrypt.py         │
        │                          │  api/decrypt.py (Flask) │
        │                          └────────────┬────────────┘
        │                                       │
        └──────────────────┬────────────────────┘
                  ┌────────▼─────────┐
                  │    Core Engine   │
                  │  (cybercrypt.core)│
                  │  Caesar → Vigenère│
                  │   → Random XOR   │
                  └──────────────────┘
```

**Encryption order (fixed):** Plain Text → Caesar → Vigenère → Random XOR → Cipher Text.
**Decryption** reverses the exact same order with identical keys.

---

## File Structure

```
.
├── api/                          # Vercel serverless backend (Flask)
│   ├── index.py                  #   Serves the web dashboard at "/"
│   ├── encrypt.py                #   POST /api/encrypt — runs the 3-layer pipeline
│   └── decrypt.py                #   POST /api/decrypt — peels off all 3 layers
├── cybercrypt/
│   ├── core/                     # Pure cryptography — zero UI dependencies
│   │   ├── alphabet.py           #   128-char printable alphabet set
│   │   ├── caesar_cipher.py      #   Layer 1: shift cipher
│   │   ├── vigenere_cipher.py    #   Layer 2: polyalphabetic substitution
│   │   ├── random_layer.py       #   Layer 3: seeded XOR keystream
│   │   └── engine.py             #   Unified multi-layer engine + key generator
│   ├── ui/
│   │   ├── screens/              # One module per application screen
│   │   │   ├── base_screen.py    #   Shared header, scroll container, safe geometry
│   │   │   ├── dashboard_screen.py  # Hero, stat cards, pipeline, layer cards
│   │   │   ├── encrypt_screen.py #   Live encryption workspace
│   │   │   ├── decrypt_screen.py #   Live decryption workspace
│   │   │   ├── analysis_screen.py#   Strength analysis and exportable reports
│   │   │   ├── architecture_screen.py # Architecture explainer
│   │   │   ├── guide_screen.py   #   User guide
│   │   │   └── about_screen.py   #   About and credits
│   │   ├── animation.py          # Color, hover, focus and flash animations
│   │   ├── background.py         # Animated glass backdrop (orbs + gradient)
│   │   ├── charts.py             # Canvas-drawn charts and meters
│   │   ├── dialogs.py            # Modal dialogs and overlays
│   │   ├── panels.py             # Pipeline panel, step details, summary popup
│   │   ├── statusbar.py          # Bottom status bar
│   │   ├── theme.py              # Colors, fonts, spacing, dark/light palettes
│   │   ├── tooltip.py            # Hover tooltip bindings
│   │   ├── visualizer.py         # Step builder for live visualization
│   │   └── widgets.py            # Glass cards, buttons, entries, keys panel
│   ├── utils/
│   │   ├── helpers.py            # Time formatting and shared helpers
│   │   └── settings.py           # Persistent app settings (load/save)
│   ├── analysis.py               # Message statistics and strength scoring
│   └── app.py                    # Main window: layout, navigation, screens
├── tests/                        # Unit tests (core ciphers + analysis)
├── index.html                    # Web dashboard (premium glass chat UI)
├── main.py                       # Desktop entry point
├── vercel.json                   # Vercel configuration
├── requirements.txt              # Serverless backend packages (Flask)
├── run_tests.py                  # Test runner script
└── README.md                     # Project documentation
```

---

## Getting Started

### 1. Prerequisite Packages

Make sure you have Python 3.10+ installed. Install CustomTkinter and Pillow for the desktop client:

```bash
pip install customtkinter pillow
```

If you plan to run the serverless web server locally:

```bash
pip install -r requirements.txt
```

### 2. Launch the Desktop App

To start the native CustomTkinter desktop application:

```bash
python main.py
```

### 3. Running Unit Tests

Run the full cryptographic and analytical test suites using:

```bash
python run_tests.py
```

---

## Web Deployment (Vercel)

CyberCrypt Pro is ready for instant cloud deployment. It utilizes the `@vercel/python` serverless builder to host the cryptographic engine, serving a responsive Web dashboard at `/` and executing the engine calculations securely at `/api/encrypt` and `/api/decrypt`.

To deploy via Vercel CLI:

```bash
vercel --prod
```

---

## Credits
Developed By **Sams Alif**
*Secure Multi-Layer Text Encryption System*
