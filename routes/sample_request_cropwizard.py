from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

router = APIRouter(tags=["sample-request"])


class CropWizardRequest(BaseModel):
    openai_key: str
    model: str = "gpt-4o-mini"
    system_prompt: str = "What crops are good to grow in united states"
    user_prompt: str = "What crops are good to grow in Illinois"
    temperature: float = 0.1
    course_name: str = "your-course-name"
    retrieval_only: bool = True


@router.post("/sample_request_cropwizard")
def sample_request_cropwizard(payload: CropWizardRequest) -> dict:
    url = "https://uiuc.chat/api/chat-api/chat"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": payload.model,
        "messages": [
            {
                "role": "system",
                "content": payload.system_prompt,
            },
            {
                "role": "user",
                "content": payload.user_prompt,
            },
        ],
        "openai_key": payload.openai_key,
        "temperature": payload.temperature,
        "course_name": payload.course_name,
        "retrieval_only": payload.retrieval_only,
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {exc}") from exc

    try:
        response_body = response.json()
    except ValueError:
        response_body = {"raw": response.text}

    contexts = response_body.get("contexts") if isinstance(response_body, dict) else None

    return {
        "status_code": response.status_code,
        "contexts": contexts,
        "response": response_body,
    }
