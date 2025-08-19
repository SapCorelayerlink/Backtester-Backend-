import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import '../models/broker_models.dart';

class BrokerProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  
  AccountInfo? _accountInfo;
  List<Position> _positions = [];
  bool _isLoading = false;
  String _error = '';

  AccountInfo? get accountInfo => _accountInfo;
  List<Position> get positions => _positions;
  bool get isLoading => _isLoading;
  String get error => _error;

  Future<void> loadAccountInfo(String brokerName) async {
    _setLoading(true);
    try {
      _accountInfo = await _apiService.getAccountInfo(brokerName);
      _error = '';
    } catch (e) {
      _error = e.toString();
    }
    _setLoading(false);
  }

  Future<void> loadPositions(String brokerName) async {
    _setLoading(true);
    try {
      _positions = await _apiService.getPositions(brokerName);
      _error = '';
    } catch (e) {
      _error = e.toString();
    }
    _setLoading(false);
  }

  Future<void> placeOrder(String brokerName, OrderRequest request) async {
    _setLoading(true);
    try {
      await _apiService.placeOrder(brokerName, request);
      // Reload account info and positions after order
      await loadAccountInfo(brokerName);
      await loadPositions(brokerName);
      _error = '';
    } catch (e) {
      _error = e.toString();
    }
    _setLoading(false);
  }

  void _setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void clearError() {
    _error = '';
    notifyListeners();
  }
}
