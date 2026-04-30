#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincronizacao Prometheus -> Zabbix (NOVO MODELO)
- 1 host unico 'prometheus' no Zabbix
- Items parametrizados: prom.alert.{status,severity,summary,payload}[alertname,instance]
- Triggers com nome=summary + tags=labels do Prometheus
- Push periodico via zabbix_sender
"""

import sys
import time
import ssl
import json
import re
import argparse
import socket
import struct
import requests

from config import (
    logger,
    ZABBIX_API_URL, ZABBIX_USER, ZABBIX_PASSWORD, ZABBIX_VERIFY_SSL,
    PROMETHEUS_URL, PROMETHEUS_USER, PROMETHEUS_PASS, PROMETHEUS_VERIFY_SSL,
)

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------
ZABBIX_SERVER = "10.43.69.137"
ZABBIX_TRAPPER_PORT = "10151"

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

VALUE_TYPE = {
    "status":   3,  # Numeric unsigned
    "severity": 3,  # Numeric unsigned
    "summary":  1,  # Character (max 255)
    "payload":  4,  # Text
}

META_LABELS = frozenset([
    "__name__", "alertname", "alertstate", "severity",
    "instance", "job", "monitor", "prometheus",
    "prometheus_replica", "replica", "exported_instance",
    "exported_job", "summary", "description",
])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def sanitize(name, maxlen=64):
    """Sanitiza nomes para Zabbix: [a-zA-Z0-9._-]"""
    out = ""
    for c in str(name).strip():
        out += c if c.isalnum() or c in "._-" else "_"
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_").lower()[:maxlen] or "unknown"


def sanitize_key_param(value):
    """Sanitiza parametros de keys: [alertname,instance]"""
    # Remove caracteres especiais para safe key
    return re.sub(r'[^a-zA-Z0-9._-]', '_', str(value).lower())


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


def build_prometheus_label_tags(labels):
    """Monta as 3 tags padrao das labels Prometheus para triggers."""
    return [
        {"tag": "prometheus_service", "value": str(labels.get("service", ""))[:255]},
        {"tag": "prometheus_type", "value": str(labels.get("type", ""))[:255]},
        {"tag": "prometheus_apps", "value": str(labels.get("apps", ""))[:255]},
    ]


# ===========================================================================
# PrometheusSync - Novo Modelo
# ===========================================================================


class PrometheusSync:

    def __init__(self):
        self.auth_token = None
        self._group_id = None
        self._session = requests.Session()
        self._single_host_id = None
        self._single_host_name = "prometheus"

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

    def get_or_create_single_host(self):
        """Get or create o host unico 'prometheus'"""
        gid = self.get_group_id("Prometheus")

        # Procurar host existente
        hosts = self._zabbix_call("host.get", {
            "output": ["hostid", "host"],
            "filter": {"host": self._single_host_name},
        })

        if hosts:
            self._single_host_id = hosts[0]["hostid"]
            logger.info("Host existente encontrado: %s (id=%s)",
                       self._single_host_name, self._single_host_id)
        else:
            # Criar novo host
            r = self._zabbix_call("host.create", {
                "host": self._single_host_name,
                "name": "Prometheus Alerts",
                "groups": [{"groupid": gid}],
                "interfaces": [{
                    "type": 1, "main": 1, "useip": 1,
                    "ip": "127.0.0.1", "dns": "", "port": "10050",
                }],
            })
            self._single_host_id = r["hostids"][0]
            logger.info("Host criado: %s (id=%s)",
                       self._single_host_name, self._single_host_id)

        return self._single_host_id

    def prefetch_items(self, hostid):
        """Obtem todas as keys existentes neste host"""
        items = self._zabbix_call("item.get", {
            "output": ["key_"],
            "hostids": hostid,
        })
        return set(i["key_"] for i in items)

    def prefetch_triggers(self, hostid):
        """Obtem todas as trigger expressions neste host"""
        trigs = self._zabbix_call("trigger.get", {
            "output": ["expression", "triggerid"],
            "hostids": hostid,
        })
        return {t["expression"]: t["triggerid"] for t in trigs}

    def batch_create_items(self, items_list):
        """Cria multiplos items numa unica chamada"""
        if not items_list:
            return 0
        try:
            result = self._zabbix_call("item.create", items_list)
            return len(result.get("itemids", []))
        except RuntimeError as e:
            err = str(e).lower()
            if "already exists" in err:
                created = 0
                for item in items_list:
                    try:
                        self._zabbix_call("item.create", [item])
                        created += 1
                    except RuntimeError:
                        pass
                return created
            logger.warning("Batch item.create erro: %s", e)
            return 0

    def batch_create_triggers(self, triggers_list):
        """Cria multiplas triggers numa unica chamada"""
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
                        self._zabbix_call("trigger.create", [trig])
                        created += 1
                    except RuntimeError:
                        pass
                return created
            logger.warning("Batch trigger.create erro: %s", e)
            return 0

    def update_trigger_tags(self, triggers_list):
        """Atualiza tags de triggers existentes usando o triggerid no payload."""
        updated = 0
        for trig in triggers_list:
            try:
                self._zabbix_call("trigger.update", {
                    "triggerid": trig["triggerid"],
                    "tags": trig["tags"],
                })
                updated += 1
            except RuntimeError as e:
                logger.warning("trigger.update tags erro (%s): %s",
                               trig.get("triggerid"), e)
        return updated

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

    def get_active_alerts(self):
        """Obtem TODOS os alertas activos"""
        data = self._prom_get("/api/v1/alerts")
        alerts = data.get("data", {}).get("alerts", [])
        logger.info("Prometheus alertas activos: %d instancias", len(alerts))
        return alerts

    def get_alert_rules(self):
        """Obtem regras de alerta"""
        data = self._prom_get("/api/v1/rules")
        rules = {}
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
                summary = annotations.get("summary", "")[:255]

                rules[alert_name] = {
                    "severity": severity,
                    "summary": summary,
                    "labels": labels,
                }

        logger.info("Prometheus rules: %d regras unicas", len(rules))
        return rules

    # -----------------------------------------------------------------------
    # Build Plan: Items + Triggers com Model Unico Host
    # -----------------------------------------------------------------------

    def build_all_items_plan(self, active_alerts, rules):
        """
        Build plan de ALL items para o host unico.
        Items parametrizados: prom.alert.{status,severity,summary,payload}[alertname,instance]
        """
        plan = {}  # key -> item_config

        # Coletar todas as combinacoes unicas (alertname, instance)
        alert_instances = {}  # (alertname, instance) -> list de alerts

        for alert in active_alerts:
            labels = alert.get("labels", {})
            alertname = labels.get("alertname", "")
            instance = labels.get("instance", "")
            if not alertname or not instance:
                continue

            key = (alertname, instance)
            if key not in alert_instances:
                alert_instances[key] = []
            alert_instances[key].append(alert)

        # Para cada (alertname, instance) criar os 4 items
        for (alertname, instance), alerts_list in alert_instances.items():
            alert_key_safe = sanitize_key_param(alertname)
            instance_safe = sanitize_key_param(instance)
            base_key = "prom.alert"

            rule_info = rules.get(alertname, {})
            summary = rule_info.get("summary", alertname)

            # Pegar os labels (todos) do primeiro alert
            alert_labels = alerts_list[0].get("labels", {}) if alerts_list else {}

            # Criar os 4 items
            for item_type in ["status", "severity", "summary", "payload"]:
                key_str = "%s.%s[%s,%s]" % (base_key, item_type,
                                            alert_key_safe, instance_safe)

                if key_str not in plan:
                    plan[key_str] = {
                        "key_": key_str,
                        "name": "%s (%s) - %s" % (alertname, instance, item_type),
                        "type": 2,  # Trapper
                        "value_type": VALUE_TYPE[item_type],
                        "description": "%s [%s]" % (summary, item_type),
                    }

        logger.info("Build plan: %d items unicas", len(plan))
        return list(plan.values())

    def build_all_triggers_plan(self, active_alerts, rules):
        """
        Build plan de triggers para o host unico.
        Nome = summary do alert (com macros substituidas)
        Tags = labels do Prometheus
        Expression = baseada no status/severity
        """
        plan = {}  # key -> trigger_config

        # Group alerts por (alertname, instance, severity)
        alert_groups = {}

        for alert in active_alerts:
            labels = alert.get("labels", {})
            alertname = labels.get("alertname", "")
            instance = labels.get("instance", "")
            severity = labels.get("severity", "warning").lower()

            if not alertname or not instance:
                continue

            key = (alertname, instance, severity)
            if key not in alert_groups:
                alert_groups[key] = []
            alert_groups[key].append(alert)

        # Para cada grupo criar uma trigger
        for (alertname, instance, severity), alerts_list in alert_groups.items():
            alert_key_safe = sanitize_key_param(alertname)
            instance_safe = sanitize_key_param(instance)

            # Pegar info da regra
            rule_info = rules.get(alertname, {})
            summary = rule_info.get("summary", alertname)

            # Substituir macros {$labels.*} no summary pelo valor real
            def macro_replace(text, labels_dict):
                def repl(m):
                    key = m.group(1)
                    return str(labels_dict.get(key, m.group(0)))
                return re.sub(r"\{\$labels\.([a-zA-Z0-9_]+)\}", repl, text)

            # Pega labels do primeiro alerta do grupo
            first_labels = alerts_list[0].get("labels", {}) if alerts_list else {}
            summary_final = macro_replace(summary, first_labels)

            # Tags padrao a partir das labels reais do alerta activo
            tags = build_prometheus_label_tags(first_labels)

            # Expressao baseada no status item
            item_key = "prom.alert.status[%s,%s]" % (alert_key_safe, instance_safe)
            thr = SEVERITY_THRESHOLD.get(severity, 2)
            expr = "{%s:%s.last()}>=%d" % (
                self._single_host_name, item_key, thr)

            # Criar key unica para trigger (alertname + instance + severity)
            trig_key = "%s_%s_%s" % (alert_key_safe, instance_safe, severity)

            plan[trig_key] = {
                "description": summary_final[:255],
                "expression": expr,
                "priority": PRIORITY_MAP.get(severity, 2),
                "type": 0,
                "tags": tags,
            }

        logger.info("Build plan: %d triggers", len(plan))
        return list(plan.values())

    # -----------------------------------------------------------------------
    # Sync All (novo)
    # -----------------------------------------------------------------------

    def sync_all(self):
        """Sincroniza: cria 1 host unico + items + triggers"""
        logger.info("=" * 70)
        logger.info("SYNC ALL (NOVO MODELO)")
        logger.info("=" * 70)

        try:
            # 1. Criar/obter host unico
            hostid = self.get_or_create_single_host()

            # 2. Obter dados Prometheus
            active_alerts = self.get_active_alerts()
            rules = self.get_alert_rules()

            if not active_alerts:
                logger.warning("Sem alertas activos no Prometheus")
                return 1

            # 3. Pre-fetch items/triggers existentes
            existing_keys = self.prefetch_items(hostid)
            existing_trigs = self.prefetch_triggers(hostid)
            logger.info("Host: %d items, %d triggers existentes",
                       len(existing_keys), len(existing_trigs))

            # 4. Build plan
            items_plan = self.build_all_items_plan(active_alerts, rules)
            triggers_plan = self.build_all_triggers_plan(active_alerts, rules)

            # 5. Filtrar novos
            new_items = [
                i for i in items_plan
                if i["key_"] not in existing_keys
            ]
            new_items_for_api = [
                {
                    "name": i["name"],
                    "key_": i["key_"],
                    "hostid": hostid,
                    "type": i["type"],
                    "value_type": i["value_type"],
                    "description": i["description"],
                }
                for i in new_items
            ]

            new_triggers = [
                t for t in triggers_plan
                if t["expression"] not in existing_trigs
            ]
            existing_triggers_for_update = [
                {
                    "triggerid": existing_trigs[t["expression"]],
                    "tags": t["tags"],
                }
                for t in triggers_plan
                if t["expression"] in existing_trigs
            ]

            # 6. Criar items
            ci = self.batch_create_items(new_items_for_api)
            logger.info("Items criados: %d", ci)

            # 7. Criar triggers
            ct = self.batch_create_triggers(new_triggers)
            logger.info("Triggers criadas: %d", ct)

            # 8. Atualizar tags das triggers ja existentes
            ut = self.update_trigger_tags(existing_triggers_for_update)
            logger.info("Triggers existentes atualizadas com tags: %d", ut)

            logger.info("=" * 70)
            logger.info("SYNC COMPLETO")
            logger.info("  Items: %d (novos: +%d)", len(items_plan), ci)
            logger.info("  Triggers: %d (novas: +%d, atualizadas: %d)",
                        len(triggers_plan), ct, ut)
            logger.info("=" * 70)

            return 0

        except Exception as e:
            logger.error("Erro no sync: %s", e)
            return 1

    # -----------------------------------------------------------------------
    # Push Alerts (novo)
    # -----------------------------------------------------------------------

    def push_alerts(self):
        """Push alertas activos para items via zabbix_sender"""
        logger.info("=" * 70)
        logger.info("PUSH ALERTS")
        logger.info("=" * 70)

        try:
            # 1. Obter alertas activos
            active_alerts = self.get_active_alerts()

            if not active_alerts:
                logger.warning("Sem alertas activos")
                return 1

            # 2. Build dados para enviar
            # Formato: host key clock value
            sender_data = []
            now = int(time.time())

            for alert in active_alerts:
                labels = alert.get("labels", {})
                alertname = labels.get("alertname", "")
                instance = labels.get("instance", "")
                severity = labels.get("severity", "warning").lower()

                if not alertname or not instance:
                    continue

                alert_key_safe = sanitize_key_param(alertname)
                instance_safe = sanitize_key_param(instance)

                # Status (0=OK, threshold do severity)
                status_value = SEVERITY_THRESHOLD.get(severity, 2)

                # Severity (0-6 como severity)
                severity_value = PRIORITY_MAP.get(severity, 0)

                # Summary
                annotations = alert.get("annotations", {})
                summary = annotations.get("summary", alertname)

                # Payload (JSON com todos os labels)
                payload = json.dumps(labels, separators=(",", ":"))[:255]

                # Adicionar valores
                for item_type, value in [
                    ("status", status_value),
                    ("severity", severity_value),
                    ("summary", summary[:255]),
                    ("payload", payload),
                ]:
                    item_key = "prom.alert.%s[%s,%s]" % (
                        item_type, alert_key_safe, instance_safe)

                    sender_data.append({
                        "host": self._single_host_name,
                        "key": item_key,
                        "clock": now,
                        "value": str(value),
                    })

            logger.info("Preparado: %d valores para enviar", len(sender_data))

            # 3. Enviar via zabbix_sender
            sent = self._send_trapper_data(sender_data)

            logger.info("=" * 70)
            logger.info("PUSH COMPLETO: %d/%d valores enviados",
                       sent, len(sender_data))
            logger.info("=" * 70)

            return 0 if sent > 0 else 1

        except Exception as e:
            logger.error("Erro no push: %s", e)
            return 1

    def _send_trapper_data(self, data):
        """Envia dados via protocolo Zabbix Trapper (TCP socket + JSON)"""
        if not data:
            return 0

        payload = {
            "request": "sender data",
            "data": [
                {
                    "host": d["host"],
                    "key": d["key"],
                    "value": str(d["value"]),
                    "clock": d["clock"],
                }
                for d in data
            ],
        }

        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = b"ZBXD\x01" + struct.pack("<Q", len(body))

        logger.info("Zabbix Trapper: %s:%s (%d valores)",
                    ZABBIX_SERVER, ZABBIX_TRAPPER_PORT, len(data))

        try:
            with socket.create_connection(
                    (ZABBIX_SERVER, int(ZABBIX_TRAPPER_PORT)), timeout=30) as sock:
                sock.sendall(header + body)

                resp_header = sock.recv(13)
                if len(resp_header) < 13 or resp_header[:5] != b"ZBXD\x01":
                    logger.warning("Resposta inesperada do Zabbix Trapper")
                    return 0

                resp_len = struct.unpack("<Q", resp_header[5:13])[0]
                resp_body = sock.recv(resp_len).decode("utf-8")
                resp = json.loads(resp_body)

                info = resp.get("info", "")
                logger.info("Trapper resposta: %s", info)

                m = re.search(r"processed:\s*(\d+)", info)
                return int(m.group(1)) if m else 0

        except Exception as e:
            logger.error("Erro com Zabbix Trapper: %s", e)
            return 0


# ===========================================================================
# CLI
# ===========================================================================

def main():
    logger.info("=" * 70)
    logger.info("SINCRONIZADOR PROMETHEUS -> ZABBIX (NOVO MODELO)")
    logger.info("=" * 70)

    parser = argparse.ArgumentParser(
        description="Sincronizar alertas Prometheus com Zabbix (modelo unico host)")
    parser.add_argument("--all", action="store_true",
                       help="Criar 1 host + items parametrizados + triggers")
    parser.add_argument("--push", action="store_true",
                       help="Enviar alertas activos para items parametrizados")
    parser.add_argument("--verbose", action="store_true",
                       help="Modo verbose")
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
        if args.all:
            return sync.sync_all()
        elif args.push:
            return sync.push_alerts()
        else:
            parser.print_help()
            return 1
    except Exception as e:
        logger.error("Erro: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
