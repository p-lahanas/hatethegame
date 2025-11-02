from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    USER_EMAIL: str
    USER_PWD: str
    HOST: str

    model_config = SettingsConfigDict(
        env_prefix='condeco_',
        env_file=('.env', '.env.prod'),  # , env_file_encoding="utf-8"
    )
