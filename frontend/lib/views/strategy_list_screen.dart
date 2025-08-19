import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:provider/provider.dart';
import '../providers/strategy_provider.dart';
import '../widgets/modern_card.dart';
import 'run_backtest_screen.dart';

class StrategyListScreen extends StatefulWidget {
  const StrategyListScreen({super.key});

  @override
  State<StrategyListScreen> createState() => _StrategyListScreenState();
}

class _StrategyListScreenState extends State<StrategyListScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<StrategyProvider>().loadStrategies();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<StrategyProvider>(
      builder: (context, strategyProvider, child) {
        if (strategyProvider.isLoading) {
          return const Center(
            child: CupertinoActivityIndicator(
              radius: 20,
            ),
          );
        }

        if (strategyProvider.error.isNotEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    CupertinoIcons.exclamationmark_triangle_fill,
                    size: 64,
                    color: const Color(0xFFFF3B30),
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'Error loading strategies',
                    style: Theme.of(context).textTheme.headlineMedium,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    strategyProvider.error,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: const Color(0xFF8E8E93),
                        ),
                  ),
                  const SizedBox(height: 32),
                  ModernButton(
                    text: 'Retry',
                    icon: CupertinoIcons.refresh,
                    onPressed: () {
                      strategyProvider.clearError();
                      strategyProvider.loadStrategies();
                    },
                  ),
                ],
              ),
            ),
          );
        }

        if (strategyProvider.strategies.isEmpty) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(32),
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    CupertinoIcons.chart_bar,
                    size: 64,
                    color: const Color(0xFF8E8E93),
                  ),
                  const SizedBox(height: 24),
                  Text(
                    'No strategies available',
                    style: Theme.of(context).textTheme.headlineMedium,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    'Check your connection and try again',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: const Color(0xFF8E8E93),
                        ),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.symmetric(vertical: 8),
          itemCount: strategyProvider.strategies.length,
          itemBuilder: (context, index) {
            final strategy = strategyProvider.strategies[index];
            return ModernListTile(
              leading: Container(
                width: 48,
                height: 48,
                decoration: BoxDecoration(
                  color: _getStrategyColor(index).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  _getStrategyIcon(index),
                  color: _getStrategyColor(index),
                  size: 24,
                ),
              ),
              title: Text(
                strategy.name,
                style: Theme.of(context).textTheme.titleLarge,
              ),
              subtitle: Text(
                strategy.description,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: const Color(0xFF8E8E93),
                    ),
              ),
              trailing: Icon(
                CupertinoIcons.chevron_right,
                color: const Color(0xFFC7C7CC),
                size: 20,
              ),
              onTap: () {
                Navigator.push(
                  context,
                  CupertinoPageRoute(
                    builder: (context) => RunBacktestScreen(strategy: strategy),
                  ),
                );
              },
            );
          },
        );
      },
    );
  }

  Color _getStrategyColor(int index) {
    final colors = [
      const Color(0xFF007AFF), // Blue
      const Color(0xFF5856D6), // Purple
      const Color(0xFF34C759), // Green
      const Color(0xFFFF9500), // Orange
      const Color(0xFFFF3B30), // Red
      const Color(0xFFAF52DE), // Pink
    ];
    return colors[index % colors.length];
  }

  IconData _getStrategyIcon(int index) {
    final icons = [
      CupertinoIcons.chart_bar_alt_fill,
      CupertinoIcons.graph_circle_fill,
      CupertinoIcons.chart_bar_fill,
      CupertinoIcons.creditcard_fill,
      CupertinoIcons.cart_fill,
      CupertinoIcons.settings,
    ];
    return icons[index % icons.length];
  }
}
