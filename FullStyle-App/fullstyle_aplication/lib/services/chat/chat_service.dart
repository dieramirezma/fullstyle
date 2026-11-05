import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:fullstyle_aplication/services/auth/backend_session.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:fullstyle_aplication/models/message.dart';
import 'package:fullstyle_aplication/services/chatbot/chatbot_repository.dart';
import 'package:fullstyle_aplication/config/app_config.dart';

class ChatService {
  final FirebaseFirestore _firestore = FirebaseFirestore.instance;
  final FirebaseAuth _auth = FirebaseAuth.instance;
  late final BackendSession backendSession = BackendSession(
    baseUrl: AppConfig.backendBaseUrl,
    client: http.Client(),
    firebaseToken: () async {
      final user = _auth.currentUser;
      if (user == null) throw StateError('Inicia sesion Firebase.');
      return (await user.getIdToken(true))!;
    },
  );
  final String _chatBotId = 'chatbot';

  final Map<String, ChatbotRepository> _repositoryCache = {};

  ChatbotRepository _getRepositoryForChat(String chatId) {
    if (!_repositoryCache.containsKey(chatId)) {
      if (AppConfig.debugMode) {
        _repositoryCache[chatId] = MockChatbotRepository();
      } else {
        _repositoryCache[chatId] = ApiChatbotRepository(
          baseUrl: AppConfig.chatbotApiBaseUrl,
          accessToken: backendSession.accessToken,
          sessionId: chatId,
        );
      }
    }
    return _repositoryCache[chatId]!;
  }

  Stream<List<Map<String, dynamic>>> getUsersStream() {
    return _firestore.collection('Users').snapshots().map((snapshot) {
      return snapshot.docs.map((doc) {
        final user = doc.data();
        return user;
      }).toList();
    });
  }

  Future<void> sendMessage({required String message}) async {
    final String currentUserId = _auth.currentUser!.uid;
    final String currentUserEmail = _auth.currentUser!.email!;
    final Timestamp timestamp = Timestamp.now();
    String chatId = _chatBotId + currentUserId;

    // Enviar mensaje del usuario
    Message userMessage = Message(
      senderId: currentUserId,
      senderEmail: currentUserEmail,
      message: message,
      timestamp: timestamp,
    );

    await _firestore
        .collection(AppConfig.firebaseCollection)
        .doc(chatId)
        .collection(AppConfig.firebaseCollectionMessages)
        .add(userMessage.toMap());

    final repository = _getRepositoryForChat(chatId);

    try {
      final botResponse = await repository.getResponse(message, chatId);

      Message botMessage = Message(
        senderId: _chatBotId,
        senderEmail: 'chatbot@fullstyle.app',
        message: botResponse,
        timestamp: Timestamp.now(),
      );

      await _firestore
          .collection(AppConfig.firebaseCollection)
          .doc(chatId)
          .collection(AppConfig.firebaseCollectionMessages)
          .add(botMessage.toMap());
    } catch (e) {
      debugPrint("Error al obtener respuesta del chatbot: $e");
    }
  }

  Future<bool> isFirstConversation(String userId) async {
    String chatId = _chatBotId + userId;

    final messages =
        await _firestore
            .collection(AppConfig.firebaseCollection)
            .doc(chatId)
            .collection(AppConfig.firebaseCollectionMessages)
            .limit(1)
            .get();

    return messages.docs.isEmpty;
  }

  Future<void> sendWelcomeMessage(String userId) async {
    String chatId = _chatBotId + userId;

    Message welcomeMessage = Message(
      senderId: _chatBotId,
      senderEmail: 'chatbot@fullstyle.app',
      message:
          "¡Bienvenido al chatbot de FullStyle! Este chat utiliza inteligencia artificial para responder tus preguntas. Tus datos están seguros y solo se utilizan para mejorar nuestro servicio.",
      timestamp: Timestamp.now(),
    );

    await _firestore
        .collection(AppConfig.firebaseCollection)
        .doc(chatId)
        .collection(AppConfig.firebaseCollectionMessages)
        .add(welcomeMessage.toMap());
  }

  Stream<QuerySnapshot> getMessages(String senderId) {
    String chatId = _chatBotId + senderId;
    return _firestore
        .collection(AppConfig.firebaseCollection)
        .doc(chatId)
        .collection(AppConfig.firebaseCollectionMessages)
        .orderBy('timestamp', descending: false)
        .snapshots();
  }

  Future<void> deleteAllMessages(String userId) async {
    try {
      String chatId = _chatBotId + userId;

      // Obtener referencia a la colección de mensajes
      final collectionRef = _firestore
          .collection(AppConfig.firebaseCollection)
          .doc(chatId)
          .collection(AppConfig.firebaseCollectionMessages);

      final messagesSnapshot = await collectionRef.get();

      if (messagesSnapshot.docs.isEmpty) {
        await sendWelcomeMessage(userId);
        return;
      }

      // Eliminar en lotes
      const int batchSize = 100;
      List<List<DocumentSnapshot>> batches = [];

      // Dividir documentos en lotes
      for (var i = 0; i < messagesSnapshot.docs.length; i += batchSize) {
        int end =
            (i + batchSize < messagesSnapshot.docs.length)
                ? i + batchSize
                : messagesSnapshot.docs.length;
        batches.add(messagesSnapshot.docs.sublist(i, end));
      }

      // Procesar cada lote
      for (var batch in batches) {
        final writeBatch = _firestore.batch();
        for (var doc in batch) {
          writeBatch.delete(doc.reference);
        }
        await writeBatch.commit();
      }

      await sendWelcomeMessage(userId);
    } catch (e) {
      debugPrint("Error al borrar mensajes: $e");
      rethrow;
    }
  }
}
