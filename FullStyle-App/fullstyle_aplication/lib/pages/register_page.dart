import 'package:flutter/material.dart';
import 'package:fullstyle_aplication/services/auth/auth_service.dart';
import 'package:fullstyle_aplication/components/auth_button.dart';
import 'package:fullstyle_aplication/components/auth_textfield.dart';

class RegisterPage extends StatelessWidget {
  RegisterPage({super.key, required this.switchAuthType});
  final TextEditingController _nameController = TextEditingController();
  final TextEditingController _sureNameController = TextEditingController();
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _confirmPasswordController =
      TextEditingController();
  final void Function()? switchAuthType;

  void register(BuildContext context) async {
    final authService = AuthService();

    final name = _nameController.text.trim();
    final surname = _sureNameController.text.trim();
    final email = _emailController.text.trim();
    final password = _passwordController.text;
    final confirmPassword = _confirmPasswordController.text;

    // Validación de campos vacíos
    if (name.isEmpty ||
        surname.isEmpty ||
        email.isEmpty ||
        password.isEmpty ||
        confirmPassword.isEmpty) {
      _showErrorDialog(context, 'Error', 'Completa todos los campos.');
      return;
    }

    // Validación de nombre y apellido
    final nameRegex = RegExp(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$');
    if (!nameRegex.hasMatch(name) || !nameRegex.hasMatch(surname)) {
      _showErrorDialog(
        context,
        'Error',
        'El nombre y apellido solo deben contener letras.',
      );
      return;
    }

    // Validación de correo electrónico
    final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
    if (!emailRegex.hasMatch(email)) {
      _showErrorDialog(
        context,
        'Error',
        'Ingresa un correo electrónico válido.',
      );
      return;
    }

    final hasUppercase = RegExp(r'[A-Z]').hasMatch(password);
    final hasLowercase = RegExp(r'[a-z]').hasMatch(password);
    final hasDigits = RegExp(r'[0-9]').hasMatch(password);

    if (!hasUppercase || !hasLowercase || !hasDigits || password.length < 8) {
      _showErrorDialog(
        context,
        'Contraseña débil',
        'La contraseña debe incluir al menos:\n'
            '• 8 caracteres\n'
            '• Una letra mayúscula\n'
            '• Una letra minúscula\n'
            '• Un número\n',
      );
      return;
    }

    // Validación de coincidencia de contraseñas
    if (password != confirmPassword) {
      _showErrorDialog(context, 'Error', 'Las contraseñas no coinciden.');
      return;
    }

    try {
      await authService.signUp(email, password, name, surname);
    } catch (e) {
      // Analizar el error para dar mensajes más específicos
      String errorMessage = e.toString();
      if (errorMessage.contains('email-already-in-use')) {
        errorMessage = 'Este correo electrónico ya está en uso.';
      } else if (errorMessage.contains('invalid-email')) {
        errorMessage = 'El formato del correo electrónico es inválido.';
      } else if (errorMessage.contains('weak-password')) {
        errorMessage = 'La contraseña es demasiado débil.';
      }

      if (!context.mounted) return;
      _showErrorDialog(context, 'Error de registro', errorMessage);
    }
  }

  // Función auxiliar para mostrar diálogos de error
  void _showErrorDialog(BuildContext context, String title, String content) {
    showDialog(
      context: context,
      builder:
          (context) => AlertDialog(
            title: Text(title),
            content: Text(content),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(context).pop(),
                child: Text('Aceptar'),
              ),
            ],
          ),
    );
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
              'Crea una cuenta en FullStyle',
              style: TextStyle(
                color: Theme.of(context).colorScheme.inversePrimary,
                fontSize: 16,
              ),
            ),
            const SizedBox(height: 25),
            AuthTextfield(
              hintText: 'Nombres',
              obscureText: false,
              controller: _nameController,
            ),
            const SizedBox(height: 10),
            AuthTextfield(
              hintText: 'Apellidos',
              obscureText: false,
              controller: _sureNameController,
            ),
            const SizedBox(height: 10),
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
            const SizedBox(height: 10),
            AuthTextfield(
              hintText: 'Confirmar Contraseña',
              obscureText: true,
              controller: _confirmPasswordController,
            ),
            const SizedBox(height: 10),
            AuthButton(
              buttonText: 'Crear Cuenta',
              onTap: () => register(context),
            ),
            const SizedBox(height: 25),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Text(
                  '¿Ya tienes una cuenta? ',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurface,
                  ),
                ),
                GestureDetector(
                  onTap: switchAuthType,
                  child: Text(
                    'Iniciar Sesión',
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
