from setuptools import setup, find_packages

setup(
    name="spotify-podcast-agent",
    version="2.0.0",
    packages=find_packages(),  # This will automatically include all subpackages
    install_requires=[
        "langchain>=0.1.0",
        "langchain-community>=0.0.1",
        "langchain-openai>=0.0.1",
        "openai>=1.6.0",
        "spotipy>=2.23.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "schedule>=1.2.0",
        # MCP dependencies
        "asyncio-mqtt>=0.11.0",
        "websockets>=11.0.0",
        "jsonrpc-base>=2.0.0",
        "typing-extensions>=4.5.0",
    ],
    extras_require={
        "legacy": [],  # No extra deps for legacy mode
        "mcp": [
            "asyncio-mqtt>=0.11.0",
            "websockets>=11.0.0", 
            "jsonrpc-base>=2.0.0"
        ]
    }
)