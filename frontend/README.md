# Bactester Flutter Frontend

A Flutter application for the Bactester trading backtesting API.

## Features

- **Strategy Management**: View available strategies and run backtests
- **Backtest Results**: View detailed backtest results with equity curves and trade lists
- **Market Data**: View candlestick charts for any symbol and timeframe
- **Broker Dashboard**: Monitor account information and positions
- **Order Placement**: Place buy/sell orders through the paper trading broker

## Setup

1. **Install Flutter**: Make sure you have Flutter installed on your system
   ```bash
   flutter --version
   ```

2. **Install Dependencies**: Navigate to the frontend directory and install dependencies
   ```bash
   cd frontend
   flutter pub get
   ```

3. **Start Backend**: Make sure your Bactester backend is running on `http://localhost:8000`

4. **Run the App**: Start the Flutter application
   ```bash
   flutter run
   ```

## Project Structure

```
lib/
├── main.dart                 # App entry point
├── models/                   # Data models
│   ├── strategy_models.dart  # Strategy and backtest models
│   ├── market_data_models.dart # Market data models
│   └── broker_models.dart    # Broker and order models
├── services/                 # API services
│   └── api_service.dart      # HTTP client for API calls
├── providers/                # State management
│   ├── api_provider.dart     # API connection state
│   ├── strategy_provider.dart # Strategy and backtest state
│   └── broker_provider.dart  # Broker state
├── views/                    # Screen widgets
│   ├── home_screen.dart      # Main navigation screen
│   ├── strategy_list_screen.dart # Strategy list
│   ├── run_backtest_screen.dart # Run backtest form
│   ├── backtest_results_screen.dart # Backtest results list
│   ├── backtest_result_screen.dart # Detailed backtest view
│   ├── market_data_screen.dart # Market data chart
│   ├── broker_dashboard_screen.dart # Broker dashboard
│   └── place_order_screen.dart # Order placement
└── widgets/                  # Reusable widgets
    ├── equity_chart.dart     # Equity curve chart
    └── trade_list.dart       # Trade list widget
```

## Dependencies

- **dio**: HTTP client for API calls
- **provider**: State management
- **intl**: Internationalization and formatting
- **fl_chart**: Charts for equity curves
- **candlesticks**: Candlestick charts for market data

## API Endpoints

The app connects to the following backend endpoints:

- `GET /strategies/available` - List available strategies
- `POST /strategies/start` - Start a backtest
- `GET /strategies/results` - List backtest results
- `GET /strategies/results/{run_id}` - Get specific backtest result
- `GET /data/{symbol}/{timeframe}` - Get market data
- `GET /broker/paper/account-info` - Get account information
- `GET /broker/paper/positions` - Get positions
- `POST /broker/paper/order` - Place an order

## Usage

1. **View Strategies**: Navigate to the Strategies tab to see available trading strategies
2. **Run Backtest**: Tap on a strategy to configure and run a backtest
3. **View Results**: Check the Results tab to see completed backtests
4. **Market Data**: Use the Market Data tab to view candlestick charts
5. **Broker Info**: Monitor your account and positions in the Broker tab
6. **Place Orders**: Use the Trade tab to place buy/sell orders

## Configuration

The API base URL is configured in `lib/services/api_service.dart`:
```dart
static const String baseUrl = "http://localhost:8000/api/v1";
```

Change this URL if your backend is running on a different host or port.

## Building for Production

To build the app for production:

```bash
# For Android
flutter build apk --release

# For iOS
flutter build ios --release

# For Web
flutter build web --release
```

## Troubleshooting

1. **Connection Issues**: Make sure your backend is running and accessible
2. **API Errors**: Check the backend logs for any API errors
3. **Chart Issues**: Ensure you have the latest version of fl_chart and candlesticks packages
4. **Build Issues**: Run `flutter clean` and `flutter pub get` to reset dependencies
