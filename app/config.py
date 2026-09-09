"""Configuración de la aplicación, leída de variables de entorno (.env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_uri: str = "mongodb://localhost:27017/?replicaSet=rs0"
    db_name: str = "registro_visitas"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
