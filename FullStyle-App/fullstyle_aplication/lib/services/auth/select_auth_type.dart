import 'package:flutter/material.dart';
import 'package:fullstyle_aplication/pages/login_page.dart';
import 'package:fullstyle_aplication/pages/register_page.dart';

class SelectAuthType extends StatefulWidget {
  const SelectAuthType({super.key});

  @override
  State<SelectAuthType> createState() => _SelectAuthTypeState();
}

class _SelectAuthTypeState extends State<SelectAuthType> {
  bool showLogin = true;

  void toggleAuthType() {
    setState(() {
      showLogin = !showLogin;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (showLogin) {
      return LoginPage(switchAuthType: toggleAuthType);
    } else {
      return RegisterPage(switchAuthType: toggleAuthType);
    }
  }
}
