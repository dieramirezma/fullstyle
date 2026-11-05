import 'dart:convert';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:fullstyle_aplication/services/auth/backend_session.dart';
import 'package:fullstyle_aplication/services/chatbot/chatbot_repository.dart';

void main() {
  test(
    'MFA challenge preserves Firebase proof and makes one prompted attempt',
    () async {
      var calls = 0;
      var prompts = 0;
      final session = BackendSession(
        baseUrl: 'http://local.invalid/api',
        firebaseToken: () async => 'firebase-proof',
        requestOtp: () async {
          prompts++;
          return '123456';
        },
        client: MockClient((request) async {
          calls++;
          final body = jsonDecode(request.body);
          expect(body['firebase_token'], 'firebase-proof');
          if (calls == 1) {
            expect(body.containsKey('otp'), false);
            return http.Response('{"mfa_required":true}', 401);
          }
          expect(body['otp'], '123456');
          return http.Response('{"access_token":"mfa-sql-token"}', 200);
        }),
      );
      expect(await session.accessToken(), 'mfa-sql-token');
      expect(calls, 2);
      expect(prompts, 1);
    },
  );

  test(
    'invalid OTP stops authentication without repeated prompts or chat writes',
    () async {
      var calls = 0;
      var prompts = 0;
      final session = BackendSession(
        baseUrl: 'http://local.invalid/api',
        firebaseToken: () async => 'firebase-proof',
        requestOtp: () async {
          prompts++;
          return 'wrong';
        },
        client: MockClient((request) async {
          calls++;
          return http.Response('{"mfa_required":true}', 401);
        }),
      );
      await expectLater(session.accessToken(), throwsStateError);
      expect(calls, 2);
      expect(prompts, 1);
    },
  );

  test(
    'chat uses configured destination and verified backend Bearer',
    () async {
      final repository = ApiChatbotRepository(
        baseUrl: 'http://local.invalid/chatbot',
        sessionId: 'same-session',
        accessToken: () async => 'verified-sql-token',
        client: MockClient((request) async {
          expect(
            request.url.toString(),
            'http://local.invalid/chatbot/api/v1/chat/send',
          );
          expect(request.headers['Authorization'], 'Bearer verified-sql-token');
          expect(jsonDecode(request.body)['session_id'], 'same-session');
          return http.Response('{"reply":"authorized result"}', 200);
        }),
      );
      expect(
        await repository.getResponse('mis citas', 'same-session'),
        'authorized result',
      );
    },
  );

  test('unlinked Firebase account cannot call business through chat', () async {
    var calls = 0;
    final session = BackendSession(
      baseUrl: 'http://local.invalid/business/api',
      firebaseToken: () async => 'verified-firebase-proof',
      client: MockClient((request) async {
        expect(request.url.path, '/business/api/identity/firebase/session');
        expect(jsonDecode(request.body), {
          'firebase_token': 'verified-firebase-proof',
        });
        return http.Response('{"message":"link required"}', 403);
      }),
    );
    final repository = ApiChatbotRepository(
      baseUrl: 'http://local.invalid/chatbot',
      sessionId: 'one',
      accessToken: session.accessToken,
      client: MockClient((request) async {
        calls++;
        return http.Response('{}', 200);
      }),
    );
    await expectLater(
      repository.getResponse('cancelar 1', 'one'),
      throwsStateError,
    );
    expect(calls, 0);
  });

  test(
    'linking requires SQL login and Firebase proof with current password',
    () async {
      final paths = <String>[];
      final session = BackendSession(
        baseUrl: 'http://local.invalid/api',
        firebaseToken: () async => 'firebase-proof',
        client: MockClient((request) async {
          paths.add(request.url.path);
          if (request.url.path == '/api/login') {
            expect(jsonDecode(request.body), {
              'email': 'owner@synthetic.invalid',
              'password': 'synthetic-password',
            });
            return http.Response('{"access_token":"sql-proof"}', 200);
          }
          expect(request.headers['Authorization'], 'Bearer sql-proof');
          expect(jsonDecode(request.body), {
            'firebase_token': 'firebase-proof',
            'password': 'synthetic-password',
          });
          return http.Response('{"linked":true}', 201);
        }),
      );
      await session.link('owner@synthetic.invalid', 'synthetic-password');
      expect(paths, ['/api/login', '/api/identity/firebase/link']);
    },
  );
}
