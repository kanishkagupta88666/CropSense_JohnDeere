# CropSense - John Deere Hackathon

AI-powered crop disease diagnosis system built at the UIUC Precision Digital Agriculture Hackathon 2026. CropSense helps farmers identify crop diseases through an intuitive mobile app that combines computer vision, real-time weather data, and multi-model AI consensus for accurate, actionable diagnosis and treatment recommendations.

## Overview

CropSense integrates three specialized components:

- **Flutter Mobile App (Frontend)**: Farmer-friendly interface with voice input, photo capture, and PDF report generation
- **FastAPI Orchestration Layer (Backend)**: Coordinates diagnosis pipeline, manages sessions, and integrates external services
- **ML Disease Detection (MLBackend)**: Multi-agent LLM council, VGG16 vision model, and CropWizard RAG system

The system processes crop images, farmer descriptions, and geolocation context to deliver comprehensive disease diagnosis with confidence scoring and treatment guidance.

---

## Architecture
```
┌─────────────────┐
│  Flutter App    │ ← Voice/text input, camera, GPS
│  (Frontend)     │ → PDF reports, TTS playback
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FastAPI        │ ← Session mgmt, orchestration
│  (Backend)      │ → Supabase upload, field conditions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ML Pipeline    │ ← VGG16 CNN, LLM council
│  (MLBackend)    │ → CropWizard RAG, weather context
└─────────────────┘
```

---

## Features

### Core Capabilities
- **Multimodal Input**: Photo upload + voice/text symptom description
- **Geolocation-Aware**: Real-time weather and soil conditions via Open-Meteo
- **Hybrid AI Diagnosis**:
  - Traditional ML: VGG16-based disease classification
  - LLM Diagnosis: CropWizard RAG system with field context
  - Multi-Model Council: Consensus from multiple LLMs (Gemma, Qwen, etc.)
- **Farmer-Friendly UX**:
  - Speech-to-text input
  - Text-to-speech response playback
  - Structured treatment recommendations
  - Shareable PDF diagnostic reports
- **Session Management**: Persistent diagnosis history and chat flow

### Technical Highlights
- Confidence scoring for all predictions
- Parallel LLM council evaluation
- Signed Supabase URLs for secure image handling
- Swagger API documentation at `/docs`

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | Flutter, Dart, Riverpod, GoRouter, `geolocator`, `speech_to_text`, `flutter_tts`, `pdf` |
| **Backend** | Python, FastAPI, Requests, Pydantic, python-dotenv |
| **MLBackend** | VGG16 (TensorFlow/Keras), Multi-agent LLM council, CropWizard RAG |
| **Infrastructure** | Supabase (storage), Open-Meteo (weather), ngrok (dev tunneling) |

---

## Repository Structure
```text
CropSense_JohnDeere/
│
├── frontend/                    # Flutter mobile application
│   ├── lib/
│   │   ├── main.dart           # App bootstrap
│   │   ├── models/             # Data models
│   │   ├── providers/          # Riverpod state management
│   │   ├── router/             # GoRouter navigation
│   │   ├── screens/            # UI screens
│   │   ├── services/           # API, location, PDF, TTS services
│   │   ├── theme/              # App theming
│   │   └── widgets/            # Reusable components
│   └── pubspec.yaml
│
├── backend/                     # FastAPI orchestration layer
│   ├── main.py                 # FastAPI app entry
│   ├── prompts.py              # LLM prompt templates
│   ├── routes/
│   │   ├── detect_crop_disease.py    # Main diagnosis pipeline
│   │   ├── llm_council.py            # Multi-model council
│   │   ├── supabase_upload.py        # Image storage
│   │   ├── traditional_ml_prediction.py
│   │   └── tools/
│   │       └── get_field_conditions.py
│   ├── files/                  # Session JSON storage
│   ├── llm-council-files/      # Council output logs
│   └── requirements.txt
│
└── mlbackend/                   # ML models and training
    ├── VGG16 model files       # Traditional CV model
    └── LLM council configs     # Multi-agent setup
```

---

## Getting Started

### Prerequisites
- **Flutter SDK** 3.11+
- **Python** 3.8+
- **Xcode + CocoaPods** (iOS)
- **Supabase** project with storage bucket
- **API Keys**: CropWizard, LLM providers (if using council)

### 1. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cat > .env << EOF
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_key
SUPABASE_BUCKET=crop-images
SUPABASE_FOLDER=uploads
SUPABASE_SIGNED_URL_EXPIRES_IN=3600
SUPABASE_BUCKET_PUBLIC=true
EOF

# Run server
uvicorn main:app --reload
```

**Backend will be available at:**
- API: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup
```bash
cd frontend

# Install dependencies
flutter pub get

# Update API endpoint in lib/services/api_service.dart
# Replace temporary URLs with your backend URL

# Run app
flutter run
```

**iOS Notes:**
- Ensure `ios/Pods` dependencies are installed
- Verify location/microphone permissions in `Info.plist`

### 3. MLBackend Setup

The ML models are called via the backend routes. Ensure:
- VGG16 model files are accessible to `traditional_ml_prediction.py`
- LLM council API keys are configured in `llm_council.py`
- External ML prediction endpoint is reachable (currently hardcoded ngrok URL)

---

## API Reference

### Key Endpoints

#### `POST /detect_crop_disease`
**Main diagnosis orchestration endpoint**

**Request:**
```json
{
  "imagebase64": "data:image/jpeg;base64,...",
  "location": {
    "latitude": 40.1123,
    "longitude": -88.2432
  },
  "farmers_issue_description": "Yellow-brown spots on leaves"
}
```

**Response:**
```json
{
  "session_id": "06a535216c01...",
  "supabase_url": "https://...",
  "field_conditions": {...},
  "llm_diagnosis": {...},
  "ml_prediction": {...}
}
```

**Process flow:**
1. Upload image to Supabase
2. Fetch weather/soil conditions
3. Run LLM diagnosis (CropWizard)
4. Run traditional ML prediction (VGG16)
5. Save combined result to `files/<session_id>.json`

#### `POST /llm_consortium`
**Multi-model LLM council for consensus diagnosis**

**Request (session-based):**
```json
{
  "session_id": "06a535216c01..."
}
```

**Request (question-based):**
```json
{
  "user_question": "What should I do in the next 7 days?"
}
```

**Response:**
```json
{
  "best_model": "Qwen/Qwen2.5-VL-72B-Instruct",
  "best_response": "...",
  "all_outputs": {
    "gemma3:27b": {"response": "...", "score": 7.0},
    "Qwen/Qwen2.5-VL-72B-Instruct": {"response": "...", "score": 10.0}
  }
}
```

### Additional Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health-check` | GET | Service health status |
| `/supabase/upload-image` | POST | Direct image upload |
| `/get_field_conditions` | POST | Weather/soil data retrieval |
| `/send_crop_img` | POST | Direct CropWizard diagnosis |
| `/traditional_ml_prediction` | POST | VGG16 disease classification |

Full API documentation: `http://127.0.0.1:8000/docs`

---

## Data Artifacts

### Session Files (`backend/files/`)
```json
{
  "session_id": "06a535216c01...",
  "timestamp": "2026-03-08T14:32:00",
  "image_url": "https://...",
  "location": {"latitude": 40.1123, "longitude": -88.2432},
  "farmer_description": "...",
  "field_conditions": {...},
  "llm_diagnosis": {...},
  "ml_prediction": {...}
}
```

### LLM Council Logs (`backend/llm-council-files/`)
```json
{
  "gemma3:27b": {
    "response": "Diagnosis...",
    "is_best": false,
    "score": 7.0
  },
  "Qwen/Qwen2.5-VL-72B-Instruct": {
    "response": "Treatment...",
    "is_best": true,
    "score": 10.0
  }
}
```

---

## Configuration Notes

### Environment Variables (Backend)
```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_BUCKET=crop-images
SUPABASE_FOLDER=uploads
SUPABASE_SIGNED_URL_EXPIRES_IN=3600
SUPABASE_BUCKET_PUBLIC=true

# External APIs (move from hardcoded values)
CROPWIZARD_API_KEY=your-key
TRADITIONAL_ML_ENDPOINT=https://your-ml-service.ngrok-free.app
```

### Frontend API Configuration
Update `lib/services/api_service.dart`:
```dart
class ApiService {
  static const String baseUrl = 'http://your-backend-url:8000';
  // ...
}
```

**Production checklist:**
- [ ] Replace all ngrok URLs with stable endpoints
- [ ] Move API keys from hardcoded values to env vars
- [ ] Enable HTTPS for all services
- [ ] Configure CORS policies
- [ ] Set up proper error logging

---

## Development Workflow

### Running All Services Locally

**Terminal 1: Backend**
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload
```

**Terminal 2: Frontend**
```bash
cd frontend
flutter run -d ios  # or android
```

**Terminal 3: ML Service** (if running separately)
```bash
cd mlbackend
# Follow MLBackend-specific setup
```

### Useful Commands
```bash
# Backend
python -m pytest              # Run tests
python -m black .             # Format code
python -m flake8              # Lint

# Frontend
flutter analyze               # Static analysis
flutter test                  # Run tests
flutter run -d ios --release  # Release build
```

---

## Deployment Considerations

### Backend
- Use **Gunicorn/Uvicorn** with workers for production
- Store secrets in environment variables or secret manager
- Set up **HTTPS** and **CORS** properly
- Implement rate limiting for external API calls
- Monitor `files/` and `llm-council-files/` disk usage

### Frontend
- Configure **environment-specific** API URLs (`--dart-define`)
- Implement offline fallback for network issues
- Add analytics/crash reporting (Firebase, Sentry)
- Test on multiple iOS/Android versions

### MLBackend
- Containerize models (Docker)
- Use GPU instances for inference
- Implement model versioning
- Cache frequent predictions

---

## Future Improvements

### Technical
- [ ] Move all API URLs to centralized config service
- [ ] Add comprehensive unit/integration tests
- [ ] Implement CI/CD pipeline (GitHub Actions)
- [ ] Add request/response validation middleware
- [ ] Set up centralized logging (ELK, CloudWatch)
- [ ] Implement database for session persistence (PostgreSQL)

### Features
- [ ] Multi-language support (i18n)
- [ ] Offline diagnosis with cached models
- [ ] Historical trend analysis per farm
- [ ] Integration with John Deere Operations Center
- [ ] Push notifications for treatment reminders
- [ ] Community forum for farmers

### UX
- [ ] Onboarding tutorial flow
- [ ] Dark mode theme
- [ ] Accessibility improvements (screen readers)
- [ ] Expanded PDF report customization

---

## Troubleshooting

### Common Issues

**"Connection refused" when frontend calls backend:**
- Verify backend is running on expected port
- Check firewall/network settings
- Use correct IP if testing on physical device (not `localhost`)

**"Permission denied" for location/microphone:**
- iOS: Check `Info.plist` permission keys
- Android: Verify runtime permission handling

**Supabase upload fails:**
- Verify `.env` credentials are correct
- Check bucket exists and is accessible
- Ensure `SUPABASE_BUCKET_PUBLIC=true` if using signed URLs

**LLM council timeout:**
- Reduce number of models in council
- Increase timeout values in `llm_council.py`
- Check external API rate limits

---

## Contributing

This project was built during a hackathon. For production use:

1. **Security audit**: Review all hardcoded credentials
2. **Testing**: Add test coverage for critical paths
3. **Documentation**: Expand inline code comments
4. **Code review**: Refactor quick-fix solutions

Pull requests welcome for bug fixes and documentation improvements. 

---

## License

See `LICENSE` file for details.

---

## Acknowledgments

Built at the **UIUC Precision Digital Agriculture Hackathon 2026** sponsored by John Deere.

**Key Technologies:**
- CropWizard RAG system
- Open-Meteo weather API
- Supabase cloud storage
- Flutter framework
- FastAPI framework

---

## Contact

For questions about this project, please open an issue in the repository.  
