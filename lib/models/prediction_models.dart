class HarvestPredictionRequest {
  final String greenhouseId;
  final String cropType;
  final String variety;
  final double avgTemperatureC;
  final double minTemperatureC;
  final double maxTemperatureC;
  final double humidityPercent;
  final double co2Ppm;
  final double lightIntensityLux;
  final double photoperiodHours;
  final double irrigationMm;
  final double fertilizerNKgHa;
  final double fertilizerPKgHa;
  final double fertilizerKKgHa;
  final double pestSeverity;
  final double soilPh;

  HarvestPredictionRequest({
    required this.greenhouseId,
    required this.cropType,
    required this.variety,
    required this.avgTemperatureC,
    required this.minTemperatureC,
    required this.maxTemperatureC,
    required this.humidityPercent,
    required this.co2Ppm,
    required this.lightIntensityLux,
    required this.photoperiodHours,
    required this.irrigationMm,
    required this.fertilizerNKgHa,
    required this.fertilizerPKgHa,
    required this.fertilizerKKgHa,
    required this.pestSeverity,
    required this.soilPh,
  });

  Map<String, dynamic> toJson() {
    return {
      'greenhouse_id': greenhouseId,
      'crop_type': cropType,
      'variety': variety,
      'avg_temperature_C': avgTemperatureC,
      'min_temperature_C': minTemperatureC,
      'max_temperature_C': maxTemperatureC,
      'humidity_percent': humidityPercent,
      'co2_ppm': co2Ppm,
      'light_intensity_lux': lightIntensityLux,
      'photoperiod_hours': photoperiodHours,
      'irrigation_mm': irrigationMm,
      'fertilizer_N_kg_ha': fertilizerNKgHa,
      'fertilizer_P_kg_ha': fertilizerPKgHa,
      'fertilizer_K_kg_ha': fertilizerKKgHa,
      'pest_severity': pestSeverity,
      'soil_pH': soilPh,
    };
  }
}

class HarvestPredictionResponse {
  final String predictionId;
  final String? predictedHarvestDate;
  final int? predictedDaysRemaining;
  final double? predictedYieldKgM2;
  final double? confidenceScore;

  HarvestPredictionResponse({
    required this.predictionId,
    this.predictedHarvestDate,
    this.predictedDaysRemaining,
    this.predictedYieldKgM2,
    this.confidenceScore,
  });

  factory HarvestPredictionResponse.fromJson(Map<String, dynamic> json) {
    return HarvestPredictionResponse(
      predictionId: json['prediction_id'],
      predictedHarvestDate: json['predicted_harvest_date'],
      predictedDaysRemaining: json['predicted_days_remaining'],
      predictedYieldKgM2: json['predicted_yield_kg_m2']?.toDouble(),
      confidenceScore: json['confidence_score']?.toDouble(),
    );
  }
}

class DiseaseRiskRequest {
  final String greenhouseId;
  final double? avgHumidityLast7d;
  final double? avgTempLast7d;
  final double? diseaseProbFromVision;

  DiseaseRiskRequest({
    required this.greenhouseId,
    this.avgHumidityLast7d,
    this.avgTempLast7d,
    this.diseaseProbFromVision,
  });

  Map<String, dynamic> toJson() {
    return {
      'greenhouse_id': greenhouseId,
      if (avgHumidityLast7d != null) 'avg_humidity_last_7d': avgHumidityLast7d,
      if (avgTempLast7d != null) 'avg_temp_last_7d': avgTempLast7d,
      if (diseaseProbFromVision != null) 'disease_prob_from_vision': diseaseProbFromVision,
    };
  }
}

class DiseaseRiskResponse {
  final String greenhouseId;
  final double riskScore;
  final String riskLevel;
  final String recommendation;

  DiseaseRiskResponse({
    required this.greenhouseId,
    required this.riskScore,
    required this.riskLevel,
    required this.recommendation,
  });

  factory DiseaseRiskResponse.fromJson(Map<String, dynamic> json) {
    return DiseaseRiskResponse(
      greenhouseId: json['greenhouse_id'],
      riskScore: json['risk_score'].toDouble(),
      riskLevel: json['risk_level'],
      recommendation: json['recommendation'],
    );
  }
}
