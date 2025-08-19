import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../providers/strategy_provider.dart';
import '../models/strategy_models.dart';
import '../widgets/equity_chart.dart';

class BacktestResultScreen extends StatefulWidget {
  final String runId;

  const BacktestResultScreen({super.key, required this.runId});

  @override
  State<BacktestResultScreen> createState() => _BacktestResultScreenState();
}

class _BacktestResultScreenState extends State<BacktestResultScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<StrategyProvider>().loadBacktestResult(widget.runId);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Backtest Result - ${widget.runId}'),
        backgroundColor: Colors.blue[800],
        foregroundColor: Colors.white,
      ),
      body: Consumer<StrategyProvider>(
        builder: (context, provider, child) {
          if (provider.isLoadingBacktestResult) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.backtestResultError != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error, size: 64, color: Colors.red[300]),
                  const SizedBox(height: 16),
                  Text(
                    'Error loading backtest result',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    provider.backtestResultError!,
                    style: Theme.of(context).textTheme.bodyMedium,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () => provider.loadBacktestResult(widget.runId),
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          final result = provider.currentBacktestResult;
          if (result == null) {
            return const Center(
              child: Text('No backtest result found'),
            );
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Strategy Info Card
                Card(
                  elevation: 4,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Strategy Information',
                          style: Theme.of(context)
                              .textTheme
                              .headlineSmall
                              ?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Strategy:',
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodyMedium
                                        ?.copyWith(
                                          fontWeight: FontWeight.w600,
                                        ),
                                  ),
                                  Text(
                                    result.strategy,
                                    style:
                                        Theme.of(context).textTheme.bodyMedium,
                                  ),
                                ],
                              ),
                            ),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Timeframe:',
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodyMedium
                                        ?.copyWith(
                                          fontWeight: FontWeight.w600,
                                        ),
                                  ),
                                  Text(
                                    _getStrategyTimeframe(result.strategy),
                                    style:
                                        Theme.of(context).textTheme.bodyMedium,
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Period:',
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodyMedium
                                        ?.copyWith(
                                          fontWeight: FontWeight.w600,
                                        ),
                                  ),
                                  Text(
                                    '${result.startDate} to ${result.endDate}',
                                    style:
                                        Theme.of(context).textTheme.bodyMedium,
                                  ),
                                ],
                              ),
                            ),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'Initial Capital:',
                                    style: Theme.of(context)
                                        .textTheme
                                        .bodyMedium
                                        ?.copyWith(
                                          fontWeight: FontWeight.w600,
                                        ),
                                  ),
                                  Text(
                                    '\$${NumberFormat('#,##0').format(result.initialCapital)}',
                                    style:
                                        Theme.of(context).textTheme.bodyMedium,
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),

                // PnL Summary Card
                Card(
                  elevation: 4,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'PnL Summary',
                          style: Theme.of(context)
                              .textTheme
                              .headlineSmall
                              ?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                        const SizedBox(height: 16),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceAround,
                          children: [
                            _buildPnLItem(
                              'Total P&L',
                              result.pnl.total,
                              isCurrency: true,
                            ),
                            _buildPnLItem(
                              'Return %',
                              result.pnl.percentage,
                              isPercentage: true,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // Equity Curve Chart
                Card(
                  elevation: 4,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Equity Curve',
                          style: Theme.of(context)
                              .textTheme
                              .headlineSmall
                              ?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                        const SizedBox(height: 16),
                        SizedBox(
                          height: 300,
                          child: EquityChart(equityPoints: result.equityCurve),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),

                // Trades Table
                Card(
                  elevation: 4,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Trades (${result.trades.length})',
                          style: Theme.of(context)
                              .textTheme
                              .headlineSmall
                              ?.copyWith(
                                fontWeight: FontWeight.bold,
                              ),
                        ),
                        const SizedBox(height: 16),
                        _buildTradesTable(result.trades),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildPnLItem(String label, double value,
      {bool isCurrency = false, bool isPercentage = false}) {
    final isPositive = value >= 0;
    final color = isPositive ? Colors.green : Colors.red;

    String formattedValue;
    if (isCurrency) {
      formattedValue = NumberFormat.currency(symbol: '\$').format(value);
    } else if (isPercentage) {
      formattedValue = '${value.toStringAsFixed(2)}%';
    } else {
      formattedValue = value.toStringAsFixed(2);
    }

    return Column(
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Colors.grey[600],
              ),
        ),
        const SizedBox(height: 4),
        Text(
          formattedValue,
          style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                color: color,
                fontWeight: FontWeight.bold,
              ),
        ),
      ],
    );
  }

  Widget _buildTradesTable(List<Trade> trades) {
    if (trades.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(32),
          child: Text('No trades found'),
        ),
      );
    }

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      child: DataTable(
        columns: const [
          DataColumn(label: Text('Time')),
          DataColumn(label: Text('Symbol')),
          DataColumn(label: Text('Side')),
          DataColumn(label: Text('Qty')),
          DataColumn(label: Text('Price')),
        ],
        rows: trades.map((trade) {
          final dateTime = DateTime.tryParse(trade.time);
          final formattedTime = dateTime != null
              ? DateFormat('dd MMM yyyy HH:mm').format(dateTime)
              : trade.time;

          final isBuy = trade.side.toUpperCase() == 'BUY';
          final sideColor = isBuy ? Colors.green : Colors.red;

          return DataRow(
            cells: [
              DataCell(Text(formattedTime)),
              DataCell(Text(trade.symbol)),
              DataCell(
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: sideColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    trade.side,
                    style: TextStyle(
                      color: sideColor,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ),
              DataCell(Text(trade.qty.toString())),
              DataCell(Text(
                  NumberFormat.currency(symbol: '\$').format(trade.price))),
            ],
          );
        }).toList(),
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
