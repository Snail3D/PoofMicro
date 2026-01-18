from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.core.builder import ESP32Builder, ESP32Simulator, BuildContext, BuildResult


# Request/Response Models
class LibrarySearchRequest(BaseModel):
    query: str
    board_type: str = "esp32"


class MaterialSearchRequest(BaseModel):
    query: str
    board_type: str = "esp32"


class BuildRequest(BaseModel):
    project_name: str
    board_type: str = "esp32"
    description: str
    features: List[str] = []
    libraries: List[Dict[str, str]] = []
    wifi_config: Optional[Dict[str, str]] = None
    custom_code: Optional[str] = None
    board_context: Optional[str] = None
    materials: List[Dict[str, Any]] = []


class SimulateRequest(BaseModel):
    project_name: str
    board_type: str = "esp32"


class ApiKeyUpdateRequest(BaseModel):
    api_key: str


class VisionImageSearchRequest(BaseModel):
    object_name: str
    max_images: int = 10


class VisionModelRequest(BaseModel):
    object_name: str
    object_description: str = ""


class VisionProjectRequest(BaseModel):
    project_name: str
    objects_to_detect: List[str]
    board_type: str = "esp32-cam"


# Router
router = APIRouter(prefix="/api")

# Global instances
builder = ESP32Builder()
simulator = ESP32Simulator()


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PoofMicro ESP32 Builder"}


@router.post("/search/libraries")
async def search_libraries(request: LibrarySearchRequest) -> List[Dict[str, str]]:
    """Search for ESP32 libraries using GLM 4.7"""
    try:
        results = await builder.search_libraries(request.query, request.board_type)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/materials")
async def search_materials(request: MaterialSearchRequest) -> List[Dict[str, Any]]:
    """Search for ESP32 materials and components"""
    try:
        results = await builder.search_materials(request.query, request.board_type)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build")
async def build_project(request: BuildRequest) -> BuildResult:
    """Generate and build ESP32 project"""
    try:
        context = BuildContext(
            project_name=request.project_name,
            board_type=request.board_type,
            description=request.description,
            features=request.features,
            libraries=request.libraries,
            wifi_config=request.wifi_config,
            custom_code=request.custom_code,
            board_context=request.board_context,
            materials=request.materials,
        )

        result = await builder.generate_code(context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/simulate")
async def simulate_project(request: SimulateRequest) -> Dict[str, Any]:
    """Simulate an ESP32 project (WACWI-like)"""
    try:
        project_path = Path(builder.projects_path) / request.project_name.replace(" ", "_").lower()

        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        result = await simulator.simulate_project(project_path, request.board_type)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/simulate/{project_name}")
async def get_simulation(project_name: str) -> Dict[str, Any]:
    """Get simulation status"""
    result = simulator.get_simulation(project_name)

    if not result:
        raise HTTPException(status_code=404, detail="Simulation not found")

    return result


@router.delete("/simulate/{project_name}")
async def stop_simulation(project_name: str) -> Dict[str, str]:
    """Stop a simulation"""
    success = simulator.stop_simulation(project_name)

    if not success:
        raise HTTPException(status_code=404, detail="Simulation not found")

    return {"message": "Simulation stopped"}


# Vision API Endpoints

@router.post("/vision/search-images")
async def search_object_images(request: VisionImageSearchRequest) -> List[Dict[str, Any]]:
    """Search for images of an object for training detection models"""
    try:
        results = await builder.search_object_images(request.object_name, request.max_images)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vision/create-model")
async def create_detection_model(request: VisionModelRequest) -> Dict[str, Any]:
    """Create custom detection model configuration for ESP32"""
    try:
        result = await builder.create_detection_model(request.object_name, request.object_description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/vision/build")
async def build_vision_project(request: VisionProjectRequest) -> BuildResult:
    """Build complete ESP32-CAM vision project with custom detection"""
    try:
        result = await builder.generate_vision_project(
            request.project_name,
            request.objects_to_detect,
            request.board_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects")
async def list_projects() -> List[Dict[str, Any]]:
    """List all projects"""
    try:
        projects_path = Path(builder.projects_path)
        projects = []

        for project_dir in projects_path.iterdir():
            if project_dir.is_dir():
                projects.append({
                    "name": project_dir.name,
                    "path": str(project_dir),
                    "created": project_dir.stat().st_ctime,
                })

        return projects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_name}/files")
async def get_project_files(project_name: str) -> List[Dict[str, Any]]:
    """Get project files"""
    try:
        project_path = Path(builder.projects_path) / project_name.replace(" ", "_").lower()

        if not project_path.exists():
            raise HTTPException(status_code=404, detail="Project not found")

        files = []
        for file_path in project_path.rglob("*"):
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "path": str(file_path.relative_to(project_path)),
                    "size": file_path.stat().st_size,
                })

        return files
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_name}/file/{file_path:path}")
async def get_project_file(project_name: str, file_path: str) -> Dict[str, str]:
    """Get specific file content"""
    try:
        project_path = Path(builder.projects_path) / project_name.replace(" ", "_").lower()
        full_path = project_path / file_path

        if not full_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        content = full_path.read_text()

        return {
            "name": full_path.name,
            "path": file_path,
            "content": content,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/build")
async def websocket_build(websocket: WebSocket):
    """WebSocket for real-time build updates"""
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "build":
                # Process build and send updates
                context = BuildContext(**data.get("context", {}))

                # Send progress updates
                await websocket.send_json({
                    "type": "progress",
                    "message": "Starting build...",
                    "progress": 10,
                })

                result = await builder.generate_code(context)

                await websocket.send_json({
                    "type": "progress",
                    "message": "Code generated...",
                    "progress": 50,
                })

                await websocket.send_json({
                    "type": "complete",
                    "result": result.__dict__,
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.send_json({
            "type": "error",
            "message": str(e),
        })
        await websocket.close()
