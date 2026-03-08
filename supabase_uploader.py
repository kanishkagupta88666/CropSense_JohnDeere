import base64
import os
import uuid
from typing import Any

import requests
from dotenv import load_dotenv


class SupabaseImageUploader:
    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        bucket_name: str = "crop-images",
        folder: str = "uploads",
    ) -> None:
        self.supabase_url = supabase_url.rstrip("/")
        self.supabase_key = supabase_key
        self.bucket_name = bucket_name
        self.folder = folder.strip("/")

    def _auth_headers(self, content_type: str | None = None) -> dict[str, str]:
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _extension_from_mime(self, mime_type: str) -> str:
        mapping = {
            "image/jpeg": "jpg",
            "image/jpg": "jpg",
            "image/png": "png",
            "image/webp": "webp",
            "image/gif": "gif",
        }
        return mapping.get(mime_type.lower(), "jpg")

    def _parse_base64_image(self, base64_img: str) -> tuple[bytes, str]:
        default_mime = "image/jpeg"
        payload = base64_img.strip()

        if payload.startswith("data:"):
            try:
                metadata, encoded = payload.split(",", 1)
            except ValueError as exc:
                raise ValueError("Invalid data URI format.") from exc

            mime_type = metadata.split(";")[0].replace("data:", "") or default_mime
            encoded = encoded.strip().replace("\n", "")
            padding = (-len(encoded)) % 4
            if padding:
                encoded += "=" * padding
            image_bytes = base64.b64decode(encoded)
            return image_bytes, mime_type

        payload = payload.replace("\n", "")
        padding = (-len(payload)) % 4
        if padding:
            payload += "=" * padding
        image_bytes = base64.b64decode(payload)
        return image_bytes, default_mime

    def _create_signed_url(self, file_path: str, expires_in: int = 3600) -> str | None:
        sign_url = (
            f"{self.supabase_url}/storage/v1/object/sign/{self.bucket_name}/{file_path}"
        )
        response = requests.post(
            sign_url,
            headers=self._auth_headers("application/json"),
            json={"expiresIn": expires_in},
            timeout=30,
        )
        if response.status_code not in {200, 201}:
            return None

        body = response.json()
        signed_path = body.get("signedURL") or body.get("signedUrl")
        if not signed_path:
            return None
        if signed_path.startswith("http"):
            return signed_path
        return f"{self.supabase_url}{signed_path}"

    def _ensure_bucket_exists(self, make_public: bool = True) -> None:
        get_bucket_url = f"{self.supabase_url}/storage/v1/bucket/{self.bucket_name}"
        get_response = requests.get(
            get_bucket_url,
            headers=self._auth_headers(),
            timeout=30,
        )

        if get_response.status_code == 200:
            return

        if get_response.status_code not in {400, 404}:
            raise RuntimeError(
                "Unable to verify bucket existence: "
                f"{get_response.status_code} {get_response.text}"
            )

        create_bucket_url = f"{self.supabase_url}/storage/v1/bucket"
        create_response = requests.post(
            create_bucket_url,
            headers=self._auth_headers("application/json"),
            json={
                "id": self.bucket_name,
                "name": self.bucket_name,
                "public": make_public,
            },
            timeout=30,
        )

        if create_response.status_code not in {200, 201, 409}:
            raise RuntimeError(
                "Bucket create failed: "
                f"{create_response.status_code} {create_response.text}"
            )

    def base64_to_url(
        self,
        base64_img: str,
        signed_url_expires_in: int = 3600,
        bucket_public: bool = True,
    ) -> dict[str, Any]:
        try:
            self._ensure_bucket_exists(make_public=bucket_public)
            image_bytes, mime_type = self._parse_base64_image(base64_img)
            file_ext = self._extension_from_mime(mime_type)
            filename = f"{uuid.uuid4().hex}.{file_ext}"
            file_path = f"{self.folder}/{filename}" if self.folder else filename

            upload_url = (
                f"{self.supabase_url}/storage/v1/object/{self.bucket_name}/{file_path}"
            )
            headers = self._auth_headers(mime_type)
            headers["x-upsert"] = "true"

            upload_response = requests.post(
                upload_url,
                headers=headers,
                data=image_bytes,
                timeout=60,
            )
            if upload_response.status_code not in {200, 201}:
                return {
                    "success": False,
                    "error": (
                        "Upload failed with status "
                        f"{upload_response.status_code}: {upload_response.text}"
                    ),
                }

            public_url = (
                f"{self.supabase_url}/storage/v1/object/public/"
                f"{self.bucket_name}/{file_path}"
            )
            signed_url = self._create_signed_url(file_path, expires_in=signed_url_expires_in)

            # For public buckets, clients should use the stable public URL.
            primary_url = public_url if bucket_public else (signed_url or public_url)

            return {
                "success": True,
                "url": primary_url,
                "public_url": public_url,
                "signed_url": signed_url,
                "path": file_path,
            }
        except Exception as exc:  # noqa: BLE001
            return {"success": False, "error": str(exc)}


def jpg_to_base64_data_uri(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


if __name__ == "__main__":
    # Temporary local test: convert a JPG file to base64 and upload to Supabase.
    load_dotenv()

    supabase_url = os.getenv("SUPABASE_URL", "")
    supabase_key = os.getenv("SUPABASE_KEY", "")
    supabase_bucket = os.getenv("SUPABASE_BUCKET", "crop-images")
    supabase_folder = os.getenv("SUPABASE_FOLDER", "uploads")

    if not supabase_url or not supabase_key:
        raise RuntimeError("Set SUPABASE_URL and SUPABASE_KEY in .env before testing.")

    image_path = "image_data/cotton.jpg"
    base64_img = jpg_to_base64_data_uri(image_path)

    uploader = SupabaseImageUploader(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        bucket_name=supabase_bucket,
        folder=supabase_folder,
    )
    result = uploader.base64_to_url(base64_img)

    if result.get("success"):
        print(result.get("url"))
    else:
        print(result.get("error"))
