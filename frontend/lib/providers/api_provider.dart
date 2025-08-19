import 'package:flutter/foundation.dart';
import '../services/api_service.dart';

class ApiProvider extends ChangeNotifier {
  final ApiService _apiService = ApiService();
  bool _isConnected = false;
  String _error = '';

  bool get isConnected => _isConnected;
  String get error => _error;

  Future<void> checkConnection() async {
    try {
      final health = await _apiService.getHealth();
      _isConnected = health.status == 'ok';
      _error = '';
    } catch (e) {
      _isConnected = false;
      _error = e.toString();
    }
    notifyListeners();
  }

  void clearError() {
    _error = '';
    notifyListeners();
  }
}
