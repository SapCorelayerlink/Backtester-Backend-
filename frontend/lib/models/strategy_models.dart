class Strategy {
  final String name;
  final String description;

  Strategy({
    required this.name,
    required this.description,
  });

  factory Strategy.fromJson(Map<String, dynamic> json) {
    return Strategy(
      name: json['name'] ?? '',
      description: json['description'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'description': description,
    };
  }
}

class StartStrategyRequest {
  final String name;
  final String broker;
  final Map<String, dynamic> params;

  StartStrategyRequest({
    required this.name,
    required this.broker,
    required this.params,
  });

  Map<String, dynamic> toJson() {
    return {
      'name': name,
      'broker': broker,
      'params': params,
    };
  }
}

class StartStrategyResponse {
  final String status;
  final String strategy;
  final String message;

  StartStrategyResponse({
    required this.status,
    required this.strategy,
    required this.message,
  });

  factory StartStrategyResponse.fromJson(Map<String, dynamic> json) {
    return StartStrategyResponse(
      status: json['status'] ?? '',
      strategy: json['strategy'] ?? '',
      message: json['message'] ?? '',
    );
  }
}

class BacktestResult {
  final String runId;
  final String strategy;
  final String status;
  final String startDate;
  final String endDate;
  final double initialCapital;
  final double finalCapital;
  final int totalTrades;
  final List<EquityPoint> equityCurve;
  final PnLSummary pnl;
  final List<Trade> trades;

  BacktestResult({
    required this.runId,
    required this.strategy,
    required this.status,
    required this.startDate,
    required this.endDate,
    required this.initialCapital,
    required this.finalCapital,
    required this.totalTrades,
    required this.equityCurve,
    required this.pnl,
    required this.trades,
  });

  factory BacktestResult.fromJson(Map<String, dynamic> json) {
    return BacktestResult(
      runId: json['run_id'] ?? '',
      strategy: json['strategy'] ?? '',
      status: json['status'] ?? '',
      startDate: json['start_date'] ?? '',
      endDate: json['end_date'] ?? '',
      initialCapital: (json['initial_capital'] ?? 0.0).toDouble(),
      finalCapital: (json['final_capital'] ?? 0.0).toDouble(),
      totalTrades: json['total_trades'] ?? 0,
      equityCurve: (json['equity_curve'] as List<dynamic>?)
          ?.map((e) => EquityPoint.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
      pnl: PnLSummary.fromJson(json['pnl'] as Map<String, dynamic>),
      trades: (json['trades'] as List<dynamic>?)
          ?.map((e) => Trade.fromJson(e as Map<String, dynamic>))
          .toList() ?? [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'run_id': runId,
      'strategy': strategy,
      'status': status,
      'start_date': startDate,
      'end_date': endDate,
      'initial_capital': initialCapital,
      'final_capital': finalCapital,
      'total_trades': totalTrades,
      'equity_curve': equityCurve.map((e) => e.toJson()).toList(),
      'pnl': pnl.toJson(),
      'trades': trades.map((e) => e.toJson()).toList(),
    };
  }
}

class PnLSummary {
  final double total;
  final double percentage;

  PnLSummary({
    required this.total,
    required this.percentage,
  });

  factory PnLSummary.fromJson(Map<String, dynamic> json) {
    return PnLSummary(
      total: (json['total'] as num?)?.toDouble() ?? 0.0,
      percentage: (json['percentage'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'total': total,
      'percentage': percentage,
    };
  }
}

class Trade {
  final String symbol;
  final String side;
  final int qty;
  final double price;
  final String time;

  Trade({
    required this.symbol,
    required this.side,
    required this.qty,
    required this.price,
    required this.time,
  });

  factory Trade.fromJson(Map<String, dynamic> json) {
    return Trade(
      symbol: json['symbol'] ?? '',
      side: json['side'] ?? '',
      qty: json['qty'] ?? 0,
      price: (json['price'] as num?)?.toDouble() ?? 0.0,
      time: json['time'] ?? '',
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'symbol': symbol,
      'side': side,
      'qty': qty,
      'price': price,
      'time': time,
    };
  }
}

class EquityPoint {
  final String timestamp;
  final double equity;

  EquityPoint({
    required this.timestamp,
    required this.equity,
  });

  factory EquityPoint.fromJson(Map<String, dynamic> json) {
    return EquityPoint(
      timestamp: json['timestamp'] ?? '',
      equity: (json['equity'] as num?)?.toDouble() ?? 0.0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'timestamp': timestamp,
      'equity': equity,
    };
  }
}

class BacktestListItem {
  final String runId;
  final String strategy;
  final String status;

  BacktestListItem({
    required this.runId,
    required this.strategy,
    required this.status,
  });

  factory BacktestListItem.fromJson(Map<String, dynamic> json) {
    return BacktestListItem(
      runId: json['run_id'] ?? '',
      strategy: json['strategy'] ?? '',
      status: json['status'] ?? '',
    );
  }
}
