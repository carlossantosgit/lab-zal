#!/usr/bin/env python3
# -*- coding: ascii -*-
"""
Sincronizacao Prometheus -> Zabbix (OPTIMIZADO)
- Pre-fetch de items/triggers existentes (2 chamadas vs 2*N)
- Batch create de items e triggers (2 chamadas/host vs 84)
- 3 chamadas Prometheus total (/targets, /rules, /alerts)
"""

import sys
import time
import ssl
import json
import re
import hashlib
import argparse
import socket
import struct
import subprocess
import tempfile
import requests
from collections import defaultdict

from config import (
    logger,
    ZABBIX_API_URL, ZABBIX_USER, ZABBIX_PASSWORD, ZABBIX_VERIFY_SSL,
    PROMETHEUS_URL, PROMETHEUS_USER, PROMETHEUS_PASS, PROMETHEUS_VERIFY_SSL,
)

# ---------------------------------------------------------------------------
# Zabbix priority por severidade Prometheus
# 0=Not classified, 1=Information, 2=Warning, 3=Average, 4=High, 5=Disaster
# ---------------------------------------------------------------------------
PRIORITY_MAP = {
    "info":      1,
    "none":      1,
    "warning":   2,
    "average":   3,
    "high":      4,
    "critical":  5,
    "emergency": 5,
    "page":      5,
}

# Threshold UNICO por severidade -> expressoes trigger diferentes
SEVERITY_THRESHOLD = {
    "info":      1,
    "none":      1,
    "warning":   2,
    "average":   3,
    "high":      4,
    "critical":  5,
    "emergency": 6,
    "page":      6,
}

# Labels standard - NAO distinguem instancias
META_LABELS = frozenset([
    "__name__", "alertname", "alertstate", "severity",
    "instance", "job", "monitor", "prometheus",
    "prometheus_replica", "replica", "exported_instance",
    "exported_job",
])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize(name, maxlen=64):
    out = ""
    for c in str(name).strip():
        out += c if c.isalnum() or c in "._-" else "_"
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_").lower()[:maxlen] or "unknown"


def hostname_from_instance(instance):
    if "://" in instance:
        try:
            from urllib.parse import urlparse
            return urlparse(instance).hostname or instance
        except Exception:
            return instance
    if instance.startswith("["):
        idx = instance.find("]")
        if idx > 0:
            return instance[1:idx]
    return instance.split(":")[0] if ":" in instance else instance


def instance_uid(labels_dict):
    s = json.dumps(labels_dict, sort_keys=True)
    return hashlib.md5(s.encode()).hexdigest()[:8]


def extract_instance_labels(labels):
    extra = {}
    for k, v in labels.items():
        if k not in META_LABELS and v:
            extra[k] = v
    return extra


def _is_ip(host):
    """Verifica se host e um endereco IPv4."""
    parts = host.split(".")
    if len(parts) != 4:
        return False
    return all(p.isdigit() and 0 <= int(p) <= 255 for p in parts)


# ===========================================================================
# PrometheusSync
# ===========================================================================

class PrometheusSync:

    def __init__(self):
        self.auth_token = None
        self._group_id = None
        self._session = requests.Session()
        self._canonical_map = {}  # IP/alias -> canonical hostname

    # -----------------------------------------------------------------------
    # Zabbix API
    # -----------------------------------------------------------------------

    def _zabbix_call(self, method, params, retries=3):
        body = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        if self.auth_token:
            body["auth"] = self.auth_token

        for attempt in range(retries):
            try:
                r = self._session.post(
                    ZABBIX_API_URL, json=body,
                    verify=ZABBIX_VERIFY_SSL, timeout=120,
                )
                r.raise_for_status()
                data = r.json()
                if "error" in data:
                    raise RuntimeError(str(data["error"]))
                return data["result"]
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout,
                    ConnectionResetError, OSError, ssl.SSLError) as e:
                if attempt < retries - 1:
                    wait = 2 ** (attempt + 1)
                    logger.warning("Retry %s em %ds: %s", method, wait, e)
                    time.sleep(wait)
                else:
                    raise

    def login_zabbix(self):
        self.auth_token = self._zabbix_call(
            "user.login",
            {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD},
        )
        logger.info("Zabbix: login OK")
        return True

    def get_group_id(self, name="Prometheus"):
        if self._group_id:
            return self._group_id
        gs = self._zabbix_call("hostgroup.get", {"filter": {"name": name}})
        if gs:
            self._group_id = gs[0]["groupid"]
        else:
            r = self._zabbix_call("hostgroup.create", {"name": name})
            self._group_id = r["groupids"][0]
        return self._group_id

    def get_all_hosts(self):
        hosts = self._zabbix_call("host.get", {"output": ["hostid", "host"]})
        return {h["host"]: h["hostid"] for h in hosts}

    def create_host(self, hostname, display_name, group_id):
        r = self._zabbix_call("host.create", {
            "host": hostname,
            "name": (display_name or hostname)[:128],
            "groups": [{"groupid": group_id}],
            "interfaces": [{
                "type": 1, "main": 1, "useip": 1,
                "ip": "127.0.0.1", "dns": "", "port": "10050",
            }],
        })
        return r["hostids"][0]

    # -----------------------------------------------------------------------
    # Pre-fetch: obter TODOS os items/triggers do grupo em 2 chamadas
    # -----------------------------------------------------------------------

    def prefetch_group_items(self, group_id):
        """Obtem todos os item keys por hostid do grupo (1 chamada API)."""
        items = self._zabbix_call("item.get", {
            "output": ["key_", "hostid"],
            "groupids": group_id,
        })
        by_host = defaultdict(set)
        for i in items:
            by_host[i["hostid"]].add(i["key_"])
        logger.info("Pre-fetch: %d items em %d hosts", len(items),
                    len(by_host))
        return by_host

    def prefetch_group_triggers(self, group_id):
        """Obtem todas as trigger expressions por hostid do grupo (1 chamada)."""
        trigs = self._zabbix_call("trigger.get", {
            "output": ["expression"],
            "groupids": group_id,
            "selectHosts": ["hostid"],
        })
        by_host = defaultdict(set)
        for t in trigs:
            for h in t.get("hosts", []):
                by_host[h["hostid"]].add(t["expression"])
        logger.info("Pre-fetch: %d triggers em %d hosts", len(trigs),
                    len(by_host))
        return by_host

    # -----------------------------------------------------------------------
    # Batch create: criar N items ou triggers numa unica chamada API
    # -----------------------------------------------------------------------

    def batch_create_items(self, items_list):
        """Cria multiplos items numa unica chamada. Retorna quantidade criada."""
        if not items_list:
            return 0
        try:
            result = self._zabbix_call("item.create", items_list)
            return len(result.get("itemids", []))
        except RuntimeError as e:
            err = str(e).lower()
            if "already exists" in err:
                # Algum item ja existe -> criar um a um os restantes
                created = 0
                for item in items_list:
                    try:
                        self._zabbix_call("item.create", item)
                        created += 1
                    except RuntimeError:
                        pass
                return created
            logger.warning("Batch item.create erro: %s", e)
            return 0

    def batch_create_triggers(self, triggers_list):
        """Cria multiplas triggers numa unica chamada. Retorna qtd criada."""
        if not triggers_list:
            return 0
        try:
            result = self._zabbix_call("trigger.create", triggers_list)
            return len(result.get("triggerids", []))
        except RuntimeError as e:
            err = str(e).lower()
            if "already exists" in err:
                created = 0
                for trig in triggers_list:
                    try:
                        self._zabbix_call("trigger.create", trig)
                        created += 1
                    except RuntimeError:
                        pass
                return created
            logger.warning("Batch trigger.create erro: %s", e)
            return 0

    # -----------------------------------------------------------------------
    # Prometheus API
    # -----------------------------------------------------------------------

    def _prom_get(self, path, params=None):
        resp = requests.get(
            "%s%s" % (PROMETHEUS_URL, path),
            params=params,
            auth=(PROMETHEUS_USER, PROMETHEUS_PASS) if PROMETHEUS_PASS else None,
            verify=PROMETHEUS_VERIFY_SSL,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def get_targets(self):
        """Obtem TODOS os targets activos com consolidacao de hosts.
        Hosts com mesmo IP mas nomes diferentes sao agrupados num
        unico hostname canonico (preferencia para nome vs IP).
        Retorna (targets_by_job, all_targets).
        """
        data = self._prom_get("/api/v1/targets")

        # Pass 1: Recolher targets com metadata para consolidacao
        raw = []
        ip_to_names = defaultdict(set)

        for t in data.get("data", {}).get("activeTargets", []):
            labels = t.get("labels", {})
            instance = labels.get("instance", "")
            job = labels.get("job", "")
            if not instance:
                continue

            host = sanitize(hostname_from_instance(instance))

            # Extrair IP de discoveredLabels ou scrapeUrl
            ip = None
            disc = t.get("discoveredLabels", {})
            for source in [disc.get("__address__", ""),
                           t.get("scrapeUrl", "")]:
                if source:
                    raw_host = hostname_from_instance(source)
                    if _is_ip(raw_host):
                        ip = raw_host
                        break

            # Se o host ja e IP, usar directamente
            if not ip and _is_ip(host):
                ip = host

            # Mapear IP -> todos os nomes conhecidos
            if ip:
                ip_to_names[ip].add(host)

            raw.append({"host": host, "instance": instance,
                        "job": job, "ip": ip})

        # Pass 2: Canonical map a partir dos metadados
        canonical = {}
        for ip, names in ip_to_names.items():
            if len(names) <= 1:
                continue
            # Preferir nome (nao-IP), alfabeticamente primeiro
            non_ip = sorted(n for n in names if not _is_ip(n))
            if non_ip:
                canon = non_ip[0]
                for n in names:
                    if n != canon:
                        canonical[n] = canon

        # Pass 3: DNS reverso para IPs sem canonical
        ip_only = set()
        all_names = set(e["host"] for e in raw)
        for entry in raw:
            h = entry["host"]
            if _is_ip(h) and h not in canonical:
                ip_only.add(h)

        if ip_only:
            logger.info("DNS reverso para %d hosts IP...", len(ip_only))
            resolved = 0
            for ip in ip_only:
                try:
                    fqdn = socket.gethostbyaddr(ip)[0]
                    short = sanitize(fqdn.split(".")[0])
                    if short and not _is_ip(short):
                        # Verificar se o hostname ja existe nos targets
                        if short in all_names:
                            canonical[ip] = short
                            resolved += 1
                        else:
                            # Hostname novo - usar como canonical
                            canonical[ip] = short
                            all_names.add(short)
                            resolved += 1
                except (socket.herror, socket.gaierror, OSError):
                    pass
            if resolved:
                logger.info("  DNS: %d IPs resolvidos", resolved)

        # Guardar canonical map para uso em build_host_plan
        self._canonical_map = canonical

        if canonical:
            logger.info("Consolidacao: %d hosts mapeados", len(canonical))
            for old, new in sorted(canonical.items())[:15]:
                logger.info("  %s -> %s", old, new)

        # Pass 4: Construir targets consolidados
        targets_by_job = defaultdict(list)
        all_targets = {}

        for entry in raw:
            host = canonical.get(entry["host"], entry["host"])
            instance = entry["instance"]
            job = entry["job"]

            if host not in all_targets:
                all_targets[host] = instance
            if job:
                exists = any(e["hostname"] == host
                             for e in targets_by_job[job])
                if not exists:
                    targets_by_job[job].append(
                        {"hostname": host, "display": instance})

        logger.info("Prometheus targets: %d hosts, %d jobs",
                    len(all_targets), len(targets_by_job))
        return targets_by_job, all_targets

    def get_alert_rules(self):
        """Obtem regras de alerta. Retorna {alertname: {severities, jobs}}."""
        data = self._prom_get("/api/v1/rules")
        rules = defaultdict(lambda: {"severities": {}, "jobs": set()})
        count = 0

        for group in data.get("data", {}).get("groups", []):
            for rule in group.get("rules", []):
                if rule.get("type") not in ("alerting", "alert"):
                    continue
                alert_name = rule.get("alert", "") or rule.get("name", "")
                if not alert_name:
                    continue
                count += 1

                labels = rule.get("labels", {})
                annotations = rule.get("annotations", {})
                expr = rule.get("query", "") or rule.get("expr", "") or ""
                severity = labels.get("severity", "warning").lower()
                desc = (annotations.get("description", "")
                        or annotations.get("summary", ""))[:200]

                rules[alert_name]["severities"][severity] = {
                    "expr": expr, "desc": desc,
                }

                for m in re.finditer(r'job\s*=~?\s*"([^"]+)"', expr):
                    rules[alert_name]["jobs"].add(m.group(1))
                job_label = labels.get("job", "")
                if job_label and "{{" not in job_label:
                    rules[alert_name]["jobs"].add(job_label)

                # Extrair jobs dos alertas activos DENTRO da regra
                for active in rule.get("alerts", []):
                    al = active.get("labels", {})
                    aj = al.get("job", "")
                    if aj:
                        rules[alert_name]["jobs"].add(aj)

        logger.info("Prometheus rules: %d regras -> %d alertas unicos",
                    count, len(rules))
        all_sevs = set()
        for r in rules.values():
            all_sevs.update(r["severities"].keys())
        logger.info("  Severidades encontradas: %s",
                    ", ".join(sorted(all_sevs)))

        return dict(rules)

    def get_active_alerts(self):
        """Obtem TODOS os alertas activos (1 unica chamada)."""
        data = self._prom_get("/api/v1/alerts")
        alerts = data.get("data", {}).get("alerts", [])
        logger.info("Prometheus alertas activos: %d instancias", len(alerts))
        return alerts

    # -----------------------------------------------------------------------
    # Descoberta de jobs para regras sem job explicito
    # -----------------------------------------------------------------------

    def _extract_metric(self, expr):
        """Extrai metrica de PromQL, incluindo label selectors se houver.
        Ex: up{service="tomcat"} em vez de so 'up'."""
        if not expr:
            return None
        # Padrao 1: metric{labels} -> retorna tudo para query precisa
        m = re.search(r'([a-zA-Z_:][a-zA-Z0-9_:]*\s*\{[^}]*\})', expr)
        if m:
            return m.group(1).strip()
        # Padrao 2: metric sem labels
        SKIP = frozenset([
            "abs", "absent", "avg", "by", "ceil", "changes", "clamp",
            "clamp_max", "clamp_min", "count", "count_values", "delta",
            "deriv", "exp", "floor", "group", "histogram_quantile",
            "hour", "idelta", "increase", "irate", "label_join",
            "label_replace", "ln", "log2", "log10", "max", "min",
            "minute", "month", "predict_linear", "quantile", "rate",
            "resets", "round", "scalar", "sgn", "sort", "sort_desc",
            "sqrt", "stddev", "stdvar", "sum", "time", "timestamp",
            "topk", "bottomk", "vector", "year", "without", "on",
            "ignoring", "group_left", "group_right", "bool", "and",
            "or", "unless", "offset", "instance", "mode", "job",
        ])
        for m in re.finditer(r'([a-zA-Z_][a-zA-Z0-9_:]*)', expr):
            name = m.group(1)
            if name.lower() not in SKIP and len(name) > 1:
                return name
        return None

    def _query_metric_jobs(self, metric):
        """Consulta Prometheus: quais jobs exportam esta metrica?"""
        try:
            data = self._prom_get(
                "/api/v1/query",
                params={"query": "count by (job) (%s)" % metric})
            jobs = set()
            for result in data.get("data", {}).get("result", []):
                job = result.get("metric", {}).get("job", "")
                if job:
                    jobs.add(job)
            return jobs
        except Exception:
            return set()

    def resolve_rule_jobs(self, rules, targets_by_job, active_alerts):
        """Resolve jobs para TODAS as regras:
        1) Enriquecer com jobs dos alertas activos
        2) Resolver padroes regex (ex: Linux.* -> Linux Host xyz)
        3) Descobrir via metricas PromQL (ex: node_* -> job node)
        """
        all_jobs = set(targets_by_job.keys())

        # 1) Enriquecer com jobs dos alertas activos
        for alert in active_alerts:
            labels = alert.get("labels", {})
            aname = labels.get("alertname", "")
            job = labels.get("job", "")
            if aname and job and aname in rules:
                rules[aname]["jobs"].add(job)

        # 2) Resolver padroes regex para jobs reais
        for rule_data in rules.values():
            resolved = set()
            for pattern in list(rule_data["jobs"]):
                if pattern in all_jobs:
                    resolved.add(pattern)
                else:
                    # Tentar como regex
                    try:
                        for actual_job in all_jobs:
                            if re.fullmatch(pattern, actual_job):
                                resolved.add(actual_job)
                    except re.error:
                        pass
            rule_data["jobs"] = resolved

        # 3) Descobrir jobs via metricas para TODAS as regras
        metrics_cache = {}
        before_counts = {n: len(r["jobs"]) for n, r in rules.items()}

        logger.info("Descobrindo jobs via metricas para %d regras...",
                    len(rules))
        for alert_name, rule_data in rules.items():
            for sev_data in rule_data["severities"].values():
                expr = sev_data.get("expr", "")
                metric = self._extract_metric(expr)
                if not metric:
                    continue

                if metric not in metrics_cache:
                    jobs = self._query_metric_jobs(metric)
                    metrics_cache[metric] = jobs

                jobs = metrics_cache[metric]
                if jobs:
                    rule_data["jobs"].update(jobs)
                    break

        # 4) Fallback: familia de prefixo de metrica
        #    Se node_cpu resolve para jobs, node_memory tambem deve
        prefix_jobs = {}
        for metric, jobs in metrics_cache.items():
            if not jobs:
                continue
            base = metric.split("{")[0].strip()
            parts = base.split("_")
            if len(parts) >= 2:
                prefix = parts[0] + "_"
                if prefix not in prefix_jobs:
                    prefix_jobs[prefix] = set()
                prefix_jobs[prefix].update(jobs)

        fallback_count = 0
        for alert_name, rule_data in rules.items():
            if rule_data["jobs"]:
                continue
            for sev_data in rule_data["severities"].values():
                expr = sev_data.get("expr", "")
                metric = self._extract_metric(expr)
                if not metric:
                    continue
                base = metric.split("{")[0].strip()
                parts = base.split("_")
                if len(parts) >= 2:
                    prefix = parts[0] + "_"
                    if prefix in prefix_jobs:
                        rule_data["jobs"].update(prefix_jobs[prefix])
                        fallback_count += 1
                        logger.info("  %s -> %d jobs (via prefixo %s)",
                                    alert_name[:30],
                                    len(prefix_jobs[prefix]), prefix)
                        break

        # Log resumo
        improved = sum(1 for n, r in rules.items()
                       if len(r["jobs"]) > before_counts[n])
        with_jobs = sum(1 for r in rules.values() if r["jobs"])
        without_jobs = sum(1 for r in rules.values() if not r["jobs"])
        logger.info("Metric discovery: %d regras melhoradas, "
                    "%d via prefixo", improved, fallback_count)
        logger.info("Jobs resolvidos: %d com jobs, %d sem jobs",
                    with_jobs, without_jobs)
        if without_jobs > 0:
            no_jobs = [n for n, r in rules.items() if not r["jobs"]]
            logger.info("  Sem jobs: %s", ", ".join(sorted(no_jobs)))

    # -----------------------------------------------------------------------
    # Build sync plan per host
    # -----------------------------------------------------------------------

    def _match_rules_to_host(self, hostname, rules, targets_by_job):
        """Determina quais regras se aplicam a este host via jobs.
        SEM fallback 'aplica a todos' - so matcheia via jobs reais.
        """
        matched = set()
        for alert_name, rule_data in rules.items():
            if not rule_data["jobs"]:
                # Sem jobs conhecidos - nao aplica (sera adicionado
                # via alertas activos se estiver a disparar neste host)
                continue
            for job in rule_data["jobs"]:
                targets = targets_by_job.get(job, [])
                if any(t["hostname"] == hostname for t in targets):
                    matched.add(alert_name)
                    break
        return matched

    def build_host_plan(self, hostname, rules, active_alerts,
                        targets_by_job):
        """Constroi plano de items+triggers para um host."""
        plan = {}

        # 1) Items BASE a partir das regras
        matched_rules = self._match_rules_to_host(hostname, rules,
                                                   targets_by_job)
        for alert_name in matched_rules:
            rule_data = rules[alert_name]
            item_key = "prometheus.%s" % sanitize(alert_name, 50)

            if item_key not in plan:
                plan[item_key] = {
                    "item_key": item_key,
                    "item_name": alert_name,
                    "item_desc": "Prometheus alert: %s" % alert_name,
                    "triggers": [],
                }

            for sev in rule_data["severities"]:
                thr = SEVERITY_THRESHOLD.get(sev, 2)
                prio = PRIORITY_MAP.get(sev, 2)
                if not any(t["threshold"] == thr
                           for t in plan[item_key]["triggers"]):
                    plan[item_key]["triggers"].append({
                        "desc": "%s [%s]" % (alert_name, sev.capitalize()),
                        "priority": prio,
                        "threshold": thr,
                    })

        # 2) Items INSTANCIA a partir de alertas activos
        for alert in active_alerts:
            labels = alert.get("labels", {})
            instance = labels.get("instance", "")
            if not instance:
                continue

            alert_host = sanitize(hostname_from_instance(instance))
            alert_host = self._canonical_map.get(alert_host, alert_host)
            if alert_host != hostname:
                continue

            alert_name = labels.get("alertname", "")
            severity = labels.get("severity", "warning").lower()
            if not alert_name:
                continue

            extra = extract_instance_labels(labels)

            if extra:
                uid = instance_uid(extra)
                item_key = "prometheus.%s.%s" % (
                    sanitize(alert_name, 40), uid)
                desc_parts = ["%s=%s" % (k, v)
                              for k, v in sorted(extra.items())[:5]]
                item_name = "%s (%s)" % (alert_name,
                                         ", ".join(desc_parts))
            else:
                item_key = "prometheus.%s" % sanitize(alert_name, 50)
                item_name = alert_name

            if item_key not in plan:
                plan[item_key] = {
                    "item_key": item_key,
                    "item_name": item_name[:255],
                    "item_desc": "Prometheus: %s" % item_name[:200],
                    "triggers": [],
                }

            thr = SEVERITY_THRESHOLD.get(severity, 2)
            prio = PRIORITY_MAP.get(severity, 2)
            if not any(t["threshold"] == thr
                       for t in plan[item_key]["triggers"]):
                plan[item_key]["triggers"].append({
                    "desc": "%s [%s]" % (
                        plan[item_key]["item_name"][:200],
                        severity.capitalize()),
                    "priority": prio,
                    "threshold": thr,
                })

        return list(plan.values())

    # -----------------------------------------------------------------------
    # Sync execution (OPTIMIZADO com batch + pre-fetch)
    # -----------------------------------------------------------------------

    def _sync_host_batch(self, hostname, hostid, plan,
                         existing_keys, existing_trigs):
        """Sync um host usando batch create (2 chamadas max por host)."""

        # Filtrar items NOVOS
        new_items = []
        for entry in plan:
            if entry["item_key"] not in existing_keys:
                new_items.append({
                    "name": entry["item_name"][:255],
                    "key_": entry["item_key"],
                    "hostid": hostid,
                    "type": 2,
                    "value_type": 3,
                    "description": entry["item_desc"][:255],
                })

        # Criar items em batch
        ci = self.batch_create_items(new_items)

        # Filtrar triggers NOVAS
        new_triggers = []
        for entry in plan:
            for trig in entry["triggers"]:
                expr = "{%s:%s.last()}>=%d" % (
                    hostname, entry["item_key"], trig["threshold"])
                if expr not in existing_trigs:
                    new_triggers.append({
                        "description": trig["desc"][:255],
                        "expression": expr,
                        "priority": trig["priority"],
                        "type": 0,
                    })

        # Criar triggers em batch
        ct = self.batch_create_triggers(new_triggers)

        return ci, ct

    def sync_all(self):
        """Sincroniza TODOS os hosts (optimizado)."""
        gid = self.get_group_id("Prometheus")
        zabbix_hosts = self.get_all_hosts()
        logger.info("Zabbix: %d hosts existentes", len(zabbix_hosts))

        # Consultar Prometheus (3 chamadas)
        targets_by_job, all_targets = self.get_targets()
        rules = self.get_alert_rules()
        active_alerts = self.get_active_alerts()

        # Resolver jobs para todas as regras
        self.resolve_rule_jobs(rules, targets_by_job, active_alerts)

        if not all_targets:
            logger.error("Sem targets no Prometheus")
            return 1

        self._log_discovery_summary(rules, active_alerts, all_targets)

        # Pre-fetch TODOS os items e triggers existentes (2 chamadas)
        logger.info("")
        logger.info("Pre-fetching items e triggers existentes...")
        items_by_host = self.prefetch_group_items(gid)
        trigs_by_host = self.prefetch_group_triggers(gid)

        logger.info("")
        logger.info("=" * 70)
        logger.info("INICIANDO SINCRONIZACAO")
        logger.info("=" * 70)

        total_items = total_triggers = total_hosts = 0
        hostnames = sorted(all_targets.keys())
        t_start = time.time()

        for n, hostname in enumerate(hostnames, 1):
            display = all_targets[hostname]

            # Criar host se nao existe
            if hostname not in zabbix_hosts:
                try:
                    hid = self.create_host(hostname, display, gid)
                    zabbix_hosts[hostname] = hid
                except Exception as e:
                    logger.warning("Saltar %s: %s", hostname, e)
                    continue

            hid = zabbix_hosts[hostname]

            # Build plan
            plan = self.build_host_plan(hostname, rules, active_alerts,
                                        targets_by_job)

            # Usar dados pre-fetched
            existing_keys = items_by_host.get(hid, set())
            existing_trigs = trigs_by_host.get(hid, set())

            # Sync com batch create
            ci, ct = self._sync_host_batch(hostname, hid, plan,
                                           existing_keys, existing_trigs)

            total_items += ci
            total_triggers += ct
            total_hosts += 1

            n_items = len(plan)
            n_trigs = sum(len(e["triggers"]) for e in plan)

            if n <= 10 or n % 200 == 0 or n == len(hostnames):
                elapsed = time.time() - t_start
                rate = n / elapsed if elapsed > 0 else 0
                eta = (len(hostnames) - n) / rate if rate > 0 else 0
                logger.info(
                    "  [%4d/%d] %-30s: %3di %3dt -> +%di +%dt  "
                    "(%.0f/s, ETA %.0fm)",
                    n, len(hostnames), hostname[:30],
                    n_items, n_trigs, ci, ct, rate, eta / 60)

        elapsed = time.time() - t_start
        logger.info("=" * 70)
        logger.info("CONCLUIDO em %.0f segundos (%.1f min)", elapsed,
                    elapsed / 60)
        logger.info("  Hosts: %d", total_hosts)
        logger.info("  Items criados:    %d", total_items)
        logger.info("  Triggers criadas: %d", total_triggers)
        logger.info("=" * 70)

        return 0

    def sync_host(self, hostname_input):
        """Sincroniza um host especifico."""
        gid = self.get_group_id("Prometheus")
        zabbix_hosts = self.get_all_hosts()
        h = sanitize(hostname_input)

        if h not in zabbix_hosts:
            hid = self.create_host(h, hostname_input, gid)
            logger.info("Host criado: %s", h)
        else:
            hid = zabbix_hosts[h]

        targets_by_job, all_targets = self.get_targets()
        rules = self.get_alert_rules()
        active_alerts = self.get_active_alerts()

        # Resolver jobs para todas as regras
        self.resolve_rule_jobs(rules, targets_by_job, active_alerts)

        plan = self.build_host_plan(h, rules, active_alerts, targets_by_job)

        existing_keys = self.prefetch_group_items(gid).get(hid, set())
        existing_trigs = self.prefetch_group_triggers(gid).get(hid, set())

        ci, ct = self._sync_host_batch(h, hid, plan,
                                       existing_keys, existing_trigs)

        n_items = len(plan)
        n_trigs = sum(len(e["triggers"]) for e in plan)

        logger.info("Host %s:", h)
        logger.info("  Plano: %d items, %d triggers", n_items, n_trigs)
        logger.info("  Criados: +%d items, +%d triggers", ci, ct)

        for entry in plan:
            trigs_str = ", ".join(
                "%s(>=%d)" % (t["desc"].split("[")[-1].rstrip("]"),
                              t["threshold"])
                for t in entry["triggers"])
            logger.info("    %s -> %s", entry["item_key"], trigs_str)

        return 0

    # -----------------------------------------------------------------------
    # Push: enviar estado dos alertas ao Zabbix via trapper (porta 10051)
    # -----------------------------------------------------------------------

    def push_alerts(self):
        """Envia estado dos alertas Prometheus para items trapper no Zabbix.
        - Alertas activos: envia o threshold da severidade (trigger dispara)
        - Sem alerta: envia 0 (trigger fica OK)
        Deve ser executado periodicamente via cron (ex: cada 2 minutos).
        """
        gid = self.get_group_id("Prometheus")

        # Obter alertas activos do Prometheus
        targets_by_job, all_targets = self.get_targets()
        active_alerts = self.get_active_alerts()

        # Mapear alertas activos: (hostname, item_key) -> max threshold
        alert_values = {}

        for alert in active_alerts:
            labels = alert.get("labels", {})
            instance = labels.get("instance", "")
            if not instance:
                continue

            host = sanitize(hostname_from_instance(instance))
            host = self._canonical_map.get(host, host)
            alert_name = labels.get("alertname", "")
            severity = labels.get("severity", "warning").lower()
            if not alert_name:
                continue

            # Base item
            item_key = "prometheus.%s" % sanitize(alert_name, 50)
            thr = SEVERITY_THRESHOLD.get(severity, 2)
            if thr > alert_values.get((host, item_key), 0):
                alert_values[(host, item_key)] = thr

            # Instance item (com labels extra)
            extra = extract_instance_labels(labels)
            if extra:
                uid = instance_uid(extra)
                inst_key = "prometheus.%s.%s" % (
                    sanitize(alert_name, 40), uid)
                if thr > alert_values.get((host, inst_key), 0):
                    alert_values[(host, inst_key)] = thr

        # Obter items e hosts do grupo Prometheus no Zabbix
        all_items = self._zabbix_call("item.get", {
            "output": ["key_", "hostid"],
            "groupids": gid,
        })
        prom_items = [i for i in all_items
                      if i["key_"].startswith("prometheus.")]

        hosts = self._zabbix_call("host.get", {
            "output": ["hostid", "host"],
            "groupids": gid,
        })
        hid_to_name = {h["hostid"]: h["host"] for h in hosts}

        # Construir dados: valor do alerta ou 0 (OK)
        sender_data = []
        active_count = 0
        now = int(time.time())

        for item in prom_items:
            hostname = hid_to_name.get(item["hostid"], "")
            if not hostname:
                continue
            key = item["key_"]
            value = alert_values.get((hostname, key), 0)
            sender_data.append({
                "host": hostname,
                "key": key,
                "value": str(value),
                "clock": now,
            })
            if value > 0:
                active_count += 1

        logger.info("Push: %d items (%d activos, %d OK)",
                    len(sender_data), active_count,
                    len(sender_data) - active_count)

        if not sender_data:
            logger.warning("Sem items para enviar")
            return 0

        # Enviar via protocolo Zabbix trapper
        sent = self._send_trapper_data(sender_data)
        logger.info("Push concluido: %d/%d valores enviados",
                    sent, len(sender_data))
        return 0

    def _send_trapper_data(self, data):
        """Envia dados via zabbix_sender ao Zabbix server (K3s)."""
        import os

        # Zabbix server K3s ClusterIP e porta trapper
        server = "10.43.69.137"
        port = "10151"

        # Construir ficheiro de input
        # Formato com timestamp: hostname key clock value
        lines = []
        for d in data:
            lines.append("%s %s %s %s" % (
                d["host"], d["key"], d["clock"], d["value"]))

        tmp = tempfile.NamedTemporaryFile(
            mode='w', suffix='.txt', delete=False, prefix='zbx_')
        tmp.write("\n".join(lines) + "\n")
        tmp.close()

        try:
            cmd = ["zabbix_sender",
                   "-z", server,
                   "-p", port,
                   "-i", tmp.name, "-T"]

            logger.info("zabbix_sender: enviando %d valores para %s:%s...",
                        len(data), server, port)
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=120)

            if result.stdout:
                logger.info("  %s", result.stdout.strip())
            if result.returncode != 0 and result.stderr:
                logger.warning("  stderr: %s", result.stderr.strip())

            return len(data) if result.returncode == 0 else 0

        except Exception as e:
            logger.error("Erro com zabbix_sender: %s", e)
            return 0

        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

    # -----------------------------------------------------------------------
    # Validacao / Info
    # -----------------------------------------------------------------------

    def validate_prometheus(self):
        """Mostra dados Prometheus e plano sem executar sync."""
        logger.info("=" * 70)
        logger.info("VALIDACAO: DADOS DO PROMETHEUS")
        logger.info("=" * 70)

        try:
            targets_by_job, all_targets = self.get_targets()
            rules = self.get_alert_rules()
            active_alerts = self.get_active_alerts()

            # Resolver jobs para todas as regras
            self.resolve_rule_jobs(rules, targets_by_job, active_alerts)

            logger.info("")
            logger.info("REGRAS DE ALERTA (%d):", len(rules))
            logger.info("-" * 70)
            for alert_name in sorted(rules.keys()):
                rd = rules[alert_name]
                sevs = ", ".join(sorted(rd["severities"].keys()))
                jobs = ", ".join(sorted(rd["jobs"])) if rd["jobs"] else "(todas)"
                logger.info("  %-35s sevs=[%s]  jobs=[%s]",
                            alert_name[:35], sevs, jobs)

            logger.info("")
            logger.info("ALERTAS ACTIVOS POR HOST:")
            logger.info("-" * 70)

            host_instances = defaultdict(lambda: defaultdict(list))
            for alert in active_alerts:
                labels = alert.get("labels", {})
                instance = labels.get("instance", "")
                if not instance:
                    continue
                host = sanitize(hostname_from_instance(instance))
                host = self._canonical_map.get(host, host)
                alert_name = labels.get("alertname", "")
                severity = labels.get("severity", "?")
                extra = extract_instance_labels(labels)
                host_instances[host][alert_name].append({
                    "severity": severity, "labels": extra,
                })

            hosts_sorted = sorted(
                host_instances.items(),
                key=lambda x: sum(len(v) for v in x[1].values()),
                reverse=True)

            for host, alerts in hosts_sorted[:20]:
                total_inst = sum(len(v) for v in alerts.values())
                logger.info("  %s: %d alertas, %d instancias",
                            host, len(alerts), total_inst)
                for aname in sorted(alerts.keys()):
                    instances = alerts[aname]
                    sevs = set(i["severity"] for i in instances)
                    logger.info("    %-30s x%d inst  sevs=[%s]",
                                aname[:30], len(instances),
                                ",".join(sorted(sevs)))

            if hosts_sorted:
                example_host = hosts_sorted[0][0]
                plan = self.build_host_plan(example_host, rules,
                                            active_alerts, targets_by_job)
                n_items = len(plan)
                n_trigs = sum(len(e["triggers"]) for e in plan)

                logger.info("")
                logger.info("EXEMPLO PLANO PARA: %s", example_host)
                logger.info("-" * 70)
                logger.info("  Total items: %d", n_items)
                logger.info("  Total triggers: %d", n_trigs)

                for entry in plan[:15]:
                    logger.info("  Item: %s", entry["item_key"])
                    for t in entry["triggers"]:
                        logger.info("    -> %s (prio=%d, thr>=%d)",
                                    t["desc"][:60], t["priority"],
                                    t["threshold"])
                if len(plan) > 15:
                    logger.info("  ... e mais %d items", len(plan) - 15)

            logger.info("")
            logger.info("=" * 70)
            logger.info("RESUMO")
            logger.info("=" * 70)
            logger.info("  Hosts: %d", len(all_targets))
            logger.info("  Regras: %d", len(rules))
            logger.info("  Alertas activos: %d instancias", len(active_alerts))
            logger.info("  Hosts com alertas activos: %d",
                        len(host_instances))

            return 0

        except Exception as e:
            logger.error("Erro na validacao: %s", e)
            return 1

    def _log_discovery_summary(self, rules, active_alerts, all_targets):
        logger.info("")
        logger.info("=" * 70)
        logger.info("DESCOBERTA PROMETHEUS")
        logger.info("=" * 70)
        logger.info("  Targets: %d", len(all_targets))
        logger.info("  Regras unicas: %d", len(rules))
        logger.info("  Alertas activos: %d instancias", len(active_alerts))

        sev_counts = defaultdict(int)
        for r in rules.values():
            for sev in r["severities"]:
                sev_counts[sev] += 1
        for sev, count in sorted(sev_counts.items()):
            logger.info("    %s: %d regras", sev.capitalize(), count)

        host_inst = defaultdict(int)
        for alert in active_alerts:
            labels = alert.get("labels", {})
            instance = labels.get("instance", "")
            if instance:
                host = sanitize(hostname_from_instance(instance))
                host = self._canonical_map.get(host, host)
                host_inst[host] += 1

        if host_inst:
            avg_inst = sum(host_inst.values()) / len(host_inst)
            max_inst = max(host_inst.values())
            logger.info("  Instancias activas por host: media=%.1f, max=%d",
                        avg_inst, max_inst)

    def diag_host(self, hostname_input):
        """Mostra diagnostico detalhado de matching para um host."""
        h = sanitize(hostname_input)
        targets_by_job, all_targets = self.get_targets()
        rules = self.get_alert_rules()
        active_alerts = self.get_active_alerts()
        self.resolve_rule_jobs(rules, targets_by_job, active_alerts)

        # Jobs do host
        host_jobs = set()
        for job, targets in targets_by_job.items():
            if any(t["hostname"] == h for t in targets):
                host_jobs.add(job)

        logger.info("")
        logger.info("=" * 70)
        logger.info("DIAGNOSTICO: %s", h)
        logger.info("=" * 70)
        logger.info("Jobs do host (%d): %s",
                    len(host_jobs),
                    ", ".join(sorted(host_jobs)) or "(nenhum)")
        logger.info("")

        matched = []
        unmatched = []
        for alert_name in sorted(rules.keys()):
            rule_data = rules[alert_name]
            if not rule_data["jobs"]:
                unmatched.append((alert_name, "sem jobs resolvidos"))
                continue
            common = rule_data["jobs"] & host_jobs
            if common:
                matched.append(alert_name)
                sevs = ", ".join(sorted(rule_data["severities"].keys()))
                logger.info("  MATCH  %-30s sevs=[%s]  jobs=[%s]",
                            alert_name[:30], sevs,
                            ", ".join(sorted(common)[:3]))
            else:
                sample = ", ".join(sorted(rule_data["jobs"])[:3])
                extra = "..." if len(rule_data["jobs"]) > 3 else ""
                unmatched.append((alert_name,
                                  "%s%s" % (sample, extra)))

        logger.info("")
        logger.info("MATCHED: %d regras", len(matched))
        logger.info("NAO MATCHED: %d regras", len(unmatched))
        for name, reason in sorted(unmatched):
            logger.info("  %-30s  rule_jobs=[%s]", name[:30], reason)

        plan = self.build_host_plan(h, rules, active_alerts, targets_by_job)
        n_items = len(plan)
        n_trigs = sum(len(e["triggers"]) for e in plan)

        logger.info("")
        logger.info("PLANO: %d items, %d triggers", n_items, n_trigs)
        for entry in plan:
            trigs = ", ".join(
                "%s(>=%d)" % (t["desc"].split("[")[-1].rstrip("]"),
                              t["threshold"])
                for t in entry["triggers"])
            logger.info("  %s -> %s", entry["item_key"], trigs)

        return 0

    def generate_mapping_report(self, rules):
        logger.info("")
        logger.info("=" * 70)
        logger.info("MAPEAMENTO POR CATEGORIA")
        logger.info("=" * 70)

        categories = {
            "SO": [], "CPU": [], "Disco": [], "Memory": [],
            "Network": [], "Aplicacoes": [], "Outros": []
        }

        keywords = {
            "SO": ["linux", "windows", "host", "down", "reboot",
                   "kernel", "uptime", "boot"],
            "CPU": ["cpu", "processador", "load", "processor"],
            "Disco": ["disk", "storage", "filesystem", "partition",
                      "io", "mount", "volume", "inode"],
            "Memory": ["memory", "ram", "swap", "heap", "oom",
                        "cache", "buffer"],
            "Network": ["network", "interface", "packet", "connection",
                        "bandwidth", "latency", "socket", "port", "tcp",
                        "dns", "http"],
            "Aplicacoes": ["apache", "nginx", "mysql", "redis", "tomcat",
                           "mirth", "weblogic", "elasticsearch", "logstash",
                           "php", "iis", "zookeeper", "holodeck", "soffice",
                           "ssl", "cert", "jvm", "jdbc", "queue", "thread",
                           "forms", "session", "exporter"],
        }

        for alert_name in rules.keys():
            found = False
            for cat, kw_list in keywords.items():
                if any(kw in alert_name.lower() for kw in kw_list):
                    categories[cat].append(alert_name)
                    found = True
                    break
            if not found:
                categories["Outros"].append(alert_name)

        for cat in ["SO", "CPU", "Disco", "Memory", "Network",
                     "Aplicacoes", "Outros"]:
            alerts = categories[cat]
            if not alerts:
                continue
            logger.info("")
            logger.info("%s (%d alertas):", cat, len(alerts))
            for aname in sorted(alerts):
                sevs = ", ".join(sorted(rules[aname]["severities"].keys()))
                logger.info("  - %-35s [%s]", aname[:35], sevs)

        logger.info("")
        logger.info("Total: %d alertas mapeados", len(rules))
        return categories


# ===========================================================================
# CLI
# ===========================================================================

def main():
    logger.info("=" * 70)
    logger.info("SINCRONIZADOR PROMETHEUS -> ZABBIX")
    logger.info("=" * 70)

    parser = argparse.ArgumentParser(
        description="Sincronizar alertas Prometheus com Zabbix")
    parser.add_argument("--all", action="store_true",
                        help="Sincronizar TODOS os hosts")
    parser.add_argument("--host",
                        help="Sincronizar host especifico")
    parser.add_argument("--validate", action="store_true",
                        help="Validar dados Prometheus sem sync")
    parser.add_argument("--info", action="store_true",
                        help="Mostrar mapeamento por categoria")
    parser.add_argument("--verbose", action="store_true",
                        help="Modo verbose/debug")
    parser.add_argument("--push", action="store_true",
                        help="Enviar alertas activos para Zabbix trapper")
    parser.add_argument("--diag",
                        help="Diagnostico: mostra matching para host")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(1)

    sync = PrometheusSync()

    try:
        if not sync.login_zabbix():
            logger.error("Nao conseguiu conectar ao Zabbix")
            return 1
    except Exception as e:
        logger.error("Erro conectando ao Zabbix: %s", e)
        return 1

    try:
        if args.validate:
            return sync.validate_prometheus()
        elif args.diag:
            return sync.diag_host(args.diag)
        elif args.info:
            targets_by_job, _ = sync.get_targets()
            rules = sync.get_alert_rules()
            sync.generate_mapping_report(rules)
            return 0
        elif args.all:
            return sync.sync_all()
        elif args.push:
            return sync.push_alerts()
        elif args.host:
            return sync.sync_host(args.host)
        else:
            parser.print_help()
            return 1
    except Exception as e:
        logger.error("Erro: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
