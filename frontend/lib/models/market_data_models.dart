class MarketDataResponse {
  final String symbol;
  final String timeframe;
  final List<CandleData> data;

  MarketDataResponse({
    required this.symbol,
    required this.timeframe,
    required this.data,
  });

  factory MarketDataResponse.fromJson(Map<String, dynamic> json) {
    return MarketDataResponse(
      symbol: json['symbol'] ?? '',
      timeframe: json['timeframe'] ?? '',
      data: (json['data'] as List<dynamic>?)
              ?.map((candle) => CandleData.fromJson(candle))
              .toList() ??
          [],
    );
  }
}

class CandleData {
  final String timestamp;
  final double open;
  final double high;
  final double low;
  final double close;
  final int volume;

  CandleData({
    required this.timestamp,
    required this.open,
    required this.high,
    required this.low,
    required this.close,
    required this.volume,
  });

  factory CandleData.fromJson(Map<String, dynamic> json) {
    return CandleData(
      timestamp: json['timestamp'] ?? '',
      open: (json['open'] ?? 0.0).toDouble(),
      high: (json['high'] ?? 0.0).toDouble(),
      low: (json['low'] ?? 0.0).toDouble(),
      close: (json['close'] ?? 0.0).toDouble(),
      volume: json['volume'] ?? 0,
    );
  }

  DateTime get dateTime {
    return DateTime.tryParse(timestamp) ?? DateTime.now();
  }
}
