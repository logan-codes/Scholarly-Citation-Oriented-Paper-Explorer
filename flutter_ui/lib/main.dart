import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';
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

  Future<void> searchPapers(String query, {int limit = 100}) async {
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
              // SliverToBoxAdapter(
              //   child: _buildControlsBar(),
              // ),
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

  // Removed unused controls bar
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
    final rawAuthors = widget.paper["authors"];
    String authorsStr = "Unknown Authors";
    if (rawAuthors is List) {
      authorsStr = rawAuthors
          .map((a) => a is Map ? (a["name"] ?? "Unknown") : a.toString())
          .join(", ");
    } else if (rawAuthors is String) {
      authorsStr = rawAuthors;
    }

    final venue = widget.paper["venue"] ?? "Various";
    final year = widget.paper["year"]?.toString() ?? "N/A";
    final citationCount = widget.paper["citation_count"]?.toString() ?? "0";
    final abstract = widget.paper["abstract"] ?? "No abstract available.";
    final contribution = widget.paper["contribution"] ?? "";
    final doi = widget.paper["doi"] ?? "";

    final displayAuthors =
        authorsStr.length > 100 ? '${authorsStr.substring(0, 100)}...' : authorsStr;

    final List<dynamic> fields = widget.paper["fields"] ?? [];
    final double trustScore = (widget.paper["final_score"] ?? 0.0) * 100;
    final String trustScoreStr = trustScore.toStringAsFixed(1) + "%";

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
                  builder: (context) => PaperDetailPage(paper: widget.paper),
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
                        // Category tags top
                        if (fields.isNotEmpty)
                          Wrap(
                            spacing: 8,
                            runSpacing: 4,
                            children: fields.take(3).map((f) => Container(
                              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color: const Color(0xFF242936),
                                borderRadius: BorderRadius.circular(16),
                              ),
                              child: Text(
                                f.toString(),
                                style: const TextStyle(color: Color(0xFFD1D5DB), fontSize: 10, fontWeight: FontWeight.w500),
                              ),
                            )).toList(),
                          ),
                        const SizedBox(height: 12),

                        // Title
                        Text(
                          widget.paper['title'] ?? 'No Title',
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
                        
                        if (contribution.isNotEmpty) ...[
                          const SizedBox(height: 12),
                          Text(
                            "Contribution: $contribution",
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 13,
                              color: Color(0xFFF99015),
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                        ],
                        
                        const SizedBox(height: 16),

                        // Bottom row metrics
                        Wrap(
                          spacing: 16,
                          runSpacing: 8,
                            children: [
                              _buildMetric(Icons.calendar_today, year),
                              _buildMetric(Icons.format_quote, citationCount),
                              _buildMetric(Icons.auto_stories, venue),
                              if (doi.isNotEmpty) _buildMetric(Icons.link, doi.toString().replaceFirst("https://doi.org/", "")),
                              _buildTrustScore(trustScoreStr),
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
                    onPressed: () {
                      if (doi.isNotEmpty) {
                        final url = doi.toString().startsWith("http") ? doi.toString() : "https://doi.org/$doi";
                        Clipboard.setData(ClipboardData(text: url));
                        ScaffoldMessenger.of(context).hideCurrentSnackBar();
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(
                            content: Text("Copied DOI URL", textAlign: TextAlign.center),
                            duration: Duration(seconds: 1),
                            behavior: SnackBarBehavior.floating,
                            width: 180,
                          ),
                        );
                        launchUrl(Uri.parse(url));
                      }
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFF99015),
                      foregroundColor: const Color(0xFF0D0F16),
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                    ),
                    icon: const Icon(Icons.open_in_new, size: 16),
                    label: const Text('Source', style: TextStyle(fontWeight: FontWeight.bold)),
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

  const PaperDetailPage({super.key, required this.paper});

  @override
  Widget build(BuildContext context) {
    final title = paper["title"] ?? "No Title";

    // Extract authors safely
    final rawAuthors = paper["authors"];
    final List<Map<String, dynamic>> authors = [];
    if (rawAuthors is List) {
      for (var a in rawAuthors) {
        if (a is Map) {
          authors.add({
            "name": a["name"] ?? "Unknown",
            "openalex_id": a["openalex_id"] ?? "N/A",
          });
        }
      }
    }

    final venue = paper["venue"] ?? "Various";
    final year = paper["year"]?.toString() ?? "N/A";
    final citationCount = paper["citation_count"]?.toString() ?? "0";
    final abstract = paper["abstract"] ?? "No abstract available.";
    final contribution = paper["contribution"] ?? "";
    final List<dynamic> fields = paper["fields"] ?? [];
    final doi = paper["doi"] ?? "";

    final double trustScoreValue = (paper["final_score"] ?? 0.0) * 100;
    final String trustScoreStr = trustScoreValue.toStringAsFixed(1) + "%";

    final double relevancyScore = paper["relevancy_score"] ?? 0.0;
    final double bm25Score = paper["B25_score"] ?? 0.0;
    final double prScore = paper["pr_score"] ?? 0.0;
    final double velocityScore = paper["velocity_score"] ?? 0.0;

    return Scaffold(
      backgroundColor: const Color(0xFF0D0F16),
      appBar: AppBar(
        backgroundColor: Colors.transparent,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text('Paper Details', style: TextStyle(color: Colors.white, fontSize: 18)),
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
                    if (fields.isNotEmpty)
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: fields.map((f) => Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: const Color(0xFF242936),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Text(
                            f.toString(),
                            style: const TextStyle(color: Color(0xFFD1D5DB), fontSize: 11, fontWeight: FontWeight.w500),
                          ),
                        )).toList(),
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
                    Wrap(
                      spacing: 24,
                      runSpacing: 12,
                      children: [
                        _DetailMetric(icon: Icons.calendar_today, label: 'Year', value: year),
                        _DetailMetric(icon: Icons.format_quote, label: 'Citations', value: citationCount),
                        _DetailMetric(icon: Icons.auto_stories, label: 'Venue', value: venue),
                        if (doi.isNotEmpty) _DetailMetric(icon: Icons.link, label: 'DOI', value: doi.toString().replaceFirst("https://doi.org/", "")),
                        _DetailMetric(icon: Icons.verified_user_outlined, label: 'Trust Score', value: trustScoreStr, color: const Color(0xFF10B981)),
                      ],
                    ),
                    const SizedBox(height: 24),
                    ElevatedButton.icon(
                      onPressed: () {
                        if (doi.isNotEmpty) {
                          final url = doi.toString().startsWith("http") ? doi.toString() : "https://doi.org/$doi";
                          Clipboard.setData(ClipboardData(text: url));
                          ScaffoldMessenger.of(context).hideCurrentSnackBar();
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(
                              content: Text("Copied DOI URL", textAlign: TextAlign.center),
                              duration: Duration(seconds: 1),
                              behavior: SnackBarBehavior.floating,
                              width: 180,
                            ),
                          );
                          launchUrl(Uri.parse(url));
                        }
                      },
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFF99015),
                        foregroundColor: const Color(0xFF0D0F16),
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(30)),
                      ),
                      icon: const Icon(Icons.open_in_new),
                      label: const Text('View Source', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                    ),
                    const SizedBox(height: 32),
                    
                    // Detailed Scores Section
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        color: const Color(0xFF161A23),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: const Color(0xFF2A2E39)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Ranking Metrics',
                            style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                          const SizedBox(height: 16),
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              _ScoreInfo(label: 'Relevancy', value: relevancyScore.toStringAsFixed(3)),
                              _ScoreInfo(label: 'BM25', value: bm25Score.toStringAsFixed(2)),
                              _ScoreInfo(label: 'PageRank', value: prScore.toStringAsFixed(4)),
                              _ScoreInfo(label: 'Velocity', value: velocityScore.toStringAsFixed(2)),
                            ],
                          ),
                        ],
                      ),
                    ),
                    
                    const SizedBox(height: 48),
                    if (contribution.isNotEmpty) ...[
                      const Text(
                        'Key Contribution',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 16),
                      Text(
                        contribution,
                        style: const TextStyle(
                          fontSize: 16,
                          color: Color(0xFFF99015),
                          height: 1.6,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                      const SizedBox(height: 32),
                    ],
                    
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
                      'Authors',
                      style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold, color: Colors.white),
                    ),
                    const SizedBox(height: 16),
                    Wrap(
                      spacing: 12,
                      runSpacing: 12,
                      children: authors.map((author) => Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                        decoration: BoxDecoration(
                          color: const Color(0xFF161A23),
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: const Color(0xFF2A2E39)),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              author["name"],
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                                color: Colors.white,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              "Author ID: ${author["openalex_id"]}",
                              style: const TextStyle(
                                fontSize: 11,
                                color: Color(0xFF9CA3AF),
                              ),
                            ),
                          ],
                        ),
                      )).toList(),
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

class _ScoreInfo extends StatelessWidget {
  final String label;
  final String value;

  const _ScoreInfo({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 11, color: Color(0xFF6B7280)),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: const TextStyle(fontSize: 14, fontWeight: FontWeight.bold, color: Colors.white),
        ),
      ],
    );
  }
}
