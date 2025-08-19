import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/strategy_provider.dart';
import 'backtest_result_screen.dart';

class BacktestResultsScreen extends StatefulWidget {
  const BacktestResultsScreen({super.key});

  @override
  State<BacktestResultsScreen> createState() => _BacktestResultsScreenState();
}

class _BacktestResultsScreenState extends State<BacktestResultsScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<StrategyProvider>().loadBacktestResults();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Consumer<StrategyProvider>(
        builder: (context, strategyProvider, child) {
          if (strategyProvider.isLoading) {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }

          if (strategyProvider.error.isNotEmpty) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.error_outline,
                    size: 64,
                    color: Colors.red[300],
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Error loading results',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    strategyProvider.error,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.red[300],
                        ),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      strategyProvider.clearError();
                      strategyProvider.loadBacktestResults();
                    },
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          if (strategyProvider.backtestResults.isEmpty) {
            return const Center(
              child: Text('No backtest results available'),
            );
          }

          return ListView.builder(
            itemCount: strategyProvider.backtestResults.length,
            itemBuilder: (context, index) {
              final result = strategyProvider.backtestResults[index];
              return Card(
                margin: const EdgeInsets.symmetric(
                  horizontal: 16,
                  vertical: 4,
                ),
                child: ListTile(
                  title: Text(
                    'Strategy: ${result.strategy}',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Run ID: ${result.runId}'),
                      const SizedBox(height: 4),
                      Container(
                        padding: const EdgeInsets.symmetric(
                            horizontal: 6, vertical: 2),
                        decoration: BoxDecoration(
                          color: Colors.blue[50],
                          borderRadius: BorderRadius.circular(4),
                        ),
                        child: Text(
                          'Timeframe: ${_getStrategyTimeframe(result.strategy)}',
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.blue[700],
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ),
                  trailing: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: result.status == 'completed'
                          ? Colors.green[100]
                          : Colors.orange[100],
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      result.status.toUpperCase(),
                      style: TextStyle(
                        color: result.status == 'completed'
                            ? Colors.green[800]
                            : Colors.orange[800],
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ),
                  onTap: () {
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (context) => BacktestResultScreen(
                          runId: result.runId,
                        ),
                      ),
                    );
                  },
                ),
              );
            },
          );
        },
      ),
    );
  }

  String _getStrategyTimeframe(String strategyName) {
    switch (strategyName) {
      case 'IntradaySupertrendMA':
        return '1min base, 30min MAs, 3h SuperTrend';
      case 'TurtleStrategy':
        return '1h';
      case 'BB5EMAStrategy':
        return '4h';
      case 'SRTrend4H':
        return '4h';
      case 'SwingFailureStrategy':
        return '1h';
      case 'RSIVWAPStrategy':
        return '4h';
      case 'PivotStrategy':
        return '15min';
      case 'FibonacciStrategy':
        return '4h';
      default:
        return 'N/A';
    }
  }
}
