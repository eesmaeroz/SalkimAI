import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ResultScreen extends StatefulWidget {
  final Uint8List imageBytes;
  const ResultScreen({super.key, required this.imageBytes});

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  static const String _baseUrl = 'https://salkimai-production.up.railway.app';
  static const String _testPhone = '05553972301';
  static const String _testPassword = 'Test1234!';

  bool _isLoading = true;
  String _statusMessage = 'Giriş yapılıyor...';
  bool _hasError = false;
  Map<String, dynamic>? _analysisResult;

  @override
  void initState() {
    super.initState();
    _runFullFlow();
  }

  Future<void> _runFullFlow() async {
    try {
      // 1. Giriş yap, token al
      setState(() => _statusMessage = 'Giriş yapılıyor...');
      final token = await _login();

      // 2. Fotoğrafı yükle
      setState(() => _statusMessage = 'Fotoğraf yükleniyor...');
      final imageId = await _uploadImage(token);

      // 3. Sonucu bekle (polling)
      setState(() => _statusMessage = 'Analiz ediliyor...');
      final result = await _pollResult(token, imageId);

      setState(() {
        _analysisResult = result;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _hasError = true;
        _statusMessage = 'Hata: $e';
        _isLoading = false;
      });
    }
  }

  Future<String> _login() async {
    final response = await http.post(
      Uri.parse('$_baseUrl/api/v1/auth/token'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'phone': _testPhone, 'password': _testPassword}),
    );
    if (response.statusCode != 200) {
      throw Exception('Giriş başarısız: ${response.body}');
    }
    final data = jsonDecode(response.body);
    return data['access_token'];
  }

  Future<String> _uploadImage(String token) async {
    final uri = Uri.parse('$_baseUrl/api/v1/images/upload');
    final request = http.MultipartRequest('POST', uri);
    request.headers['Authorization'] = 'Bearer $token';
    request.files.add(
      http.MultipartFile.fromBytes(
        'file',
        widget.imageBytes,
        filename: 'photo.jpg',
      ),
    );
    final streamedResponse = await request.send();
    final response = await http.Response.fromStream(streamedResponse);
    if (response.statusCode != 202) {
      throw Exception('Yükleme başarısız: ${response.body}');
    }
    final data = jsonDecode(response.body);
    return data['image_id'];
  }

  Future<Map<String, dynamic>> _pollResult(String token, String imageId) async {
    for (int i = 0; i < 20; i++) {
      await Future.delayed(const Duration(seconds: 3));
      final response = await http.get(
        Uri.parse('$_baseUrl/api/v1/images/$imageId/result'),
        headers: {'Authorization': 'Bearer $token'},
      );
      if (response.statusCode != 200) {
        throw Exception('Sonuç alınamadı: ${response.body}');
      }
      final data = jsonDecode(response.body);
      if (data['status'] == 'completed') {
        return data;
      }
      if (data['status'] == 'failed') {
        throw Exception('Analiz başarısız oldu.');
      }
      setState(() => _statusMessage = 'Analiz ediliyor... (${data['status']})');
    }
    throw Exception('Zaman aşımı: analiz çok uzun sürdü.');
  }

  Color _getColor(String? maturityClass) {
    if (maturityClass == 'red') return Colors.red;
    if (maturityClass == 'turning') return Colors.orange;
    if (maturityClass == 'green') return Colors.green;
    return Colors.grey;
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
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const CircularProgressIndicator(color: Colors.green),
                  const SizedBox(height: 16),
                  Text(_statusMessage),
                ],
              ),
            )
          : _hasError
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24.0),
                    child: Text(
                      _statusMessage,
                      style: const TextStyle(color: Colors.red, fontSize: 16),
                      textAlign: TextAlign.center,
                    ),
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
                        '${_analysisResult?['total_tomatoes'] ?? 0} domates tespit edildi',
                        style: const TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: _getColor(
                              _analysisResult?['maturity_class'],
                            ),
                          ),
                          title: Text(
                            'Olgunluk: ${_analysisResult?['maturity_class'] ?? "-"}',
                          ),
                          subtitle: Text(
                            'Hastalık: ${_analysisResult?['disease_class'] ?? "-"}',
                          ),
                          trailing: Text(
                            '%${((_analysisResult?['disease_prob'] ?? 0) * 100).toInt()}',
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
    );
  }
}
