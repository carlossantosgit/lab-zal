#!/usr/bin/env python3
"""
Setup Zabbix host for Prometheus alerts
"""
import requests
import json
import time

ZABBIX_URL = "http://localhost:8080/api_jsonrpc.php"
ZABBIX_USER = "Admin"
ZABBIX_PASSWORD = "zabbix"

def zabbix_call(method, params, auth_token=None):
    """Make a Zabbix API call"""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }

    if auth_token:
        payload["auth"] = auth_token

    response = requests.post(ZABBIX_URL, json=payload)
    return response.json()

def login():
    """Login to Zabbix"""
    result = zabbix_call("user.login", {
        "user": ZABBIX_USER,
        "password": ZABBIX_PASSWORD
    })

    if "error" in result:
        print(f"❌ Login failed: {result['error']}")
        return None

    token = result["result"]
    print(f"✅ Logged in successfully")
    return token

def create_hostgroup(auth_token, name):
    """Create a host group"""
    result = zabbix_call("hostgroup.create", {
        "name": name
    }, auth_token)

    if "error" in result:
        print(f"⚠️  Host group '{name}' creation: {result['error']}")
        # Try to get existing group
        groups = zabbix_call("hostgroup.get", {"filter": {"name": name}}, auth_token)
        if "result" in groups and groups["result"]:
            return groups["result"][0]["groupid"]
        return None

    groupid = result["result"]["groupids"][0]
    print(f"✅ Created host group: {name} (ID: {groupid})")
    return groupid

def create_host(auth_token, hostname, groupid):
    """Create a host"""
    result = zabbix_call("host.create", {
        "host": hostname,
        "name": hostname,
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

    if "error" in result:
        print(f"⚠️  Host '{hostname}' creation: {result['error']}")
        # Try to get existing host
        hosts = zabbix_call("host.get", {"filter": {"host": hostname}}, auth_token)
        if "result" in hosts and hosts["result"]:
            return hosts["result"][0]["hostid"]
        return None

    hostid = result["result"]["hostids"][0]
    print(f"✅ Created host: {hostname} (ID: {hostid})")
    return hostid

def create_trapper_item(auth_token, hostid, key, name):
    """Create a trapper item"""
    result = zabbix_call("item.create", {
        "name": name,
        "key_": key,
        "hostid": hostid,
        "type": 2,  # Trapper
        "value_type": 3,  # Unsigned (0=int, 1=float, 2=char, 3=log, 4=text, 5=raw)
        "history": "7d",
        "trends": "30d"
    }, auth_token)

    if "error" in result:
        print(f"ℹ️  Item '{key}': {result['error']}")
        return None

    print(f"✅ Created item: {key}")
    return result["result"]["itemids"][0]

def create_trigger(auth_token, hostid, name, key, threshold=None):
    """Create a trigger"""
    if threshold:
        expression = f'last(/prometheus-lab/{key})>0'
    else:
        expression = f'last(/prometheus-lab/{key})=0'

    result = zabbix_call("trigger.create", {
        "description": name,
        "expression": expression,
        "priority": 2,  # Warning
        "type": 0
    }, auth_token)

    if "error" in result:
        print(f"ℹ️  Trigger '{name}': {result['error']}")
        return None

    print(f"✅ Created trigger: {name}")
    return result["result"]["triggerids"][0]

def main():
    print("=" * 50)
    print("🔧 Zabbix Setup for Prometheus")
    print("=" * 50)

    # Login
    auth_token = login()
    if not auth_token:
        return

    # Create host group
    groupid = create_hostgroup(auth_token, "Prometheus")
    if not groupid:
        print("❌ Failed to create/get host group")
        return

    # Create host
    hostid = create_host(auth_token, "prometheus-lab", groupid)
    if not hostid:
        print("❌ Failed to create/get host")
        return

    # Create items and triggers
    alerts = [
        {"key": "prometheus.deadmansswitch", "name": "Dead Man's Switch"},
        {"key": "prometheus.highcpu", "name": "High CPU"},
        {"key": "prometheus.lowmemory", "name": "Low Memory"},
    ]

    print("\n📊 Creating items and triggers...")
    for alert in alerts:
        itemid = create_trapper_item(auth_token, hostid, alert["key"], alert["name"])
        if itemid:
            create_trigger(auth_token, hostid, alert["name"], alert["key"])

    print("\n" + "=" * 50)
    print("✅ Setup completed!")
    print("=" * 50)

if __name__ == "__main__":
    time.sleep(5)  # Wait for Zabbix to be ready
    main()
