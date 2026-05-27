import httpx
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

SEVERITY_MAP = {
    "info": 1, "warning": 2, "average": 3, "high": 4, "disaster": 5,
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
}
VALUE_TYPE_MAP = {
    "float": 0, "numeric": 0, "uint": 3, "unsigned": 3,
    "string": 1, "str": 1, "text": 4, "log": 2,
    "0": 0, "1": 1, "2": 2, "3": 3, "4": 4,
}


class ZabbixManager:
    """Extended Zabbix API client with full create/manage capabilities."""

    def __init__(self, url: str, user: str, password: str):
        self.url = url.rstrip("/")
        self.user = user
        self.password = password
        self.auth_token: Optional[str] = None
        self._req_id = 1

    async def _call(self, method: str, params: dict) -> Any:
        if not self.auth_token and method != "user.login":
            await self.authenticate()
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._req_id,
        }
        if self.auth_token:
            payload["auth"] = self.auth_token
        self._req_id += 1
        async with httpx.AsyncClient(verify=False) as client:
            r = await client.post(
                f"{self.url}/api_jsonrpc.php",
                json=payload,
                timeout=15,
            )
            r.raise_for_status()
            data = r.json()
        if "error" in data:
            raise Exception(data["error"].get("data", str(data["error"])))
        return data["result"]

    async def authenticate(self) -> bool:
        try:
            result = await self._call("user.login", {"user": self.user, "password": self.password})
            self.auth_token = result
            logger.info(f"Authenticated with Zabbix at {self.url}")
            return True
        except Exception as e:
            logger.error(f"Zabbix auth failed: {e}")
            return False

    # ── Read operations ───────────────────────────────────────────────────────

    async def get_hosts(self) -> List[Dict]:
        return await self._call("host.get", {
            "output": ["hostid", "host", "name"],
            "selectGroups": ["groupid", "name"],
        })

    async def get_templates(self) -> List[Dict]:
        return await self._call("template.get", {
            "output": ["templateid", "host", "name"],
        })

    async def get_hostgroups(self) -> List[Dict]:
        return await self._call("hostgroup.get", {"output": ["groupid", "name"]})

    async def get_items(self, hostid: str) -> List[Dict]:
        return await self._call("item.get", {
            "output": ["itemid", "name", "key_", "value_type", "units", "delay"],
            "hostids": hostid,
            "limit": 200,
        })

    async def get_triggers(self, hostid: str = None) -> List[Dict]:
        params: Dict = {
            "output": ["triggerid", "description", "expression", "priority", "status"],
            "expandExpression": True,
        }
        if hostid:
            params["hostids"] = hostid
        return await self._call("trigger.get", params)

    def find_host(self, name: str, hosts: List[Dict]) -> Optional[Dict]:
        """Find host by exact or partial name match."""
        nl = name.lower()
        for h in hosts:
            if h["host"].lower() == nl:
                return h
        for h in hosts:
            if nl in h["host"].lower() or h["host"].lower() in nl:
                return h
        return None

    def find_hostgroup(self, name: str, groups: List[Dict]) -> Optional[Dict]:
        """Find host group by exact or partial name match."""
        nl = name.lower()
        for g in groups:
            if g["name"].lower() == nl:
                return g
        for g in groups:
            if nl in g["name"].lower():
                return g
        # fallback: return first group
        return groups[0] if groups else None

    # ── Create operations ─────────────────────────────────────────────────────

    async def create_item(self, hostid: str, name: str, key_: str,
                          value_type: Any = 0, item_type: int = 2,
                          delay: str = "60s", units: str = "") -> Dict:
        """Create a Zabbix item. item_type=2 means Zabbix trapper (no agent needed for testing)."""
        vt = VALUE_TYPE_MAP.get(str(value_type).lower(), value_type if isinstance(value_type, int) else 0)
        result = await self._call("item.create", {
            "hostid": hostid,
            "name": name,
            "key_": key_,
            "type": item_type,
            "value_type": vt,
            "delay": delay if item_type != 2 else "0",
            "units": units,
        })
        return result

    async def create_trigger(self, description: str, expression: str,
                             priority: Any = 2, comments: str = "") -> Dict:
        """Create a Zabbix trigger."""
        prio = SEVERITY_MAP.get(str(priority).lower(), priority if isinstance(priority, int) else 2)
        result = await self._call("trigger.create", {
            "description": description,
            "expression": expression,
            "priority": prio,
            "comments": comments,
            "status": 0,
        })
        return result

    async def create_template(self, name: str, group_ids: List[str] = None,
                              description: str = "") -> Dict:
        if not group_ids:
            groups = await self.get_hostgroups()
            tmpl_groups = [g for g in groups if "template" in g["name"].lower()]
            group_ids = [tmpl_groups[0]["groupid"]] if tmpl_groups else [groups[0]["groupid"]] if groups else []
        result = await self._call("template.create", {
            "host": name,
            "name": name,
            "description": description,
            "groups": [{"groupid": gid} for gid in group_ids],
        })
        return result

    async def create_host(self, hostname: str, group_ids: List[str],
                          ip: str = "127.0.0.1", port: int = 10050,
                          template_ids: List[str] = None) -> Dict:
        params: Dict = {
            "host": hostname,
            "interfaces": [{
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": ip,
                "dns": "",
                "port": str(port),
            }],
            "groups": [{"groupid": gid} for gid in group_ids],
        }
        if template_ids:
            params["templates"] = [{"templateid": tid} for tid in template_ids]
        return await self._call("host.create", params)

    async def create_hostgroup(self, name: str) -> Dict:
        return await self._call("hostgroup.create", {"name": name})

    # ── Diagnostic operations ─────────────────────────────────────────────────

    async def get_active_problems(self, hostid: str = None) -> List[Dict]:
        params: Dict = {
            "output": ["eventid", "name", "severity", "clock", "acknowledged"],
            "selectHosts": ["hostid", "host"],
            "selectAcknowledges": ["message", "clock"],
            "limit": 100,
        }
        if hostid:
            params["hostids"] = hostid
        problems = await self._call("problem.get", params)
        now = int(datetime.now().timestamp())
        for p in problems:
            age = now - int(p.get("clock", now))
            if age < 60:
                p["duration"] = f"{age}s"
            elif age < 3600:
                p["duration"] = f"{age // 60}m"
            elif age < 86400:
                p["duration"] = f"{age // 3600}h {(age % 3600) // 60}m"
            else:
                p["duration"] = f"{age // 86400}d {(age % 86400) // 3600}h"
            p["acknowledged"] = p.get("acknowledged") == "1"
        return problems

    async def get_host_availability(self, hostid: str) -> Dict:
        result = await self._call("host.get", {
            "output": ["hostid", "host", "available", "error", "ipmi_available", "snmp_available"],
            "hostids": hostid,
        })
        return result[0] if result else {}

    async def acknowledge_problem(self, eventid: str, message: str) -> Dict:
        return await self._call("event.acknowledge", {
            "eventids": eventid,
            "action": 6,  # acknowledge + add message
            "message": message,
        })

    async def close_problem(self, eventid: str, message: str) -> Dict:
        """Try to close the problem event. Falls back to acknowledge-only if close not allowed."""
        try:
            return await self._call("event.acknowledge", {
                "eventids": eventid,
                "action": 7,  # close (1) + acknowledge (2) + message (4)
                "message": message,
            })
        except Exception:
            return await self.acknowledge_problem(eventid, message)

    async def disable_trigger(self, triggerid: str) -> Dict:
        return await self._call("trigger.update", {"triggerid": triggerid, "status": 1})

    async def enable_trigger(self, triggerid: str) -> Dict:
        return await self._call("trigger.update", {"triggerid": triggerid, "status": 0})

    async def create_maintenance(self, name: str, hostids: List[str], duration_hours: int = 4) -> Dict:
        import time
        now = int(time.time())
        till = now + duration_hours * 3600
        return await self._call("maintenance.create", {
            "name": name,
            "active_since": now,
            "active_till": till,
            "hostids": hostids,
            "timeperiods": [{"timeperiod_type": 0, "period": duration_hours * 3600}],
        })

    _COMMON_WORDS = {"zabbix", "server", "with", "from", "this", "that", "have", "host", "item", "the"}

    async def setup_internal_monitoring(self, hostid: str) -> List[str]:
        """Add Zabbix internal check items (type=5) that work without an agent."""
        candidates = [
            {"name": "Zabbix: Host availability",         "key_": "zabbix[host,,available]",              "value_type": 3},
            {"name": "Zabbix: Queue size",                 "key_": "zabbix[queue]",                        "value_type": 3},
            {"name": "Zabbix: Monitored hosts",            "key_": "zabbix[hosts]",                        "value_type": 3},
            {"name": "Zabbix: Monitored items",            "key_": "zabbix[items]",                        "value_type": 3},
            {"name": "Zabbix: Required performance (nvps)","key_": "zabbix[rcache,buffer,pused]",           "value_type": 0},
            {"name": "Zabbix: Trapper busy %",             "key_": "zabbix[process,trapper,avg,busy]",     "value_type": 0},
            {"name": "Zabbix: Housekeeper busy %",         "key_": "zabbix[process,housekeeper,avg,busy]", "value_type": 0},
        ]
        existing = await self.get_items(hostid)
        existing_keys = {i["key_"] for i in existing}
        created = []
        for item in candidates:
            if item["key_"] in existing_keys:
                continue
            try:
                await self._call("item.create", {
                    "hostid": hostid,
                    "name": item["name"],
                    "key_": item["key_"],
                    "type": 5,        # Zabbix internal
                    "value_type": item["value_type"],
                    "delay": "60s",
                })
                created.append(item["name"])
            except Exception as e:
                logger.debug(f"Internal item {item['key_']} skipped: {e}")
        return created

    async def find_trigger_by_problem(self, hostid: str, problem_name: str) -> Optional[Dict]:
        """Find the trigger whose description best matches a problem name using word overlap scoring."""
        triggers = await self._call("trigger.get", {
            "output": ["triggerid", "description", "expression", "status"],
            "hostids": hostid,
            "expandExpression": True,
        })
        pn = problem_name.lower()

        # Exact match first
        for t in triggers:
            if t["description"].lower() == pn:
                return t

        # Substring match (problem name starts with trigger description)
        for t in triggers:
            desc = t["description"].lower()
            if pn.startswith(desc) or desc in pn:
                return t

        # Scored word overlap — skip common/noise words
        pn_words = {w.strip("().,") for w in pn.split()
                    if len(w.strip("().,")) > 4 and w.strip("().,") not in self._COMMON_WORDS}

        best_score, best_trigger = 0, None
        for t in triggers:
            desc_words = {w.strip("().,") for w in t["description"].lower().split()
                          if len(w.strip("().,")) > 4 and w.strip("().,") not in self._COMMON_WORDS}
            overlap = len(pn_words & desc_words)
            if overlap > best_score:
                best_score = overlap
                best_trigger = t

        # Require at least 2 meaningful word matches to avoid false positives
        return best_trigger if best_score >= 2 else None
