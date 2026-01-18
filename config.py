import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings"""

    def __init__(self):
        # GLM 4.7 API Configuration
        self.glm_api_key = os.getenv("GLM_API_KEY", "6f8730568f884cb2b3626ad06224c493.tjzNgDr8p0HfP4Tt")
        self.glm_api_base = os.getenv("GLM_API_BASE", "https://open.bigmodel.cn/api/paas/v4/")
        self.glm_model = os.getenv("GLM_MODEL", "glm-4.7")

        # Server Configuration
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        self.debug = os.getenv("DEBUG", "false").lower() == "true"

        # ESP32 Configuration
        self.esp32_port = os.getenv("ESP32_PORT", "/dev/ttyUSB0")
        self.esp32_baud = int(os.getenv("ESP32_BAUD", "115200"))

        # Database
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///./poofmicro.db")

        # Paths
        self.esp32_projects_path = os.getenv("ESP32_PROJECTS_PATH", "./esp32_projects")


settings = Settings()
