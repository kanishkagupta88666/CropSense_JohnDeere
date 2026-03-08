from fastapi import APIRouter
from pydantic import BaseModel

from routes.send_crop_img import SendCropImgRequest, send_crop_img
from routes.supabase_upload import SupabaseUploadRequest, upload_image_to_supabase
from routes.tools.get_field_conditions import LocationRequest, get_field_conditions

router = APIRouter(tags=["crop-disease"])


class LocationData(BaseModel):
    latitude: float
    longitude: float


class DetectCropDiseaseRequest(BaseModel):
    imagebase64: str
    location: LocationData 
    farmers_issue_description: str


@router.post("/detect_crop_disease")
def detect_crop_disease(payload: DetectCropDiseaseRequest) -> dict:
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

    # Step 4: Return all intermediate and final outputs for now.
    return {
        "message": "data recieved successfully",
        # "received_data": payload.model_dump(),
        "image_url": image_url,
        "field_conditions": field_conditions,
        "crop_diagnosis": crop_diagnosis_result,
    }
