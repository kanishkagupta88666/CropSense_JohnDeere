# CropSense_JohnDeere

AI-powered crop disease backend built at the UIUC Precision Digital Agriculture Hackathon 2026.

This service combines:
- Image upload to Supabase
- Weather and field conditions from Open-Meteo
- LLM-based crop diagnosis (CropWizard)
- Traditional ML disease prediction
- LLM council comparison across multiple models

## Tech Stack

- Python
- FastAPI
- Requests
- Pydantic
- python-dotenv

## Project Structure

```text
CropSense_JohnDeere/
	main.py
	requirements.txt
	prompts.py
	routes/
		detect_crop_disease.py
		health_check.py
		llm_council.py
		sample_request_cropwizard.py
		send_crop_img.py
		supabase_upload.py
		traditional_ml_prediction.py
		tools/
			get_field_conditions.py
	files/
	llm-council-files/
```

## Setup

### 1. Create virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

Create `.env` in project root:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_service_or_anon_key
SUPABASE_BUCKET=crop-images
SUPABASE_FOLDER=uploads
SUPABASE_SIGNED_URL_EXPIRES_IN=3600
SUPABASE_BUCKET_PUBLIC=true
```

### 4. Run API

```bash
uvicorn main:app --reload
```

Default server URL:
- `http://127.0.0.1:8000`

Swagger docs:
- `http://127.0.0.1:8000/docs`

## API Routes

### `GET /health-check`
Simple health endpoint.

### `POST /detect_crop_disease`
Main orchestration endpoint.

Request body:
```json
{
	"imagebase64": "data:image/jpeg;base64,...",
	"location": {
		"latitude": 40.1123,
		"longitude": -88.2432
	},
	"farmers_issue_description": "Leaves have yellow-brown angular spots"
}
```

What it does:
- Uploads image to Supabase
- Fetches field conditions
- Calls LLM diagnosis (`/send_crop_img` logic)
- Calls traditional ML prediction (`/traditional_ml_prediction` logic)
- Generates a `session_id`
- Saves combined payload to `files/<session_id>.json`

### `POST /supabase/upload-image`
Uploads a base64 image to Supabase storage.

Request body:
```json
{
	"base64_image": "data:image/jpeg;base64,..."
}
```

### `POST /get_field_conditions`
Fetches weather + soil context from Open-Meteo.

Request body:
```json
{
	"lat": 40.1123,
	"lon": -88.2432
}
```

### `POST /send_crop_img`
Direct CropWizard LLM diagnosis endpoint using image URL + field conditions.

### `POST /traditional_ml_prediction`
Calls external traditional ML model:
- `https://noninflectionally-nonchivalrous-jacki.ngrok-free.dev/predict`

Request body:
```json
{
	"image_base64": "data:image/jpeg;base64,..."
}
```

### `POST /llm_consortium`
Runs model council and returns best result plus debug metadata.

Accepted request body examples:

1. Session-driven input:
```json
{
	"session_id": "06a535216c01426ab430900f32c360d8"
}
```

2. Question-driven fallback:
```json
{
	"user_question": "What should I do in the next 7 days?"
}
```

Notes:
- If `session_id` is provided, the route loads `files/<session_id>.json`.
- The route calls all configured council models in parallel.
- It stores all model outputs in `llm-council-files/<session_id_or_timestamp>.json` as top-level model keys.

### `POST /sample_request_cropwizard`
Test endpoint for generic upstream CropWizard chat call.

## Data Artifacts

- `files/<session_id>.json`
	- Combined pipeline output from `/detect_crop_disease`

- `llm-council-files/<session_id_or_timestamp>.json`
	- LLM council outputs by model name, for example:

```json
{
	"gemma3:27b": {
		"response": "...",
		"is_best": false,
		"score": 7.0
	},
	"Qwen/Qwen2.5-VL-72B-Instruct": {
		"response": "...",
		"is_best": true,
		"score": 10.0
	}
}
```

## Important Notes

- Keep secrets in `.env` only. Do not commit private keys.
- Some upstream endpoints and keys are hardcoded in route files for hackathon speed. Move these to env vars before production use.
- `llm_council.py` prints debug logs to console for easier tracing.
