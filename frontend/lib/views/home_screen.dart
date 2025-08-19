import 'package:flutter/material.dart';
import 'package:flutter/cupertino.dart';
import 'package:provider/provider.dart';
import '../providers/api_provider.dart';
import 'strategy_list_screen.dart';
import 'backtest_results_screen.dart';
import 'market_data_screen.dart';
import 'broker_dashboard_screen.dart';
import 'place_order_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> with TickerProviderStateMixin {
  int _currentIndex = 0;
  late AnimationController _animationController;
  late Animation<double> _fadeAnimation;

  final List<Widget> _screens = [
    const StrategyListScreen(),
    const BacktestResultsScreen(),
    const MarketDataScreen(),
    const BrokerDashboardScreen(),
    const PlaceOrderScreen(),
  ];

  final List<Map<String, dynamic>> _navigationItems = [
    {
      'icon': CupertinoIcons.chart_bar_alt_fill,
      'label': 'Strategies',
      'color': Color(0xFF007AFF),
    },
    {
      'icon': CupertinoIcons.graph_circle_fill,
      'label': 'Results',
      'color': Color(0xFF5856D6),
    },
    {
      'icon': CupertinoIcons.chart_bar_fill,
      'label': 'Market Data',
      'color': Color(0xFF34C759),
    },
    {
      'icon': CupertinoIcons.creditcard_fill,
      'label': 'Broker',
      'color': Color(0xFFFF9500),
    },
    {
      'icon': CupertinoIcons.cart_fill,
      'label': 'Trade',
      'color': Color(0xFFFF3B30),
    },
  ];

  @override
  void initState() {
    super.initState();
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));
    _animationController.forward();

    // Check API connection on startup
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<ApiProvider>().checkConnection();
    });
  }

  @override
  void dispose() {
    _animationController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return CupertinoPageScaffold(
      navigationBar: CupertinoNavigationBar(
        middle: const Text(
          'Bactester Trading',
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w600,
            letterSpacing: -0.4,
          ),
        ),
        trailing: Consumer<ApiProvider>(
          builder: (context, apiProvider, child) {
            return CupertinoButton(
              padding: EdgeInsets.zero,
              onPressed: null,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    apiProvider.isConnected
                        ? CupertinoIcons.wifi
                        : CupertinoIcons.wifi_slash,
                    color: apiProvider.isConnected
                        ? const Color(0xFF34C759)
                        : const Color(0xFFFF3B30),
                    size: 16,
                  ),
                  const SizedBox(width: 4),
                  Text(
                    apiProvider.isConnected ? 'Connected' : 'Disconnected',
                    style: TextStyle(
                      color: apiProvider.isConnected
                          ? const Color(0xFF34C759)
                          : const Color(0xFFFF3B30),
                      fontSize: 12,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ],
              ),
            );
          },
        ),
        backgroundColor: const Color(0xFFF2F2F7).withOpacity(0.8),
        border: null,
      ),
      child: SafeArea(
        child: Column(
          children: [
            // Main content area
            Expanded(
              child: FadeTransition(
                opacity: _fadeAnimation,
                child: IndexedStack(
                  index: _currentIndex,
                  children: _screens,
                ),
              ),
            ),

            // Custom bottom navigation bar
            Container(
              decoration: BoxDecoration(
                color: const Color(0xFFFFFFFF),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF000000).withOpacity(0.1),
                    blurRadius: 10,
                    offset: const Offset(0, -2),
                  ),
                ],
              ),
              child: SafeArea(
                child: Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceAround,
                    children: List.generate(
                      _navigationItems.length,
                      (index) => _buildNavigationItem(index),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNavigationItem(int index) {
    final item = _navigationItems[index];
    final isSelected = _currentIndex == index;

    return GestureDetector(
      onTap: () {
        setState(() {
          _currentIndex = index;
        });
        _animationController.reset();
        _animationController.forward();
      },
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeInOut,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color:
              isSelected ? item['color'].withOpacity(0.1) : Colors.transparent,
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              item['icon'],
              color: isSelected ? item['color'] : const Color(0xFF8E8E93),
              size: 24,
            ),
            const SizedBox(height: 4),
            Text(
              item['label'],
              style: TextStyle(
                color: isSelected ? item['color'] : const Color(0xFF8E8E93),
                fontSize: 11,
                fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
