import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:fullstyle_aplication/config/app_config.dart';

abstract class ChatbotRepository {
  Future<String> getResponse(String message, String sessionId);
}

class ApiChatbotRepository implements ChatbotRepository {
  final String baseUrl;
  final http.Client _client;
  final String sessionId;
  final Future<String> Function() accessToken;

  ApiChatbotRepository({
    required this.baseUrl,
    required this.accessToken,
    http.Client? client,
    required this.sessionId,
  }) : _client = client ?? http.Client();

  @override
  Future<String> getResponse(String message, String sessionId) async {
    try {
      if (message.length > AppConfig.messageCharacterLimit) {
        message = message.substring(0, AppConfig.messageCharacterLimit);
      }

      // URL completa con la estructura correcta
      final url = '${baseUrl.replaceFirst(RegExp(r'/$'), '')}/api/v1/chat/send';

      final token = await accessToken();
      final response = await _client
          .post(
            Uri.parse(url),
            headers: {
              'Content-Type': 'application/json',
              'Accept': 'application/json',
              'Authorization': 'Bearer $token',
            },
            body: json.encode({'message': message, 'session_id': sessionId}),
          )
          .timeout(const Duration(seconds: 12));

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return data['reply'] ?? 'Lo siento, no pude entender tu mensaje.';
      } else {
        throw StateError('Asistente no disponible (${response.statusCode}).');
      }
    } catch (e) {
      debugPrint('Error connecting to chatbot: $e');
      rethrow;
    }
  }
}

// Mock para pruebas
class MockChatbotRepository implements ChatbotRepository {
  @override
  Future<String> getResponse(String message, String sessionId) async {
    await Future.delayed(const Duration(seconds: 2)); // Simular demora
    return "Esta es una respuesta de prueba a: $message";
  }
}
