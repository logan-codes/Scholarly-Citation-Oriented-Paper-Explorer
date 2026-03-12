import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'config.dart';

void main() {
  runApp(const SCOPEApp());
}

class SCOPEApp extends StatelessWidget {
  const SCOPEApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'SCOPE',
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0D0F16),
        primaryColor: const Color(0xFFF99015),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFFF99015),
          surface: Color(0xFF161A23),
          background: Color(0xFF0D0F16),
        ),
        fontFamily: 'Inter',
      ),
      home: const SplashScreen(),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> with TickerProviderStateMixin {
  late AnimationController _fadeController;
  late AnimationController _scaleController;
  late Animation<double> _fadeAnimation;
  late Animation<double> _scaleAnimation;

  @override
  void initState() {
    super.initState();
    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    
    _scaleController = AnimationController(
      duration: const Duration(milliseconds: 1000),
      vsync: this,
    );
    
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeInOut,
    ));

    _scaleAnimation = Tween<double>(
      begin: 0.8,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _scaleController,
      curve: Curves.elasticOut,
    ));

    _fadeController.forward();
    _scaleController.forward();
    
    Future.delayed(const Duration(seconds: 3), () {
      if (mounted) {
        Navigator.of(context).pushReplacement(
          PageRouteBuilder(
            pageBuilder: (context, animation, secondaryAnimation) => const MainScreen(),
            transitionsBuilder: (context, animation, secondaryAnimation, child) {
              return FadeTransition(opacity: animation, child: child);
            },
            transitionDuration: const Duration(milliseconds: 500),
          ),
        );
      }
    });
  }

  @override
  void dispose() {
    _fadeController.dispose();
    _scaleController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF0D0F16),
      body: Stack(
        children: [
          Positioned.fill(
            child: Opacity(
              opacity: 0.1,
              child: CustomPaint(
                painter: NetworkBackgroundPainter(),
              ),
            ),
          ),
          Center(
            child: FadeTransition(
              opacity: _fadeAnimation,
              child: ScaleTransition(
                scale: _scaleAnimation,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 140,
                      height: 140,
                      decoration: BoxDecoration(
                        color: const Color(0xFF161A23),
                        borderRadius: BorderRadius.circular(30),
                        border: Border.all(color: const Color(0xFF2A2E39)),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withOpacity(0.5),
                            blurRadius: 20,
                            offset: const Offset(0, 10),
                          ),
                        ],
                      ),
                      child: const Icon(
                        Icons.search,
                        size: 80,
                        color: Color(0xFFF99015),
                      ),
                    ),
                    const SizedBox(height: 40),
                    const Text(
                      'SCOPE',
                      style: TextStyle(
                        fontSize: 56,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                        letterSpacing: 4,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 40),
                      child: Text(
                        'Scholarly Citation-Oriented Paper Explorer',
                        style: TextStyle(
                          fontSize: 18,
                          color: const Color(0xFF9CA3AF), // Gray 400
                          fontStyle: FontStyle.italic,
                          height: 1.4,
                        ),
                        textAlign: TextAlign.center,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  final TextEditingController _searchController = TextEditingController();
  bool _isLoading = false;
  List<dynamic> _searchResults = [];
  String _selectedCategory = 'All';
  String _selectedSort = 'Relevance';

  final List<String> _categories = [
    'All', 'Machine Learning', 'Neuroscience', 'Physics', 'Biology', 'Mathematics', 'Computer Science'
  ];

  final List<String> _sortOptions = ['Relevance', 'Trust Score', 'Most Cited', 'Newest'];

  Future<void> searchPapers(String query, {int limit = 10}) async {
    if (query.trim().isEmpty) return;

    setState(() {
      _isLoading = true;
      _searchResults = [];
    });

    try {
      final response = await http.post(
        Uri.parse(ApiConfig.searchEndpoint),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"query": query, "limit": limit}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _searchResults = data["results"] ?? [];
        });
      } else {
        _showError("Server error: ${response.statusCode}");
      }
    } catch (e) {
      _showError("Failed to connect to backend: ${e.toString()}");
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message), backgroundColor: Colors.red[800]),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Background subtle network/constellation effect
          Positioned.fill(
            child: Opacity(
              opacity: 0.1,
              child: CustomPaint(
                painter: NetworkBackgroundPainter(),
              ),
            ),
          ),
          CustomScrollView(
            slivers: [
              _buildAppBar(),
              SliverToBoxAdapter(
                child: _buildHeroSection(),
              ),
              SliverToBoxAdapter(
                child: _buildControlsBar(),
              ),
              if (_isLoading)
                const SliverFillRemaining(
                  child: Center(child: CircularProgressIndicator(color: Color(0xFFF99015))),
                )
              else if (_searchResults.isEmpty)
                 SliverFillRemaining(
                  child: Center(
                    child: Text(
                      'Search to explore papers',
                      style: TextStyle(color: Colors.grey[600], fontSize: 16),
                    ),
                  ),
                )
              else
                SliverPadding(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                  sliver: SliverList(
                    delegate: SliverChildBuilderDelegate(
                      (context, index) {
                        return PaperCard(
                          paper: _searchResults[index],
                          index: index,
                        );
                      },
                      childCount: _searchResults.length,
                    ),
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildAppBar() {
    return SliverAppBar(
      backgroundColor: Colors.transparent,
      pinned: true,
      elevation: 0,
      title: Padding(
        padding: const EdgeInsets.only(left: 16.0),
        child: Row(
          children: [
            const Text(
              'SCOPE',
              style: TextStyle(fontWeight: FontWeight.bold, color: Colors.white, fontSize: 20, letterSpacing: 2),
            ),
          ],
        ),
      ),
      actions: [
        _buildNavButton('Explore'),
        _buildNavButton('Trending'),
        _buildNavButton('About'),
        const SizedBox(width: 32),
      ],
    );
  }

  Widget _buildNavButton(String text) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 8.0),
      child: TextButton(
        onPressed: () {},
        child: Text(
          text,
          style: const TextStyle(color: Color(0xFF9CA3AF), fontSize: 14),
        ),
      ),
    );
  }

  Widget _buildHeroSection() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 80, horizontal: 24),
      child: Column(
        children: [
          RichText(
            textAlign: TextAlign.center,
            text: const TextSpan(
              style: TextStyle(fontSize: 56, fontWeight: FontWeight.bold, color: Colors.white, height: 1.2),
              children: [
                TextSpan(text: 'Explore the frontier of\n'),
                TextSpan(text: 'knowledge', style: TextStyle(color: Color(0xFFF99015))),
              ],
            ),
          ),
          const SizedBox(height: 24),
          const Text(
            'Search millions of research papers across every discipline.',
            style: TextStyle(fontSize: 18, color: Color(0xFF9CA3AF)),
          ),
          const SizedBox(height: 48),
          _buildSearchBar(),
        ],
      ),
    );
  }

  Widget _buildSearchBar() {
    return Container(
      constraints: const BoxConstraints(maxWidth: 800),
      decoration: BoxDecoration(
        color: const Color(0xFF1A1D27), // Dark slightly bluish background
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFF2A2E39)),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: Row(
        children: [
          const Icon(Icons.search, color: Color(0xFF9CA3AF), size: 20),
          const SizedBox(width: 12),
          Expanded(
            child: TextField(
              controller: _searchController,
              style: const TextStyle(color: Colors.white, fontSize: 16),
              decoration: const InputDecoration(
                hintText: 'Search papers, authors, topics...',
                hintStyle: TextStyle(color: Color(0xFF5A6270), fontWeight: FontWeight.normal),
                border: InputBorder.none,
                isDense: true,
              ),
              onSubmitted: (val) => searchPapers(val),
            ),
          ),
          ElevatedButton(
             onPressed: () => searchPapers(_searchController.text),
            style: ElevatedButton.styleFrom(
              backgroundColor: const Color(0xFFF99015),
              foregroundColor: const Color(0xFF1F2937), // Dark text on orange
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              elevation: 0,
            ),
            child: const Text('Search', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14)),
          ),
        ],
      ),
    );
  }

  Widget _buildControlsBar() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1000), // Match approx content width
          child: LayoutBuilder(
            builder: (context, constraints) {
              bool isDesktop = constraints.maxWidth > 800;
              
              if (isDesktop) {
                 return Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: _categories.map((c) => _buildCategoryBadge(c)).toList(),
                      ),
                    ),
                    const SizedBox(width: 16),
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.center,
                      children: [
                        const Icon(Icons.swap_vert, color: Color(0xFF5A6270), size: 18), // Sort icon
                        const SizedBox(width: 8),
                        ..._sortOptions.map((s) => _buildSortBadge(s)),
                      ],
                    )
                  ],
                );
              }
              
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _categories.map((c) => _buildCategoryBadge(c)).toList(),
                  ),
                  const SizedBox(height: 16),
                   Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      const Icon(Icons.swap_vert, color: Color(0xFF5A6270), size: 18),
                      const SizedBox(width: 4),
                      ..._sortOptions.map((s) => _buildSortBadge(s)),
                    ],
                  )
                ],
              );
            },
          )
        ),
      ),
    );
  }

  Widget _buildCategoryBadge(String category) {
    bool isSelected = _selectedCategory == category;
    return InkWell(
      onTap: () => setState(() => _selectedCategory = category),
      borderRadius: BorderRadius.circular(20),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? const Color(0xFFF99015) : const Color(0xFF242936),
          borderRadius: BorderRadius.circular(20),
        ),
        child: Text(
          category,
          style: TextStyle(
            color: isSelected ? const Color(0xFF0D0F16) : const Color(0xFFD1D5DB),
            fontSize: 13,
            fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
          ),
        ),
      ),
    );
  }

  Widget _buildSortBadge(String sort) {
    bool isSelected = _selectedSort == sort;
    return Padding(
      padding: const EdgeInsets.only(left: 8),
      child: InkWell(
        onTap: () => setState(() => _selectedSort = sort),
        borderRadius: BorderRadius.circular(20),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          decoration: BoxDecoration(
            color: isSelected ? const Color(0xFFF99015) : const Color(0xFF242936),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
               color: isSelected ? Colors.transparent : Colors.transparent
            )
          ),
          child: Text(
            sort,
            style: TextStyle(
              color: isSelected ? const Color(0xFF0D0F16) : const Color(0xFFD1D5DB),
              fontSize: 13,
              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
            ),
          ),
        ),
      ),
    );
  }
}

class PaperCard extends StatefulWidget {
  final dynamic paper;
  final int index;

  const PaperCard({super.key, required this.paper, required this.index});

  @override
  State<PaperCard> createState() => _PaperCardState();
}

class _PaperCardState extends State<PaperCard> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final title = widget.paper["title"] ?? "No Title";
    
    // Extract authors safely
    final rawAuthors = widget.paper["authors"];
    String authors = "Unknown Authors";
    if (rawAuthors is List) {
      authors = rawAuthors.join(", ");
    } else if (rawAuthors is String) {
      authors = rawAuthors;
    }
    
    final venue = widget.paper["venue"] ?? "Various";
    final year = widget.paper["year"]?.toString() ?? "N/A";
    final citationCount = widget.paper["citation_count"]?.toString() ?? "0";
    final abstract = widget.paper["abstract"] ?? "No abstract available.";
    
    final displayAuthors = authors.length > 100 ? '${authors.substring(0, 100)}...' : authors;

    // Simulate different categories based on index just for visuals
    final cats = ['Machine Learning', 'Computer Science', 'Biology', 'Physics'];
    final category = cats[widget.index % cats.length];

    return Center(
      child: Container(
        constraints: const BoxConstraints(maxWidth: 1000), // Max width of cards
        margin: const EdgeInsets.only(bottom: 16),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onHover: (val) => setState(() => _isHovered = val),
            onTap: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (context) => PaperDetailPage(paper: widget.paper, category: category),
                ),
              );
            },
            borderRadius: BorderRadius.circular(12),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 200),
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: const Color(0xFF161A23),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: _isHovered ? const Color(0xFFF99015) : const Color(0xFF2A2E39),
                  width: _isHovered ? 1.5 : 1.0,
                ),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Number column
            SizedBox(
              width: 40,
              child: Text(
                '${widget.index + 1}',
                style: const TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF374151), // Dark gray
                ),
              ),
            ),
            
            // Main Content
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Category tag top
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: const Color(0xFF242936),
                      borderRadius: BorderRadius.circular(16),
                    ),
                    child: Text(
                      category,
                      style: const TextStyle(color: Color(0xFFD1D5DB), fontSize: 11, fontWeight: FontWeight.w500),
                    ),
                  ),
                  const SizedBox(height: 12),
                  
                  // Title
                  Text(
                    title,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: Colors.white,
                    ),
                  ),
                  const SizedBox(height: 8),
                  
                  // Authors
                  Text(
                    displayAuthors,
                    style: const TextStyle(
                      fontSize: 14,
                      color: Color(0xFF9CA3AF), // Gray 400
                    ),
                  ),
                  const SizedBox(height: 12),
                  
                  // Abstract snippet
                  Text(
                    abstract,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 14,
                      color: Color(0xFF6B7280), // Gray 500
                      height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 16),
                  
                  // Bottom row metrics
                  Wrap(
                    spacing: 16,
                    runSpacing: 8,
                    children: [
                      _buildMetric(Icons.calendar_today, year),
                      _buildMetric(Icons.format_quote, citationCount),
                      _buildMetric(Icons.auto_stories, venue),
                       // Added Trust Score manually to emulate the screenshot
                      _buildTrustScore('97%'),
                    ],
                  ),
                ],
              ),
            ),
            
            // Action Buttons (Right)
            if (MediaQuery.of(context).size.width > 600) ...[
              const SizedBox(width: 24),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  ElevatedButton.icon(
                    onPressed: () {},
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFF99015),
                      foregroundColor: const Color(0xFF0D0F16),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                    ),
                    icon: const Icon(Icons.open_in_new, size: 16),
                    label: const Text('Source', style: TextStyle(fontWeight: FontWeight.bold)),
                  ),
                  const SizedBox(height: 12),
                  ElevatedButton.icon(
                    onPressed: () {},
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF2B303B),
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                      elevation: 0,
                    ),
                    icon: const Icon(Icons.download, size: 16),
                    label: const Text('PDF'),
                  ),
                ],
              )
            ]
          ],
        ),
      ),
    ))));
  }

  Widget _buildMetric(IconData icon, String text) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: const Color(0xFF6B7280)),
        const SizedBox(width: 4),
        Text(
          text,
          style: const TextStyle(
            fontSize: 13,
            color: Color(0xFF9CA3AF),
          ),
        ),
      ],
    );
  }

  Widget _buildTrustScore(String score) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        const Icon(Icons.verified_user_outlined, size: 14, color: Color(0xFF10B981)),
        const SizedBox(width: 4),
        Text(
          score,
          style: const TextStyle(
            fontSize: 13,
            color: Color(0xFF10B981),
            fontWeight: FontWeight.w600,
          ),
        ),
      ],
    );
  }
}

// A simple custom painter to draw connected nodes in the background
// to emulate the "network" look from the second screenshot
class NetworkBackgroundPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white
      ..strokeWidth = 1.0
      ..style = PaintingStyle.fill;
      
    final linePaint = Paint()
      ..color = Colors.white.withOpacity(0.5)
      ..strokeWidth = 0.5
      ..style = PaintingStyle.stroke;

    // A few static points mapping roughly across typical window bounds
    final points = [
      const Offset(100, 100),
      const Offset(250, 150),
      const Offset(400, 80),
      const Offset(150, 300),
      const Offset(350, 280),
      const Offset(600, 200),
      const Offset(700, 350),
      const Offset(800, 100),
      const Offset(900, 250),
      const Offset(500, 400),
      const Offset(200, 500),
      const Offset(100, 400),
    ];

    // Scale them to size loosely
    final mappedPoints = points.map((p) => Offset(p.dx * (size.width / 1000).clamp(0.5, 2.0), p.dy * (size.height / 600).clamp(0.5, 2.0))).toList();

    for (int i = 0; i < mappedPoints.length; i++) {
       canvas.drawCircle(mappedPoints[i], 3, paint);
       for (int j = i + 1; j < mappedPoints.length; j++) {
         double dist = (mappedPoints[i] - mappedPoints[j]).distance;
         if (dist < 300) {
           canvas.drawLine(mappedPoints[i], mappedPoints[j], linePaint);
         }
       }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class PaperDetailPage extends StatelessWidget {
  final dynamic paper;
  final String category;

  const PaperDetailPage({super.key, required this.paper, required this.category});

  @override
  Widget build(BuildContext context) {
    final title = paper["title"] ?? "No Title";
    
    // Extract authors safely
    final rawAuthors = paper["authors"];
    String authors = "Unknown Authors";
    if (rawAuthors is List) {
      authors = rawAuthors.join(", ");
    } else if (rawAuthors is String) {
      authors = rawAuthors;
    }
    
    final venue = paper["venue"] ?? "Various";
    final year = paper["year"]?.toString() ?? "N/A";
    final citationCount = paper["citation_count"]?.toString() ?? "0";
    final abstract = paper["abstract"] ?? "No abstract available.";
    
    return Scaffold(
      backgroundColor: const Color(0xFF0D0F16),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: Stack(
        children: [
          Positioned.fill(
            child: Opacity(
              opacity: 0.1,
              child: CustomPaint(
                painter: NetworkBackgroundPainter(),
              ),
            ),
          ),
          SingleChildScrollView(
            padding: const EdgeInsets.all(24.0),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 1000),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                      decoration: BoxDecoration(
                        color: const Color(0xFF242936),
                        borderRadius: BorderRadius.circular(16),
                      ),
                      child: Text(
                        category,
                        style: const TextStyle(color: Color(0xFFD1D5DB), fontSize: 11, fontWeight: FontWeight.w500),
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                        height: 1.2,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      authors,
                      style: const TextStyle(
                        fontSize: 16,
                        color: Color(0xFF9CA3AF),
                      ),
                    ),
                    const SizedBox(height: 24),
                    Wrap(
                      spacing: 24,
                      runSpacing: 12,
                      children: [
                        _DetailMetric(icon: Icons.calendar_today, label: 'Year', value: year),
                        _DetailMetric(icon: Icons.format_quote, label: 'Citations', value: citationCount),
                        _DetailMetric(icon: Icons.auto_stories, label: 'Venue', value: venue),
                        const _DetailMetric(icon: Icons.verified_user_outlined, label: 'Trust Score', value: '97%', color: Color(0xFF10B981)),
                      ],
                    ),
                    const SizedBox(height: 48),
                    const Text(
                      'Abstract',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      abstract,
                      style: const TextStyle(
                        fontSize: 16,
                        color: Color(0xFFD1D5DB),
                        height: 1.6,
                      ),
                    ),
                    const SizedBox(height: 48),
                    const Text(
                      'Raw Server Data',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Colors.white,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: const Color(0xFF161A23),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFF2A2E39)),
                      ),
                      child: SelectableText(
                        const JsonEncoder.withIndent('  ').convert(paper),
                        style: const TextStyle(
                          color: Color(0xFF9CA3AF),
                          fontFamily: 'monospace',
                          fontSize: 13,
                        ),
                      ),
                    ),
                    const SizedBox(height: 48),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _DetailMetric extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;
  final Color? color;

  const _DetailMetric({required this.icon, required this.label, required this.value, this.color});

  @override
  Widget build(BuildContext context) {
    final displayColor = color ?? const Color(0xFF6B7280);
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 20, color: displayColor),
        const SizedBox(width: 8),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              label,
              style: TextStyle(fontSize: 12, color: displayColor),
            ),
            Text(
              value,
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: color ?? Colors.white),
            ),
          ],
        ),
      ],
    );
  }
}

