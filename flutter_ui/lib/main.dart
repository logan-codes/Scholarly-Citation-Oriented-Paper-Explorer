import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const ResearchPaperSearchApp());
}

class ResearchPaperSearchApp extends StatelessWidget {
  const ResearchPaperSearchApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'Research Paper Search',
      theme: ThemeData(
        primarySwatch: Colors.indigo,
      ),
      home: const SearchPage(),
    );
  }
}

class SearchPage extends StatefulWidget {
  const SearchPage({super.key});

  @override
  State<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends State<SearchPage> {
  final TextEditingController _controller = TextEditingController();
  bool _isLoading = false;
  List<dynamic> _results = [];

  /// CHANGE THIS TO YOUR FASTAPI URL
  final String backendUrl = "https://localhost:8000/search"; 
  // Use 10.0.2.2 for Android emulator
  // Use http://localhost:8000 for web

  Future<void> searchPapers(String query) async {
    if (query.isEmpty) return;

    setState(() {
      _isLoading = true;
      _results = [];
    });

    try {
      final response = await http.post(
        Uri.parse(backendUrl),
        headers: {"Content-Type": "application/json"},
        body: jsonEncode({"query": query}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          _results = data["results"];
        });
      } else {
        _showError("Server error: ${response.statusCode}");
      }
    } catch (e) {
      _showError("Failed to connect to backend");
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Research Paper Search"),
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            TextField(
              controller: _controller,
              decoration: InputDecoration(
                hintText: "Search research papers...",
                suffixIcon: IconButton(
                  icon: const Icon(Icons.search),
                  onPressed: () => searchPapers(_controller.text),
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(10),
                ),
              ),
              onSubmitted: searchPapers,
            ),
            const SizedBox(height: 16),
            Expanded(
              child: _isLoading
                  ? const Center(child: CircularProgressIndicator())
                  : _results.isEmpty
                      ? const Center(
                          child: Text(
                            "No results",
                            style: TextStyle(color: Colors.grey),
                          ),
                        )
                      : ListView.builder(
                          itemCount: _results.length,
                          itemBuilder: (context, index) {
                            final paper = _results[index];
                            return PaperCard(paper: paper);
                          },
                        ),
            ),
          ],
        ),
      ),
    );
  }
}

class PaperCard extends StatelessWidget {
  final dynamic paper;

  const PaperCard({super.key, required this.paper});

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 3,
      margin: const EdgeInsets.symmetric(vertical: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              paper["title"] ?? "No Title",
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Text(
              paper["authors"] ?? "Unknown Authors",
              style: const TextStyle(
                fontSize: 13,
                color: Colors.grey,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              paper["abstract"] ?? "No abstract available",
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  "Score: ${paper["score"]?.toStringAsFixed(2) ?? "N/A"}",
                  style: const TextStyle(fontSize: 12),
                ),
                TextButton(
                  onPressed: () {
                    // Open URL later (url_launcher)
                  },
                  child: const Text("View Paper"),
                )
              ],
            )
          ],
        ),
      ),
    );
  }
}
