import 'package:flutter/material.dart';
import 'package:fullstyle_aplication/services/auth/backend_session.dart';

Future<void> showAccountLinkDialog(
  BuildContext context,
  BackendSession session,
) async {
  final email = TextEditingController();
  final password = TextEditingController();
  final otp = TextEditingController();
  try {
    await showDialog<void>(
      context: context,
      builder:
          (dialogContext) => AlertDialog(
            title: const Text('Vincular cuenta FullStyle'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'Confirma tus credenciales SQL. Tu cuenta Firebase se conserva.',
                ),
                TextField(
                  controller: email,
                  decoration: const InputDecoration(labelText: 'Correo SQL'),
                ),
                TextField(
                  controller: password,
                  obscureText: true,
                  decoration: const InputDecoration(
                    labelText: 'Contraseña SQL',
                  ),
                ),
                TextField(
                  controller: otp,
                  keyboardType: TextInputType.number,
                  decoration: const InputDecoration(
                    labelText: 'Código MFA (si está activo)',
                  ),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(dialogContext),
                child: const Text('Cancelar'),
              ),
              FilledButton(
                onPressed: () async {
                  try {
                    await session.link(
                      email.text,
                      password.text,
                      otp: otp.text.isEmpty ? null : otp.text,
                    );
                    if (!dialogContext.mounted) return;
                    Navigator.pop(dialogContext);
                  } catch (error) {
                    if (!dialogContext.mounted) return;
                    ScaffoldMessenger.of(
                      dialogContext,
                    ).showSnackBar(SnackBar(content: Text('$error')));
                  }
                },
                child: const Text('Vincular'),
              ),
            ],
          ),
    );
  } finally {
    email.dispose();
    password.dispose();
    otp.dispose();
  }
}
