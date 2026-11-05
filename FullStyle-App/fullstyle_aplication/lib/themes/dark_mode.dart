import 'package:flutter/material.dart';

ThemeData darkMode = ThemeData(
  colorScheme: ColorScheme.dark(
    // Colores principales
    primary: Color(
      0xFF2B5D8B,
    ), // Version más clara del azul original para mejor visibilidad
    secondary: Color(
      0xFFFFB649,
    ), // Dorado más brillante para contrastar con fondo oscuro
    tertiary: Color(0xFF2C2C2C), // Gris oscuro para elementos de fondo
    // Colores de texto
    onPrimary: Colors.white, // Texto sobre color primario
    onSecondary: Colors.black, // Texto sobre color secundario
    onTertiary: Color(0xFFE0E0E0), // Color de fondo estándar para modo oscuro
    surface: Color(
      0xFF1E1E1E,
    ), // Superficies ligeramente más claras que el fondo
    onSurface: Color(0xFFE0E0E0), // Texto sobre superficies
    // Otros
    error: Color(0xFFCF6679), // Rojo más suave para errores
    onError: Colors.black, // Texto sobre error
    inversePrimary: Colors.white, // Color inverso para casos especiales
    // Contenedores
    primaryContainer: Color(
      0xFF1A3D5D,
    ), // Versión original del azul para contenedores
    secondaryContainer: Color(
      0xFFAB7B20,
    ), // Dorado más oscuro para contenedores
  ),
);
