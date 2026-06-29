import os
from pathlib import Path
from typing import Any, Dict, List
import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_YAML_PATH = BASE_DIR / "config.yaml"

class Settings(BaseSettings):
    # App Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "info"
    
    # Storage Settings
    DATABASE_URL: str = "sqlite+aiosqlite:///jobs.db"
    
    # LLM Service Provider Settings
    AI_PROVIDER: str = "mock"
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Pipeline Config loaded from config.yaml
    pipeline_config: Dict[str, Any] = Field(default_factory=dict)

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def load_yaml_config(self) -> None:
        """Loads and parses the config.yaml parameters into the settings."""
        if CONFIG_YAML_PATH.exists():
            try:
                with open(CONFIG_YAML_PATH, "r", encoding="utf-8") as f:
                    self.pipeline_config = yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Failed to load config.yaml: {e}")
        else:
            print(f"Warning: config.yaml not found at {CONFIG_YAML_PATH}")

# Instantiate global settings
settings = Settings()
settings.load_yaml_config()
