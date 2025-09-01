from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  DATABASE_URL: str
  GEMINI_API_KEY: str
  SECRET_KEY: str
  HASH_ALGORITHM: str
  ACCESS_TOKEN_EXPIRE_MINUTES: int

  @property
  def async_database_url(self) -> str:
    return self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

  model_config = SettingsConfigDict(
    env_file=".env"
  )

settings = Settings()