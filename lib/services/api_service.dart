import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/prediction_models.dart';

class ApiService {
  // Use 10.0.2.2 for Android emulator to reach localhost, or localhost for iOS simulator
  static const String baseUrl = 'http://10.0.2.2:8000/api/v1';
  
  // Hardcoded values for simulation
  static const String dummyToken = 'dummy_token_for_simulation';
  static const String defaultGreenhouseId = '123e4567-e89b-12d3-a456-426614174000';

  Future<HarvestPredictionResponse> predictHarvest(HarvestPredictionRequest request) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/predictions/harvest'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $dummyToken',
        },
        body: jsonEncode(request.toJson()),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return HarvestPredictionResponse.fromJson(jsonDecode(response.body));
      } else {
        print('Harvest API Error: ${response.statusCode} - ${response.body}');
        return _getMockHarvestResponse();
      }
    } catch (e) {
      print('Harvest API Exception: $e');
      return _getMockHarvestResponse();
    }
  }

  Future<DiseaseRiskResponse> predictDiseaseRisk(DiseaseRiskRequest request) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/predictions/disease_risk'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $dummyToken',
        },
        body: jsonEncode(request.toJson()),
      );

      if (response.statusCode == 200 || response.statusCode == 201) {
        return DiseaseRiskResponse.fromJson(jsonDecode(response.body));
      } else {
        print('Disease Risk API Error: ${response.statusCode} - ${response.body}');
        return _getMockDiseaseRiskResponse();
      }
    } catch (e) {
      print('Disease Risk API Exception: $e');
      return _getMockDiseaseRiskResponse();
    }
  }

  // Fallback mocks for simulation when backend is unavailable or auth fails
  HarvestPredictionResponse _getMockHarvestResponse() {
    return HarvestPredictionResponse(
      predictionId: 'mock-pred-id',
      predictedHarvestDate: '2026-09-15',
      predictedDaysRemaining: 44,
      predictedYieldKgM2: 24.5,
      confidenceScore: 0.89,
    );
  }

  DiseaseRiskResponse _getMockDiseaseRiskResponse() {
    return DiseaseRiskResponse(
      greenhouseId: defaultGreenhouseId,
      riskScore: 0.75,
      riskLevel: 'high',
      recommendation: 'Hemen fungisit uygulaması yapın ve sera havalandırmasını artırın.',
    );
  }
}
