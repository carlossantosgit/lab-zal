"""
Prometheus Sync Module - Sincroniza alerting rules do Prometheus com Zabbix
Cria items e triggers dinamicamente baseado nas regras do Prometheus
"""

import requests
import json
import logging
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)

ZABBIX_API_URL = os.getenv("ZABBIX_API_URL", "http://localhost:8080/api_jsonrpc.php")
PROMETHEUS_API_URL = os.getenv("PROMETHEUS_API_URL", "http://prometheus:9090")

# Severity mapping: Prometheus severity → Zabbix priority
SEVERITY_MAP = {
    "info": 0,        # Not classified
    "warning": 2,     # Average
    "critical": 4,    # High
}

class PrometheusSync:
    """Sincroniza regras do Prometheus com Zabbix"""

    def __init__(self, auth_token: str = None, use_fake: bool = False):
        self.auth_token = auth_token
        self.use_fake = use_fake
        self.rules_cache = None

    def get_prometheus_rules(self) -> List[Dict]:
        """Obtém regras de alerta do Prometheus"""
        try:
            if self.use_fake:
                return self._get_fake_rules()

            url = f"{PROMETHEUS_API_URL}/api/v1/rules"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            data = response.json()
            rules = []

            # Parseia todas as alerting rules
            for group in data.get("data", {}).get("groups", []):
                for rule in group.get("rules", []):
                    if rule.get("type") == "alerting":
                        rules.append({
                            "alert": rule.get("alert"),
                            "expr": rule.get("expr"),
                            "for": rule.get("for", "5m"),
                            "severity": rule.get("labels", {}).get("severity", "warning"),
                            "description": rule.get("annotations", {}).get("description", "Alert rule"),
                            "summary": rule.get("annotations", {}).get("summary", rule.get("alert"))
                        })

            logger.info(f"✅ Obtidas {len(rules)} regras do Prometheus")
            return rules

        except Exception as e:
            logger.error(f"❌ Erro ao obter regras Prometheus: {str(e)}")
            return []

    def _get_fake_rules(self) -> List[Dict]:
        """Obtém regras do arquivo fake (para demo)"""
        try:
            fake_file = os.path.join(os.path.dirname(__file__), "fake_prometheus_rules.json")

            if not os.path.exists(fake_file):
                logger.warning(f"Arquivo fake não encontrado: {fake_file}")
                return []

            with open(fake_file, "r") as f:
                data = json.load(f)

            rules = []
            for group in data.get("data", {}).get("groups", []):
                for rule in group.get("rules", []):
                    rules.append({
                        "alert": rule.get("alert"),
                        "expr": rule.get("expr"),
                        "for": rule.get("for", "5m"),
                        "severity": rule.get("labels", {}).get("severity", "warning"),
                        "description": rule.get("annotations", {}).get("description", "Alert rule"),
                        "summary": rule.get("annotations", {}).get("summary", rule.get("alert"))
                    })

            logger.info(f"✅ Carregadas {len(rules)} regras do arquivo fake")
            return rules

        except Exception as e:
            logger.error(f"❌ Erro ao carregar rules fake: {str(e)}")
            return []

    def create_item_from_rule(self, rule: Dict, hostid: str, auth_token: str = None) -> bool:
        """Cria item no Zabbix baseado em regra Prometheus"""
        token = auth_token or self.auth_token
        if not token:
            logger.error("❌ Auth token não fornecido")
            return False

        alert_name = rule.get("alert", "").lower()
        item_key = f"prometheus.{alert_name}"

        payload = {
            "jsonrpc": "2.0",
            "method": "item.create",
            "params": {
                "name": rule.get("summary", alert_name),
                "key_": item_key,
                "hostid": hostid,
                "type": 2,           # Trapper
                "value_type": 0,     # Float
                "history": "7d",
                "trends": "30d",
                "description": rule.get("description", "Alert rule from Prometheus")
            },
            "auth": token,
            "id": 1
        }

        try:
            response = requests.post(ZABBIX_API_URL, json=payload, timeout=5)
            result = response.json()

            if "error" in result:
                logger.error(f"❌ Erro ao criar item {item_key}: {result['error']}")
                return False

            if "result" in result and result["result"].get("itemids"):
                itemid = result["result"]["itemids"][0]
                logger.info(f"✅ Item criado: {item_key} (ID: {itemid})")
                return True

            return False

        except Exception as e:
            logger.error(f"❌ Exceção ao criar item {item_key}: {str(e)}")
            return False

    def create_trigger_from_rule(self, rule: Dict, hostname: str, auth_token: str = None) -> bool:
        """Cria trigger no Zabbix baseado em regra Prometheus"""
        token = auth_token or self.auth_token
        if not token:
            logger.error("❌ Auth token não fornecido")
            return False

        alert_name = rule.get("alert", "").lower()
        item_key = f"prometheus.{alert_name}"

        # Construir expressão da trigger
        expression = "{" + hostname + ":" + item_key + ".last()}>0"

        # Mapear severity
        severity = SEVERITY_MAP.get(rule.get("severity", "warning"), 2)

        payload = {
            "jsonrpc": "2.0",
            "method": "trigger.create",
            "params": {
                "description": rule.get("summary", alert_name),
                "expression": expression,
                "priority": severity,
                "url": ""
            },
            "auth": token,
            "id": 1
        }

        try:
            response = requests.post(ZABBIX_API_URL, json=payload, timeout=5)
            result = response.json()

            if "error" in result:
                logger.error(f"❌ Erro ao criar trigger {alert_name}: {result['error']}")
                return False

            if "result" in result and result["result"].get("triggerids"):
                triggerid = result["result"]["triggerids"][0]
                logger.info(f"✅ Trigger criada: {alert_name} (ID: {triggerid})")
                return True

            return False

        except Exception as e:
            logger.error(f"❌ Exceção ao criar trigger {alert_name}: {str(e)}")
            return False

    def sync_host(self, hostname: str, hostid: str, auth_token: str = None) -> Dict:
        """Sincroniza todas as regras Prometheus para um host em Zabbix"""
        token = auth_token or self.auth_token
        if not token:
            logger.error("❌ Auth token não fornecido")
            return {"success": False, "message": "No auth token"}

        logger.info(f"🔄 Sincronizando regras para host: {hostname}")

        rules = self.get_prometheus_rules()
        if not rules:
            logger.warning(f"⚠️  Nenhuma regra encontrada")
            return {"success": False, "message": "No rules found"}

        items_created = 0
        triggers_created = 0
        errors = []

        for rule in rules:
            try:
                # Criar item
                if self.create_item_from_rule(rule, hostid, token):
                    items_created += 1
                else:
                    errors.append(f"Falha ao criar item para {rule.get('alert')}")

                # Criar trigger
                if self.create_trigger_from_rule(rule, hostname, token):
                    triggers_created += 1
                else:
                    errors.append(f"Falha ao criar trigger para {rule.get('alert')}")

            except Exception as e:
                logger.error(f"❌ Erro ao processar regra {rule.get('alert')}: {str(e)}")
                errors.append(str(e))

        result = {
            "success": True,
            "hostname": hostname,
            "rules_total": len(rules),
            "items_created": items_created,
            "triggers_created": triggers_created,
            "errors": errors if errors else None
        }

        logger.info(f"✅ Sincronização concluída: {items_created} items, {triggers_created} triggers")
        return result

# Função auxiliar para uso em receiver.py
def sync_prometheus_rules_for_host(hostname: str, hostid: str, auth_token: str, use_fake: bool = False) -> Dict:
    """Função auxiliar que sincroniza regras Prometheus para um host específico"""
    sync = PrometheusSync(auth_token=auth_token, use_fake=use_fake)
    return sync.sync_host(hostname, hostid, auth_token)
