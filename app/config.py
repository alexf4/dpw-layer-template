from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DPW_API_KEY: str
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env"}


settings = Settings()
