from setuptools import setup, find_packages

setup(
    name="poofmicro",
    version="0.1.0",
    description="ESP32 Program Builder with GLM 4.7 AI",
    author="Snail3D",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
        "python-dotenv>=1.0.0",
        "zhipuai>=2.1.5",
        "httpx>=0.26.0",
        "jinja2>=3.1.3",
        "aiofiles>=23.2.1",
        "websockets>=12.0",
        "platformio>=6.1.11",
        "pyserial>=3.5",
        "playwright>=1.41.0",
    ],
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "poofmicro=main:app",
        ],
    },
)
