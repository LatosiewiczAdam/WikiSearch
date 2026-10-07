from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    azure_devops_pat: str
    azure_devops_org: str
    azure_devops_project: str
    anthropic_api_key: str = ""
    ollama_base_url: str = "http://localhost:11434"
    ollama_embed_model: str = "nomic-embed-text"
    chroma_persist_dir: str = "./chroma_db"

    class Config:
        env_file = ".env"


settings = Settings()
