# 🏦 Interactive Brokers (IBKR) Setup Guide

**Complete step-by-step guide for non-technical users to set up IBKR Gateway for algorithmic trading**

## 📋 Prerequisites

Before starting, make sure you have:
- ✅ An Interactive Brokers account (you can open one at [interactivebrokers.com](https://www.interactivebrokers.com))
- ✅ Windows, Mac, or Linux computer
- ✅ Stable internet connection
- ✅ Basic computer skills (installing software, following instructions)

## 🎯 What You'll Accomplish

By the end of this guide, you'll have:
1. ✅ IBKR Gateway installed and configured
2. ✅ API access enabled for algorithmic trading
3. ✅ Paper trading account set up for safe testing
4. ✅ Connection verified with the trading strategy

---

## 📥 Step 1: Download IBKR Gateway

### Why IB Gateway vs TWS?

- **IB Gateway**: Lightweight, stable, perfect for automated trading
- **TWS (Trader Workstation)**: Full trading platform with charts and analysis

**Recommendation**: Use IB Gateway for running algorithms, TWS for manual trading.

### Download Instructions

1. **Go to IBKR Website**:
   - Visit: [https://www.interactivebrokers.com/en/trading/ib-api.php](https://www.interactivebrokers.com/en/trading/ib-api.php)
   - Look for the **"IB Gateway"** section

2. **Choose Your Operating System**:
   - **Windows**: Download `ibgateway-10.19-standalone-win64.exe` (or latest version)
   - **Mac**: Download `ibgateway-10.19-standalone-macos-x64.dmg`
   - **Linux**: Download `ibgateway-10.19-standalone-linux-x64.sh`

3. **Download and Save**:
   - Save the file to your Downloads folder
   - File size is typically 200-300 MB

---

## 🛠️ Step 2: Install IB Gateway

### Windows Installation

1. **Run the Installer**:
   - Double-click the downloaded `.exe` file
   - If Windows asks "Do you want to allow this app to make changes?", click **"Yes"**

2. **Follow the Installation Wizard**:
   - Click **"Next"** through the welcome screens
   - Accept the license agreement
   - Choose installation location (default is fine: `C:\Program Files\IB Gateway`)
   - Click **"Install"**

3. **Complete Installation**:
   - Wait for installation to complete (2-3 minutes)
   - Click **"Finish"**
   - You should see an IB Gateway icon on your desktop

### Mac Installation

1. **Open the DMG File**:
   - Double-click the downloaded `.dmg` file
   - Drag the IB Gateway icon to the Applications folder

2. **Security Settings**:
   - If Mac says "IB Gateway can't be opened because it's from an unidentified developer"
   - Go to **System Preferences** → **Security & Privacy**
   - Click **"Open Anyway"** next to the IB Gateway message

### Linux Installation

1. **Make the File Executable**:
   ```bash
   chmod +x ibgateway-10.19-standalone-linux-x64.sh
   ```

2. **Run the Installer**:
   ```bash
   ./ibgateway-10.19-standalone-linux-x64.sh
   ```

3. **Follow the Text-Based Installer**:
   - Press Enter to accept defaults
   - Type 'Y' to accept the license

---

## 🔑 Step 3: First Login and Basic Setup

### Launch IB Gateway

1. **Start the Application**:
   - **Windows**: Double-click the desktop icon or find in Start Menu
   - **Mac**: Open from Applications folder
   - **Linux**: Run from installation directory

2. **Initial Screen**:
   - You'll see the IB Gateway login window
   - It should look like a simple login form

### Login to Your Account

1. **Enter Your Credentials**:
   - **Username**: Your IBKR username
   - **Password**: Your IBKR password

2. **Choose Trading Mode**:
   - **Paper Trading** (RECOMMENDED): Use virtual money, no risk
   - **Live Trading**: Real money trading (only after you're comfortable)

3. **Select Server**:
   - **US**: For most US-based users
   - **Hong Kong**: For Asian users
   - **Europe**: For European users

4. **Click "Login"**:
   - First login may take 30-60 seconds
   - You may see security prompts - click "Accept"

### Understanding the Gateway Interface

After login, you'll see a small window with:
- **Connection status** (should show "Connected")
- **Account information**
- **Menu bar** with settings

**Important**: Keep this window open while running trading strategies!

---

## ⚙️ Step 4: Enable API Access (CRITICAL STEP)

This is the most important step - without API access, the trading strategy cannot connect.

### Open API Settings

1. **In IB Gateway Window**:
   - Click **"Configure"** in the menu bar
   - Select **"Settings"** from the dropdown
   - Choose **"API"** from the left sidebar
   - Click **"Settings"** under the API section

### Configure API Settings

You'll see a window with several options. Configure each as follows:

#### ✅ Enable ActiveX and Socket Clients
- **Check the box** next to "Enable ActiveX and Socket Clients"
- This allows external programs (like our strategy) to connect

#### ✅ Socket Port
- **Paper Trading**: Set to `4002`
- **Live Trading**: Set to `4001`
- This is the "address" our strategy will use to connect

#### ✅ Master API Client ID
- Set to `1000` (or any number above 100)
- This prevents conflicts with manual trading

#### ✅ Read-Only API
- **Leave UNCHECKED** if you want to place trades
- **Check** if you only want to test data connections (no trading)

#### ✅ Trusted IPs
- Click the **"+"** button
- Add: `127.0.0.1`
- This allows connections from your local computer

### Apply Settings

1. Click **"OK"** to save settings
2. Click **"OK"** again to close the settings window
3. **Restart IB Gateway** (important for settings to take effect):
   - Close IB Gateway completely
   - Restart it and log in again

---

## 🧪 Step 5: Set Up Paper Trading (Highly Recommended)

Paper trading lets you test strategies with virtual money - no financial risk!

### Access Paper Trading

1. **During Login**:
   - Select **"Paper Trading"** instead of "Live Trading"
   - Everything else remains the same

2. **Paper Trading Features**:
   - ✅ $1,000,000 virtual starting capital
   - ✅ Real market data and prices
   - ✅ Same interface as live trading
   - ✅ No risk to your real money
   - ✅ Perfect for testing strategies

### Verify Paper Trading Setup

1. **After Login**:
   - Look for "Paper Trading" indicator in the Gateway window
   - Account number should start with "DU" (Demo User)

2. **Test Order (Optional)**:
   - You can manually place a test order to verify everything works
   - Buy 1 share of QQQ to confirm order routing

---

## 🔌 Step 6: Test Your Connection

Before running the full strategy, let's test the connection.

### Quick Connection Test

1. **Ensure IB Gateway is Running**:
   - Window should show "Connected"
   - API should be enabled (from Step 4)

2. **Test with Python**:
   ```python
   from ib_insync import IB
   
   # Create connection
   ib = IB()
   
   try:
       # Connect (use 4001 for paper trading, 4002 for live)
ib.connect('127.0.0.1', 4001, clientId=1)
       print("✅ SUCCESS: Connected to IBKR Gateway!")
       
       # Get account info
       accounts = ib.managedAccounts()
       print(f"📊 Account(s): {accounts}")
       
       # Disconnect
       ib.disconnect()
       print("🔌 Disconnected cleanly")
       
   except Exception as e:
       print(f"❌ ERROR: {e}")
       print("🔍 Check that:")
       print("   - IB Gateway is running and logged in")
       print("   - API is enabled in Gateway settings")
       print("   - Port 4001 is set for paper trading")
   ```

3. **Run the Test**:
   - Save the code above as `test_connection.py`
   - Run: `python test_connection.py`
   - You should see the success message

---

## 🚨 Troubleshooting Common Issues

### Issue 1: "Connection Refused" Error

**Symptoms**: 
```
[WinError 1225] The remote computer refused the network connection
```

**Solutions**:
1. ✅ **Check IB Gateway is Running**: Look for the Gateway window
2. ✅ **Verify Login**: Make sure you're logged into Gateway
3. ✅ **Check Port Number**: 4001 for paper, 4002 for live
4. ✅ **Restart Gateway**: Close completely and restart
5. ✅ **Check Firewall**: Windows may be blocking the connection

### Issue 2: "clientId Already in Use"

**Symptoms**:
```
clientId 1 is already in use
```

**Solutions**:
1. ✅ **Change Client ID**: Use a different number (2, 3, 4, etc.)
2. ✅ **Close Other Connections**: Make sure no other programs are connected
3. ✅ **Restart Gateway**: This clears all existing connections

### Issue 3: "API Not Enabled"

**Symptoms**:
```
API not enabled or connection limit exceeded
```

**Solutions**:
1. ✅ **Re-check API Settings**: Follow Step 4 again carefully
2. ✅ **Verify "Enable ActiveX and Socket Clients" is checked**
3. ✅ **Restart Gateway** after changing settings
4. ✅ **Check Connection Limit**: Only a few API connections allowed simultaneously

### Issue 4: "No Market Data"

**Symptoms**: Connection works but no price data

**Solutions**:
1. ✅ **Check Market Hours**: US stock market is open 9:30 AM - 4:00 PM ET
2. ✅ **Verify Market Data Subscriptions**: Some symbols require paid data
3. ✅ **Try QQQ First**: It's included in most basic subscriptions
4. ✅ **Check Symbol Format**: Use "QQQ" not "NASDAQ:QQQ"

### Issue 5: "Permission Denied for Trading"

**Symptoms**: Can connect but can't place orders

**Solutions**:
1. ✅ **Uncheck "Read-Only API"** in Gateway settings
2. ✅ **Use Paper Trading** for testing (safer)
3. ✅ **Check Account Permissions**: Some restrictions may apply to new accounts
4. ✅ **Verify Sufficient Buying Power** in account

---

## ✅ Final Verification Checklist

Before running the trading strategy, verify:

- [ ] **IB Gateway is installed and runs without errors**
- [ ] **You can log in successfully (paper trading recommended)**
- [ ] **API is enabled with correct settings**:
  - [ ] "Enable ActiveX and Socket Clients" is checked
  - [ ] Port 4001 (paper) or 4002 (live) is set
  - [ ] "127.0.0.1" is in Trusted IPs
- [ ] **Connection test passes** (see Step 6)
- [ ] **You understand paper vs live trading**
- [ ] **Gateway window stays open during strategy execution**

---

## 🎓 Understanding Your Setup

### What You've Accomplished

1. **Installed IBKR Gateway**: Your connection to Interactive Brokers
2. **Enabled API Access**: Allows algorithmic trading programs to connect
3. **Set Up Paper Trading**: Safe testing environment with virtual money
4. **Verified Connection**: Confirmed everything works correctly

### How It All Works Together

```
[Your Trading Strategy] → [IBKR API] → [IB Gateway] → [IBKR Servers] → [Stock Market]
```

1. **Trading Strategy**: Python code that makes buy/sell decisions
2. **IBKR API**: Communication layer (ib-insync library)
3. **IB Gateway**: Your local connection to Interactive Brokers
4. **IBKR Servers**: Interactive Brokers' trading infrastructure
5. **Stock Market**: Where actual trades are executed

### Security and Safety

- 🔒 **API access is local only**: Only your computer can connect
- 🛡️ **Paper trading has no risk**: Virtual money only
- 🚦 **You control the connection**: Close Gateway to stop all trading
- 📊 **All trades are logged**: Full audit trail available

---

## 🚀 Next Steps

Now that IBKR Gateway is set up:

1. **Return to the main README.md** for strategy configuration
2. **Run your first backtest** to see historical performance
3. **Test with live data** using paper trading
4. **Monitor results** and adjust parameters as needed

**Remember**: Always test thoroughly with paper trading before considering live trading!

---

## 📞 Additional Resources

### IBKR Official Documentation
- **API Documentation**: [interactivebrokers.github.io/tws-api](https://interactivebrokers.github.io/tws-api/)
- **Gateway User Guide**: Available in your IBKR client portal
- **Market Data Subscriptions**: [www.interactivebrokers.com/en/trading/marketData.php](https://www.interactivebrokers.com/en/trading/marketData.php)

### Helpful IBKR Support
- **Phone Support**: Available in your local region
- **Live Chat**: Available in IBKR client portal
- **Ticket System**: Submit detailed questions through client portal

---

**Congratulations! 🎉 You now have IBKR Gateway set up and ready for algorithmic trading!**

*Remember: Start with paper trading, understand the system, and never risk more than you can afford to lose.*
