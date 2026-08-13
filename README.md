# JARVIS — Local-First AI Smart Room Assistant

JARVIS is a physical, local-first AI room assistant. It features voice capture, speech-to-text, local intent parsing, audio responses, Spotify controls, and ESP-NOW relay triggers.

---

## 1. Directory Structure

```
jarvis/
├── docs/                     # Detailed installation, deployment, and schemas
│   ├── ARCHITECTURE.md
│   ├── PROTOCOL.md
│   ├── SETUP.md
│   ├── DEPLOYMENT.md
│   └── TROUBLESHOOTING.md
├── server/                   # FastAPI backend server
│   ├── app/                  # Main server components
│   ├── requirements.txt      # Python dependencies
│   └── main.py               # Server entry point
├── dashboard/                # React dashboard control panel
│   ├── src/                  # React source files
│   └── package.json          # Node dependencies
├── firmware/                 # ESP32 C++ firmware
│   ├── main_esp32/           # Main coordinator unit firmware
│   └── node_esp32/           # Secondary relay node firmware
└── hardware/                 # Circuit schematics and BOM list
    ├── diagrams/             # SVG circuit layouts
    └── bom/                  # BOM list
```

---

## 2. Quickstart

### Step 1: Start local AI (Ollama)
```bash
ollama serve
ollama pull llama3.2:1b
```

### Step 2: Configure Environment
Copy and customize `.env`:
```bash
cp .env.example .env
```

### Step 3: Run the Server
```bash
cd server
python -m venv .venv
# Activate venv
.venv\Scripts\Activate.ps1   # On Windows
pip install -r requirements.txt
python main.py
```

### Step 4: Run the Dashboard
```bash
cd dashboard
npm install
npm run dev
```

### Step 5: Flash ESP32
Open `firmware/main_esp32/JARVIS_Main/JARVIS_Main.ino` and `firmware/node_esp32/JARVIS_Node/JARVIS_Node.ino` in Arduino IDE, adjust settings in `config.h`, and upload to your dev kits.

For full setup details, refer to [docs/SETUP.md](file:///c:/Users/muhdu/PATHU/jarvis/docs/SETUP.md).
For commands and libraries check, refer to [docs/DEPLOYMENT.md](file:///c:/Users/muhdu/PATHU/jarvis/docs/DEPLOYMENT.md).
For debugging guide, refer to [docs/TROUBLESHOOTING.md](file:///c:/Users/muhdu/PATHU/jarvis/docs/TROUBLESHOOTING.md).
