class AccountInfo {
  final String accountId;
  final double cashBalance;
  final double equity;
  final double buyingPower;

  AccountInfo({
    required this.accountId,
    required this.cashBalance,
    required this.equity,
    required this.buyingPower,
  });

  factory AccountInfo.fromJson(Map<String, dynamic> json) {
    return AccountInfo(
      accountId: json['account_id'] ?? '',
      cashBalance: (json['cash_balance'] ?? 0.0).toDouble(),
      equity: (json['equity'] ?? 0.0).toDouble(),
      buyingPower: (json['buying_power'] ?? 0.0).toDouble(),
    );
  }
}

class Position {
  final String symbol;
  final double quantity;
  final double avgPrice;
  final double marketPrice;
  final double unrealizedPl;

  Position({
    required this.symbol,
    required this.quantity,
    required this.avgPrice,
    required this.marketPrice,
    required this.unrealizedPl,
  });

  factory Position.fromJson(Map<String, dynamic> json) {
    return Position(
      symbol: json['symbol'] ?? '',
      quantity: (json['quantity'] ?? 0.0).toDouble(),
      avgPrice: (json['avg_price'] ?? 0.0).toDouble(),
      marketPrice: (json['market_price'] ?? 0.0).toDouble(),
      unrealizedPl: (json['unrealized_pl'] ?? 0.0).toDouble(),
    );
  }
}

class OrderRequest {
  final String symbol;
  final double qty;
  final String side;
  final String type;

  OrderRequest({
    required this.symbol,
    required this.qty,
    required this.side,
    required this.type,
  });

  Map<String, dynamic> toJson() {
    return {
      'symbol': symbol,
      'qty': qty,
      'side': side,
      'type': type,
    };
  }
}

class OrderResponse {
  final String status;
  final String symbol;
  final double qty;
  final double filledPrice;

  OrderResponse({
    required this.status,
    required this.symbol,
    required this.qty,
    required this.filledPrice,
  });

  factory OrderResponse.fromJson(Map<String, dynamic> json) {
    return OrderResponse(
      status: json['status'] ?? '',
      symbol: json['symbol'] ?? '',
      qty: (json['qty'] ?? 0.0).toDouble(),
      filledPrice: (json['filled_price'] ?? 0.0).toDouble(),
    );
  }
}

class HealthResponse {
  final String status;

  HealthResponse({
    required this.status,
  });

  factory HealthResponse.fromJson(Map<String, dynamic> json) {
    return HealthResponse(
      status: json['status'] ?? '',
    );
  }
}
