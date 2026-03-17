#!/usr/bin/env python3
"""
Sincronização de Regras Prometheus → Zabbix
Versão Produção
"""

import requests
import argparse
import sys
import os
import logging
from typing import Dict, List, Optional

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Carregar configuração
from config import (
    ZABBIX_API_URL,
    ZABBIX_USER,
    ZABBIX_PASSWORD,
    PROMETHEUS_API_URL,
    SEVERITY_MAP
)


class PrometheusSync:
    """Sincroniza regras Prometheus com Zabbix"""

    def __init__(self, auth_token: str = None):
        self.auth_token = auth_token

    def login_zabbix(self) -> Optional[str]:
        """Login no Zabbix e retorna token"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "user.login",
                "params": {
                    "user": ZABBIX_USER,
                    "password": ZABBIX_PASSWORD
                },
                "id": 1
            }
            resp = requests.post(ZABBIX_API_URL, json=payload, timeout=10)
            result = resp.json()

            if "result" in result:
                logger.info("✅ Login Zabbix bem-sucedido")
                return result["result"]
            else:
                logger.error(f"❌ Login Zabbix falhou: {result.get('error')}")
                return None
        except Exception as e:
            logger.error(f"❌ Erro ao conectar Zabbix: {str(e)}")
            return None

    def get_prometheus_rules(self) -> List[Dict]:
        """Obtém alerting rules do Prometheus"""
        try:
            url = f"{PROMETHEUS_API_URL}/api/v1/rules"
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()

            data = resp.json()
            rules = []

            for group in data.get("data", {}).get("groups", []):
                for rule in group.get("rules", []):
                    if rule.get("type") == "alerting":
                        rules.append({
                            "alert": rule.get("alert"),
                            "expr": rule.get("expr"),
                            "for": rule.get("for", "5m"),
                            "severity": rule.get("labels", {}).get("severity", "warning"),
                            "description": rule.get("annotations", {}).get("description", ""),
                            "summary": rule.get("annotations", {}).get("summary", rule.get("alert"))
                        })

            logger.info(f"✅ Obtidas {len(rules)} regras do Prometheus")
            return rules

        except Exception as e:
            logger.error(f"❌ Erro ao obter regras: {str(e)}")
            return []

    def get_all_hosts(self) -> List[Dict]:
        """Obtém todos os hosts do Zabbix"""
        try:
            payload = {
                "jsonrpc": "2.0",
                "method": "host.get",
                "params": {
                    "output": ["hostid", "host", "name"],
                    "limit": 1000
                },
                "auth": self.auth_token,
                "id": 1
            }
            resp = requests.post(ZABBIX_API_URL, json=payload, timeout=10)
            result = resp.json()

            if "result" in result:
                return result["result"]
            else:
                logger.error(f"Erro ao obter hosts: {result.get('error')}")
                return []
        except Exception as e:
            logger.error(f"Erro: {str(e)}")
            return []

    def create_item(self, rule: Dict, hostid: str) -> bool:
        """Cria item no Zabbix"""
        try:
            key = f"prometheus.{rule['alert'].lower()}"

            payload = {
                "jsonrpc": "2.0",
                "method": "item.create",
                "params": {
                    "name": f"Prometheus: {rule['alert']}",
                    "key_": key,
                    "hostid": hostid,
                    "type": 2,  # Zabbix trapper
                    "value_type": 3,  # Numeric (unsigned)
                    "description": rule.get('description', rule.get('summary', ''))
                },
                "auth": self.auth_token,
                "id": 1
            }

            resp = requests.post(ZABBIX_API_URL, json=payload, timeout=10)
            result = resp.json()

            if "result" in result and result["result"].get("itemids"):
                logger.debug(f"✅ Item criado: {key}")
                return True
            else:
                error = result.get('error', {}).get('data', str(result.get('error')))
                if "already exists" not in str(error):
                    logger.warning(f"⚠️  Item existente ou erro: {key}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao criar item: {str(e)}")
            return False

    def create_trigger(self, rule: Dict, hostname: str) -> bool:
        """Cria trigger no Zabbix"""
        try:
            expression = f"{{{{TRIGGER.VALUE}}}}=1 and last(/{hostname}/prometheus.{rule['alert'].lower()}/)>0"
            priority = SEVERITY_MAP.get(rule.get('severity', 'warning'), 2)

            payload = {
                "jsonrpc": "2.0",
                "method": "trigger.create",
                "params": {
                    "description": rule.get('summary', rule['alert']),
                    "expression": expression,
                    "priority": priority,
                    "type": 0
                },
                "auth": self.auth_token,
                "id": 1
            }

            resp = requests.post(ZABBIX_API_URL, json=payload, timeout=10)
            result = resp.json()

            if "result" in result and result["result"].get("triggerids"):
                logger.debug(f"✅ Trigger criada: {rule['alert']}")
                return True
            else:
                logger.warning(f"⚠️  Trigger existente ou erro: {rule['alert']}")
                return False

        except Exception as e:
            logger.error(f"❌ Erro ao criar trigger: {str(e)}")
            return False

    def sync_host(self, hostname: str, hostid: str) -> Dict:
        """Sincroniza todas as regras para um host"""
        try:
            rules = self.get_prometheus_rules()

            if not rules:
                logger.warning(f"⚠️  Nenhuma regra encontrada para {hostname}")
                return {"success": False, "items": 0, "triggers": 0}

            items_created = 0
            triggers_created = 0

            for rule in rules:
                if self.create_item(rule, hostid):
                    items_created += 1

                if self.create_trigger(rule, hostname):
                    triggers_created += 1

            logger.info(f"✅ {hostname}: {items_created} items, {triggers_created} triggers")
            return {
                "success": True,
                "hostname": hostname,
                "items": items_created,
                "triggers": triggers_created
            }

        except Exception as e:
            logger.error(f"❌ Erro ao sincronizar: {str(e)}")
            return {"success": False, "items": 0, "triggers": 0}


def main():
    parser = argparse.ArgumentParser(description="Sincronizar regras Prometheus com Zabbix")
    parser.add_argument("--list", action="store_true", help="Listar hosts")
    parser.add_argument("--host", help="Sincronizar host específico")
    parser.add_argument("--all", action="store_true", help="Sincronizar todos os hosts")
    parser.add_argument("--verbose", action="store_true", help="Modo verbose")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Login
    sync = PrometheusSync()
    token = sync.login_zabbix()
    if not token:
        logger.error("Não conseguiu conectar ao Zabbix")
        return 1

    sync.auth_token = token

    # Operações
    if args.list:
        hosts = sync.get_all_hosts()
        logger.info(f"\n📋 {len(hosts)} hosts encontrados:\n")
        for h in hosts:
            logger.info(f"  • {h['host']:<30} (ID: {h['hostid']})")
        return 0

    if args.host:
        hosts = sync.get_all_hosts()
        host = next((h for h in hosts if h['host'] == args.host), None)

        if not host:
            logger.error(f"Host '{args.host}' não encontrado")
            return 1

        result = sync.sync_host(args.host, host['hostid'])
        if result['success']:
            logger.info(f"✅ Sincronização concluída: {result['items']} items, {result['triggers']} triggers")
            return 0
        else:
            logger.error("❌ Falha na sincronização")
            return 1

    if args.all:
        hosts = sync.get_all_hosts()
        logger.info(f"\n🔄 Sincronizando {len(hosts)} hosts...\n")

        total_items = 0
        total_triggers = 0

        for host in hosts:
            result = sync.sync_host(host['host'], host['hostid'])
            total_items += result.get('items', 0)
            total_triggers += result.get('triggers', 0)

        logger.info(f"\n✅ Total: {total_items} items, {total_triggers} triggers")
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
