import 'package:flutter/material.dart';
import '../models/prediction_models.dart';
import '../services/api_service.dart';
import '../services/history_service.dart';

class HarvestFormWidget extends StatefulWidget {
  const HarvestFormWidget({super.key});

  @override
  State<HarvestFormWidget> createState() => _HarvestFormWidgetState();
}

class _HarvestFormWidgetState extends State<HarvestFormWidget> with SingleTickerProviderStateMixin {
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

  late AnimationController _animController;
  late Animation<double> _fadeAnim;

  @override
  void initState() {
    super.initState();
    _animController = AnimationController(vsync: this, duration: const Duration(milliseconds: 600));
    _fadeAnim = CurvedAnimation(parent: _animController, curve: Curves.easeOutCubic);
  }

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
    _animController.dispose();
    super.dispose();
  }

  Future<void> _submitSimulation() async {
    if (!_formKey.currentState!.validate()) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Lütfen formdaki hatalı alanları düzeltin.')),
      );
      return;
    }

    setState(() {
      _isLoading = true;
      _result = null;
      _animController.reset();
    });

    try {
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
      _animController.forward();
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Tahmin alınırken hata oluştu: $e')),
        );
      }
    }
  }

  Widget _buildSectionCard(String title, IconData icon, List<Widget> children) {
    return Card(
      elevation: 1,
      margin: const EdgeInsets.only(bottom: 20),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: Colors.green[700], size: 22),
                const SizedBox(width: 10),
                Text(
                  title,
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Colors.green[900]),
                ),
              ],
            ),
            const Divider(height: 24),
            ...children,
          ],
        ),
      ),
    );
  }

  Widget _buildField(String label, TextEditingController controller, {String? suffix, IconData? prefixIcon}) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12.0),
      child: TextFormField(
        controller: controller,
        keyboardType: const TextInputType.numberWithOptions(decimal: true),
        decoration: InputDecoration(
          labelText: label,
          labelStyle: TextStyle(color: Colors.grey[700]),
          prefixIcon: prefixIcon != null ? Icon(prefixIcon, size: 20, color: Colors.grey[500]) : null,
          suffixText: suffix,
          suffixStyle: const TextStyle(fontWeight: FontWeight.w500, color: Colors.grey),
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey[300]!),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.grey[300]!),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(12),
            borderSide: BorderSide(color: Colors.green[500]!, width: 2),
          ),
          filled: true,
          fillColor: Colors.grey[50],
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        ),
        validator: (value) {
          if (value == null || value.isEmpty) return 'Boş bırakılamaz';
          if (double.tryParse(value) == null) return 'Geçerli sayı';
          return null;
        },
      ),
    );
  }

  Widget _buildResultsCard() {
    if (_result == null) return const SizedBox.shrink();
    
    return FadeTransition(
      opacity: _fadeAnim,
      child: Card(
        elevation: 4,
        margin: const EdgeInsets.only(bottom: 24),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: BorderSide(color: Colors.green[400]!, width: 2),
        ),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(16),
            gradient: LinearGradient(
              colors: [Colors.green[50]!, Colors.white],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
          padding: const EdgeInsets.all(20.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Icon(Icons.check_circle, color: Colors.green[700], size: 28),
                  const SizedBox(width: 8),
                  Text(
                    'Analiz Tamamlandı',
                    style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.green[800]),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              _buildResultRow(Icons.calendar_month, 'Tahmini Hasat', _result!.predictedHarvestDate ?? '-', Colors.green),
              const Padding(padding: EdgeInsets.symmetric(vertical: 8), child: Divider(height: 1)),
              _buildResultRow(Icons.timer, 'Kalan Gün', '${_result!.predictedDaysRemaining ?? '-'} gün', Colors.orange),
              const Padding(padding: EdgeInsets.symmetric(vertical: 8), child: Divider(height: 1)),
              _buildResultRow(Icons.scale, 'Beklenen Verim', '${_result!.predictedYieldKgM2?.toStringAsFixed(2) ?? '-'} kg/m²', Colors.blue),
              const Padding(padding: EdgeInsets.symmetric(vertical: 8), child: Divider(height: 1)),
              _buildResultRow(Icons.analytics, 'Model Güven Skoru', '%${((_result!.confidenceScore ?? 0) * 100).toInt()}', Colors.purple),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildResultRow(IconData icon, String label, String value, MaterialColor color) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: color[100], 
            borderRadius: BorderRadius.circular(12)
          ),
          child: Icon(icon, color: color[700], size: 22),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Text(label, style: TextStyle(color: Colors.grey[700], fontSize: 16, fontWeight: FontWeight.w500)),
        ),
        Text(value, style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18, color: Colors.grey[900])),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.only(left: 16.0, right: 16.0, top: 20.0, bottom: 100.0), // Padding for sticky button
                child: Form(
                  key: _formKey,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      const Text(
                        'Ortam Verilerini Doğrulayın',
                        style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Yapay zeka modelimizin en doğru hasat tahminini yapabilmesi için seranızın mevcut değerlerini girin.',
                        style: TextStyle(color: Colors.grey, height: 1.4, fontSize: 15),
                      ),
                      const SizedBox(height: 24),
                      
                      if (_result != null) _buildResultsCard(),

                      _buildSectionCard('İklim ve Ortam', Icons.thermostat, [
                        _buildField('Ortalama Sıcaklık', _tempAvg, suffix: '°C', prefixIcon: Icons.device_thermostat),
                        Row(
                          children: [
                            Expanded(child: _buildField('Min Sıc.', _tempMin, suffix: '°C')),
                            const SizedBox(width: 12),
                            Expanded(child: _buildField('Max Sıc.', _tempMax, suffix: '°C')),
                          ],
                        ),
                        Row(
                          children: [
                            Expanded(child: _buildField('Nem', _humidity, suffix: '%', prefixIcon: Icons.water_drop_outlined)),
                            const SizedBox(width: 12),
                            Expanded(child: _buildField('CO2', _co2, suffix: 'ppm', prefixIcon: Icons.cloud_outlined)),
                          ],
                        ),
                      ]),

                      _buildSectionCard('Işık ve Aydınlatma', Icons.wb_sunny, [
                        Row(
                          children: [
                            Expanded(child: _buildField('Işık Şiddeti', _light, suffix: 'Lux', prefixIcon: Icons.light_mode)),
                            const SizedBox(width: 12),
                            Expanded(child: _buildField('Fotoperiyot', _photo, suffix: 'Saat', prefixIcon: Icons.access_time)),
                          ],
                        ),
                      ]),

                      _buildSectionCard('Besin ve Sulama', Icons.water, [
                        _buildField('Günlük Sulama', _irrigation, suffix: 'mm', prefixIcon: Icons.water_drop),
                        Row(
                          children: [
                            Expanded(child: _buildField('Gübre N', _fertN, suffix: 'kg/ha', prefixIcon: Icons.science)),
                            const SizedBox(width: 8),
                            Expanded(child: _buildField('Gübre P', _fertP, suffix: 'kg/ha')),
                            const SizedBox(width: 8),
                            Expanded(child: _buildField('Gübre K', _fertK, suffix: 'kg/ha')),
                          ],
                        ),
                      ]),

                      _buildSectionCard('Toprak ve Sağlık', Icons.eco, [
                        Row(
                          children: [
                            Expanded(child: _buildField('Zararlı Oranı', _pest, suffix: '(0-1)', prefixIcon: Icons.bug_report)),
                            const SizedBox(width: 12),
                            Expanded(child: _buildField('Toprak pH', _ph, prefixIcon: Icons.grass)),
                          ],
                        ),
                      ]),
                    ],
                  ),
                ),
              ),
            ),
          ],
        ),

        // Background dimming when loading
        if (_isLoading)
          Positioned.fill(
            child: Container(
              color: Colors.white.withOpacity(0.5),
            ),
          ),

        // Sticky Bottom Button
        Positioned(
          left: 0,
          right: 0,
          bottom: 0,
          child: Container(
            padding: const EdgeInsets.only(left: 16, right: 16, top: 16, bottom: 24),
            decoration: BoxDecoration(
              color: Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  offset: const Offset(0, -6),
                  blurRadius: 12,
                ),
              ],
            ),
            child: SafeArea(
              top: false,
              child: ElevatedButton(
                onPressed: _isLoading ? null : _submitSimulation,
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.green[700],
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 18),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                  elevation: 2,
                ),
                child: _isLoading
                    ? const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          SizedBox(
                            width: 24,
                            height: 24,
                            child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5),
                          ),
                          SizedBox(width: 12),
                          Text('Yapay Zeka Analiz Ediyor...', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600)),
                        ],
                      )
                    : const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.auto_awesome, size: 24),
                          SizedBox(width: 10),
                          Text('Hasat Tahmini İste', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                        ],
                      ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
