import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import '../models/strategy_models.dart';
import '../models/market_data_models.dart';
import '../models/broker_models.dart';

class ApiService {
  static const String baseUrl = "http://localhost:8000/api/v1";
  late Dio _dio;

  ApiService() {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
      },
    ));

    // Add error interceptor
    _dio.interceptors.add(InterceptorsWrapper(
      onError: (error, handler) {
        debugPrint('API Error: ${error.message}');
        handler.next(error);
      },
    ));
  }

  // Strategy APIs
  Future<List<Strategy>> getAvailableStrategies() async {
    try {
      final response = await _dio.get('/strategies/available');
      return (response.data as List)
          .map((json) => Strategy.fromJson(json))
          .toList();
    } catch (e) {
      throw Exception('Failed to fetch strategies: $e');
    }
  }

  Future<StartStrategyResponse> startStrategy(StartStrategyRequest request) async {
    try {
      final response = await _dio.post('/strategies/start', data: request.toJson());
      return StartStrategyResponse.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to start strategy: $e');
    }
  }

  Future<BacktestResult> getBacktestResult(String runId) async {
    try {
      final response = await _dio.get('/strategies/results/$runId');
      return BacktestResult.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to fetch backtest result: $e');
    }
  }

  Future<List<BacktestListItem>> getBacktestResults() async {
    try {
      final response = await _dio.get('/strategies/results');
      return (response.data as List)
          .map((json) => BacktestListItem.fromJson(json))
          .toList();
    } catch (e) {
      throw Exception('Failed to fetch backtest results: $e');
    }
  }

  // Market Data APIs
  Future<MarketDataResponse> getMarketData(
    String symbol,
    String timeframe,
    String startDate,
    String endDate,
  ) async {
    try {
      final response = await _dio.get(
        '/data/$symbol/$timeframe',
        queryParameters: {
          'start_date': startDate,
          'end_date': endDate,
        },
      );
      return MarketDataResponse.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to fetch market data: $e');
    }
  }

  // Broker APIs
  Future<AccountInfo> getAccountInfo(String brokerName) async {
    try {
      final response = await _dio.get('/broker/$brokerName/account-info');
      return AccountInfo.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to fetch account info: $e');
    }
  }

  Future<List<Position>> getPositions(String brokerName) async {
    try {
      final response = await _dio.get('/broker/$brokerName/positions');
      return (response.data as List)
          .map((json) => Position.fromJson(json))
          .toList();
    } catch (e) {
      throw Exception('Failed to fetch positions: $e');
    }
  }

  Future<OrderResponse> placeOrder(String brokerName, OrderRequest request) async {
    try {
      final response = await _dio.post(
        '/broker/$brokerName/order',
        data: request.toJson(),
      );
      return OrderResponse.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to place order: $e');
    }
  }

  // Health Check
  Future<HealthResponse> getHealth() async {
    try {
      final response = await _dio.get('/health');
      return HealthResponse.fromJson(response.data);
    } catch (e) {
      throw Exception('Failed to check health: $e');
    }
  }
}
