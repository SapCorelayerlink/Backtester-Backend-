# IBKR Gateway Setup Guide

## Prerequisites

1. **IBKR Account**: You need an Interactive Brokers account
2. **API Access**: Enable API access in your IBKR account settings
3. **IBKR Gateway**: Download and install IBKR Gateway from IBKR website

## Step 1: Download IBKR Gateway

1. Go to [IBKR Downloads](https://www.interactivebrokers.com/en/trading/ib-api.php)
2. Download "IBKR Gateway" for your operating system
3. Install the application

## Step 2: Configure IBKR Gateway

### First Time Setup

1. **Launch IBKR Gateway**
   - Windows: `C:\Program Files\IBKR\TWS\ibgateway\start.bat`
   - Mac: `/Applications/IBKR Gateway/`
   - Linux: `~/ibgateway/`

2. **Login with your IBKR credentials**
   - Enter your username and password
   - Complete 2FA if enabled

3. **Configure API Settings**
   - Go to `File` → `Global Configuration` (or `Edit` → `Preferences`)
   - Navigate to `API` → `Settings`
   - Enable `Enable ActiveX and Socket Clients`
   - Set `Socket port` to `4001`
   - Enable `Allow connections from localhost`
   - Set `Read-Only API` to `No` (if you want to place trades)

4. **Save Configuration**
   - Click `OK` to save settings
   - Restart IBKR Gateway

### Important Settings

```
Socket port: 4001
Enable ActiveX and Socket Clients: ✓
Allow connections from localhost: ✓
Read-Only API: No (for trading) / Yes (for data only)
```

## Step 3: Test Connection

### Quick Test
```bash
python quick_ibkr_test.py
```

### Full Test (includes API server)
```bash
python test_ibkr_connection.py
```

## Step 4: Troubleshooting

### Common Issues

1. **Port 4001 not open**
   - Check if IBKR Gateway is running
   - Verify port 4001 is configured in Gateway settings
   - Check Windows Firewall settings

2. **Connection refused**
   - Ensure API connections are enabled in Gateway
   - Check if another application is using port 4001
   - Restart IBKR Gateway

3. **Authentication failed**
   - Verify your IBKR credentials
   - Check if 2FA is properly configured
   - Ensure API access is enabled in your IBKR account

4. **Market data not available**
   - Check if markets are open
   - Verify you have market data subscriptions
   - Check account permissions

### Windows Firewall

If you're on Windows, you may need to allow IBKR Gateway through the firewall:

1. Open Windows Defender Firewall
2. Click "Allow an app or feature through Windows Defender Firewall"
3. Find IBKR Gateway in the list or add it manually
4. Allow it on both Private and Public networks

### Port Check

To verify the port is open:
```bash
# Windows PowerShell
Test-NetConnection -ComputerName localhost -Port 4001

# Or use telnet
telnet localhost 4001
```

## Step 5: Start Trading

Once the connection is working:

1. **Run the quick test**:
   ```bash
   python quick_ibkr_test.py
   ```

2. **Start the full API server**:
   ```bash
   python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
   ```

3. **Access the web interface**:
   - Open browser to `http://127.0.0.1:8000`
   - Navigate to the dashboard

## Security Notes

- Keep your IBKR credentials secure
- Use a strong password
- Enable 2FA on your IBKR account
- Only allow connections from localhost in production
- Consider using a paper trading account for testing

## Support

If you encounter issues:

1. Check IBKR Gateway logs
2. Verify your IBKR account status
3. Contact IBKR support if needed
4. Check the project's documentation in `docs/` folder
