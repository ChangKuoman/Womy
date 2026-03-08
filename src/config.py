"""
Configuración de la aplicación
"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


def _as_bool(value: str, default: bool = False) -> bool:
    """Convierte valores de entorno a bool de forma segura."""
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "si", "s"}


class Settings(BaseSettings):
    """Configuración de la aplicación"""

    # API Keys
    featherless_api_key: str = os.getenv("FEATHERLESS_API_KEY", "")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    fish_audio_api_key: str = os.getenv("FISH_AUDIO_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")

    # Telegram Bot Token
    telegram_token: str = os.getenv("TELEGRAM_TOKEN", "")

    # ElevenLabs
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "")
    enviar_audio_respuesta: bool = _as_bool(os.getenv("ENVIAR_AUDIO_RESPUESTA", "false"), False)

    # Speech-to-Text (transcripción)
    aceptar_audio_entrada: bool = _as_bool(os.getenv("ACEPTAR_AUDIO_ENTRADA", "true"), True)
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")

    # Database
    database_path: str = os.getenv("DATABASE_PATH", "data/finanzas_mujeres.db")

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))

    # Featherless Model
    featherless_model: str = "meta-llama/Meta-Llama-3.1-8B-Instruct"
    featherless_base_url: str = "https://api.featherless.ai/v1"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignorar variables no definidas


settings = Settings()
