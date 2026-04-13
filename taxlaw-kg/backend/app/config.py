"""
TaxLaw KG 配置管理
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    app_name: str = "TaxLaw KG"
    app_version: str = "1.0.0"
    debug: bool = False

    # 安全
    secret_key: str = "your-secret-key-change-in-production"
    access_token_expire_minutes: int = 1440  # 24小时

    # Redis (用于所有数据存储)
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 0

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "neo4j@1234"

    # Milvus
    milvus_uri: str = "http://localhost:19530"
    milvus_db_name: str = "taxlaw_kg"

    # LLM (DashScope / 千问)
    dashscope_api_key: str = ""
    dashscope_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model_name: str = "qwen-turbo"

    # Embedding
    embedding_model: str = "text-embedding-v3"
    embedding_dim: int = 1024

    # 文件存储
    upload_dir: str = "./uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB

    # LightRAG
    lightrag_working_dir: str = "./lightrag_working"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略 .env 中未定义的字段


@lru_cache()
def get_settings() -> Settings:
    return Settings()
