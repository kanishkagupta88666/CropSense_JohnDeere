import requests
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from prompts import new_crop_detection_prompt

router = APIRouter(tags=["crop-image"])


class SendCropImgRequest(BaseModel):
    image_description: str
    image_url: str
    field_conditions: dict


@router.post("/send_crop_img")
def send_crop_img(payload: SendCropImgRequest) -> dict:
    url = "https://uiuc.chat/api/chat-api/chat"
    headers = {"Content-Type": "application/json"}
    data = {
        "model": "gpt-5",
        "messages": [
            {
                "role": "system",
                "content": new_crop_detection_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Weather Conditions: {json.dumps(payload.field_conditions, indent=2)}
                                    User's Observation:
                                    {payload.image_description}
                                    Please analyze this crop image and provide disease diagnosis considering the field conditions. Include diagnosis, treatment options, preventive measures, monitoring advice, and whether lab confirmation is recommended."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": payload.image_url,
                        },
                    },
                ],
            },
        ],
        "api_key": "uc_3fc20373173944c09d0ee8a0b62af79c",
        "course_name": "cropwizard-1.5",
        "stream": True,
        "temperature": 0.1,
        "retrieval_only": False,
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=240)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Upstream request failed: {exc}") from exc

    try:
        response_body = response.json()
    except ValueError:
        response_body = {"raw": response.text}

    return {
        "status_code": response.status_code,
        "response": response_body,
    }
