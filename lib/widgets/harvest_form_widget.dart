import 'package:flutter/material.dart';
import '../models/prediction_models.dart';
import '../services/api_service.dart';
import '../services/history_service.dart';

class HarvestFormWidget extends StatefulWidget {
  const HarvestFormWidget({super.key});

  @override
  State<HarvestFormWidget> createState() => _HarvestFormWidgetState();
}

class _HarvestFormWidgetState extends State<HarvestFormWidget> {
  final ApiService _apiService = ApiService();
  final HistoryService _historyService = HistoryService();
  bool _isLoading = false;
  HarvestPredictionResponse? _result;

  final _formKey = GlobalKey<FormState>();

  // Form Controllers with defaults
  final _tempAvg = TextEditingController(text: '22.5');
  final _tempMin = TextEditingController(text: '18.0');
  final _tempMax = TextEditingController(text: '28.0');
  final _humidity = TextEditingController(text: '65.0');
  final _co2 = TextEditingController(text: '800.0');
  final _light = TextEditingController(text: '45000.0');
  final _photo = TextEditingController(text: '14.0');
  final _irrigation = TextEditingController(text: '5.0');
  final _fertN = TextEditingController(text: '150.0');
  final _fertP = TextEditingController(text: '80.0');
  final _fertK = TextEditingController(text: '200.0');
  final _pest = TextEditingController(text: '0.1');
  final _ph = TextEditingController(text: '6.2');

  @override
  void dispose() {
    _tempAvg.dispose();
    _tempMin.dispose();
    _tempMax.dispose();
    _humidity.dispose();
    _co2.dispose();
    _light.dispose();
    _photo.dispose();
    _irrigation.dispose();
    _fertN.dispose();
    _fertP.dispose();
    _fertK.dispose();
    _pest.dispose();
    _ph.dispose();
    super.dispose();
  }

  Future<void> _submitSimulation() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _result = null;
    });

    final request = HarvestPredictionRequest(
      greenhouseId: ApiService.defaultGreenhouseId,
      cropType: 'Tomato',
      variety: 'Beefsteak',
      avgTemperatureC: double.tryParse(_tempAvg.text) ?? 22.5,
      minTemperatureC: double.tryParse(_tempMin.text) ?? 18.0,
      maxTemperatureC: double.tryParse(_tempMax.text) ?? 28.0,
      humidityPercent: double.tryParse(_humidity.text) ?? 65.0,
      co2Ppm: double.tryParse(_co2.text) ?? 800.0,
      lightIntensityLux: double.tryParse(_light.text) ?? 45000.0,
      photoperiodHours: double.tryParse(_photo.text) ?? 14.0,
      irrigationMm: double.tryParse(_irrigation.text) ?? 5.0,
      fertilizerNKgHa: double.tryParse(_fertN.text) ?? 150.0,
      fertilizerPKgHa: double.tryParse(_fertP.text) ?? 80.0,
      fertilizerKKgHa: double.tryParse(_fertK.text) ?? 200.0,
      pestSeverity: double.tryParse(_pest.text) ?? 0.1,
      soilPh: double.tryParse(_ph.text) ?? 6.2,
    );

    final response = await _apiService.predictHarvest(request);
    
    // Save to local history
    await _historyService.saveHarvestResult(response, request);

    setState(() {
      _result = response;
      _isLoading = false;
    });
  }

  Widget _buildField(String label, TextEditingController controller) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: TextFormField(
        controller: controller,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        decoration: InputDecoration(
          labelText: label,
          border: const OutlineInputBorder(),
          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        ),
        validator: (value) {
          if (value == null || value.isEmpty) return 'Boş bırakılamaz';
          if (double.tryParse(value) == null) return 'Geçerli bir sayı girin';
          return null;
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Hasat Tahmini Formu',
              style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Lütfen mevcut ortam verilerinizi giriniz:',
              style: TextStyle(color: Colors.grey),
            ),
            const SizedBox(height: 16),
            
            _buildField('Ortalama Sıcaklık (°C)', _tempAvg),
            Row(
              children: [
                Expanded(child: _buildField('Min Sıc.', _tempMin)),
                const SizedBox(width: 8),
                Expanded(child: _buildField('Max Sıc.', _tempMax)),
              ],
            ),
            Row(
              children: [
                Expanded(child: _buildField('Nem (%)', _humidity)),
                const SizedBox(width: 8),
                Expanded(child: _buildField('CO2 (ppm)', _co2)),
              ],
            ),
            Row(
              children: [
                Expanded(child: _buildField('Işık (Lux)', _light)),
                const SizedBox(width: 8),
                Expanded(child: _buildField('Fotoperiyot', _photo)),
              ],
            ),
            _buildField('Sulama (mm)', _irrigation),
            Row(
              children: [
                Expanded(child: _buildField('Gübre N (kg/ha)', _fertN)),
                const SizedBox(width: 8),
                Expanded(child: _buildField('Gübre P', _fertP)),
                const SizedBox(width: 8),
                Expanded(child: _buildField('Gübre K', _fertK)),
              ],
            ),
            Row(
              children: [
                Expanded(child: _buildField('Zararlı (0-1)', _pest)),
                const SizedBox(width: 8),
                Expanded(child: _buildField('Toprak pH', _ph)),
              ],
            ),
            
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: _isLoading ? null : _submitSimulation,
              icon: _isLoading
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                    )
                  : const Icon(Icons.calculate),
              label: Text(_isLoading ? 'Hesaplanıyor...' : 'Tahmin İste'),
              style: ElevatedButton.styleFrom(
                backgroundColor: Colors.green[700],
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
            if (_result != null) ...[
              const SizedBox(height: 24),
              Card(
                elevation: 4,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Sonuçlar:',
                        style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                      ),
                      const Divider(),
                      ListTile(
                        leading: const Icon(Icons.calendar_today, color: Colors.green),
                        title: const Text('Tahmini Hasat Tarihi'),
                        trailing: Text(
                          _result!.predictedHarvestDate ?? '-',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                      ),
                      ListTile(
                        leading: const Icon(Icons.timer, color: Colors.orange),
                        title: const Text('Kalan Gün'),
                        trailing: Text(
                          '${_result!.predictedDaysRemaining ?? '-'} gün',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                      ),
                      ListTile(
                        leading: const Icon(Icons.scale, color: Colors.blue),
                        title: const Text('Beklenen Verim (kg/m²)'),
                        trailing: Text(
                          '${_result!.predictedYieldKgM2?.toStringAsFixed(2) ?? '-'} kg',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                      ),
                      ListTile(
                        leading: const Icon(Icons.analytics, color: Colors.purple),
                        title: const Text('Güven Skoru'),
                        trailing: Text(
                          '%${((_result!.confidenceScore ?? 0) * 100).toInt()}',
                          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                        ),
                      ),
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
