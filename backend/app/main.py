from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routers import router as api_router
from .api.license import router as license_router

app = FastAPI(title="Kintsugi-DAM API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")
app.include_router(license_router, prefix="/api/license")

@app.get("/")
async def root():
    return {"message": "Kintsugi-DAM API is running"}
