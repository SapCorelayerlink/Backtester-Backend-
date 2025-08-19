import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../models/strategy_models.dart';

class StrategyProvider with ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  List<Strategy> _strategies = [];
  List<BacktestListItem> _backtestResults = [];
  BacktestResult? _currentBacktestResult;
  bool _isLoading = false;
  bool _isLoadingBacktestResult = false;
  String _error = '';
  String? _backtestResultError;

  // Getters
  List<Strategy> get strategies => _strategies;
  List<BacktestListItem> get backtestResults => _backtestResults;
  BacktestResult? get currentBacktestResult => _currentBacktestResult;
  bool get isLoading => _isLoading;
  bool get isLoadingBacktestResult => _isLoadingBacktestResult;
  String get error => _error;
  String? get backtestResultError => _backtestResultError;

  // Load available strategies
  Future<void> loadStrategies() async {
    _isLoading = true;
    _error = '';
    notifyListeners();

    try {
      final strategies = await _apiService.getAvailableStrategies();
      _strategies = strategies;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Load backtest results list
  Future<void> loadBacktestResults() async {
    _isLoading = true;
    _error = '';
    notifyListeners();

    try {
      final results = await _apiService.getBacktestResults();
      _backtestResults = results;
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Start a new backtest
  Future<StartStrategyResponse?> startStrategy(StartStrategyRequest request) async {
    _isLoading = true;
    _error = '';
    notifyListeners();

    try {
      final response = await _apiService.startStrategy(request);
      return response;
    } catch (e) {
      _error = e.toString();
      return null;
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Load specific backtest result
  Future<void> loadBacktestResult(String runId) async {
    _isLoadingBacktestResult = true;
    _backtestResultError = null;
    notifyListeners();

    try {
      final result = await _apiService.getBacktestResult(runId);
      _currentBacktestResult = result;
    } catch (e) {
      _backtestResultError = e.toString();
    } finally {
      _isLoadingBacktestResult = false;
      notifyListeners();
    }
  }

  // Clear current backtest result
  void clearCurrentBacktestResult() {
    _currentBacktestResult = null;
    _backtestResultError = null;
    notifyListeners();
  }

  // Clear error
  void clearError() {
    _error = '';
    notifyListeners();
  }
}
