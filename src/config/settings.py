import os
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(BASE_DIR, ".env")

class Settings(BaseSettings):
    intent_model_path: str
    sentiment_model_path: str
    intent_tokenizer: str
    sentiment_tokenizer: str
    corrector_model_path: str
    corrector_tokenizer: str
    postgres_db_conn: str
    model_config = SettingsConfigDict(env_file=ENV_PATH, env_file_encoding='utf-8', extra='ignore')

settings = Settings()