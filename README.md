# PoofMicro - ESP32 Program Builder

Full-stack ESP32 program builder powered by GLM 4.7 AI. Build, test, and simulate ESP32 projects with an intelligent dark-mode interface.

## Features

- AI-powered code generation using GLM 4.7
- Dark mode UI with card-based layout
- Library and component search
- ESP32 simulation (WACWI-like)
- Docker support
- Multiple ESP32 board support (ESP32, S2, S3, C3, C6)
- Wi-Fi, AP, Web Server, MQTT, Bluetooth templates
- Real-time build output

## Quick Start

### Using Docker (Recommended)

```bash
# Copy environment file
cp .env.example .env

# Edit .env and add your GLM API key
# GLM_API_KEY=your_api_key_here

# Build and run
docker-compose up -d

# Access at http://localhost:8000
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Install PlatformIO
pip install platformio

# Install Playwright browsers
playwright install chromium

# Run the application
python main.py

# Access at http://localhost:8000
```

## Configuration

Edit `.env` file:

```
GLM_API_KEY=your_api_key_here
GLM_API_BASE=https://open.bigmodel.cn/api/paas/v4/
GLM_MODEL=glm-4.7
HOST=0.0.0.0
PORT=8000
```

## Usage

1. **Create Project**: Fill in project name, board type, description, and select features
2. **Search Libraries**: Find and add ESP32 libraries
3. **Search Materials**: Find hardware components and sensors
4. **Add Context**: Provide additional board context or custom code
5. **Generate**: Click "Generate Project" to create the code
6. **Simulate**: Test your project with the built-in simulator

## Supported Boards

- ESP32 (Original)
- ESP32-S2
- ESP32-S3
- ESP32-C3
- ESP32-C6

## API Endpoints

- `POST /api/build` - Generate ESP32 project
- `POST /api/search/libraries` - Search for libraries
- `POST /api/search/materials` - Search for components
- `POST /api/simulate` - Simulate a project
- `GET /api/projects` - List all projects
- `GET /health` - Health check

## Project Structure

```
poofmicro/
├── src/
│   ├── api/          # API routes
│   ├── core/         # Builder core logic
│   ├── services/     # External services
│   └── utils/        # Utilities
├── static/           # Static assets
├── templates/        # HTML templates
├── esp32_projects/   # Generated projects
├── config.py         # Configuration
├── main.py           # Application entry
└── Dockerfile        # Docker configuration
```

## License

MIT
