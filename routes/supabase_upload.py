import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from supabase_uploader import SupabaseImageUploader

# Always load the .env from project root, even when uvicorn is launched elsewhere.
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

router = APIRouter(tags=["supabase"])


class SupabaseUploadRequest(BaseModel):
    base64_image: str


@router.post("/supabase/upload-image")
def upload_image_to_supabase(payload: SupabaseUploadRequest) -> dict:
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    supabase_bucket = os.getenv("SUPABASE_BUCKET", "crop-images")
    supabase_folder = os.getenv("SUPABASE_FOLDER", "uploads")
    signed_url_expires_in = int(os.getenv("SUPABASE_SIGNED_URL_EXPIRES_IN", "3600"))
    bucket_public = os.getenv("SUPABASE_BUCKET_PUBLIC", "true").lower() == "true"

    if not supabase_url or not supabase_key:
        raise HTTPException(
            status_code=500,
            detail="SUPABASE_URL and SUPABASE_KEY must be set in .env",
        )

    uploader = SupabaseImageUploader(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        bucket_name=supabase_bucket,
        folder=supabase_folder,
    )
    result = uploader.base64_to_url(
        payload.base64_image,
        signed_url_expires_in=signed_url_expires_in,
        bucket_public=bucket_public,
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=502,
            detail=result.get("error", "Unknown Supabase upload error"),
        )

    return result
