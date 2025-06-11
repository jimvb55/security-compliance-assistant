"""Configuration settings for the Security Compliance Assistant."""
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Union

from dotenv import load_dotenv


# Load environment variables from .env file if it exists
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Project root
DATA_DIR = os.getenv("DATA_DIR", os.path.join(BASE_DIR, "data"))
LOGS_DIR = os.getenv("LOGS_DIR", os.path.join(DATA_DIR, "logs"))

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))
API_DEBUG = os.getenv("API_DEBUG", "True").lower() in ("true", "1", "t")

# Vector database settings
VECTOR_DB_TYPE = os.getenv("VECTOR_DB_TYPE", "faiss").lower()  # faiss, qdrant, pgvector
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", os.path.join(DATA_DIR, "indexes"))
VECTOR_DB_DIMENSIONS = int(os.getenv("VECTOR_DB_DIMENSIONS", 768))

# Embedding settings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Document processing settings
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 300))  # words per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 50))  # words of overlap between chunks

# LLM settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock").lower()  # azure_openai, anthropic, mock
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "")
LLM_DEPLOYMENT = os.getenv("LLM_DEPLOYMENT", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", 0.0))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", 1000))

# Retrieval settings
DEFAULT_NUM_RESULTS = int(os.getenv("DEFAULT_NUM_RESULTS", 5))
DEFAULT_MIN_SCORE = float(os.getenv("DEFAULT_MIN_SCORE", 0.6))

# Create directories if they don't exist
def ensure_directories_exist() -> None:
    """Create directories if they don't exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(LOGS_DIR, exist_ok=True)
    os.makedirs(VECTOR_DB_PATH, exist_ok=True)


# Print settings
def print_settings() -> None:
    """Print the current settings."""
    print("\n" + "=" * 50)
    print("Security Compliance Assistant - Settings")
    print("=" * 50)
    
    # General settings
    print("\nGeneral Settings:")
    print(f"  DATA_DIR: {DATA_DIR}")
    print(f"  LOGS_DIR: {LOGS_DIR}")
    
    # API settings
    print("\nAPI Settings:")
    print(f"  API_HOST: {API_HOST}")
    print(f"  API_PORT: {API_PORT}")
    print(f"  API_DEBUG: {API_DEBUG}")
    
    # Vector database settings
    print("\nVector Database Settings:")
    print(f"  VECTOR_DB_TYPE: {VECTOR_DB_TYPE}")
    print(f"  VECTOR_DB_PATH: {VECTOR_DB_PATH}")
    print(f"  VECTOR_DB_DIMENSIONS: {VECTOR_DB_DIMENSIONS}")
    
    # Embedding settings
    print("\nEmbedding Settings:")
    print(f"  EMBEDDING_MODEL: {EMBEDDING_MODEL}")
    
    # Document processing settings
    print("\nDocument Processing Settings:")
    print(f"  CHUNK_SIZE: {CHUNK_SIZE}")
    print(f"  CHUNK_OVERLAP: {CHUNK_OVERLAP}")
    
    # LLM settings
    print("\nLLM Settings:")
    print(f"  LLM_PROVIDER: {LLM_PROVIDER}")
    print(f"  LLM_MODEL: {LLM_MODEL}")
    print(f"  LLM_TEMPERATURE: {LLM_TEMPERATURE}")
    print(f"  LLM_MAX_TOKENS: {LLM_MAX_TOKENS}")
    
    # Retrieval settings
    print("\nRetrieval Settings:")
    print(f"  DEFAULT_NUM_RESULTS: {DEFAULT_NUM_RESULTS}")
    print(f"  DEFAULT_MIN_SCORE: {DEFAULT_MIN_SCORE}")
    
    print("\n" + "=" * 50 + "\n")


# Ensure directories exist when module is imported
ensure_directories_exist()
