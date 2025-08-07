# 🚀 Quick Setup Guide

Get your Stock Screener with AI Agent up and running in just a few minutes!

## ⚡ Super Quick Start (5 minutes)

### Step 1: Prerequisites Check
- ✅ Node.js installed? `node --version`
- ✅ Python installed? `python --version`
- ✅ Git installed? `git --version`

### Step 2: Install Ollama (2 minutes)
```bash
# Visit https://ollama.ai and download for your OS
# OR for macOS/Linux:
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama (keep this running in a terminal)
ollama serve

# In another terminal, install Qwen model
ollama pull qwen
```

### Step 3: Setup Project (2 minutes)
```bash
# Clone and navigate
git clone <your-repo-url>
cd stock-stream-viz-99

# Install everything at once (Windows users)
setup_project.bat

# OR manually:
npm install
cd backend && pip install -r requirements.txt
```

### Step 4: Launch (1 minute)
```bash
# Terminal 1: Start backend
cd backend
python start_server.py

# Terminal 2: Start frontend  
cd ..
npm run dev
```

🎉 **Done!** Open http://localhost:5173

## 🐛 Quick Fixes

**Backend won't start?**
```bash
cd backend
python test_backend.py  # Check what's wrong
```

**Ollama not working?**
```bash
ollama list           # Check models
ollama pull qwen      # Install Qwen if missing
ollama serve         # Make sure it's running
```

**Frontend can't connect?**
- Check backend is on port 5000
- Check browser console for errors
- Ensure CORS is enabled

## 🧪 Quick Test

1. Open http://localhost:5173
2. Try chat: *"Show me day gainers"*
3. Use manual screener controls
4. Check technical analysis dashboard

**All working? You're ready to go! 🚀**

## 🆘 Need Help?

- Check main [README.md](README.md) for detailed docs
- Run `python backend/test_backend.py` for diagnostics
- Check backend [README.md](backend/README.md) for API details
