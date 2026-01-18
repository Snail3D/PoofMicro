from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from contextlib import asynccontextmanager

from src.api.routes import router
from config import settings

# Add src to Python path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    print(f"PoofMicro ESP32 Builder starting on {settings.host}:{settings.port}")
    yield
    # Shutdown
    print("PoofMicro ESP32 Builder shutting down")


# Create FastAPI app
app = FastAPI(
    title="PoofMicro ESP32 Builder",
    description="Full-stack ESP32 program builder powered by GLM 4.7",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include API routes
app.include_router(router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main UI page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "healthy", "service": "PoofMicro"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
