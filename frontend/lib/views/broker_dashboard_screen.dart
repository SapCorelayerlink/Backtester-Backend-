import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../providers/broker_provider.dart';
import '../models/broker_models.dart';

class BrokerDashboardScreen extends StatefulWidget {
  const BrokerDashboardScreen({super.key});

  @override
  State<BrokerDashboardScreen> createState() => _BrokerDashboardScreenState();
}

class _BrokerDashboardScreenState extends State<BrokerDashboardScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final brokerProvider = context.read<BrokerProvider>();
      brokerProvider.loadAccountInfo('paper');
      brokerProvider.loadPositions('paper');
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Consumer<BrokerProvider>(
        builder: (context, brokerProvider, child) {
          if (brokerProvider.isLoading) {
            return const Center(
              child: CircularProgressIndicator(),
            );
          }

          if (brokerProvider.error.isNotEmpty) {
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
                    'Error loading broker data',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    brokerProvider.error,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.red[300],
                    ),
                  ),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      brokerProvider.clearError();
                      brokerProvider.loadAccountInfo('paper');
                      brokerProvider.loadPositions('paper');
                    },
                    child: const Text('Retry'),
                  ),
                ],
              ),
            );
          }

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Account Info Card
              if (brokerProvider.accountInfo != null) ...[
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Account Information',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 16),
                        _AccountInfoRow(
                          label: 'Account ID',
                          value: brokerProvider.accountInfo!.accountId,
                        ),
                        const SizedBox(height: 8),
                        _AccountInfoRow(
                          label: 'Cash Balance',
                          value: '\$${NumberFormat('#,##0.00').format(brokerProvider.accountInfo!.cashBalance)}',
                          color: Colors.blue,
                        ),
                        const SizedBox(height: 8),
                        _AccountInfoRow(
                          label: 'Equity',
                          value: '\$${NumberFormat('#,##0.00').format(brokerProvider.accountInfo!.equity)}',
                          color: Colors.green,
                        ),
                        const SizedBox(height: 8),
                        _AccountInfoRow(
                          label: 'Buying Power',
                          value: '\$${NumberFormat('#,##0.00').format(brokerProvider.accountInfo!.buyingPower)}',
                          color: Colors.orange,
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
              ],

              // Positions Card
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Positions',
                            style: Theme.of(context).textTheme.titleLarge,
                          ),
                          Text(
                            '${brokerProvider.positions.length} positions',
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                              color: Colors.grey[600],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      if (brokerProvider.positions.isEmpty)
                        const Center(
                          child: Padding(
                            padding: EdgeInsets.all(32),
                            child: Text(
                              'No open positions',
                              style: TextStyle(
                                color: Colors.grey,
                                fontSize: 16,
                              ),
                            ),
                          ),
                        )
                      else
                        ...brokerProvider.positions.map((position) => _PositionCard(position: position)),
                    ],
                  ),
                ),
              ),
            ],
          );
        },
      ),
    );
  }
}

class _AccountInfoRow extends StatelessWidget {
  final String label;
  final String value;
  final Color? color;

  const _AccountInfoRow({
    required this.label,
    required this.value,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: Colors.grey[600],
          ),
        ),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: color,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }
}

class _PositionCard extends StatelessWidget {
  final Position position;

  const _PositionCard({required this.position});

  @override
  Widget build(BuildContext context) {
    final isPositive = position.unrealizedPl >= 0;
    
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[50],
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.grey[200]!),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                position.symbol,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: isPositive ? Colors.green[100] : Colors.red[100],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  isPositive ? 'LONG' : 'SHORT',
                  style: TextStyle(
                    color: isPositive ? Colors.green[700] : Colors.red[700],
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Expanded(
                child: _PositionInfo(
                  label: 'Quantity',
                  value: position.quantity.toString(),
                ),
              ),
              Expanded(
                child: _PositionInfo(
                  label: 'Avg Price',
                  value: '\$${NumberFormat('#,##0.00').format(position.avgPrice)}',
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Row(
            children: [
              Expanded(
                child: _PositionInfo(
                  label: 'Market Price',
                  value: '\$${NumberFormat('#,##0.00').format(position.marketPrice)}',
                ),
              ),
              Expanded(
                child: _PositionInfo(
                  label: 'Unrealized P&L',
                  value: '\$${NumberFormat('#,##0.00').format(position.unrealizedPl)}',
                  color: isPositive ? Colors.green : Colors.red,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _PositionInfo extends StatelessWidget {
  final String label;
  final String value;
  final Color? color;

  const _PositionInfo({
    required this.label,
    required this.value,
    this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Colors.grey[600],
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
            color: color,
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }
}
