import httpx
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ZabbixClient:
    def __init__(self, url: str, user: str, password: str):
        self.url = url
        self.user = user
        self.password = password
        self.auth_token = None
        self.request_id = 1

    async def authenticate(self):
        """Authenticate with Zabbix API"""
        logger.info(f"🔌 Attempting Zabbix auth: {self.url}")
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "user.login",
                    "params": {
                        "user": self.user,
                        "password": self.password,
                    },
                    "id": self.request_id,
                }
                self.request_id += 1

                response = await client.post(
                    f"{self.url}/api_jsonrpc.php",
                    json=payload,
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()

                if "result" in data:
                    self.auth_token = data["result"]
                    logger.info(f"✅ Authenticated with Zabbix at {self.url}")
                    return True
                else:
                    error_msg = data.get('error', {}).get('data', str(data.get('error')))
                    logger.error(f"❌ Auth failed: {error_msg}")
                    return False
        except Exception as e:
            logger.error(f"❌ Authentication error: {type(e).__name__}: {e}")
            return False

    async def get_events(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent events/alerts from Zabbix"""
        if not self.auth_token:
            await self.authenticate()

        try:
            async with httpx.AsyncClient() as client:
                # Calculate time range
                from_time = int((datetime.utcnow() - timedelta(hours=hours)).timestamp())

                payload = {
                    "jsonrpc": "2.0",
                    "method": "event.get",
                    "params": {
                        "output": ["eventid", "clock", "ns", "value", "source"],
                        "selectHosts": ["hostid", "host"],
                        "selectRelatedObject": "extend",
                        "sortfield": ["clock"],
                        "sortorder": "DESC",
                        "limit": 100,
                        "filter": {"clock": {">": from_time}},
                    },
                    "auth": self.auth_token,
                    "id": self.request_id,
                }
                self.request_id += 1

                response = await client.post(
                    f"{self.url}/api_jsonrpc.php",
                    json=payload,
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()

                if "result" in data:
                    logger.info(f"✅ Retrieved {len(data['result'])} events")
                    return data["result"]
                else:
                    logger.error(f"❌ Error getting events: {data.get('error')}")
                    return []
        except Exception as e:
            logger.error(f"❌ Error fetching events: {e}")
            return []

    async def get_problems(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get current problems from Zabbix"""
        if not self.auth_token:
            await self.authenticate()

        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "problem.get",
                    "params": {
                        "output": ["eventid", "name", "severity", "clock"],
                        "selectHosts": ["host"],
                        "selectAcknowledges": "extend",
                        "sortfield": ["severity", "clock"],
                        "sortorder": ["DESC", "DESC"],
                        "limit": 200,
                    },
                    "auth": self.auth_token,
                    "id": self.request_id,
                }
                self.request_id += 1

                response = await client.post(
                    f"{self.url}/api_jsonrpc.php",
                    json=payload,
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()

                if "result" in data:
                    logger.info(f"✅ Retrieved {len(data['result'])} problems")
                    return data["result"]
                else:
                    logger.error(f"❌ Error getting problems: {data.get('error')}")
                    return []
        except Exception as e:
            logger.error(f"❌ Error fetching problems: {e}")
            return []

    def _parse_severity(self, severity_code: int) -> str:
        """Convert Zabbix severity code to string"""
        severity_map = {
            0: "info",
            1: "warning",
            2: "average",
            3: "high",
            4: "disaster",
        }
        return severity_map.get(severity_code, "unknown")
