# Aetios-Med

**Offline-first Medical Study Assistant with Living Knowledge Graph**

An Electron app that wraps a quantized medical LLM (OpenBioLLM-8B) to act as a Meta-Assistant with a living knowledge graph for UK medical students.

## 🚀 Quick Start

### One-Command Install

**macOS/Linux:**
```bash
./scripts/install.sh
```

**Windows:**
```powershell
.\scripts\install.ps1
```

### Run
```bash
npm start
```

### First-Time Setup
1. Open Settings → Download AI Model (one-time, ~4GB download)
2. Configure your Anki export folder
3. Configure your Notability folder (optional)
4. Start studying!

## 🎯 Features

- 🧠 **Local AI Tutor** - OpenBioLLM-8B with Metal/CUDA optimization
- 📊 **Knowledge Graph** - 75+ UK medical curriculum topics visualized
- 🎴 **Anki Integration** - Auto-parse .apkg files with topic mapping
- 📈 **Spaced Repetition** - FSRS-4 algorithm for optimal review
- 🎯 **Quiz Generation** - AI-powered quizzes from weak areas
- 📅 **Study Planning** - Personalized plans with ICS export
- 🔒 **Offline-First** - Works completely offline after setup
- 🔐 **Secure** - AES-256 encryption with platform keyring

## 📁 Structure

- `backend/` - Python FastAPI (9 services, 6 routers, agent with 18 tools)
- `frontend/` - React + TypeScript (38+ components, Cytoscape.js graph)
- `electron/` - Desktop wrapper
- `scripts/` - Installation and build scripts

## 🧪 Testing

```bash
cd backend && pytest
cd frontend && npm test
```

## 📚 API Docs

- Backend: http://localhost:8741/docs
- Frontend: http://localhost:5173

## 📊 Coverage

75+ topics across Cardiovascular, Respiratory, GI, Neurology, Renal, Endocrine, MSK, Haematology, Infectious Disease, Pharmacology, Clinical Skills

## 🏗️ Development

### Prerequisites
- Node.js 18-22 (LTS recommended, avoid odd-numbered versions)
- Python 3.10+
- Git

### Manual Setup

```bash
# Clone
git clone https://github.com/Hider74/Aetios-Med.git
cd Aetios-Med

# Backend
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt && cd ..

# Frontend
cd frontend && npm install && cd ..

# Root
npm install

# Run (3 terminals)
cd backend && uvicorn app.main:app --reload --port 8741
cd frontend && npm run dev
npm run electron:dev
```

### Build for Production

**macOS:**
```bash
./scripts/build-mac.sh
```

**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-win.ps1
```

## 📄 License

MIT - see LICENSE

## 🙏 Credits

- OpenBioLLM-8B by Ankit Pal
- llama.cpp for inference
- UK medical students for feedback

---

**Note**: Educational tool only. Verify medical information with qualified professionals
