# ❓ Frequently Asked Questions

**Common questions and troubleshooting for the Intraday SuperTrend MA Strategy**

## 🏦 IBKR Setup Questions

### Q: Do I need a real Interactive Brokers account?
**A**: Yes, but you can use **Paper Trading** mode which gives you $1,000,000 virtual money to test with. This is identical to live trading but with no financial risk.

### Q: What's the difference between IB Gateway and TWS?
**A**: 
- **IB Gateway**: Lightweight, stable, perfect for automated trading (recommended)
- **TWS**: Full trading platform with charts, news, analysis tools
- **For algorithmic trading**: Use Gateway for running strategies, TWS for manual analysis

### Q: Which ports should I use?
**A**:
- **4002**: IB Gateway Paper Trading (recommended for testing)
- **4001**: IB Gateway Live Trading
- **7497**: TWS Paper Trading
- **7496**: TWS Live Trading

### Q: Can I run this on a free IBKR account?
**A**: Yes! Paper trading is free, and the strategy works with any IBKR account type. Some market data may require subscriptions for live trading.

---

## 💰 Trading and Risk Questions

### Q: How much money do I need to start?
**A**: 
- **Paper Trading**: Free (virtual money)
- **Live Trading**: Minimum $25,000 for day trading (US regulation), but you can start smaller for swing trading
- **Recommendation**: Start with paper trading, then begin live with $5,000-$10,000

### Q: What's a realistic return expectation?
**A**: 
- **Conservative**: 8-15% annually
- **Moderate**: 15-25% annually  
- **Aggressive**: 25%+ annually (higher risk)
- **Reality Check**: Past performance doesn't guarantee future results

### Q: How much risk is involved?
**A**: 
- **Per Trade Risk**: 1-3% of account (configurable via stop loss)
- **Maximum Drawdown**: Can be 10-20% during bad periods
- **Black Swan Risk**: Unexpected market events can cause larger losses
- **Mitigation**: Start small, use stops, diversify

### Q: Can I lose more than I invest?
**A**: No, with stock trading you can only lose your invested amount. The strategy doesn't use leverage or margin by default.

---

## 🔧 Technical Setup Questions

### Q: What operating system requirements?
**A**: 
- **Windows**: 10 or newer
- **Mac**: macOS 10.14 or newer  
- **Linux**: Most distributions (Ubuntu 18.04+)
- **RAM**: 4GB minimum, 8GB recommended
- **Internet**: Stable broadband connection

### Q: Do I need programming experience?
**A**: 
- **Basic Usage**: No, just follow the setup guides
- **Customization**: Basic Python knowledge helpful
- **Advanced Features**: Some programming experience recommended

### Q: Can I run this on a VPS/cloud server?
**A**: Yes! Many traders run strategies on:
- **AWS EC2**
- **Google Cloud**
- **DigitalOcean**
- **Vultr**

Benefits: 24/7 uptime, faster internet, no local computer dependency.

---

## 📊 Strategy Questions

### Q: What symbols work best with this strategy?
**A**:
- **Excellent**: QQQ, SPY (ETFs, very liquid)
- **Good**: AAPL, MSFT, GOOGL (large cap stocks)
- **Challenging**: Small cap stocks, low volume symbols
- **Avoid**: Penny stocks, volatile biotech, recently IPO'd companies

### Q: What timeframes should I use?
**A**:
- **Default**: 30min MAs with 3h SuperTrend (recommended)
- **More Aggressive**: 15min MAs with 1h SuperTrend
- **More Conservative**: 1h MAs with 6h SuperTrend
- **Don't Use**: Very short timeframes (1min, 5min) due to noise

### Q: How often does the strategy trade?
**A**:
- **Typical**: 2-8 trades per week per symbol
- **Active Periods**: Up to 2-3 trades per day
- **Quiet Periods**: May go days without trading
- **Depends On**: Market volatility, symbol chosen, parameters

### Q: Why does the strategy sometimes not trade for days?
**A**: This is **normal and good**! The strategy waits for:
- ✅ SuperTrend direction alignment
- ✅ Moving average order confirmation
- ✅ Clean entry setups

**Better to wait** for good setups than force bad trades.

---

## 🛠️ Technical Issues

### Q: "Connection refused" error when connecting to IBKR
**A**: **Solutions in order**:
1. ✅ Check IB Gateway is running and logged in
2. ✅ Verify API is enabled: Configure → Settings → API → Settings
3. ✅ Confirm correct port (4001 for paper trading)
4. ✅ Add 127.0.0.1 to Trusted IPs
5. ✅ Restart IB Gateway completely
6. ✅ Try different client ID (1, 2, 3, etc.)
7. ✅ Check Windows firewall isn't blocking

### Q: "No market data received" error
**A**: **Check these**:
1. ✅ Market hours (9:30 AM - 4:00 PM ET for US stocks)
2. ✅ Symbol exists and is tradeable (try QQQ first)
3. ✅ Market data subscriptions in IBKR account
4. ✅ Weekend/holiday (markets closed)
5. ✅ Paper trading mode has some data limitations

### Q: Strategy runs but makes no trades
**A**: **This could be normal**, but check:
1. ✅ Market conditions may not meet entry criteria
2. ✅ SuperTrend and MAs may not be aligned
3. ✅ Market hours settings
4. ✅ Position sizing (too large positions may be rejected)
5. ✅ Account permissions (some accounts have trading restrictions)

### Q: Python import errors
**A**: **Fix dependencies**:
```bash
pip install --upgrade pandas numpy ib-insync matplotlib nest-asyncio
```

If still having issues:
```bash
pip uninstall ib-insync
pip install ib-insync==0.9.86
```

---

## 📈 Performance Questions

### Q: My backtest shows losses, is the strategy broken?
**A**: **Not necessarily**:
- ✅ Test different time periods (bear markets vs bull markets)
- ✅ Check if symbol is appropriate (avoid low-volume stocks)
- ✅ Verify parameters aren't over-optimized
- ✅ Consider transaction costs and slippage
- ✅ Some periods are naturally unprofitable

### Q: How do I know if my parameters are good?
**A**: **Key metrics to check**:
- ✅ **Win Rate**: 45-70% (higher isn't always better)
- ✅ **Profit Factor**: > 1.3 (gross profit / gross loss)
- ✅ **Total Trades**: > 30 for statistical significance
- ✅ **Max Drawdown**: < 20% ideally
- ✅ **Sharpe Ratio**: > 1.0 is good, > 2.0 is excellent

### Q: Should I optimize parameters?
**A**: **Yes, but carefully**:
- ✅ **Do**: Test on historical data, validate on recent data
- ✅ **Do**: Change one parameter at a time
- ✅ **Don't**: Over-optimize (curve fitting)
- ✅ **Don't**: Use future data in optimization
- ✅ **Rule**: If it looks too good to be true, it probably is

---

## 🔄 Operational Questions

### Q: Can I run multiple strategies simultaneously?
**A**: Yes! **Best practices**:
- ✅ Use different client IDs for each strategy
- ✅ Monitor total position size across all strategies
- ✅ Avoid trading highly correlated symbols
- ✅ Ensure sufficient account equity

### Q: What happens if my computer crashes during trading?
**A**: **Risk mitigation**:
- ✅ Bracket orders (stop/target) remain active on IBKR servers
- ✅ Open positions won't automatically close
- ✅ You can manually close positions through TWS
- ✅ Consider running on a VPS for reliability

### Q: How do I monitor the strategy remotely?
**A**: **Options**:
- ✅ Email alerts (see USAGE_EXAMPLES.md)
- ✅ Telegram/Discord bots
- ✅ Remote desktop to your trading computer
- ✅ VPS with web interface
- ✅ IBKR mobile app for position monitoring

### Q: What about taxes and reporting?
**A**: **Important considerations**:
- ✅ IBKR provides detailed trade reports
- ✅ Frequent trading may generate significant tax events
- ✅ Consult a tax professional familiar with trading
- ✅ Consider tax-advantaged accounts where appropriate

---

## 🚨 Emergency Procedures

### Q: How do I stop all trading immediately?
**A**: **Emergency stops**:
1. **Close the Python script** (Ctrl+C)
2. **Close IB Gateway** (disconnects all API clients)
3. **Use TWS** to manually close positions if needed
4. **Call IBKR** if unable to access accounts

### Q: What if the strategy starts trading erratically?
**A**: **Immediate actions**:
1. **Stop the script** immediately
2. **Check account balance** and open positions
3. **Close any unwanted positions** manually
4. **Review recent trades** for anomalies
5. **Don't restart** until you understand what happened

### Q: Position sizing seems wrong
**A**: **Verify**:
- ✅ Account equity is being calculated correctly
- ✅ Position size parameters (quantity setting)
- ✅ No leverage/margin being used unintentionally
- ✅ Currency conversions (if trading non-USD symbols)

---

## 📚 Learning and Development

### Q: How can I learn more about the strategy logic?
**A**: **Resources**:
- ✅ Read the complete code with comments
- ✅ Study SuperTrend and Moving Average indicators
- ✅ Paper trade and observe decision-making
- ✅ Backtest on different market conditions
- ✅ Join trading communities and forums

### Q: Can I modify the strategy?
**A**: **Absolutely!** **Start with**:
- ✅ Parameter adjustments (safer)
- ✅ Additional filters (market conditions, volatility)
- ✅ Different exit conditions
- ✅ Portfolio management features
- ✅ **Test thoroughly** before live trading

### Q: Where can I get help?
**A**: **Support options**:
- ✅ **This documentation** (most common issues covered)
- ✅ **IBKR Support** for account/platform issues
- ✅ **Python/Pandas Documentation** for coding questions
- ✅ **Trading Forums** for strategy discussions
- ✅ **Code Comments** explain the logic

---

## 🎓 Best Practices Summary

### For Beginners:
1. ✅ **Start with paper trading** for at least 1 month
2. ✅ **Use default parameters** initially
3. ✅ **Trade only QQQ or SPY** to start
4. ✅ **Monitor closely** for the first few weeks
5. ✅ **Keep detailed notes** of what works/doesn't work

### For Intermediate Traders:
1. ✅ **Optimize parameters** systematically
2. ✅ **Test multiple symbols** and timeframes
3. ✅ **Implement risk management** enhancements
4. ✅ **Set up monitoring** and alerts
5. ✅ **Plan for different market regimes**

### For Advanced Users:
1. ✅ **Develop custom strategies** based on this framework
2. ✅ **Implement portfolio management**
3. ✅ **Use machine learning** for parameter optimization
4. ✅ **Deploy on cloud infrastructure**
5. ✅ **Contribute back** to the community

---

**Remember**: Trading involves risk. Start small, learn continuously, and never risk more than you can afford to lose. The best strategy is one you understand completely and can execute with discipline.
