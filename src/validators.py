import re
from pathlib import Path
from typing import Optional


class ValidationError(Exception):
    """Custom validation error"""
    pass


def validate_project_name(name: str) -> str:
    """Validate project name"""
    if not name or not name.strip():
        raise ValidationError("Project name cannot be empty")

    if len(name) > 100:
        raise ValidationError("Project name too long (max 100 characters)")

    # Alphanumeric, spaces, hyphens, underscores only
    if not re.match(r'^[a-zA-Z0-9_\- ]+$', name):
        raise ValidationError("Project name contains invalid characters")

    return name.strip()


def validate_esp32_board(board: str) -> str:
    """Validate ESP32 board type"""
    valid_boards = [
        "esp32",
        "esp32s2",
        "esp32s3",
        "esp32c3",
        "esp32c6",
        "esp32-c3",
        "esp32-c6",
        "esp32-s2",
        "esp32-s3",
    ]

    board = board.lower().strip()

    if board not in valid_boards:
        raise ValidationError(f"Invalid board type. Must be one of: {', '.join(valid_boards)}")

    return board


def validate_api_key(api_key: str) -> str:
    """Validate GLM API key format"""
    if not api_key or not api_key.strip():
        raise ValidationError("API key cannot be empty")

    api_key = api_key.strip()

    # Basic format check for GLM API keys
    if not re.match(r'^[a-z0-9]+\.[A-Za-z0-9]+$', api_key):
        raise ValidationError("Invalid API key format")

    return api_key


def validate_file_path(path: str, must_exist: bool = False) -> Path:
    """Validate file path"""
    try:
        path_obj = Path(path).resolve()

        if must_exist and not path_obj.exists():
            raise ValidationError(f"File does not exist: {path}")

        return path_obj
    except Exception as e:
        raise ValidationError(f"Invalid file path: {e}")


def validate_code_content(code: str, max_length: int = 100000) -> str:
    """Validate code content"""
    if not code or not code.strip():
        raise ValidationError("Code content cannot be empty")

    if len(code) > max_length:
        raise ValidationError(f"Code content too long (max {max_length} characters)")

    return code


def validate_wifi_credentials(ssid: str, password: Optional[str] = None) -> tuple:
    """Validate Wi-Fi credentials"""
    ssid = ssid.strip()

    if not ssid:
        raise ValidationError("SSID cannot be empty")

    if len(ssid) > 32:
        raise ValidationError("SSID too long (max 32 characters)")

    if password is not None:
        if len(password) < 8:
            raise ValidationError("Password must be at least 8 characters")
        if len(password) > 64:
            raise ValidationError("Password too long (max 64 characters)")

    return ssid, password
