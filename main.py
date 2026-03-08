from fastapi import FastAPI

from routes.detect_crop_disease import router as detect_crop_disease_router
from routes.health_check import router as health_check_router
from routes.send_crop_img import router as send_crop_img_router
from routes.sample_request_cropwizard import router as sample_request_cropwizard_router
from routes.supabase_upload import router as supabase_upload_router
from routes.tools.get_field_conditions import router as get_field_conditions_router

app = FastAPI(title="Backend API")

# Register route modules here as the project grows.
app.include_router(health_check_router)
app.include_router(sample_request_cropwizard_router)
app.include_router(send_crop_img_router)
app.include_router(supabase_upload_router)
app.include_router(detect_crop_disease_router)
app.include_router(get_field_conditions_router)
