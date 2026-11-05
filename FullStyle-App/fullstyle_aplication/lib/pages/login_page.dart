import 'package:flutter/material.dart';
import 'package:fullstyle_aplication/services/auth/auth_service.dart';
import 'package:fullstyle_aplication/components/auth_button.dart';
import 'package:fullstyle_aplication/components/auth_textfield.dart';

class LoginPage extends StatelessWidget {
  LoginPage({super.key, required this.switchAuthType});

  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final void Function()? switchAuthType;

  void login(BuildContext context) async {
    final authService = AuthService();

    try {
      await authService.signIn(_emailController.text, _passwordController.text);
    } catch (e) {
      if (!context.mounted) return;
      showDialog(
        context: context,
        builder:
            (context) => AlertDialog(
              title: Text('Error'),
              content: Text(e.toString()),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: Text('Aceptar'),
                ),
              ],
            ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.surface,
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Image.asset('assets/images/logo-fullstyle.png', width: 100),
            const SizedBox(height: 20),
            Text(
              'Bienvenido a la aplicación de FullStyle',
              style: TextStyle(
                color: Theme.of(context).colorScheme.inversePrimary,
                fontSize: 16,
              ),
            ),
            const SizedBox(height: 25),
            AuthTextfield(
              hintText: 'Correo',
              obscureText: false,
              controller: _emailController,
            ),
            const SizedBox(height: 10),
            AuthTextfield(
              hintText: 'Contraseña',
              obscureText: true,
              controller: _passwordController,
            ),
            const SizedBox(height: 25),
            AuthButton(
              buttonText: 'Iniciar Sesión',
              onTap: () => login(context),
            ),
            const SizedBox(height: 25),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  '¿No tienes una cuenta? ',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurface,
                  ),
                ),
                GestureDetector(
                  onTap: switchAuthType,
                  child: Text(
                    'Crear cuenta',
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.secondary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
