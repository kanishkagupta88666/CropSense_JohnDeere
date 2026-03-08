import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import requests
from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["llm-council"])

UPSTREAM_URL = "https://uiuc.chat/api/chat-api/chat"
TIMEOUT = 30

DEFAULT_MODELS = [
    "gemma3:27b",
    "Qwen/Qwen2.5-VL-72B-Instruct",
    "llama4:16x17b",
]
DEFAULT_API_KEY = "uc_3fc20373173944c09d0ee8a0b62af79c"
DEFAULT_COURSE_NAME = "cropwizard-1.5"
DEFAULT_TEMPERATURE = 0.1
DEFAULT_RETRIEVAL_ONLY = False
FILES_DIR = Path(__file__).resolve().parents[1] / "files"


class ConsortiumRequest(BaseModel):
    session_id: str | None = None
    user_question: str = "As an expert consultant, what should the farmer do NOW based on this diagnosis?"
    temperature: float = DEFAULT_TEMPERATURE
    course_name: str = DEFAULT_COURSE_NAME
    retrieval_only: bool = DEFAULT_RETRIEVAL_ONLY


class ModelResponse(BaseModel):
    model: str
    response: Any
    is_best: bool = False
    score: float = 0.0


class ConsortiumResponse(BaseModel):
    results: dict[str, ModelResponse]
    debug: dict[str, Any]


def forward_to_llm_council(data: dict[str, Any]) -> dict[str, Any]:
    # Kept as a no-op helper for compatibility with existing imports.
    return {"status": "accepted", "data": data}


def call_llm(
    model: str,
    messages: list[dict[str, str]],
    timeout: int = 40,
) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "api_key": DEFAULT_API_KEY,
        "temperature": DEFAULT_TEMPERATURE,
        "course_name": DEFAULT_COURSE_NAME,
        "stream": False,
    }

    try:
        print(f"[llm_council] Calling model={model} timeout={timeout}")
        resp = requests.post(UPSTREAM_URL, json=payload, timeout=timeout)
        resp.raise_for_status()
        print(f"[llm_council] Model={model} status={resp.status_code}")
        return str(resp.json().get("response", resp.text))[:2000]
    except Exception as exc:  # noqa: BLE001
        print(f"[llm_council] Model call failed model={model} error={exc}")
        return f"Error {model}: {exc}"


def summarize_diagnosis(raw_json: str) -> str:
    print(f"[llm_council] Summarizing diagnosis payload_len={len(raw_json)}")
    messages = [
        {
            "role": "system",
            "content": (
                "Summarize crop diagnosis in EXACTLY 5 bullets:\n"
                "- Location: lat/long\n"
                "- Weather: temp/humidity\n"
                "- Disease: common (scientific)\n"
                "- Severity/Confidence: stage/medium\n"
                "- Impact: weather effect"
            ),
        },
        {"role": "user", "content": raw_json[:4000]},
    ]
    return call_llm("llama4:16x17b", messages, timeout=30)


def build_standard_messages(
    user_question: str,
    diagnosis_summary: str | None = None,
) -> list[dict[str, str]]:
    if not diagnosis_summary:
        diagnosis_summary = (
            "DIAGNOSIS SUMMARY\n"
            "- No structured diagnosis data was provided.\n"
            "- Ask clarifying questions about crop, field conditions, and symptoms before recommending actions."
        )

    crop_type = "row crops"
    for crop in ["cotton", "corn", "soybean", "wheat"]:
        if crop in diagnosis_summary.lower():
            crop_type = crop
            break

    system_prompt = (
        f"You are a senior plant pathologist and agronomy consultant for Illinois {crop_type} farmers. "
        "You integrate weather, field observations, and diagnosis outputs into clear recommendations."
    )

    user_content = f"""Here is the current DIAGNOSIS SUMMARY for this field:

{diagnosis_summary}

Here is the FARMER QUESTION:

{user_question}

As an expert consultant, respond with EXACTLY these sections in order:
1. Farmer-friendly explanation
2. Immediate actions (next 7 days)
3. Treatment plan
4. Prevention for next season
5. Risk forecast (next 7 days)
"""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


def select_best_response(
    results: dict[str, ModelResponse],
    diagnosis_summary: str | None,
) -> ModelResponse | None:
    disease_terms: list[str] = []
    crop_terms: list[str] = []
    text_summary = diagnosis_summary.lower() if diagnosis_summary else ""

    for crop in ["cotton", "corn", "soy", "wheat"]:
        if crop in text_summary:
            crop_terms.append(crop)
    for disease in ["angular leaf spot", "bacterial blight"]:
        if disease in text_summary:
            disease_terms.append(disease)

    required_sections = [
        "explanation",
        "immediate actions",
        "treatment",
        "prevention",
        "risk forecast",
    ]

    best_model = None
    best_score = -1.0

    for model_name, mr in results.items():
        raw = str(mr.response)
        text = raw.lower()

        if any(err in text for err in ["httpsconnectionpool", "bad gateway"]):
            print(f"[llm_council] Skipping model={model_name} due to upstream error text")
            continue

        score = 0.0
        section_hits = sum(1 for sec in required_sections if sec in text)
        score += section_hits * 2
        score += sum(3 for term in disease_terms if term in text)
        score += sum(2 for term in crop_terms if term in text)

        if 500 <= len(text) <= 4000:
            score += 2
        if "illinois" in text or "row crop" in text:
            score += 1
        if "**" in raw or "###" in raw:
            score += 1

        mr.score = float(score)
        print(f"[llm_council] Scored model={model_name} score={mr.score}")
        if score > best_score:
            best_score = score
            best_model = model_name

    if not best_model and results:
        print("[llm_council] No best model by score; falling back to first result")
        return list(results.values())[0]
    if not best_model:
        print("[llm_council] No model results available")
        return None
    print(f"[llm_council] Selected best model={best_model} score={best_score}")
    return results[best_model]


@router.post("/llm_consortium", response_model=ConsortiumResponse)
def llm_consortium(payload: ConsortiumRequest | str = Body(...)) -> ConsortiumResponse:
    print("[llm_council] /llm_consortium called")
    debug: dict[str, Any] = {}

    # Accept both proper JSON object bodies and stringified JSON payloads.
    if isinstance(payload, str):
        print("[llm_council] Received string body; attempting JSON parse")
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=422,
                detail="Body must be a JSON object or a valid stringified JSON object",
            ) from exc
        if not isinstance(parsed, dict):
            raise HTTPException(status_code=422, detail="Parsed body must be a JSON object")
        payload = ConsortiumRequest.model_validate(parsed)

    # Input handling
    if payload.session_id:
        session_file = FILES_DIR / f"{payload.session_id}.json"
        print(f"[llm_council] Loading input from session file={session_file}")
        if not session_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Session file not found: files/{payload.session_id}.json",
            )
        with session_file.open("r", encoding="utf-8") as fp:
            raw_data = json.load(fp)
        debug["source"] = "session_file"
        debug["session_id"] = payload.session_id
        debug["image_url"] = raw_data.get("image_url", "none")
        field_conditions = raw_data.get("field_conditions", {})
        crop_diagnosis = raw_data.get("crop_diagnosis", {})
        flat_data = {**field_conditions, **crop_diagnosis}
        raw_input = json.dumps(flat_data)
    elif os.path.exists("sample.json"):
        json_path = "sample.json"
        print(f"[llm_council] Loading input from {json_path}")
        with open(json_path, "r", encoding="utf-8") as fp:
            raw_data = json.load(fp)
        debug["source"] = "sample.json"
        debug["session_id"] = raw_data.get("session_id", "unknown")
        debug["image_url"] = raw_data.get("image_url", "none")
        field_conditions = raw_data.get("field_conditions", {})
        crop_diagnosis = raw_data.get("crop_diagnosis", {})
        flat_data = {**field_conditions, **crop_diagnosis}
        raw_input = json.dumps(flat_data)
    else:
        print("[llm_council] Loading input from request body")
        raw_input = payload.user_question.strip()
        debug["source"] = "request_body"

    is_raw_json = len(raw_input) > 200 and any(
        kw in raw_input.lower()
        for kw in ["latitude", "diagnosis", "disease_name", "weather_context"]
    )

    if is_raw_json:
        print("[llm_council] Detected structured/raw JSON-like diagnosis input")
        diagnosis_summary = summarize_diagnosis(raw_input)
        clean_question = (
            "As an expert consultant, what should the farmer do NOW based on this diagnosis?"
        )
        debug["raw_detected"] = "yes"
        debug["summary"] = diagnosis_summary[:200]
    else:
        print("[llm_council] Treating input as plain question text")
        diagnosis_summary = None
        clean_question = payload.user_question
        debug["raw_detected"] = "no"

    messages = build_standard_messages(clean_question, diagnosis_summary)
    debug["prompt_preview"] = messages[0]["content"][:300]

    results: dict[str, ModelResponse] = {}
    with ThreadPoolExecutor(max_workers=len(DEFAULT_MODELS)) as executor:
        print(f"[llm_council] Dispatching parallel model calls count={len(DEFAULT_MODELS)}")
        futures = {
            executor.submit(
                call_llm,
                model,
                messages,
                TIMEOUT,
            ): model
            for model in DEFAULT_MODELS
        }
        for future in as_completed(futures):
            model = futures[future]
            results[model] = ModelResponse(model=model, response=future.result())
            print(f"[llm_council] Received response from model={model}")

    best = select_best_response(results, diagnosis_summary)
    if best is None:
        print("[llm_council] Returning all results; best model not found")
        return ConsortiumResponse(results=results, debug=debug)

    if "error" not in str(best.response).lower():
        print(f"[llm_council] Generating final summary with model={best.model}")
        final_messages = [
            {
                "role": "system",
                "content": (
                    "Crop expert: Summarize your detailed advice in 2 farmer-friendly paragraphs "
                    "(about 150 words total)."
                ),
            },
            {
                "role": "user",
                "content": f"DIAGNOSIS: {diagnosis_summary}\n\nYOUR ADVICE: {best.response}",
            },
        ]
        final_summary = call_llm(
            best.model,
            final_messages,
            timeout=40,
        )
        results[best.model].response = {
            "detailed": best.response,
            "final_summary": final_summary,
        }
        debug["final_summary_model"] = best.model
        debug["final_summary_length"] = len(final_summary)
    else:
        print(f"[llm_council] Skipping final summary due to error in best model={best.model}")
        debug["final_summary_skipped"] = "Best errored"

    results[best.model].is_best = True
    debug["best_model"] = best.model
    debug["best_score"] = results[best.model].score
    print(f"[llm_council] Final best model={best.model} score={results[best.model].score}")

    if best and isinstance(results[best.model].response, dict) and "final_summary" in results[best.model].response:
        print("[llm_council] Returning single highlighted best result")
        return ConsortiumResponse(results={best.model: results[best.model]}, debug=debug)

    highlighted_results = {
        model: ModelResponse(
            model=mr.model,
            response=mr.response,
            is_best=mr.is_best,
            score=mr.score,
        )
        for model, mr in results.items()
    }
    print("[llm_council] Returning highlighted results for all models")
    return ConsortiumResponse(results=highlighted_results, debug=debug)
