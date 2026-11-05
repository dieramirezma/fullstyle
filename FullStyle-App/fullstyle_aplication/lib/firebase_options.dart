// Demo-only Firebase identifiers; no real project is configured.
// ignore_for_file: type=lint
import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

/// Default [FirebaseOptions] for use with your Firebase apps.
///
/// Example:
/// ```dart
/// import 'firebase_options.dart';
/// // ...
/// await Firebase.initializeApp(
///   options: DefaultFirebaseOptions.currentPlatform,
/// );
/// ```
class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      return web;
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      case TargetPlatform.macOS:
        return macos;
      case TargetPlatform.windows:
        return windows;
      case TargetPlatform.linux:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for linux - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      default:
        throw UnsupportedError(
          'DefaultFirebaseOptions are not supported for this platform.',
        );
    }
  }

  static const FirebaseOptions web = FirebaseOptions(
    apiKey: 'demo-local-key',
    appId: '1:123:web:local',
    messagingSenderId: '123',
    projectId: 'demo-fullstyle',
    authDomain: 'demo-fullstyle.firebaseapp.com',
    storageBucket: 'demo-fullstyle.invalid',
  );

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'demo-local-key',
    appId: '1:123:web:local',
    messagingSenderId: '123',
    projectId: 'demo-fullstyle',
    storageBucket: 'demo-fullstyle.invalid',
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'demo-local-key',
    appId: '1:123:web:local',
    messagingSenderId: '123',
    projectId: 'demo-fullstyle',
    storageBucket: 'demo-fullstyle.invalid',
    iosBundleId: 'com.example.fullstyleAplication',
  );

  static const FirebaseOptions macos = FirebaseOptions(
    apiKey: 'demo-local-key',
    appId: '1:123:web:local',
    messagingSenderId: '123',
    projectId: 'demo-fullstyle',
    storageBucket: 'demo-fullstyle.invalid',
    iosBundleId: 'com.example.fullstyleAplication',
  );

  static const FirebaseOptions windows = FirebaseOptions(
    apiKey: 'demo-local-key',
    appId: '1:123:web:local',
    messagingSenderId: '123',
    projectId: 'demo-fullstyle',
    authDomain: 'demo-fullstyle.firebaseapp.com',
    storageBucket: 'demo-fullstyle.invalid',
  );
}
