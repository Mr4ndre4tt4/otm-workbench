from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    service_name: str = "otm-workbench"
    database_url: str = "sqlite:///./var/otm_workbench.db"
    artifact_root: Path = Path("var/artifacts")
    otm_data_dictionary_root: Path = Path(
        "OTM_RESOURCES/DATA_DICT26B/data_dictionary/json/data_dict"
    )
    session_ttl_minutes: int = 480

    model_config = SettingsConfigDict(env_prefix="OTM_", env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
