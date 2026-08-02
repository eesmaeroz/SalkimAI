import 'package:flutter/material.dart';
import 'dart:typed_data';
import '../models/prediction_models.dart';
import '../services/api_service.dart';
import '../services/history_service.dart';

class ResultScreen extends StatefulWidget {
  final Uint8List imageBytes;
  const ResultScreen({super.key, required this.imageBytes});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  bool _isLoading = true;
  List<Map<String, dynamic>> _results = [];
  DiseaseRiskResponse? _diseaseRiskResult;
  final ApiService _apiService = ApiService();
  final HistoryService _historyService = HistoryService();

  @override
  void initState() {
    super.initState();
    _analyzeImage();
  }

  Future<void> _analyzeImage() async {
    await Future.delayed(const Duration(seconds: 2));
    setState(() {
      _results = [
        {'id': 1, 'olgunluk': 'ripe', 'hastalik': 'healthy', 'skor': 0.99},
        {'id': 2, 'olgunluk': 'ripe', 'hastalik': 'healthy', 'skor': 0.95},
        {'id': 3, 'olgunluk': 'not_ripe', 'hastalik': 'early_blight', 'skor': 0.88},
        {'id': 4, 'olgunluk': 'ripe', 'hastalik': 'healthy', 'skor': 0.97},
      ];
    });

    // Simulated disease_prob_from_vision (e.g., from average of scores or worst score)
    double simulatedVisionProb = 0.88;

    final request = DiseaseRiskRequest(
      greenhouseId: ApiService.defaultGreenhouseId,
      avgHumidityLast7d: 70.0,
      avgTempLast7d: 25.0,
      diseaseProbFromVision: simulatedVisionProb,
    );

    final riskResponse = await _apiService.predictDiseaseRisk(request);
    
    // Save to history
    await _historyService.saveDiseaseResult(riskResponse);

    setState(() {
      _diseaseRiskResult = riskResponse;
      _isLoading = false;
    });
  }

  Color _getColor(String olgunluk) {
    if (olgunluk == 'ripe') return Colors.green;
    if (olgunluk == 'not_ripe') return Colors.orange;
    return Colors.red;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.green[50],
      appBar: AppBar(
        backgroundColor: Colors.green[700],
        title: const Text(
          'Analiz Sonucu',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
        ),
        iconTheme: const IconThemeData(color: Colors.white),
      ),
      body: _isLoading
          ? const Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  CircularProgressIndicator(color: Colors.green),
                  SizedBox(height: 16),
                  Text('Analiz ediliyor...'),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                children: [
                  ClipRRect(
                    borderRadius: BorderRadius.circular(16),
                    child: Image.memory(
                      widget.imageBytes,
                      height: 200,
                      fit: BoxFit.cover,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    '${_results.length} domates tespit edildi',
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: _results.length,
                    itemBuilder: (context, index) {
                      final r = _results[index];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: _getColor(r['olgunluk']),
                            child: Text(
                              '${r['id']}',
                              style: const TextStyle(color: Colors.white),
                            ),
                          ),
                          title: Text('Domates ${r['id']}'),
                          subtitle: Text('Hastalık: ${r['hastalik']}'),
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Text(
                                r['olgunluk'],
                                style: TextStyle(
                                  color: _getColor(r['olgunluk']),
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              Text('%${(r['skor'] * 100).toInt()}'),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                  if (_diseaseRiskResult != null) ...[
                    const SizedBox(height: 24),
                    const Text(
                      'Hastalık Riski Analizi (Sera)',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Card(
                      color: _diseaseRiskResult!.riskLevel == 'high' 
                          ? Colors.red[50] 
                          : (_diseaseRiskResult!.riskLevel == 'medium' ? Colors.orange[50] : Colors.green[50]),
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'Risk Skoru:',
                                  style: TextStyle(fontWeight: FontWeight.bold),
                                ),
                                Text(
                                  '%${(_diseaseRiskResult!.riskScore * 100).toInt()}',
                                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text(
                                  'Risk Seviyesi:',
                                  style: TextStyle(fontWeight: FontWeight.bold),
                                ),
                                Text(
                                  _diseaseRiskResult!.riskLevel.toUpperCase(),
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    color: _diseaseRiskResult!.riskLevel == 'high' 
                                        ? Colors.red 
                                        : (_diseaseRiskResult!.riskLevel == 'medium' ? Colors.orange : Colors.green),
                                  ),
                                ),
                              ],
                            ),
                            const Divider(),
                            const Text(
                              'Öneri:',
                              style: TextStyle(fontWeight: FontWeight.bold),
                            ),
                            const SizedBox(height: 4),
                            Text(_diseaseRiskResult!.recommendation),
                          ],
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
    );
  }
}