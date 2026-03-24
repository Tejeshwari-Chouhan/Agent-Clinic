from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from config import settings
from src.routes.triage import router as triage_router

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Intelligent Healthcare Triage System",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(triage_router)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "message": "Healthcare Triage System Backend"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug
    )
