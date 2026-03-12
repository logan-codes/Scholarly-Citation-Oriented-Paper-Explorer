class ApiConfig {
  // Base URL for the backend API
  static const String _baseUrl = "http://localhost:8000";
  
  // Different URLs for different platforms
  static String get baseUrl {
    // For web and desktop, use localhost
    // For Android emulator, use 10.0.2.2 (special IP to access host machine)
    // For iOS simulator, use 127.0.0.1 or localhost
    // For physical devices, use your computer's IP address on the same network
    
    return _baseUrl;
  }
  
  static String get searchEndpoint => "$baseUrl/search/";
  static String get storageEndpoint => "$baseUrl/storage/";
  
  // For mobile development, you might need to update these:
  // Android Emulator: "http://10.0.2.2:8000"
  // iOS Simulator: "http://127.0.0.1:8000"
  // Physical Device: "http://YOUR_COMPUTER_IP:8000"
}
