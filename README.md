# CropSense - John Deere Hackathon Frontend

CropSense is a Flutter application that helps farmers identify crop diseases from field photos and symptom descriptions. The app combines image input, voice/text interaction, geolocation-aware context, and AI-driven diagnosis, then presents treatment recommendations and generates a shareable PDF report.

## Key Features

- AI-assisted disease diagnosis from farmer issue text + optional crop image
- Weather and location context integrated into diagnosis flow
- Voice input (speech-to-text) for farmer-friendly interaction
- Text-to-speech playback for response accessibility
- Structured treatment guidance with confidence indicators
- PDF diagnosis report generation and document preview
- History and chat-style interaction flow
- Additional consortium/LLM analysis route for deeper results

## Tech Stack

- Flutter (Dart)
- Riverpod for state management
- GoRouter for app navigation
- `http` for backend communication
- `geolocator` + `geocoding` for location services
- `speech_to_text` + `flutter_tts` for voice UX
- `pdf` + `printing` for report generation and export

## Project Structure

```text
lib/
	main.dart                    # App bootstrap + theming
	models/                      # Data models (chat, diagnosis, etc.)
	providers/                   # Riverpod providers and state notifiers
	router/app_router.dart       # Route map and navigation setup
	screens/                     # UI screens (home, chat, history, docs, etc.)
	services/                    # API, location, PDF, TTS service layer
	theme/                       # App theme definitions
	widgets/                     # Reusable UI components
```

## Prerequisites

- Flutter SDK (3.11+ recommended based on project constraints)
- Xcode + CocoaPods for iOS builds
- A running backend endpoint for diagnosis APIs

## Setup

1. Clone the repository and open the project root:

```bash
cd CropSense_JohnDeere
```

2. Install dependencies:

```bash
flutter pub get
```

3. Configure backend URL in `lib/services/api_service.dart`:

- Update `ApiService.baseUrl` to your active backend/ngrok endpoint.
- Verify additional endpoints in the same file (for example consortium analysis) are reachable.

4. Run the app:

```bash
flutter run
```

## API Configuration Notes

The app currently uses URL constants directly in `lib/services/api_service.dart`. Before demoing or deployment:

- Replace temporary ngrok URLs with stable environment-specific endpoints
- Keep endpoint paths aligned with backend contracts:
	- `POST /detect_crop_disease`
	- `POST /llm_consortium`
	- Other helper endpoints used by the service

## iOS Notes

- Ensure CocoaPods dependencies are installed (`ios/Pods`)
- If location or microphone permissions fail, verify iOS plist permission entries and runtime permission handling

## Useful Commands

```bash
flutter analyze
flutter test
flutter run -d ios
```

## Future Improvements

- Move API URLs to environment configuration (`--dart-define` or config service)
- Add stronger error handling and offline fallback UX
- Expand unit and widget test coverage for providers and services
- Add CI checks for format, analyze, and tests

## License

This project is provided under the license specified in `LICENSE`.
