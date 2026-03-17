from flask import Flask, request
import subprocess
import logging
import requests
import time
from prometheus_sync import sync_prometheus_rules_for_host

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

ZABBIX_SERVER = "zabbix-server"
ZABBIX_API_URL = "http://zabbix-web:8080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"

# Cache de auth token para evitar múltiplos logins
_auth_token = None
_auth_timestamp = 0


def zabbix_api_call(method, params, auth_token=None):
    """Make a Zabbix API call"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    if auth_token:
        payload["auth"] = auth_token

    try:
        response = requests.post(ZABBIX_API_URL, json=payload, timeout=5)
        result = response.json()

        if "error" in result:
            logging.error(f"❌ Zabbix API error: {result['error']}")
            return None

        return result.get("result")
    except Exception as e:
        logging.error(f"❌ API call failed: {str(e)}")
        return None


def zabbix_login():
    """Login to Zabbix and return token"""
    global _auth_token, _auth_timestamp

    # Reutilizar token se ainda for válido (cache por 1 hora)
    if _auth_token and (time.time() - _auth_timestamp) < 3600:
        return _auth_token

    result = zabbix_api_call("user.login", {
        "user": ZABBIX_USER,
        "password": ZABBIX_PASSWORD
    })

    if result:
        _auth_token = result
        _auth_timestamp = time.time()
        logging.info("🔐 Zabbix API login successful")
        return result

    logging.error("❌ Zabbix API login failed")
    return None


def host_exists(zabbix_host, auth_token):
    """Check if host exists in Zabbix"""
    result = zabbix_api_call("host.get", {
        "filter": {"host": zabbix_host}
    }, auth_token)

    return bool(result and len(result) > 0)


def get_host_info(zabbix_host, auth_token):
    """Get host ID and interface info"""
    result = zabbix_api_call("host.get", {
        "filter": {"host": zabbix_host},
        "selectInterfaces": "extend"
    }, auth_token)

    if result and len(result) > 0:
        return result[0]
    return None


def get_or_create_hostgroup(auth_token):
    """Get Prometheus host group or create if doesn't exist"""
    result = zabbix_api_call("hostgroup.get", {
        "filter": {"name": "Prometheus"}
    }, auth_token)

    if result and len(result) > 0:
        return result[0]["groupid"]

    # Group doesn't exist, create it
    result = zabbix_api_call("hostgroup.create", {
        "name": "Prometheus"
    }, auth_token)

    if result and len(result) > 0:
        logging.info(f"✅ Created hostgroup: Prometheus (ID: {result[0]})")
        return result[0]

    logging.error("❌ Failed to create hostgroup")
    return None


def create_host(zabbix_host, auth_token):
    """Create a new host in Zabbix"""
    groupid = get_or_create_hostgroup(auth_token)
    if not groupid:
        logging.error("❌ Cannot create host - no hostgroup")
        return None

    result = zabbix_api_call("host.create", {
        "host": zabbix_host,
        "name": zabbix_host,
        "groups": [{"groupid": groupid}],
        "interfaces": [{
            "type": 1,
            "main": 1,
            "useip": 1,
            "ip": "127.0.0.1",
            "dns": "",
            "port": "10050"
        }]
    }, auth_token)

    if result and isinstance(result, dict) and "hostids" in result:
        hostid = result["hostids"][0]
        logging.info(f"✅ Created host in Zabbix: {zabbix_host} (ID: {hostid})")
        return hostid

    logging.error(f"❌ Failed to create host '{zabbix_host}': {result}")
    return None


def create_items(hostid, auth_token):
    """Create default prometheus items"""
    items = [
        {"key": "prometheus.deadmansswitch", "name": "Prometheus - Dead Man's Switch"},
        {"key": "prometheus.highcpu", "name": "Prometheus - High CPU"},
        {"key": "prometheus.lowmemory", "name": "Prometheus - Low Memory"}
    ]

    created_count = 0

    for item_info in items:
        result = zabbix_api_call("item.create", {
            "name": item_info["name"],
            "key_": item_info["key"],
            "hostid": hostid,
            "type": 2,        # Trapper
            "value_type": 3,  # Unsigned
            "history": "7d",
            "trends": "30d"
        }, auth_token)

        if result:
            created_count += 1
            logging.info(f"✅ Created item: {item_info['key']}")
        else:
            logging.error(f"❌ Failed to create item: {item_info['key']}")

    # Agora corrigir interfaces dos items
    if created_count > 0:
        fix_item_interfaces(hostid, auth_token)

    return created_count


def fix_item_interfaces(hostid, auth_token):
    """Fix item interfaces (trapper items need no interface, but Zabbix requires one)"""
    # Get host interface
    host_info = zabbix_api_call("host.get", {
        "hostids": [hostid],  # 🔧 PASS AS LIST
        "selectInterfaces": "extend"
    }, auth_token)

    if not host_info or len(host_info) == 0:
        logging.error(f"❌ Cannot find host {hostid}")
        return

    if not host_info[0].get("interfaces"):
        logging.error(f"❌ Host {hostid} has no interfaces")
        return

    interfaceid = host_info[0]["interfaces"][0]["interfaceid"]

    # Get items for this host
    items = zabbix_api_call("item.get", {
        "hostids": [hostid]  # 🔧 PASS AS LIST
    }, auth_token)

    if not items:
        return

    for item in items:
        zabbix_api_call("item.update", {
            "itemid": item["itemid"],
            "interfaceid": interfaceid
        }, auth_token)


def ensure_host_exists(zabbix_host, auth_token):
    """Ensure host exists in Zabbix, create if needed and sync Prometheus rules"""
    if host_exists(zabbix_host, auth_token):
        logging.info(f"✓ Host '{zabbix_host}' already exists")
        return True

    logging.info(f"🆕 Host '{zabbix_host}' not found - creating...")

    hostid = create_host(zabbix_host, auth_token)
    if not hostid:
        logging.error(f"❌ Failed to create host '{zabbix_host}'")
        return False

    items_created = create_items(hostid, auth_token)
    logging.info(f"✅ Created host '{zabbix_host}' with {items_created} items")

    # 🔄 Sincronizar regras Prometheus do arquivo fake
    logging.info(f"🔄 Sincronizando regras Prometheus para '{zabbix_host}'...")
    try:
        sync_result = sync_prometheus_rules_for_host(
            hostname=zabbix_host,
            hostid=hostid,
            auth_token=auth_token,
            use_fake=True  # Usar arquivo fake para demo
        )

        if sync_result.get("success"):
            logging.info(f"✨ Prometheus sync: {sync_result.get('items_created')} items, "
                        f"{sync_result.get('triggers_created')} triggers criados")
        else:
            logging.warning(f"⚠️  Prometheus sync falhou: {sync_result.get('message')}")

    except Exception as e:
        logging.error(f"❌ Erro ao sincronizar Prometheus rules: {str(e)}")

    return True


@app.route("/alerts", methods=["POST"])
def alerts():
    data = request.json

    logging.info(f"📬 Received {len(data.get('alerts', []))} alerts")

    # Login to Zabbix API once
    auth_token = zabbix_login()
    if not auth_token:
        logging.error("❌ Cannot connect to Zabbix API")
        return "API Error", 500

    for alert in data["alerts"]:
        labels = alert["labels"]
        annotations = alert.get("annotations", {})

        # Prioridade: zabbix_host > hostname > instance
        zabbix_host = labels.get("zabbix_host") or labels.get("hostname")

        if not zabbix_host:
            # Fallback: extrair do instance se não tiver zabbix_host
            instance = labels.get("instance", "unknown")
            zabbix_host = instance.split(":")[0]

        alertname = labels.get("alertname", "alert").lower()
        key = f"prometheus.{alertname}"

        value = "1" if alert["status"] == "firing" else "0"

        # 🆕 AUTOMÁTICO: Garantir que host existe
        if not ensure_host_exists(zabbix_host, auth_token):
            logging.error(f"❌ Will not send alert - host creation failed: {zabbix_host}")
            continue

        logging.info(f"📤 Sending to Zabbix - Host: {zabbix_host}, Key: {key}, Value: {value}, Status: {alert['status']}")

        # Enviar o alerta
        result = subprocess.run([
            "zabbix_sender",
            "-z", ZABBIX_SERVER,
            "-s", zabbix_host,
            "-k", key,
            "-o", value
        ], capture_output=True, text=True)

        if "processed: 1" in result.stderr:
            logging.info(f"✅ Successfully sent to {zabbix_host}")
        else:
            logging.error(f"❌ Failed to send: {result.stderr}")

    return "ok"


@app.route("/health", methods=["GET"])
def health():
    return "OK"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)

