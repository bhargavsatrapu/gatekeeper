import os


class Settings:
    project_name: str = "GATEKEEPER"

    db_name: str = os.environ.get("DB_NAME", "gatekeeper")
    db_user: str = os.environ.get("DB_USER", "postgres")
    db_password: str = os.environ.get("DB_PASSWORD", "0000")
    db_host: str = os.environ.get("DB_HOST", "localhost")
    db_port: str = os.environ.get("DB_PORT", "5432")
    
    # API Testing Configuration
    api_base_url: str = os.environ.get("API_BASE_URL", "http://localhost:8000")
    screenshot_dir: str = os.environ.get("SCREENSHOT_DIR", "screenshots")
    max_test_timeout: int = int(os.environ.get("MAX_TEST_TIMEOUT", "30"))
    enable_screenshots: bool = os.environ.get("ENABLE_SCREENSHOTS", "true").lower() == "true"


settings = Settings()


