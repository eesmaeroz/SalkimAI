import 'package:flutter/material.dart';
import '../widgets/harvest_form_widget.dart';

class PredictionScreen extends StatelessWidget {
  const PredictionScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        backgroundColor: Colors.green[50],
        appBar: AppBar(
          backgroundColor: Colors.green[700],
          title: const Text(
            'Tahminlemeler',
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
          ),
          iconTheme: const IconThemeData(color: Colors.white),
          bottom: const TabBar(
            labelColor: Colors.white,
            unselectedLabelColor: Colors.white70,
            indicatorColor: Colors.white,
            tabs: [
              Tab(icon: Icon(Icons.eco), text: 'Hasat Tahmini'),
              Tab(icon: Icon(Icons.coronavirus), text: 'Hastalık Riski'),
            ],
          ),
        ),
        body: const TabBarView(
          children: [
            SingleChildScrollView(child: HarvestFormWidget()),
            Center(
              child: Padding(
                padding: EdgeInsets.all(32.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.info_outline, size: 64, color: Colors.grey),
                    SizedBox(height: 16),
                    Text(
                      'Hastalık riski analizi, Ana Ekranda kamera veya galeriden domates fotoğrafı yüklediğinizde otomatik olarak yapılmaktadır.',
                      textAlign: TextAlign.center,
                      style: TextStyle(fontSize: 16, color: Colors.grey),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
