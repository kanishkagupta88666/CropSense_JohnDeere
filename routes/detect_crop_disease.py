import json
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from routes.llm_council import forward_to_llm_council
from routes.send_crop_img import SendCropImgRequest, send_crop_img
from routes.supabase_upload import SupabaseUploadRequest, upload_image_to_supabase
from routes.traditional_ml_prediction import (
    TraditionalMLPredictionRequest,
    traditional_ml_prediction,
)
from routes.tools.get_field_conditions import LocationRequest, get_field_conditions

router = APIRouter(tags=["crop-disease"])
FILES_DIR = Path(__file__).resolve().parents[1] / "files"


class LocationData(BaseModel):
    latitude: float
    longitude: float


class DetectCropDiseaseRequest(BaseModel):
    imagebase64: str
    location: LocationData 
    farmers_issue_description: str


@router.post("/detect_crop_disease")
def detect_crop_disease(
    payload: DetectCropDiseaseRequest,
    background_tasks: BackgroundTasks,
) -> dict:
    session_id = uuid4().hex

    # Step 1: Upload the incoming base64 image and get a public URL.
    upload_result = upload_image_to_supabase(
        SupabaseUploadRequest(base64_image=payload.imagebase64)
    )
    image_url = upload_result.get("url")

    # Step 2: Fetch weather/soil conditions for the provided coordinates.
    field_conditions = get_field_conditions(
        LocationRequest(
            lat=payload.location.latitude,
            lon=payload.location.longitude,
        )
    )
    print(field_conditions) 

    # Step 3: Run crop diagnosis using image URL, user notes, and field conditions.
    crop_diagnosis_result = send_crop_img(
        SendCropImgRequest(
            image_description=payload.farmers_issue_description,
            image_url=image_url,
            field_conditions=field_conditions,
        )
    )
    print(crop_diagnosis_result)

    # Step 4: Run traditional ML prediction on the same base64 image.
    traditional_ml_result = traditional_ml_prediction(
        TraditionalMLPredictionRequest(image_base64=payload.imagebase64)
    )
    print(traditional_ml_result)

    council_payload = {
        "FarmerIssueDescription": payload.farmers_issue_description,
        "session_id": session_id,
        "image_url": image_url,
        "field_conditions": field_conditions,
        "crop_diagnosis": crop_diagnosis_result,
        "traditional_ml_prediction": traditional_ml_result,
    }

    FILES_DIR.mkdir(parents=True, exist_ok=True)
    payload_file = FILES_DIR / f"{session_id}.json"
    with payload_file.open("w", encoding="utf-8") as fp:
        json.dump(council_payload, fp, indent=2)

    # Send to llm-council without delaying this API response.
    background_tasks.add_task(forward_to_llm_council, council_payload)

    # Step 5: Return all intermediate and final outputs for now.
    return {
        "message": "data recieved successfully",
        "session_id": session_id,
        "image_url": image_url,
        "field_conditions": field_conditions,
        "crop_diagnosis": crop_diagnosis_result,
        "traditional_ml_prediction": traditional_ml_result,
    }
