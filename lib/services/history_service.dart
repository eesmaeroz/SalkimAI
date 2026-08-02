import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/prediction_models.dart';

class HistoryService {
  static const String _harvestHistoryKey = 'harvest_history';
  static const String _diseaseHistoryKey = 'disease_history';

  Future<void> saveHarvestResult(HarvestPredictionResponse result, HarvestPredictionRequest request) async {
    final prefs = await SharedPreferences.getInstance();
    final List<String> history = prefs.getStringList(_harvestHistoryKey) ?? [];
    
    final Map<String, dynamic> entry = {
      'timestamp': DateTime.now().toIso8601String(),
      'request': request.toJson(),
      'response': {
        'prediction_id': result.predictionId,
        'predicted_harvest_date': result.predictedHarvestDate,
        'predicted_days_remaining': result.predictedDaysRemaining,
        'predicted_yield_kg_m2': result.predictedYieldKgM2,
        'confidence_score': result.confidenceScore,
      }
    };
    
    history.add(jsonEncode(entry));
    await prefs.setStringList(_harvestHistoryKey, history);
  }

  Future<void> saveDiseaseResult(DiseaseRiskResponse result) async {
    final prefs = await SharedPreferences.getInstance();
    final List<String> history = prefs.getStringList(_diseaseHistoryKey) ?? [];
    
    final Map<String, dynamic> entry = {
      'timestamp': DateTime.now().toIso8601String(),
      'response': {
        'greenhouse_id': result.greenhouseId,
        'risk_score': result.riskScore,
        'risk_level': result.riskLevel,
        'recommendation': result.recommendation,
      }
    };
    
    history.add(jsonEncode(entry));
    await prefs.setStringList(_diseaseHistoryKey, history);
  }

  Future<List<Map<String, dynamic>>> getHarvestHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final List<String> history = prefs.getStringList(_harvestHistoryKey) ?? [];
    return history.map((e) => jsonDecode(e) as Map<String, dynamic>).toList().reversed.toList();
  }

  Future<List<Map<String, dynamic>>> getDiseaseHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final List<String> history = prefs.getStringList(_diseaseHistoryKey) ?? [];
    return history.map((e) => jsonDecode(e) as Map<String, dynamic>).toList().reversed.toList();
  }
}
