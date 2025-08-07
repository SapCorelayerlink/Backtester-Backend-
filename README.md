# 📊 Stock Screener with AI Agent

A modern, AI-powered stock screening application that combines real-time market data with intelligent analysis using LangGraph and the Qwen AI model.

![Stock Screener](https://img.shields.io/badge/Stock-Screener-blue) ![AI Powered](https://img.shields.io/badge/AI-Powered-green) ![React](https://img.shields.io/badge/React-18-blue) ![Python](https://img.shields.io/badge/Python-3.8+-green) ![LangGraph](https://img.shields.io/badge/LangGraph-Latest-orange)

## 🚀 Features

### Frontend (React + TypeScript)
- 📈 **Real-time Stock Screeners**: Day gainers, losers, most active, tech stocks, and more
- 🤖 **AI Chat Interface**: Natural language interaction with stock screening agent
- 📊 **Technical Analysis Dashboard**: Advanced charting and indicators
- 🌟 **Market Overview**: Live market sentiment and key metrics
- 📱 **Responsive Design**: Modern UI with shadcn/ui components
- ⚡ **Real-time Updates**: Live data streaming and updates

### Backend (Python + LangGraph)
- 🧠 **LangGraph AI Agent**: Intelligent stock screening powered by Qwen model
- 🔍 **Yahoo Finance Integration**: Real-time market data and screening
- 🛡️ **Fallback Support**: Graceful handling of API failures
- 🌐 **RESTful API**: Clean Flask-based API endpoints
- 📊 **Structured Output**: Beautiful formatted stock analysis tables
- 🔄 **Memory Support**: Persistent conversation memory

## 🛠️ Technology Stack

### Frontend
- **React 18** with TypeScript
- **Vite** for fast development
- **Tailwind CSS** for styling
- **shadcn/ui** for components
- **Recharts** for data visualization
- **Lucide React** for icons

### Backend
- **Python 3.8+** 
- **LangGraph** for AI agent orchestration
- **LangChain** for LLM integration
- **Ollama** with Qwen model
- **Flask** for REST API
- **yfinance** for market data
- **Flask-CORS** for cross-origin requests

## 📋 Prerequisites

Before running the application, ensure you have:

1. **Node.js 18+** and npm
2. **Python 3.8+** and pip  
3. **Ollama** with Qwen model

### Installing Ollama and Qwen

```bash
# Install Ollama (visit https://ollama.ai for installation instructions)
# For macOS/Linux:
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull Qwen model
ollama pull qwen
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd stock-stream-viz-99

# Install frontend dependencies
npm install

# Install backend dependencies
cd backend
pip install -r requirements.txt
```

### 2. Start the Backend

```bash
# From the backend directory
cd backend

# Option 1: Using startup script (recommended)
python start_server.py

# Option 2: Direct Flask app
python app.py

# Option 3: Windows users
start_backend.bat
```

The backend will start on `http://localhost:5000`

### 3. Start the Frontend

```bash
# From the main project directory
npm run dev
```

The frontend will start on `http://localhost:5173`

### 4. Test the Integration

```bash
# Test backend endpoints
cd backend
python test_backend.py
```

## 🎯 Usage

### AI Chat Interface

Ask the AI agent natural language questions:

- *"Show me day gainers"*
- *"Find technology growth stocks"* 
- *"What are the most active stocks today?"*
- *"Undervalued large cap companies"*
- *"Best stocks for London trading session"*

### Manual Screening

Use the screening controls to filter stocks by:
- Day gainers/losers
- Most active stocks
- Technology growth
- Undervalued large caps
- Small cap gainers
- And more...

### Technical Analysis

- View advanced charts with multiple indicators
- Analyze price movements and patterns
- Monitor volume and volatility
- Track support and resistance levels

## 📁 Project Structure

```
stock-stream-viz-99/
├── backend/                    # Python backend
│   ├── app.py                 # Main Flask application
│   ├── stock_screener_tool.py # Yahoo Finance integration  
│   ├── requirements.txt       # Python dependencies
│   ├── start_server.py       # Startup script
│   ├── test_backend.py       # Testing suite
│   └── README.md             # Backend documentation
├── src/                      # React frontend
│   ├── components/           # UI components
│   ├── services/            # API services
│   ├── pages/              # Page components
│   └── lib/                # Utilities
├── public/                  # Static assets
└── README.md               # This file
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check and status |
| POST | `/chat` | Chat with AI agent |
| POST | `/screener` | Direct stock screening |
| GET | `/screeners` | Available screen types |

## 🧪 Testing

### Frontend Testing
```bash
npm run test
```

### Backend Testing
```bash
cd backend
python test_backend.py
```

### Manual Testing
1. Start both frontend and backend
2. Open http://localhost:5173
3. Try the AI chat with various stock queries
4. Test manual screening controls
5. Verify real-time data updates

## 🚀 Deployment

### Frontend Deployment
The frontend can be deployed to any static hosting service:

```bash
npm run build
# Deploy the 'dist' folder
```

### Backend Deployment
For production deployment:

1. Update CORS settings in `app.py`
2. Use a production WSGI server (gunicorn)
3. Set up environment variables
4. Configure Ollama on the server

## 🔧 Configuration

### Backend Configuration
- Port: `5000` (configurable in `app.py`)
- Model: `qwen` (configurable in `app.py`)
- CORS: Enabled for all origins (development)

### Frontend Configuration
- Backend URL: `http://localhost:5000` (configurable in `src/services/pythonBackend.ts`)
- Development port: `5173`

## 🐛 Troubleshooting

### Common Issues

1. **Backend connection errors**:
   - Ensure backend is running on port 5000
   - Check if Ollama service is running
   - Verify Qwen model is installed

2. **Ollama issues**:
   ```bash
   ollama serve
   ollama list  # Check installed models
   ollama pull qwen  # Install if missing
   ```

3. **Port conflicts**:
   - Change backend port in `app.py` 
   - Update frontend config in `pythonBackend.ts`

4. **Yahoo Finance API limits**:
   - The app includes fallback demo data
   - Check internet connection for real-time data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **LangGraph** for AI agent orchestration
- **Ollama** for local LLM hosting
- **Yahoo Finance** for market data
- **shadcn/ui** for beautiful components
- **Qwen** AI model for intelligent responses

## 📞 Support

If you encounter any issues:

1. Check the troubleshooting section
2. Review backend logs for errors
3. Test with the provided test scripts
4. Create an issue with detailed error information

---

**Happy Stock Screening! 📈🤖**