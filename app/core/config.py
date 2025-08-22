import os


class Settings:
    project_name: str = "GATEKEEPER"

    db_name: str = os.environ.get("DB_NAME", "gatekeeper")
    db_user: str = os.environ.get("DB_USER", "postgres")
    db_password: str = os.environ.get("DB_PASSWORD", "9496")
    db_host: str = os.environ.get("DB_HOST", "localhost")
    db_port: str = os.environ.get("DB_PORT", "5432")


settings = Settings()


