import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://zabbix_admin:zabbix_password@localhost:5432/ia_analyzer"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Zabbix
    zabbix_url: str = "http://host.docker.internal:8080"
    zabbix_user: str = "Admin"
    zabbix_password: str = "zabbix"

    # Grafana
    grafana_url: str = "http://host.docker.internal:3001"
    grafana_user: str = "admin"
    grafana_password: str = "admin"
    grafana_external_url: str = "http://localhost:3001"

    # Ollama
    ollama_url: str = "http://ollama:11434"
    ollama_model: str = "mistral"

    # Logging
    log_level: str = "INFO"

    # API
    api_title: str = "IA Analyzer API"
    api_version: str = "1.0.0"
    api_prefix: str = "/api/v1"

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
