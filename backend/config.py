"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """IDA-MAS configuration, loaded from .env file."""

    # DeepSeek API (Chat / LLM)
    DEEPSEEK_API_KEY: str
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"

    # SiliconFlow API (Embedding, free)
    SILICONFLOW_API_KEY: str
    SILICONFLOW_API_BASE: str = "https://api.siliconflow.cn/v1"

    # Model names
    CHAT_MODEL: str = "deepseek-chat"
    EMBEDDING_MODEL: str = "BAAI/bge-m3"

    # Chunking strategy (Chinese-optimized)
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    # Retrieval
    TOP_K_RETRIEVAL: int = 5

    # Storage paths
    UPLOAD_DIR: str = "data/uploads"
    CHROMA_DIR: str = "data/chroma"

    # Limits
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
