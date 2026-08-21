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

CyberCrypt Pro splits its architecture into three clean layers:

```
                  ┌──────────────────────────────┐
                  │          App Entry           │
                  │   (main.py / api/index.py)   │
                  └──────────────┬───────────────┘
                                 │
                  ┌──────────────▼───────────────┐
                  │           UI Layer           │
                  │  (CustomTkinter / Web UI)    │
                  └──────────────┬───────────────┘
                                 │
                  ┌──────────────▼───────────────┐
                  │          Core Engine         │
                  │      (Caesar / Vigenere /    │
                  │         Random XOR)          │
                  └──────────────────────────────┘
```

---

## File Structure

```
.
├── api/
│   └── index.py            # Vercel serverless Python Flask application
├── cybercrypt/
│   ├── core/
│   │   ├── alphabet.py     # Base ASCII printable alphabet set
│   │   ├── caesar_cipher.py# Shift encryption and decryption functions
│   │   ├── engine.py       # Unified multi-layer encryption engine
│   │   ├── random_layer.py # Seeded XOR keystream layer
│   │   └── vigenere_cipher.py # Polyalphabetic substitution layer
│   ├── ui/
│   │   ├── screens/
│   │   │   ├── base_screen.py  # Transparent base screen containing core scroll binds
│   │   │   ├── dashboard_screen.py # Dashboard screen with developer footer card
│   │   │   ├── encrypt_screen.py # Live encryption visualizer workspace
│   │   │   └── decrypt_screen.py # Live decryption visualizer workspace
│   │   ├── animation.py    # Colors, hover, focus, and flash animations
│   │   ├── theme.py        # Spacing, font, and active theme palettes (Dark/Light)
│   │   ├── panels.py       # Segmented progress bars and step-details panel widgets
│   │   └── widgets.py      # Premium glass cards, buttons, entries, and toasts
│   └── utils/
│       └── helpers.py      # Estimated time calculations and helper functions
├── tests/                  # Integration and unit tests
├── main.py                 # Desktop application launch script
├── vercel.json             # Vercel routing configurations
├── requirements.txt        # Serverless backend package list
├── run_tests.py            # Run script for the test suite
└── README.md               # Project documentation
```

---

## Getting Started

### 1. Prerequisite Packages

Make sure you have Python 3.10+ installed. Install CustomTkinter for the desktop client:

```bash
pip install customtkinter
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
