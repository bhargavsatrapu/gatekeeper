"""
Configuration management for the API Testing Agent.

This module contains all configuration settings including database connections,
API endpoints, file paths, and other application settings.
"""

import os
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    host: str = "localhost"
    database: str = "SWAGGER_API"
    user: str = "postgres"
    password: str = "9496"
    port: int = 5432

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for psycopg2 connection."""
        return {
            "host": self.host,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "port": self.port
        }


@dataclass
class APIConfig:
    """API configuration settings."""
    base_url: str = "http://localhost:3000"
    timeout: int = 30
    max_retries: int = 3


@dataclass
class LLMConfig:
    """LLM configuration settings."""
    api_key: str = "AIzaSyB3cm8W8O6U8498FbS1EXt5o8qHVe43yjc"
    model: str = "gemini-2.5-flash"
    max_tokens: int = 4000


@dataclass
class AppConfig:
    """Main application configuration."""
    swagger_file_path: str = r"C:\Bhargav\SMALL_API\swagger.json"
    log_level: str = "INFO"
    execution_delay: int = 10  # seconds between API calls
    
    # Initialize sub-configurations
    database: DatabaseConfig = None
    api: APIConfig = None
    llm: LLMConfig = None
    
    def __post_init__(self):
        """Initialize sub-configurations after dataclass creation."""
        if self.database is None:
            self.database = DatabaseConfig()
        if self.api is None:
            self.api = APIConfig()
        if self.llm is None:
            self.llm = LLMConfig()


# Global configuration instance
config = AppConfig()


def get_config() -> AppConfig:
    """Get the global configuration instance."""
    return config


def update_config(**kwargs) -> None:
    """Update configuration values."""
    global config
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        else:
            raise ValueError(f"Unknown configuration key: {key}")
