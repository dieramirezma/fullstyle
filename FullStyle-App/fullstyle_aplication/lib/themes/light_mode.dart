import 'package:flutter/material.dart';

ThemeData lightMode = ThemeData(
  colorScheme: ColorScheme.light(
    primary: Color(0xFF1A3D5D), // Main app color
    secondary: Color(0xFFEBA745), // Accent color
    tertiary: Color(0xFFF5F5F5), // Background elements
    // Text
    onPrimary: Colors.white,
    onSecondary: Colors.black,
    onTertiary: Color(0xFF4F4F4F),
    // Background
    surface: Colors.white,
    onSurface: Color(0xFF4F4F4F),
    // Other
    error: Colors.redAccent,
    onError: Colors.white,
    inversePrimary: Color(0xFF000000),
    // Shades
    primaryContainer: Color(0xFF0D2B45), // Darker navy for emphasis
    secondaryContainer: Color(0xFFD99B35), // Darker gold for emphasis
  ),
);
