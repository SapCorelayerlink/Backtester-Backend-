# ⚡ Quick Commands Reference

## 🚀 One-Command Setup

### Windows
```bash
start_bactester.bat
```

### macOS/Linux
```bash
chmod +x start_bactester.sh && ./start_bactester.sh
```

### Manual
```bash
python quick_start.py
```

## 🎯 Most Common Commands

### Start Database
```bash
cd config && docker-compose -f docker-compose.timescaledb.yml up -d
```

### Test Strategies
```bash
# RSI + VWAP Strategy (4-hour)
python test_rsi_vwap_simple.py

# Turtle Strategy (1-hour)
python test_turtle_strategy.py
```

### View Database
```bash
python view_database_data.py
```

### Start API Server
```bash
python -m api.main
```

### Reset Database
```bash
python reset_database.py
```

## 📊 Strategy Timeframes

| Strategy | Timeframe | Description |
|----------|-----------|-------------|
| Turtle | 1-hour | Intraday trend following |
| RSI+VWAP | 4-hour | RSI on VWAP signals |
| Support/Resistance | 4-hour | Dynamic S/R zones |
| Swing Failure | 4-hour | Pivot failure patterns |
| Bollinger+5EMA | Flexible | Any timeframe |

## 🔧 Troubleshooting

### Database Issues
```bash
# Restart database
docker-compose -f config/docker-compose.timescaledb.yml restart

# Reset everything
docker-compose -f config/docker-compose.timescaledb.yml down
docker volume rm bactester_timescale-data
docker-compose -f config/docker-compose.timescaledb.yml up -d
python reset_database.py
```

### Python Issues
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version
```

## 🌐 Access Points

- **API Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8000/dashboard
- **Frontend**: http://localhost:5173 (if running)

## 📝 Environment Variables

```bash
# Database
PG_HOST=localhost
PG_PORT=5432
PG_DB=bactester
PG_USER=bactester
PG_PASSWORD=bactester

# API Keys (optional)
POLYGON_API_KEY=your_key_here
IBKR_HOST=localhost
IBKR_PORT=4001
```

---

**💡 Tip**: Use `python quick_start.py` for an interactive menu with all options!
