import 'dart:convert';
import 'package:http/http.dart' as http;

/// SQL identity comes only from explicit proof of both accounts, never email/UID.
class BackendSession {
  final String baseUrl;
  final Future<String> Function() firebaseToken;
  final http.Client client;
  Future<String?> Function()? requestOtp;

  BackendSession({
    required this.baseUrl,
    required this.firebaseToken,
    required this.client,
    this.requestOtp,
  });

  Future<Map<String, dynamic>> _post(
    String path,
    Map<String, dynamic> body, {
    String? token,
  }) async {
    final response = await client
        .post(
          Uri.parse('${baseUrl.replaceFirst(RegExp(r'/$'), '')}/$path'),
          headers: {
            'Content-Type': 'application/json',
            if (token != null) 'Authorization': 'Bearer $token',
          },
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 8));
    if (response.statusCode == 401 &&
        (path == 'login' || path == 'identity/firebase/session') &&
        !body.containsKey('otp') &&
        requestOtp != null &&
        jsonDecode(response.body)['mfa_required'] == true) {
      final otp = await requestOtp!();
      if (otp != null && otp.isNotEmpty) {
        return _post(path, {...body, 'otp': otp}, token: token);
      }
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw StateError(
        response.statusCode == 403
            ? 'Vincula tu cuenta SQL desde Ajustes para usar el asistente.'
            : 'Identidad rechazada (${response.statusCode}).',
      );
    }
    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<void> link(String email, String password, {String? otp}) async {
    final proof = await firebaseToken();
    final login = await _post('login', {
      'email': email,
      'password': password,
      if (otp != null) 'otp': otp,
    });
    await _post('identity/firebase/link', {
      'firebase_token': proof,
      'password': password,
    }, token: login['access_token'] as String);
  }

  Future<String> accessToken({String? otp}) async {
    final response = await _post('identity/firebase/session', {
      'firebase_token': await firebaseToken(),
      if (otp != null) 'otp': otp,
    });
    return response['access_token'] as String;
  }
}
