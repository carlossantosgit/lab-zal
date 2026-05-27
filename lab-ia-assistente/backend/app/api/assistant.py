from fastapi import APIRouter
from pydantic import BaseModel
import logging

from ..services.zabbix_manager import ZabbixManager
from ..services.grafana_client import GrafanaClient
from ..services.assistant_engine import AssistantEngine
from ..config import settings
from .settings import get_effective_zabbix

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["assistant"])


class ChatRequest(BaseModel):
    message: str


def _make_engine() -> AssistantEngine:
    zabbix_cfg = get_effective_zabbix()
    zabbix = ZabbixManager(
        url=zabbix_cfg["url"],
        user=zabbix_cfg["user"],
        password=zabbix_cfg["password"],
    )
    grafana = GrafanaClient(
        url=settings.grafana_url,
        user=settings.grafana_user,
        password=settings.grafana_password,
    )
    return AssistantEngine(
        zabbix=zabbix,
        grafana=grafana,
        ollama_url=settings.ollama_url,
        model=settings.ollama_model,
        grafana_external_url=settings.grafana_external_url,
    )


@router.post("/chat")
async def chat(request: ChatRequest):
    """Process a natural language request and execute the action in Zabbix/Grafana."""
    logger.info(f"Assistant chat: {request.message[:100]}")
    engine = _make_engine()
    result = await engine.process(request.message)
    return {"status": "ok", "result": result}


@router.get("/status")
async def status():
    """Check connectivity to Zabbix and Grafana."""
    zabbix_cfg = get_effective_zabbix()
    zabbix = ZabbixManager(
        url=zabbix_cfg["url"],
        user=zabbix_cfg["user"],
        password=zabbix_cfg["password"],
    )
    grafana = GrafanaClient(
        url=settings.grafana_url,
        user=settings.grafana_user,
        password=settings.grafana_password,
    )
    zabbix_ok = await zabbix.authenticate()
    grafana_ok = await grafana.health_check()
    return {
        "zabbix": {"ok": zabbix_ok, "url": zabbix_cfg["url"]},
        "grafana": {"ok": grafana_ok, "url": settings.grafana_url, "external_url": settings.grafana_external_url},
        "ollama": {"url": settings.ollama_url, "model": settings.ollama_model},
    }
