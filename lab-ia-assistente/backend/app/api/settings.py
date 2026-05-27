from fastapi import APIRouter
from pydantic import BaseModel
import logging

from ..services.zabbix_client import ZabbixClient
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/settings", tags=["settings"])

# Runtime override store — populated when user saves via UI
_runtime: dict = {}


class ZabbixConfig(BaseModel):
    url: str
    user: str
    password: str


def get_effective_zabbix() -> dict:
    """Return the currently active Zabbix configuration."""
    return {
        "url":      _runtime.get("url",      settings.zabbix_url),
        "user":     _runtime.get("user",     settings.zabbix_user),
        "password": _runtime.get("password", settings.zabbix_password),
    }


@router.get("/zabbix")
async def get_zabbix_settings():
    """Return current Zabbix settings (password masked)."""
    cfg = get_effective_zabbix()
    return {
        "url":        cfg["url"],
        "user":       cfg["user"],
        "password":   "***" if cfg["password"] else "",
        "is_custom":  bool(_runtime),
        "source":     "runtime" if _runtime else "environment",
    }


@router.post("/zabbix")
async def save_zabbix_settings(config: ZabbixConfig):
    """Save Zabbix settings at runtime (no restart needed)."""
    global _runtime
    _runtime = {
        "url":      config.url.rstrip("/"),
        "user":     config.user,
        "password": config.password,
    }
    logger.info(f"✅ Zabbix settings updated: {config.url} / {config.user}")
    return {"status": "saved", "url": _runtime["url"], "user": _runtime["user"]}


@router.delete("/zabbix")
async def reset_zabbix_settings():
    """Reset to environment defaults."""
    global _runtime
    _runtime = {}
    logger.info("🔄 Zabbix settings reset to environment defaults")
    return {"status": "reset"}


@router.post("/zabbix/test")
async def test_zabbix_connection(config: ZabbixConfig):
    """Test a Zabbix connection without saving it."""
    try:
        client = ZabbixClient(
            config.url.rstrip("/"),
            config.user,
            config.password,
        )
        ok = await client.authenticate()
        if ok:
            # Try to get a small sample
            problems = await client.get_problems(hours=1)
            return {
                "status": "success",
                "message": f"Connected successfully. Found {len(problems)} active problem(s).",
                "connected": True,
            }
        else:
            return {
                "status": "error",
                "message": "Authentication failed. Check URL, username, and password.",
                "connected": False,
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection error: {str(e)}",
            "connected": False,
        }
