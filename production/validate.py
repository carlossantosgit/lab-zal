#!/usr/bin/env python3
"""
Validação Rápida - Produção
Valida que sincronização está funcionando
"""

import requests
import sys
import logging
from config import (
    ZABBIX_API_URL,
    ZABBIX_USER,
    ZABBIX_PASSWORD,
    PROMETHEUS_URL,
    PROMETHEUS_USER,
    PROMETHEUS_PASS,
    PROMETHEUS_VERIFY_SSL
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def validate():
    """Valida sincronização completa"""

    logger.info("🔍 Validando infraestrutura de sincronização...")

    # 1. Testar Prometheus
    logger.info("\n1️⃣  Testando Prometheus...")
    try:
        auth = (PROMETHEUS_USER, PROMETHEUS_PASS) if PROMETHEUS_PASS else None
        resp = requests.get(
            f"{PROMETHEUS_URL}/-/healthy",
            auth=auth,
            verify=PROMETHEUS_VERIFY_SSL,
            timeout=5
        )
        if resp.status_code == 200:
            logger.info("   ✅ Prometheus OK")
        else:
            logger.error(f"   ❌ Prometheus respondeu com {resp.status_code}")
            return False
    except Exception as e:
        logger.error(f"   ❌ Prometheus não acessível: {str(e)}")
        return False

    # 2. Testar Zabbix
    logger.info("\n2️⃣  Testando Zabbix...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {"user": ZABBIX_USER, "password": ZABBIX_PASSWORD},
            "id": 1
        }
        resp = requests.post(ZABBIX_API_URL, json=payload, timeout=5)
        result = resp.json()

        if "result" in result:
            logger.info("   ✅ Zabbix OK (login bem-sucedido)")
            token = result["result"]
        else:
            logger.error(f"   ❌ Login Zabbix falhou: {result.get('error')}")
            return False
    except Exception as e:
        logger.error(f"   ❌ Zabbix não acessível: {str(e)}")
        return False

    # 3. Contar regras Prometheus
    logger.info("\n3️⃣  Contando regras Prometheus...")
    try:
        auth = (PROMETHEUS_USER, PROMETHEUS_PASS) if PROMETHEUS_PASS else None
        resp = requests.get(
            f"{PROMETHEUS_URL}/api/v1/rules",
            auth=auth,
            verify=PROMETHEUS_VERIFY_SSL,
            timeout=5
        )
        data = resp.json()

        rule_count = 0
        for group in data.get("data", {}).get("groups", []):
            for rule in group.get("rules", []):
                if rule.get("type") == "alerting":
                    rule_count += 1

        logger.info(f"   ✅ {rule_count} alerting rules encontradas")
    except Exception as e:
        logger.error(f"   ❌ Erro ao contar regras: {str(e)}")
        return False

    # 4. Contar hosts Zabbix
    logger.info("\n4️⃣  Contando hosts Zabbix...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {"output": ["hostid"]},
            "auth": token,
            "id": 1
        }
        resp = requests.post(ZABBIX_API_URL, json=payload, timeout=5)
        result = resp.json()

        if "result" in result:
            host_count = len(result["result"])
            logger.info(f"   ✅ {host_count} hosts encontrados em Zabbix")
        else:
            logger.error(f"   ❌ Erro ao listar hosts: {result.get('error')}")
            return False
    except Exception as e:
        logger.error(f"   ❌ Erro: {str(e)}")
        return False

    logger.info("\n" + "="*60)
    logger.info("✅ VALIDAÇÃO OK - Sistema pronto para sincronização!")
    logger.info("="*60)

    return True


if __name__ == "__main__":
    success = validate()
    sys.exit(0 if success else 1)
