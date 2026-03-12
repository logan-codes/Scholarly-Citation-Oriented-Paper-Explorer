# Flutter App Connection to Docker Server

## Quick Setup

1. **Start the Docker server:**
   ```bash
   cd server
   docker-compose up --build
   ```

2. **Run the Flutter app:**
   ```bash
   cd flutter_ui
   flutter run
   ```

## Connection Configuration

The Flutter app now uses a centralized configuration in `lib/config.dart`. Update the `baseUrl` based on your target platform:

### Web/Desktop
- Uses `http://localhost:8000` ✅ (works out of the box)

### Android Emulator
- Change `baseUrl` in `config.dart` to `"http://10.0.2.2:8000"`
- `10.0.2.2` is the special IP that Android emulator uses to access the host machine

### iOS Simulator  
- Change `baseUrl` in `config.dart` to `"http://127.0.0.1:8000"`
- Or keep `http://localhost:8000`

### Physical Mobile Device
1. Find your computer's IP address:
   - **Windows**: `ipconfig` (look for IPv4 Address)
   - **Mac/Linux**: `ifconfig` or `ip addr`
2. Update `baseUrl` to `"http://YOUR_COMPUTER_IP:8000"`
3. Ensure your mobile device and computer are on the same WiFi network

## Testing the Connection

1. Start the Docker server
2. Run the Flutter app
3. Try searching for papers
4. Check the server logs: `docker-compose logs -f server`

## Troubleshooting

**Connection refused?**
- Ensure Docker server is running: `docker-compose ps`
- Check server logs: `docker-compose logs server`

**Network timeout?**
- Verify firewall isn't blocking port 8000
- For mobile devices, ensure same WiFi network
- Check IP address configuration

**CORS issues?**
- The FastAPI server should handle CORS for mobile requests
- If needed, add CORS middleware to the server
