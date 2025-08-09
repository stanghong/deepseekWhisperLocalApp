from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration loaded from environment variables.

    This settings object centralizes configuration for:
    - Local LLM runtime (Ollama)
    - ASR model (faster-whisper)
    - TTS engine (Piper)
    - Logging and request timeouts
    """

    # LLM (Ollama)
    ollama_url: str = Field(default="http://localhost:11434", env="OLLAMA_URL")
    ollama_model: str = Field(default="deepseek-r1:latest", env="OLLAMA_MODEL")

    # ASR (faster-whisper)
    asr_model_size: str = Field(default="tiny", env="ASR_MODEL_SIZE")
    asr_compute_type: str = Field(default="int8", env="ASR_COMPUTE_TYPE")
    # ASR language/task: use translate to force English output; set language None for autodetect
    asr_language: Optional[str] = Field(default=None, env="ASR_LANGUAGE")
    asr_task: str = Field(default="translate", env="ASR_TASK")
    asr_device: str = Field(default="auto", env="ASR_DEVICE")
    asr_cpu_threads: int = Field(default=4, env="ASR_CPU_THREADS")

    # TTS (Piper)
    piper_path: str = Field(default="piper", env="PIPER_PATH")
    piper_voice_path: str = Field(default="", env="PIPER_VOICE_PATH")

    # Server behavior
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    request_timeout_seconds: int = Field(default=60, env="REQUEST_TIMEOUT_SECONDS")
    max_audio_seconds: int = Field(default=60, env="MAX_AUDIO_SECONDS")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


