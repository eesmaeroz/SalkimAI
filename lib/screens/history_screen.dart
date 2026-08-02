import 'package:flutter/material.dart';
import '../services/history_service.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final HistoryService _historyService = HistoryService();
  List<Map<String, dynamic>> _harvestHistory = [];
  List<Map<String, dynamic>> _diseaseHistory = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final hHistory = await _historyService.getHarvestHistory();
    final dHistory = await _historyService.getDiseaseHistory();
    setState(() {
      _harvestHistory = hHistory;
      _diseaseHistory = dHistory;
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: Colors.green[50],
        appBar: AppBar(
          backgroundColor: Colors.green[700],
          title: const Text(
            'Geçmiş İşlemler',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
          iconTheme: const IconThemeData(color: Colors.white),
          bottom: const TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            indicatorColor: Colors.white,
            tabs: [
              Tab(icon: Icon(Icons.history), text: 'Hasat Geçmişi'),
              Tab(icon: Icon(Icons.bug_report), text: 'Hastalık Geçmişi'),
            ],
          ),
        ),
        body: _isLoading
            ? const Center(child: CircularProgressIndicator(color: Colors.green))
            : TabBarView(
                children: [
                  _buildHarvestList(),
                  _buildDiseaseList(),
                ],
              ),
      ),
    );
  }

  Widget _buildHarvestList() {
    if (_harvestHistory.isEmpty) {
      return const Center(child: Text('Henüz hasat tahmini geçmişi yok.'));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _harvestHistory.length,
      itemBuilder: (context, index) {
        final item = _harvestHistory[index];
        final response = item['response'] as Map<String, dynamic>;
        final dateStr = item['timestamp'] as String;
        final date = DateTime.parse(dateStr);
        
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ListTile(
            leading: const Icon(Icons.calendar_month, color: Colors.green),
            title: Text('Tahmin: ${response['predicted_harvest_date'] ?? '-'}'),
            subtitle: Text('Verim: ${response['predicted_yield_kg_m2']} kg/m² | İşlem: ${date.day}/${date.month}/${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}'),
          ),
        );
      },
    );
  }

  Widget _buildDiseaseList() {
    if (_diseaseHistory.isEmpty) {
      return const Center(child: Text('Henüz hastalık riski geçmişi yok.'));
    }
    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _diseaseHistory.length,
      itemBuilder: (context, index) {
        final item = _diseaseHistory[index];
        final response = item['response'] as Map<String, dynamic>;
        final dateStr = item['timestamp'] as String;
        final date = DateTime.parse(dateStr);
        final riskLevel = response['risk_level'] as String;
        
        Color riskColor = Colors.green;
        if (riskLevel == 'high') riskColor = Colors.red;
        if (riskLevel == 'medium') riskColor = Colors.orange;

        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: ListTile(
            leading: Icon(Icons.coronavirus, color: riskColor),
            title: Text('Risk: ${riskLevel.toUpperCase()}'),
            subtitle: Text('İşlem: ${date.day}/${date.month}/${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}'),
          ),
        );
      },
    );
  }
}
