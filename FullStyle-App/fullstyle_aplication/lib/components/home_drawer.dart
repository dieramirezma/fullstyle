import 'package:flutter/material.dart';
import 'package:fullstyle_aplication/pages/chatbot_page.dart';
import 'package:fullstyle_aplication/pages/contact_page.dart';
import 'package:fullstyle_aplication/services/auth/auth_service.dart';
import 'package:fullstyle_aplication/pages/settings_page.dart';

class HomeDrawer extends StatelessWidget {
  const HomeDrawer({super.key});

  void logout(BuildContext context) {
    final auth = AuthService();
    auth.signOut();
  }

  @override
  Widget build(BuildContext context) {
    return Drawer(
      backgroundColor: Theme.of(context).colorScheme.surface,
      child: Column(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Column(
            children: [
              DrawerHeader(
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primary,
                ),
                child: Center(
                  child: Image.asset(
                    'assets/images/logo-fullstyle.png',
                    width: 120,
                  ),
                ),
              ),
              ListTile(
                leading: Icon(
                  Icons.home,
                  color: Theme.of(context).colorScheme.onSurface,
                ),
                title: Text(
                  'Inicio',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurface,
                  ),
                ),
                onTap: () {
                  Navigator.pop(context);
                },
              ),
              ListTile(
                leading: Icon(
                  Icons.chat_bubble,
                  color: Theme.of(context).colorScheme.onSurface,
                ),
                title: Text(
                  'ChatBot',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurface,
                  ),
                ),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => ChatbotPage()),
                  );
                },
              ),
              ListTile(
                leading: Icon(
                  Icons.contact_page,
                  color: Theme.of(context).colorScheme.onSurface,
                ),
                title: Text(
                  'Contacto',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurface,
                  ),
                ),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => ContactPage()),
                  );
                },
              ),
            ],
          ),
          Column(
            children: [
              ListTile(
                leading: Icon(
                  Icons.settings,
                  color: Theme.of(context).colorScheme.onSurface,
                ),
                title: Text(
                  'Configuración',
                  style: TextStyle(
                    color: Theme.of(context).colorScheme.onSurface,
                  ),
                ),
                onTap: () {
                  Navigator.pop(context);
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => SettingsPage()),
                  );
                },
              ),
              Padding(
                padding: const EdgeInsets.only(bottom: 20),
                child: ListTile(
                  leading: Icon(
                    Icons.logout,
                    color: Theme.of(context).colorScheme.onSurface,
                  ),
                  title: Text(
                    'Cerrar sesión',
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.onSurface,
                    ),
                  ),
                  onTap: () {
                    Navigator.pop(context);
                    logout(context);
                  },
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
