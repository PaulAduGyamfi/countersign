from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore", frozen=True)
    database_url: str | None = None
    countersign_admin_key: str | None = None


def get_settings() -> Settings:
    return Settings()
