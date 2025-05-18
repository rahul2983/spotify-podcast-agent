# setup.py
from setuptools import setup, find_packages

setup(
    name="spotify-podcast-agent",
    version="1.0.0",
    packages=["spotify_agent"],
    install_requires=[
        "langchain>=0.1.0",
        "langchain-community>=0.0.1",
        "openai>=1.6.0",
        "spotipy>=2.23.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
        "fastapi>=0.104.0",
        "uvicorn>=0.24.0",
        "schedule>=1.2.0",
    ],
)