import 'package:flutter/material.dart';
import 'package:fullstyle_aplication/components/marketing/service_card.dart';
import 'dart:convert';

class ServicesCarousel extends StatefulWidget {
  const ServicesCarousel({super.key});

  @override
  State<ServicesCarousel> createState() => _ServicesCarouselState();
}

class _ServicesCarouselState extends State<ServicesCarousel> {
  final PageController _pageController = PageController(viewportFraction: 0.85);
  List<dynamic> services = [];
  int _currentPage = 0;

  @override
  void initState() {
    super.initState();
    loadServices();
    _pageController.addListener(_onPageChange);
  }

  void _onPageChange() {
    setState(() {
      _currentPage = _pageController.page?.round() ?? 0;
    });
  }

  Future<void> loadServices() async {
    final String jsonString = await DefaultAssetBundle.of(
      context,
    ).loadString('assets/data/services.json');
    final data = json.decode(jsonString);
    setState(() {
      services = data['services'];
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          height: 350,
          child: PageView.builder(
            controller: _pageController,
            itemCount: services.length,
            padEnds: true,
            itemBuilder: (context, index) {
              final service = services[index];
              return Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8.0),
                child: ServiceCard(
                  title: service['title'],
                  description: service['description'],
                  imageUrl: service['imageUrl'],
                  onTap: () {
                    //TODO: Add navigation to the service page
                  },
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 16),
        // Indicadores de página animados
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: List.generate(
            services.length,
            (index) => AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              margin: const EdgeInsets.symmetric(horizontal: 4),
              width: _currentPage == index ? 24 : 8,
              height: 8,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(4),
                color: Theme.of(context).colorScheme.primary.withValues(
                  alpha: _currentPage == index ? 1 : 0.3,
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _pageController.removeListener(_onPageChange);
    _pageController.dispose();
    super.dispose();
  }
}
