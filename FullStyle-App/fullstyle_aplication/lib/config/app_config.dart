class AppConfig {
  static const bool localOnly = bool.fromEnvironment(
    'FS_LOCAL_ONLY',
    defaultValue: true,
  );
  static const String localHost = String.fromEnvironment(
    'FS_LOCAL_HOST',
    defaultValue: 'localhost',
  );
  static const int localPort = int.fromEnvironment(
    'FS_LOCAL_PORT',
    defaultValue: 38080,
  );
  static const String chatbotApiBaseUrl =
      'http://$localHost:$localPort/chatbot';
  static const String backendBaseUrl =
      'http://$localHost:$localPort/business/api';
  static const int messageCharacterLimit = 500;
  static const String firebaseCollection = 'chats';
  static const String firebaseCollectionMessages = 'messages';
  static const bool debugMode = false;
}
