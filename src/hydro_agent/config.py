"""Configuration locale; les secrets ne sont jamais sérialisés dans les traces."""

from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from hydro_agent.models import Identity, Role


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    openrouter_api_key: SecretStr = SecretStr("")
    openrouter_model: str = "openai/gpt-5.6-luna"
    data_dir: Path = Field(default=Path("data"), validation_alias="HYDRO_DATA_DIR")
    db_path: Path = Field(
        default=Path(".hydro/incidents.sqlite3"), validation_alias="HYDRO_DB_PATH"
    )
    max_steps: int = Field(default=24, ge=1, le=100, validation_alias="HYDRO_MAX_STEPS")
    actor: str = Field(default="operateur-local", min_length=1, validation_alias="HYDRO_ACTOR")
    role: Role = Field(default=Role.OPERATOR, validation_alias="HYDRO_ROLE")

    @property
    def identity(self) -> Identity:
        return Identity(actor=self.actor, role=self.role)
