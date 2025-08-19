import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/strategy_provider.dart';
import '../models/strategy_models.dart';
import 'backtest_results_screen.dart';

class RunBacktestScreen extends StatefulWidget {
  final Strategy strategy;

  const RunBacktestScreen({super.key, required this.strategy});

  @override
  State<RunBacktestScreen> createState() => _RunBacktestScreenState();
}

class _RunBacktestScreenState extends State<RunBacktestScreen> {
  final _formKey = GlobalKey<FormState>();
  final _symbolController = TextEditingController(text: 'SPY');
  final _timeframeController = TextEditingController();
  final _initialCapitalController = TextEditingController(text: '100000');
  final _startDateController = TextEditingController(text: '2025-08-11');
  final _endDateController = TextEditingController(text: '2025-08-16');
  final _atrPeriodController = TextEditingController(text: '14');
  final _multiplierController = TextEditingController(text: '3.0');

  @override
  void initState() {
    super.initState();
    // Set default timeframe based on strategy
    _setDefaultTimeframe();
  }

  void _setDefaultTimeframe() {
    final strategyName = widget.strategy.name;
    if (strategyName.contains('IntradaySupertrendMA')) {
      _timeframeController.text = '1min'; // Base timeframe for intraday
    } else if (strategyName.contains('Turtle')) {
      _timeframeController.text = '1h';
    } else if (strategyName.contains('SwingFailure')) {
      _timeframeController.text = '1h';
    } else if (strategyName.contains('Pivot')) {
      _timeframeController.text = '15min';
    } else {
      _timeframeController.text = '4h'; // Default for most strategies
    }
  }

  @override
  void dispose() {
    _symbolController.dispose();
    _timeframeController.dispose();
    _initialCapitalController.dispose();
    _startDateController.dispose();
    _endDateController.dispose();
    _atrPeriodController.dispose();
    _multiplierController.dispose();
    super.dispose();
  }

  String _getStrategyTimeframe() {
    final strategyName = widget.strategy.name;
    if (strategyName.contains('IntradaySupertrendMA')) {
      return '1min';
    } else if (strategyName.contains('Turtle')) {
      return '1h';
    } else if (strategyName.contains('SwingFailure')) {
      return '1h';
    } else if (strategyName.contains('Pivot')) {
      return '15min';
    } else {
      return '4h';
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Run ${widget.strategy.name}'),
      ),
      body: Consumer<StrategyProvider>(
        builder: (context, strategyProvider, child) {
          return Form(
            key: _formKey,
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.strategy.name,
                          style: Theme.of(context).textTheme.headlineSmall,
                        ),
                        const SizedBox(height: 8),
                        Text(
                          widget.strategy.description,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                        const SizedBox(height: 12),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: Theme.of(context).colorScheme.primary.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                Icons.schedule,
                                size: 16,
                                color: Theme.of(context).colorScheme.primary,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                'Strategy Timeframe: ${_getStrategyTimeframe()}',
                                style: TextStyle(
                                  color: Theme.of(context).colorScheme.primary,
                                  fontWeight: FontWeight.w600,
                                  fontSize: 12,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Backtest Parameters',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _symbolController,
                          decoration: const InputDecoration(
                            labelText: 'Symbol',
                            border: OutlineInputBorder(),
                          ),
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Please enter a symbol';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _timeframeController,
                          decoration: const InputDecoration(
                            labelText: 'Timeframe',
                            border: OutlineInputBorder(),
                            hintText: 'e.g., 1min, 5min, 1day',
                          ),
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Please enter a timeframe';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),
                        TextFormField(
                          controller: _initialCapitalController,
                          decoration: const InputDecoration(
                            labelText: 'Initial Capital',
                            border: OutlineInputBorder(),
                          ),
                          keyboardType: TextInputType.number,
                          validator: (value) {
                            if (value == null || value.isEmpty) {
                              return 'Please enter initial capital';
                            }
                            if (double.tryParse(value) == null) {
                              return 'Please enter a valid number';
                            }
                            return null;
                          },
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
                                validator: (value) {
                                  if (value == null || value.isEmpty) {
                                    return 'Please enter start date';
                                  }
                                  return null;
                                },
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
                                validator: (value) {
                                  if (value == null || value.isEmpty) {
                                    return 'Please enter end date';
                                  }
                                  return null;
                                },
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            Expanded(
                              child: TextFormField(
                                controller: _atrPeriodController,
                                decoration: const InputDecoration(
                                  labelText: 'ATR Period',
                                  border: OutlineInputBorder(),
                                ),
                                keyboardType: TextInputType.number,
                                validator: (value) {
                                  if (value == null || value.isEmpty) {
                                    return 'Please enter ATR period';
                                  }
                                  if (int.tryParse(value) == null) {
                                    return 'Please enter a valid number';
                                  }
                                  return null;
                                },
                              ),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: TextFormField(
                                controller: _multiplierController,
                                decoration: const InputDecoration(
                                  labelText: 'Multiplier',
                                  border: OutlineInputBorder(),
                                ),
                                keyboardType: TextInputType.number,
                                validator: (value) {
                                  if (value == null || value.isEmpty) {
                                    return 'Please enter multiplier';
                                  }
                                  if (double.tryParse(value) == null) {
                                    return 'Please enter a valid number';
                                  }
                                  return null;
                                },
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                if (strategyProvider.error.isNotEmpty)
                  Card(
                    color: Colors.red[50],
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Text(
                        strategyProvider.error,
                        style: TextStyle(color: Colors.red[700]),
                      ),
                    ),
                  ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.infinity,
                  height: 50,
                  child: ElevatedButton(
                    onPressed: () async {
                      if (_formKey.currentState!.validate()) {
                        final request = StartStrategyRequest(
                          name: widget.strategy.name,
                          broker: 'paper',
                          params: {
                            'symbol': _symbolController.text,
                            'timeframe': _timeframeController.text,
                            'initial_capital':
                                double.parse(_initialCapitalController.text),
                            'start_date': _startDateController.text,
                            'end_date': _endDateController.text,
                            'atr_period': int.parse(_atrPeriodController.text),
                            'multiplier':
                                double.parse(_multiplierController.text),
                          },
                        );

                        final response =
                            await strategyProvider.startStrategy(request);
                        if (response != null && mounted) {
                          // Schedule the UI updates for the next frame to avoid async gap issues
                          WidgetsBinding.instance.addPostFrameCallback((_) {
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text(response.message),
                                  backgroundColor: Colors.green,
                                ),
                              );

                              Navigator.pushReplacement(
                                context,
                                MaterialPageRoute(
                                  builder: (context) =>
                                      const BacktestResultsScreen(),
                                ),
                              );
                            }
                          });
                        }
                      }
                    },
                    child: strategyProvider.isLoading
                        ? const CircularProgressIndicator()
                        : const Text('Run Backtest'),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }
}
