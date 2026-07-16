import 'package:flutter/material.dart';
import 'screens/home_screen.dart';

void main() {
  runApp(const SalkimApp());
}

class SalkimApp extends StatelessWidget {
  const SalkimApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Salkım AI',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.green),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}