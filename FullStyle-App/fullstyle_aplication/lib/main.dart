import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'config/app_config.dart';
import 'package:fullstyle_aplication/services/auth/auth_gate.dart';
import 'package:fullstyle_aplication/firebase_options.dart';
import 'package:fullstyle_aplication/themes/light_mode.dart';
import 'package:fullstyle_aplication/themes/dark_mode.dart';
import 'package:fullstyle_aplication/themes/theme_provider.dart';
import 'package:provider/provider.dart';
import 'package:firebase_core/firebase_core.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(
    options:
        AppConfig.localOnly
            ? const FirebaseOptions(
              apiKey: 'demo-local-key',
              appId: '1:123:web:local',
              messagingSenderId: '123',
              projectId: 'demo-fullstyle',
            )
            : DefaultFirebaseOptions.currentPlatform,
  );
  if (AppConfig.localOnly) {
    await FirebaseAuth.instance.useAuthEmulator(
      AppConfig.localHost,
      AppConfig.localPort,
    );
    FirebaseFirestore.instance.useFirestoreEmulator(
      AppConfig.localHost,
      AppConfig.localPort,
    );
  }

  runApp(
    // Cambiar el tema de la aplicación
    ChangeNotifierProvider(
      create: (context) => ThemeProvider(),
      child: const MainApp(),
    ),
  );
}

class MainApp extends StatelessWidget {
  const MainApp({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<ThemeProvider>(
      builder: (context, themeProvider, child) {
        return MaterialApp(
          theme: lightMode,
          darkTheme: darkMode,
          themeMode:
              themeProvider.isDarkMode ? ThemeMode.dark : ThemeMode.light,
          debugShowCheckedModeBanner: false,
          home: AuthGate(),
        );
      },
    );
  }
}
