import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import httpx

from zhipuai import ZhipuAI
from config import settings


@dataclass
class BuildContext:
    """Context for ESP32 project build"""
    project_name: str
    board_type: str
    description: str
    features: List[str] = field(default_factory=list)
    libraries: List[Dict[str, str]] = field(default_factory=list)
    wifi_config: Optional[Dict[str, str]] = None
    custom_code: Optional[str] = None
    board_context: Optional[str] = None
    materials: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "board_type": self.board_type,
            "description": self.description,
            "features": self.features,
            "libraries": self.libraries,
            "wifi_config": self.wifi_config,
            "custom_code": self.custom_code,
            "board_context": self.board_context,
            "materials": self.materials,
        }


@dataclass
class BuildResult:
    """Result of a build operation"""
    success: bool
    project_path: Optional[Path] = None
    code_files: Dict[str, str] = field(default_factory=dict)
    config: Dict[str, Any] = field(default_factory=dict)
    platformio_ini: str = ""
    error: Optional[str] = None
    build_log: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class ESP32Builder:
    """ESP32 Program Builder using GLM 4.7"""

    def __init__(self):
        self.client = ZhipuAI(api_key=settings.glm_api_key)
        self.model = settings.glm_model
        self.projects_path = Path(settings.esp32_projects_path)
        self.projects_path.mkdir(exist_ok=True)

    async def chat_conversation(self, message: str, history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """Handle conversational building with real-time project generation"""

        # Build conversation context
        conversation = history or []
        conversation.append({"role": "user", "content": message})

        # System prompt for the AI
        system_prompt = """You are an expert ESP32 builder assistant. Your job is to:
1. Understand what the user wants to build
2. Ask clarifying questions when needed
3. Extract project specifications from the conversation
4. Provide helpful technical guidance

When you have gathered enough information (project name, board type, main features), respond with a JSON object that includes the project specification and a "ready_to_build" flag set to true.

Your response should be conversational and helpful. When ready to build, include a JSON block at the end.

Response format when ready to build:
{
  "message": "Your conversational response here...",
  "projectSpec": {
    "projectName": "Name",
    "boardType": "esp32/esp32-cam/etc",
    "description": "Description",
    "features": ["wifi", "sensors", etc],
    "libraries": [{"name": "...", "description": "..."}],
    "materials": [{"name": "...", "description": "..."}],
    "boardContext": "Optional context"
  },
  "readyToBuild": true
}

When not ready, just respond conversationally and ask follow-up questions."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    *conversation
                ],
                temperature=0.7,
            )

            content = response.choices[0].message.content.strip()

            # Try to parse as JSON first
            try:
                # Clean up markdown code blocks
                json_content = content
                if "```json" in json_content:
                    json_content = json_content.split("```json")[1].split("```")[0].strip()
                elif "```" in json_content:
                    json_content = json_content.split("```")[1].split("```")[0].strip()

                parsed = json.loads(json_content)

                # If we got a full response with projectSpec
                if "projectSpec" in parsed:
                    return {
                        "message": parsed.get("message", content),
                        "projectSpec": parsed["projectSpec"],
                        "needsInput": False
                    }

                # If just a message was returned
                if "message" in parsed:
                    return {
                        "message": parsed["message"],
                        "projectSpec": None,
                        "needsInput": True
                    }

            except json.JSONDecodeError:
                # Not JSON, treat as conversational response
                pass

            # Return conversational response
            return {
                "message": content,
                "projectSpec": None,
                "needsInput": True
            }

        except Exception as e:
            return {
                "message": f"I encountered an error: {str(e)}. Please try again.",
                "projectSpec": None,
                "needsInput": True
            }

    async def search_libraries(self, query: str, board_type: str = "esp32") -> List[Dict[str, str]]:
        """Search for ESP32 libraries using GLM 4.7"""
        prompt = f"""Search for ESP32 libraries related to: {query}

Board type: {board_type}

Return a JSON array of libraries with this exact structure:
[
  {{
    "name": "Library Name",
    "version": "1.0.0",
    "author": "Author Name",
    "url": "https://github.com/...",
    "description": "Brief description",
    "platformio_name": "library_name"
  }}
]

Only return valid JSON, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an ESP32 library expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()

            # Clean up markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            libraries = json.loads(content)
            return libraries if isinstance(libraries, list) else []

        except Exception as e:
            print(f"Library search error: {e}")
            return []

    async def search_materials(self, query: str, board_type: str = "esp32") -> List[Dict[str, Any]]:
        """Search for ESP32 project materials, components, and references"""
        prompt = f"""Search for ESP32 project materials and components related to: {query}

Board type: {board_type}

Return a JSON array of materials with this exact structure:
[
  {{
    "name": "Component/Material Name",
    "category": "sensor|actuator|communication|power|display|other",
    "description": "Description of what it does",
    "pin_count": 4,
    "voltage": "3.3V",
    "protocol": "I2C|SPI|UART|GPIO|Analog",
    "library_needed": "Library Name",
    "example_url": "https://...",
    "typical_use_case": "Brief use case description"
  }}
]

Only return valid JSON, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an ESP32 hardware expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()

            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            materials = json.loads(content)
            return materials if isinstance(materials, list) else []

        except Exception as e:
            print(f"Materials search error: {e}")
            return []

    async def search_object_images(self, object_name: str, max_images: int = 10) -> List[Dict[str, Any]]:
        """Search for images of an object for training detection models"""
        prompt = f"""I need to find images and information about "{object_name}" for training an ESP32-CAM object detection model.

Provide a JSON response with this structure:
{{
  "object_name": "{object_name}",
  "description": "Description of what the object looks like",
  "key_features": ["feature1", "feature2", "feature3"],
  "image_sources": [
    {{
      "source": "dataset_name",
      "url": "https://...",
      "description": "Description of images",
      "license": "public domain/CC/etc"
    }}
  ],
  "detection_tips": ["tip1", "tip2"],
  "esp32_camera_settings": {{
    "resolution": "FRAMESIZE_QVGA",
    "quality": "12",
    "brightness": "0",
    "contrast": "0"
  }}
}}

Only return valid JSON, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a computer vision and machine learning expert. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            content = response.choices[0].message.content.strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            return [result] if isinstance(result, dict) else []

        except Exception as e:
            print(f"Object image search error: {e}")
            return []

    async def create_detection_model(self, object_name: str, object_description: str = "") -> Dict[str, Any]:
        """Generate custom detection model code and configuration for ESP32"""
        prompt = f"""Generate a complete custom object detection project for ESP32-CAM.

Object to detect: {object_name}
Description: {object_description or 'General object detection'}

Provide a JSON response with this structure:
{{
  "model_info": {{
    "name": "custom_{object_name.lower()}_detector",
    "type": "MobileNetSSD / TensorFlow Lite",
    "input_size": "96x96",
    "classes": ["background", "{object_name}"],
    "confidence_threshold": 0.6
  }},
  "files": {{
    "src/main.cpp": "// Complete ESP32-CAM detection code",
    "src/model.h": "// Model header file",
    "include/config.h": "// Configuration header",
    "platformio.ini": "// PlatformIO config with TFLite and ESP32-CAM support"
  }},
  "training_instructions": {{
    "dataset_format": "VOC/COCO/YOLO",
    "training_steps": ["step1", "step2"],
    "conversion_command": "Command to convert TFLite model for ESP32",
    "quantization": "INT8 quantization for ESP32"
  }},
  "hardware_requirements": {{
    "board": "ESP32-CAM / AI-Thinker",
    "psram": "4MB PSRAM required",
    "memory": "Minimum 4MB flash"
  }}
}}

Generate complete, working code that:
1. Captures images from ESP32-CAM
2. Runs the detection model
3. Draws bounding boxes on detected objects
4. Sends results via Serial and/or WiFi
5. Uses TensorFlow Lite for Microcontrollers
6. Includes error handling and debugging

Only return valid JSON, no other text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an ESP32-CAM and machine learning expert. Generate complete, working code. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
            )

            content = response.choices[0].message.content.strip()

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            result = json.loads(content)
            return result if isinstance(result, dict) else {}

        except Exception as e:
            print(f"Detection model creation error: {e}")
            return {}

    async def generate_vision_project(self, project_name: str, objects_to_detect: List[str], board_type: str = "esp32-cam") -> BuildResult:
        """Generate complete ESP32-CAM vision project with custom detection"""
        result = BuildResult(success=False)

        if not objects_to_detect:
            result.error = "No objects specified for detection"
            return result

        # Create context for vision project
        context = BuildContext(
            project_name=project_name,
            board_type=board_type,
            description=f"Custom object detection for: {', '.join(objects_to_detect)}",
            features=["camera", "wifi", "webserver", "detection"],
        )

        # Generate detection model for first object
        primary_object = objects_to_detect[0]
        model_config = await self.create_detection_model(
            primary_object,
            f"Primary detection object: {primary_object}"
        )

        if not model_config:
            result.error = "Failed to generate detection model"
            return result

        # Build the project with model configuration
        prompt = self._build_vision_prompt(context, objects_to_detect, model_config)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_vision_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
            )

            content = response.choices[0].message.content
            parsed = self._parse_generation_response(content)

            result.code_files = parsed.get("files", {})
            result.platformio_ini = parsed.get("platformio_ini", "")
            result.config = parsed.get("config", {})
            result.config["model_config"] = model_config

            # Create project directory and files
            project_path = self.projects_path / context.project_name.replace(" ", "_").lower()
            project_path.mkdir(exist_ok=True)

            result.project_path = project_path

            # Write generated files
            for filename, code_content in result.code_files.items():
                file_path = project_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(code_content)

            # Write platformio.ini
            if result.platformio_ini:
                (project_path / "platformio.ini").write_text(result.platformio_ini)

            result.success = True
            result.build_log.append(f"Vision project created at: {project_path}")
            result.build_log.append(f"Objects to detect: {', '.join(objects_to_detect)}")

        except Exception as e:
            result.error = str(e)
            result.build_log.append(f"Error: {e}")

        return result

    def _get_vision_system_prompt(self) -> str:
        return """You are an expert ESP32-CAM and computer vision developer. Generate complete, production-ready code for object detection projects.

Always respond with valid JSON in this exact format:
{
  "files": {
    "src/main.cpp": "// complete code",
    "include/config.h": "// configuration"
  },
  "platformio_ini": "// complete config",
  "config": {}
}

Requirements for ESP32-CAM projects:
- Use ESP32-CAM (AI-Thinker) pinout
- Enable camera with correct pin configuration
- Include TensorFlow Lite for Microcontrollers
- Use JPEG compression for web streaming
- Handle PSRAM allocation properly
- Include proper error handling
- Support WiFi for web interface
- Draw detection boxes on JPEG frames
- Serial output at 115200 baud for debugging
- No emojis, clean professional code"""

    def _build_vision_prompt(self, context: BuildContext, objects: List[str], model_config: Dict[str, Any]) -> str:
        prompt = f"""Generate a complete ESP32-CAM object detection project.

Project Name: {context.project_name}
Board Type: {context.board_type}
Description: {context.description}

Objects to Detect:
{chr(10).join(f'- {obj}' for obj in objects)}

Model Configuration:
- Model: {model_config.get('model_info', {}).get('type', 'MobileNetSSD')}
- Input Size: {model_config.get('model_info', {}).get('input_size', '96x96')}
- Classes: {model_config.get('model_info', {}).get('classes', ['background', objects[0]])}

Generate:
1. Complete ESP32-CAM detection code (main.cpp)
2. Camera configuration header
3. Model/tflite include header
4. platformio.ini with:
   - board = esp32cam
   - lib_deps = EloquentTinyML, esp32-camera, WiFi
5. Web streaming with detection boxes overlay
6. Serial output of detection results
7. Error handling for camera initialization
8. PSRAM allocation code

The code should:
- Initialize camera with correct pins
- Load TFLite model
- Capture frames and run detection
- Draw boxes around detected objects
- Stream video over WiFi with overlay
- Output detection results to Serial
- Handle camera init failures gracefully

Respond only with valid JSON."""

        return prompt

    async def generate_code(self, context: BuildContext) -> BuildResult:
        """Generate ESP32 code using GLM 4.7"""
        result = BuildResult(success=False)

        # Build the prompt with all context
        prompt = self._build_generation_prompt(context)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
            )

            content = response.choices[0].message.content

            # Parse the response
            parsed = self._parse_generation_response(content)
            result.code_files = parsed.get("files", {})
            result.platformio_ini = parsed.get("platformio_ini", "")
            result.config = parsed.get("config", {})

            # Create project directory and files
            project_path = self.projects_path / context.project_name.replace(" ", "_").lower()
            project_path.mkdir(exist_ok=True)

            result.project_path = project_path

            # Write generated files
            for filename, code_content in result.code_files.items():
                file_path = project_path / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(code_content)

            # Write platformio.ini
            if result.platformio_ini:
                (project_path / "platformio.ini").write_text(result.platformio_ini)

            result.success = True
            result.build_log.append(f"Project created at: {project_path}")

        except Exception as e:
            result.error = str(e)
            result.build_log.append(f"Error: {e}")

        return result

    def _get_system_prompt(self) -> str:
        return """You are an expert ESP32 developer. Generate clean, well-documented C++ code for ESP32 projects.

Always respond with valid JSON in this exact format:
{
  "files": {
    "src/main.cpp": "// code here",
    "include/config.h": "// code here"
  },
  "platformio_ini": "// platformio.ini content",
  "config": {
    "board": "esp32dev",
    "framework": "arduino",
    "lib_deps": ["lib1", "lib2"]
  }
}

Requirements:
- Use modern C++ practices
- Include comprehensive comments
- Follow Arduino/ESP32 conventions
- Handle errors appropriately
- Include Serial debugging at 115200 baud
- Never use emojis
- Keep code modular and organized"""

    def _build_generation_prompt(self, context: BuildContext) -> str:
        prompt = f"""Generate a complete ESP32 project with the following specifications:

Project Name: {context.project_name}
Board Type: {context.board_type}
Description: {context.description}

Features requested:
{chr(10).join(f'- {f}' for f in context.features) if context.features else '- Basic functionality'}

"""

        if context.board_context:
            prompt += f"\nBoard Context:\n{context.board_context}\n"

        if context.libraries:
            prompt += "\nLibraries to use:\n"
            for lib in context.libraries:
                prompt += f"- {lib.get('name', 'N/A')}: {lib.get('description', '')}\n"

        if context.materials:
            prompt += "\nHardware Components:\n"
            for mat in context.materials:
                prompt += f"- {mat.get('name', 'N/A')}: {mat.get('description', '')}\n"

        if context.wifi_config:
            prompt += f"\nWiFi Configuration: SSID will be provided at runtime\n"

        if context.custom_code:
            prompt += f"\nCustom Code Snippet to include:\n{context.custom_code}\n"

        prompt += """
Generate:
1. All necessary source files (main.cpp, headers)
2. platformio.ini configuration
3. Proper library dependencies
4. WiFi/AP functionality if requested
5. Error handling and serial debugging
6. README with build instructions

Respond only with valid JSON."""

        return prompt

    def _parse_generation_response(self, content: str) -> Dict[str, Any]:
        """Parse the GLM response"""
        # Clean up markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            # Fallback: try to extract JSON from response
            try:
                start = content.find("{")
                end = content.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(content[start:end])
            except:
                pass

            print(f"Parse error: {e}")
            print(f"Content preview: {content[:500]}")
            return {"files": {}, "platformio_ini": "", "config": {}}


class ESP32Simulator:
    """WACWI-like ESP32 simulator for testing"""

    def __init__(self):
        self.active_simulations: Dict[str, Any] = {}

    async def simulate_project(self, project_path: Path, board_type: str = "esp32") -> Dict[str, Any]:
        """Simulate an ESP32 project without actual hardware"""
        project_name = project_path.name

        simulation = {
            "project_name": project_name,
            "board_type": board_type,
            "status": "starting",
            "ip_address": None,
            "ap_ssid": None,
            "web_server": False,
            "logs": [],
            "started_at": datetime.now().isoformat(),
        }

        self.active_simulations[project_name] = simulation

        # Read and analyze main.cpp
        main_cpp = project_path / "src" / "main.cpp"

        if main_cpp.exists():
            code = main_cpp.read_text()

            # Check for WiFi
            if "WiFi" in code or "WIFI" in code:
                simulation["has_wifi"] = True
                simulation["ip_address"] = "192.168.1.100"  # Simulated IP

            # Check for AP mode
            if "WiFi.softAP" in code or "softAP" in code:
                simulation["ap_ssid"] = f"{project_name}_AP"
                simulation["ip_address"] = "192.168.4.1"

            # Check for web server
            if "WebServer" in code or "server.begin" in code or "HTTPServer" in code:
                simulation["web_server"] = True

            simulation["status"] = "running"
            simulation["logs"].append("Simulation started successfully")
            simulation["logs"].append(f"Board: {board_type}")
            if simulation.get("ip_address"):
                simulation["logs"].append(f"IP Address: {simulation['ip_address']}")
            if simulation.get("ap_ssid"):
                simulation["logs"].append(f"AP SSID: {simulation['ap_ssid']}")
            if simulation.get("web_server"):
                simulation["logs"].append(f"Web server running on http://{simulation['ip_address']}")
        else:
            simulation["status"] = "error"
            simulation["logs"].append("Error: main.cpp not found")

        return simulation

    def get_simulation(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get simulation status"""
        return self.active_simulations.get(project_name)

    def stop_simulation(self, project_name: str) -> bool:
        """Stop a simulation"""
        if project_name in self.active_simulations:
            del self.active_simulations[project_name]
            return True
        return False
