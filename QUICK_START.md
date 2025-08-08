# 🚀 Quick Start Guide

**Get up and running with the Intraday SuperTrend MA Strategy in 15 minutes**

## ⚡ 5-Step Quick Setup

### Step 1: Install Dependencies (2 minutes)
```bash
pip install -r requirements.txt
```

### Step 2: Download IB Gateway (5 minutes)
1. Go to [Interactive Brokers API Download](https://www.interactivebrokers.com/en/trading/ib-api.php)
2. Download **IB Gateway** for your operating system
3. Install and launch it

### Step 3: Configure IB Gateway (3 minutes)
1. **Login** with your IBKR credentials
2. **Select "Paper Trading"** mode (safe virtual money)
3. **Enable API**: Configure → Settings → API → Settings
   - ✅ Check "Enable ActiveX and Socket Clients"
   - ✅ Set Socket Port to `4002`
   - ✅ Add `127.0.0.1` to Trusted IPs
4. **Click OK** and restart Gateway

### Step 4: Test Connection (2 minutes)
```python
from ib_insync import IB

ib = IB()
try:
    ib.connect('127.0.0.1', 4002, clientId=1)
    print("✅ Connected successfully!")
    print(f"Account: {ib.managedAccounts()}")
    ib.disconnect()
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### Step 5: Run First Backtest (3 minutes)
```bash
python backtest_ibkr.py
```

That's it! Your first backtest is running. Results will be saved to `backtests/QQQ/[timestamp]/`

---

## 🎯 What You Just Accomplished

✅ **Installed** all required Python libraries  
✅ **Set up** IBKR Gateway with API access  
✅ **Tested** the connection to Interactive Brokers  
✅ **Ran** your first strategy backtest  
✅ **Generated** performance results and charts  

---

## 📊 Understanding Your Results

After the backtest completes, check the `backtests/QQQ/` folder for:

- **`trades.csv`**: Complete log of all trades
- **`equity_curve.png`**: Visual chart of performance
- **`status.txt`**: Execution log

**Good results to look for:**
- ✅ Total return > 5% annually
- ✅ Win rate > 50%
- ✅ At least 20+ trades for statistical significance

---

## 🔄 Next Steps

### For Beginners:
1. **Read the full [README.md](README.md)** to understand the strategy
2. **Try different symbols** (SPY, AAPL, TSLA)
3. **Experiment with parameters** using [CONFIGURATION_GUIDE.md](CONFIGURATION_GUIDE.md)

### For Intermediate Users:
1. **Run the parameter optimization** script
2. **Test with live data** (still using paper trading)
3. **Set up monitoring and alerts**

### Before Live Trading:
1. **✅ Test thoroughly** with paper trading for at least 1 month
2. **✅ Understand** all strategy parameters and risks
3. **✅ Start small** with position sizes you can afford to lose
4. **✅ Monitor constantly** during live trading

---

## 🚨 Quick Troubleshooting

**Connection Issues?**
- ✅ Make sure IB Gateway is running and logged in
- ✅ Check API is enabled (see Step 3 above)
- ✅ Try port 4002 (paper) or 4001 (live)

**No Data?**
- ✅ Ensure market is open (9:30 AM - 4:00 PM ET)
- ✅ Try QQQ first (most reliable data)
- ✅ Check your IBKR market data subscriptions

**Import Errors?**
```bash
pip install --upgrade pandas numpy ib-insync matplotlib
```

---

## 💡 Pro Tips

1. **Always start with paper trading** - it's identical to live trading but with virtual money
2. **QQQ is the best symbol for beginners** - highly liquid with consistent behavior
3. **Run backtests on different time periods** to validate strategy robustness
4. **Monitor your first live trades closely** - automated doesn't mean unattended
5. **Keep position sizes small initially** - you can always scale up later

---

**Ready to dive deeper? Check out the complete [README.md](README.md) and [IBKR_SETUP_GUIDE.md](IBKR_SETUP_GUIDE.md) for comprehensive documentation.**

Happy Trading! 📈
