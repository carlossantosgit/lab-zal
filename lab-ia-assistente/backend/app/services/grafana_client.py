import httpx
import uuid
import re
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Standard Node Exporter PromQL panels per category
_PANEL_DEFS = {
    "cpu": [
        {"title": "CPU Usage (%)", "expr": 'IFILTER100 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"ISEL}[5m])) * 100', "unit": "percent", "type": "timeseries"},
        {"title": "CPU System (%)", "expr": 'IFILTERavg by(instance)(rate(node_cpu_seconds_total{mode="system"ISEL}[5m])) * 100', "unit": "percent", "type": "timeseries"},
        {"title": "CPU User (%)", "expr": 'IFILTERavg by(instance)(rate(node_cpu_seconds_total{mode="user"ISEL}[5m])) * 100', "unit": "percent", "type": "timeseries"},
        {"title": "CPU I/O Wait (%)", "expr": 'IFILTERavg by(instance)(rate(node_cpu_seconds_total{mode="iowait"ISEL}[5m])) * 100', "unit": "percent", "type": "timeseries"},
    ],
    "memory": [
        {"title": "Memory Used (%)", "expr": 'IFILTER(1 - (node_memory_MemAvailable_bytes{ISEL} / node_memory_MemTotal_bytes{ISEL})) * 100', "unit": "percent", "type": "timeseries"},
        {"title": "Memory Available", "expr": 'IFILTERnode_memory_MemAvailable_bytes{ISEL}', "unit": "bytes", "type": "timeseries"},
        {"title": "Memory Buffers + Cache", "expr": 'IFILTER(node_memory_Buffers_bytes{ISEL} + node_memory_Cached_bytes{ISEL})', "unit": "bytes", "type": "timeseries"},
        {"title": "Swap Used", "expr": 'IFILTER(node_memory_SwapTotal_bytes{ISEL} - node_memory_SwapFree_bytes{ISEL})', "unit": "bytes", "type": "timeseries"},
    ],
    "disk": [
        {"title": 'Disk Usage / (%)', "expr": 'IFILTER(1 - node_filesystem_avail_bytes{fstype!="tmpfs",mountpoint="/"ISEL} / node_filesystem_size_bytes{fstype!="tmpfs",mountpoint="/"ISEL}) * 100', "unit": "percent", "type": "timeseries"},
        {"title": "Disk Read Bytes/s", "expr": 'IFILTERrate(node_disk_read_bytes_total{ISEL}[5m])', "unit": "Bps", "type": "timeseries"},
        {"title": "Disk Write Bytes/s", "expr": 'IFILTERrate(node_disk_written_bytes_total{ISEL}[5m])', "unit": "Bps", "type": "timeseries"},
        {"title": "Disk IOPS", "expr": 'IFILTERrate(node_disk_reads_completed_total{ISEL}[5m]) + rate(node_disk_writes_completed_total{ISEL}[5m])', "unit": "iops", "type": "timeseries"},
    ],
    "network": [
        {"title": "Network Receive Bytes/s", "expr": 'IFILTERrate(node_network_receive_bytes_total{device!="lo"ISEL}[5m])', "unit": "Bps", "type": "timeseries"},
        {"title": "Network Transmit Bytes/s", "expr": 'IFILTERrate(node_network_transmit_bytes_total{device!="lo"ISEL}[5m])', "unit": "Bps", "type": "timeseries"},
        {"title": "Network Receive Errors", "expr": 'IFILTERrate(node_network_receive_errs_total{device!="lo"ISEL}[5m])', "unit": "pps", "type": "timeseries"},
        {"title": "Network Transmit Errors", "expr": 'IFILTERrate(node_network_transmit_errs_total{device!="lo"ISEL}[5m])', "unit": "pps", "type": "timeseries"},
    ],
}


def _inject_filter(expr: str, instance_filter: str) -> str:
    """Inject instance filter into PromQL expression placeholders."""
    if not instance_filter:
        expr = expr.replace("IFILTER", "").replace("ISEL", "").replace("{}", "")
        expr = re.sub(r'\{,', '{', expr)
        return expr
    sel = f',instance=~"{instance_filter}"'
    expr = expr.replace("IFILTER", "").replace("ISEL", sel)
    expr = re.sub(r'\{,', '{', expr)
    return expr


class GrafanaClient:
    def __init__(self, url: str, user: str = "admin", password: str = "admin"):
        self.url = url.rstrip("/")
        self.user = user
        self.password = password

    async def _req(self, method: str, path: str, **kwargs) -> Any:
        async with httpx.AsyncClient(verify=False) as client:
            r = await client.request(
                method,
                f"{self.url}/api{path}",
                auth=(self.user, self.password),
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                timeout=15,
                **kwargs,
            )
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()

    async def health_check(self) -> bool:
        try:
            result = await self._req("GET", "/health")
            return result is not None
        except Exception as e:
            logger.error(f"Grafana health check failed: {e}")
            return False

    async def list_dashboards(self) -> List[Dict]:
        result = await self._req("GET", "/search?type=dash-db&limit=200")
        return result or []

    async def list_folders(self) -> List[Dict]:
        result = await self._req("GET", "/folders")
        return result or []

    async def create_folder(self, title: str) -> Dict:
        uid = re.sub(r"[^a-z0-9-]", "-", title.lower())[:40]
        return await self._req("POST", "/folders", json={"title": title, "uid": uid})

    async def create_dashboard(self, dashboard: Dict, folder_uid: str = None) -> Dict:
        payload = {"dashboard": dashboard, "overwrite": True, "message": "Created by AI Assistant"}
        if folder_uid:
            payload["folderUid"] = folder_uid
        result = await self._req("POST", "/dashboards/db", json=payload)
        logger.info(f"Dashboard created: {result.get('uid')} — {result.get('url')}")
        return result

    async def delete_dashboard(self, uid: str) -> Dict:
        return await self._req("DELETE", f"/dashboards/uid/{uid}")

    async def list_datasources(self) -> List[Dict]:
        result = await self._req("GET", "/datasources")
        return result or []

    # ── Panel builders ────────────────────────────────────────────────────────

    def _timeseries(self, pid: int, title: str, expr: str, unit: str,
                    x: int, y: int, w: int = 12, h: int = 8) -> Dict:
        return {
            "id": pid, "title": title, "type": "timeseries",
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [{"expr": expr, "legendFormat": "{{instance}}", "refId": "A"}],
            "fieldConfig": {
                "defaults": {
                    "unit": unit,
                    "color": {"mode": "palette-classic"},
                    "custom": {"lineWidth": 1, "fillOpacity": 10},
                },
                "overrides": [],
            },
            "options": {"tooltip": {"mode": "multi"}, "legend": {"displayMode": "list"}},
        }

    def _stat(self, pid: int, title: str, expr: str, unit: str,
              x: int, y: int, w: int = 6, h: int = 4) -> Dict:
        return {
            "id": pid, "title": title, "type": "stat",
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [{"expr": expr, "legendFormat": "", "instant": True, "refId": "A"}],
            "fieldConfig": {
                "defaults": {
                    "unit": unit,
                    "thresholds": {"mode": "absolute", "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 70},
                        {"color": "red", "value": 90},
                    ]},
                    "color": {"mode": "thresholds"},
                },
                "overrides": [],
            },
            "options": {"reduceOptions": {"calcs": ["lastNotNull"]}, "colorMode": "background"},
        }

    def _gauge(self, pid: int, title: str, expr: str, unit: str,
               x: int, y: int, w: int = 6, h: int = 8) -> Dict:
        return {
            "id": pid, "title": title, "type": "gauge",
            "datasource": {"type": "prometheus", "uid": "prometheus"},
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "targets": [{"expr": expr, "legendFormat": "", "instant": True, "refId": "A"}],
            "fieldConfig": {
                "defaults": {
                    "unit": unit, "min": 0, "max": 100,
                    "thresholds": {"mode": "absolute", "steps": [
                        {"color": "green", "value": None},
                        {"color": "yellow", "value": 70},
                        {"color": "red", "value": 90},
                    ]},
                    "color": {"mode": "thresholds"},
                },
                "overrides": [],
            },
        }

    # ── Dashboard builders ────────────────────────────────────────────────────

    def _make_uid(self, title: str) -> str:
        slug = re.sub(r"[^a-z0-9]", "-", title.lower())[:20]
        return f"{slug}-{str(uuid.uuid4())[:6]}"

    def _base_dashboard(self, title: str, panels: List[Dict]) -> Dict:
        return {
            "uid": self._make_uid(title),
            "title": title,
            "tags": ["ai-generated"],
            "panels": panels,
            "schemaVersion": 36,
            "version": 0,
            "refresh": "30s",
            "time": {"from": "now-1h", "to": "now"},
            "timezone": "browser",
        }

    def build_category_dashboard(self, title: str, category: str,
                                  instance_filter: str = "") -> Dict:
        """Build a dashboard for cpu/memory/disk/network."""
        defs = _PANEL_DEFS.get(category, _PANEL_DEFS["cpu"])
        panels = []
        pid = 1
        for i, d in enumerate(defs):
            x = (i % 2) * 12
            y = (i // 2) * 8
            expr = _inject_filter(d["expr"], instance_filter)
            panels.append(self._timeseries(pid, d["title"], expr, d["unit"], x, y))
            pid += 1
        return self._base_dashboard(title, panels)

    def build_overview_dashboard(self, title: str, instance_filter: str = "") -> Dict:
        """Build an overview dashboard with CPU, Memory, Disk, Network."""
        panels = []
        pid = 1
        y = 0

        def ifilter(expr: str) -> str:
            return _inject_filter(expr, instance_filter)

        cpu_expr = ifilter('IFILTER100 - avg by(instance)(rate(node_cpu_seconds_total{mode="idle"ISEL}[5m])) * 100')
        mem_expr = ifilter('IFILTER(1 - (node_memory_MemAvailable_bytes{ISEL} / node_memory_MemTotal_bytes{ISEL})) * 100')
        disk_expr = ifilter('IFILTER(1 - node_filesystem_avail_bytes{fstype!="tmpfs",mountpoint="/"ISEL} / node_filesystem_size_bytes{fstype!="tmpfs",mountpoint="/"ISEL}) * 100')

        # Row 0: stat cards
        panels.append(self._stat(pid, "CPU Usage", cpu_expr, "percent", 0, y, 8, 4)); pid += 1
        panels.append(self._stat(pid, "Memory Usage", mem_expr, "percent", 8, y, 8, 4)); pid += 1
        panels.append(self._stat(pid, "Disk Usage /", disk_expr, "percent", 16, y, 8, 4)); pid += 1
        y += 4

        # Row 1: CPU + Memory timeseries
        panels.append(self._timeseries(pid, "CPU Usage Over Time", cpu_expr, "percent", 0, y, 12, 8)); pid += 1
        panels.append(self._timeseries(pid, "Memory Usage Over Time", mem_expr, "percent", 12, y, 12, 8)); pid += 1
        y += 8

        # Row 2: Disk + Network
        panels.append(self._timeseries(pid, "Disk Usage / Over Time", disk_expr, "percent", 0, y, 12, 8)); pid += 1
        net_rx = ifilter('IFILTERrate(node_network_receive_bytes_total{device!="lo"ISEL}[5m])')
        panels.append(self._timeseries(pid, "Network Receive", net_rx, "Bps", 12, y, 12, 8)); pid += 1

        return self._base_dashboard(title, panels)

    def build_management_dashboard(self, title: str) -> Dict:
        """Executive/management dashboard: big KPI stats + trend charts."""
        panels = []
        pid = 1

        cpu_expr   = '100 - avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100'
        mem_expr   = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
        disk_expr  = '(1 - node_filesystem_avail_bytes{fstype!="tmpfs",mountpoint="/"} / node_filesystem_size_bytes{fstype!="tmpfs",mountpoint="/"}) * 100'
        net_rx     = 'sum(rate(node_network_receive_bytes_total{device!="lo"}[5m]))'
        net_tx     = 'sum(rate(node_network_transmit_bytes_total{device!="lo"}[5m]))'
        uptime     = 'node_time_seconds - node_boot_time_seconds'
        load1      = 'node_load1'

        # Row 0: KPI stat cards (full width)
        panels.append(self._stat(pid, "CPU Usage",    cpu_expr,  "percent", 0,  0, 6, 5)); pid += 1
        panels.append(self._stat(pid, "Memory Usage", mem_expr,  "percent", 6,  0, 6, 5)); pid += 1
        panels.append(self._stat(pid, "Disk Usage /", disk_expr, "percent", 12, 0, 6, 5)); pid += 1
        panels.append(self._stat(pid, "Load Average", load1,     "short",   18, 0, 6, 5)); pid += 1

        # Row 1: CPU + Memory trend
        panels.append(self._timeseries(pid, "CPU Usage — Últimas 6h",    cpu_expr, "percent", 0,  5, 12, 8)); pid += 1
        panels.append(self._timeseries(pid, "Memory Usage — Últimas 6h", mem_expr, "percent", 12, 5, 12, 8)); pid += 1

        # Row 2: Disk + Network
        panels.append(self._timeseries(pid, "Disk Usage /",          disk_expr, "percent", 0,  13, 12, 8)); pid += 1
        panels.append(self._timeseries(pid, "Network I/O (Bytes/s)", net_rx,    "Bps",     12, 13, 12, 8)); pid += 1

        # Row 3: Network TX + Uptime gauge
        panels.append(self._timeseries(pid, "Network Transmit (Bytes/s)", net_tx, "Bps", 0,  21, 12, 8)); pid += 1
        panels.append(self._gauge(pid, "Uptime (s)", uptime, "s", 12, 21, 12, 8)); pid += 1

        dash = self._base_dashboard(title, panels)
        dash["time"]    = {"from": "now-6h", "to": "now"}
        dash["tags"]    = ["ai-generated", "management", "overview"]
        return dash

    def build_custom_dashboard(self, title: str, panels_config: List[Dict]) -> Dict:
        """Build a dashboard from user-provided panel list."""
        panels = []
        pid = 1
        for i, cfg in enumerate(panels_config):
            x = (i % 2) * 12
            y = (i // 2) * 8
            ptype = cfg.get("type", "timeseries")
            if ptype == "stat":
                panels.append(self._stat(pid, cfg["title"], cfg["expr"], cfg.get("unit", "short"), x, y, 12, 8))
            elif ptype == "gauge":
                panels.append(self._gauge(pid, cfg["title"], cfg["expr"], cfg.get("unit", "percent"), x, y, 12, 8))
            else:
                panels.append(self._timeseries(pid, cfg["title"], cfg["expr"], cfg.get("unit", "short"), x, y))
            pid += 1
        return self._base_dashboard(title, panels)
