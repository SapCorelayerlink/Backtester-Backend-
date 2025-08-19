import 'package:flutter/material.dart';
import 'package:candlesticks/candlesticks.dart';
import '../services/api_service.dart';
import '../models/market_data_models.dart';

class MarketDataScreen extends StatefulWidget {
  const MarketDataScreen({super.key});

  @override
  State<MarketDataScreen> createState() => _MarketDataScreenState();
}

class _MarketDataScreenState extends State<MarketDataScreen> {
  final _apiService = ApiService();
  final _symbolController = TextEditingController(text: 'SPY');
  final _timeframeController = TextEditingController(text: '1h');
  final _startDateController = TextEditingController(text: '2025-08-11');
  final _endDateController = TextEditingController(text: '2025-08-16');

  MarketDataResponse? _marketData;
  bool _isLoading = false;
  String _error = '';

  @override
  void dispose() {
    _symbolController.dispose();
    _timeframeController.dispose();
    _startDateController.dispose();
    _endDateController.dispose();
    super.dispose();
  }

  Future<void> _loadMarketData() async {
    if (_symbolController.text.isEmpty ||
        _timeframeController.text.isEmpty ||
        _startDateController.text.isEmpty ||
        _endDateController.text.isEmpty) {
      setState(() {
        _error = 'Please fill in all fields';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _error = '';
    });

    try {
      final data = await _apiService.getMarketData(
        _symbolController.text,
        _timeframeController.text,
        _startDateController.text,
        _endDateController.text,
      );
      setState(() {
        _marketData = data;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  List<Candle> _convertToCandles() {
    if (_marketData == null) return [];

    return _marketData!.data.map((candle) {
      return Candle(
        date: candle.dateTime,
        high: candle.high,
        low: candle.low,
        open: candle.open,
        close: candle.close,
        volume: candle.volume.toDouble(),
      );
    }).toList();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Column(
        children: [
          // Controls
          Card(
            margin: const EdgeInsets.all(16),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Market Data',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 16),
                  TextFormField(
                    controller: _symbolController,
                    decoration: const InputDecoration(
                      labelText: 'Symbol',
                      border: OutlineInputBorder(),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: TextFormField(
                          controller: _timeframeController,
                          decoration: const InputDecoration(
                            labelText: 'Timeframe',
                            border: OutlineInputBorder(),
                            hintText: '1min, 5min, 1day',
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: ElevatedButton(
                          onPressed: _isLoading ? null : _loadMarketData,
                          child: _isLoading
                              ? const SizedBox(
                                  height: 20,
                                  width: 20,
                                  child:
                                      CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Text('Load Data'),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: TextFormField(
                          controller: _startDateController,
                          decoration: const InputDecoration(
                            labelText: 'Start Date',
                            border: OutlineInputBorder(),
                            hintText: 'YYYY-MM-DD',
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: TextFormField(
                          controller: _endDateController,
                          decoration: const InputDecoration(
                            labelText: 'End Date',
                            border: OutlineInputBorder(),
                            hintText: 'YYYY-MM-DD',
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          // Error Display
          if (_error.isNotEmpty)
            Container(
              margin: const EdgeInsets.symmetric(horizontal: 16),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.red[50],
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: Colors.red[200]!),
              ),
              child: Row(
                children: [
                  Icon(Icons.error_outline, color: Colors.red[700]),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      _error,
                      style: TextStyle(color: Colors.red[700]),
                    ),
                  ),
                ],
              ),
            ),

          // Chart
          Expanded(
            child: _marketData != null && _marketData!.data.isNotEmpty
                ? Padding(
                    padding: const EdgeInsets.all(16),
                    child: Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              '${_marketData!.symbol} - ${_marketData!.timeframe}',
                              style: Theme.of(context).textTheme.titleLarge,
                            ),
                            const SizedBox(height: 16),
                            Expanded(
                              child: Candlesticks(
                                candles: _convertToCandles(),
                                onLoadMoreCandles: () async {
                                  // Optional callback for loading more candles
                                  return;
                                },
                                actions: [],
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  )
                : const Center(
                    child: Text('Load market data to view chart'),
                  ),
          ),
        ],
      ),
    );
  }
}
