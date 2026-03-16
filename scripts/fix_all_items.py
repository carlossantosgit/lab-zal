#!/usr/bin/env python3
"""Fix interface for all prometheus items"""
import requests

ZABBIX_URL = "http://localhost:8080/api_jsonrpc.php"

def zabbix_call(method, params, auth_token=None):
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

# Login
result = zabbix_call("user.login", {"user": "Admin", "password": "zabbix"})
token = result["result"]

# Get all hosts that start with "node-" or "prometheus-"
hosts = zabbix_call("host.get", {}, token)
target_hosts = [h for h in hosts["result"] if h["host"] in ["node-01", "prometheus-server"]]

print(f"Found {len(target_hosts)} target hosts\n")

for host in target_hosts:
    print(f"🔧 Host: {host['host']}")

    # Get interface
    interfaces = zabbix_call("hostinterface.get", {"hostids": host["hostid"]}, token)
    if not interfaces["result"]:
        print(f"   ⚠️  No interface found\n")
        continue

    interfaceid = interfaces["result"][0]["interfaceid"]
    print(f"   Interface ID: {interfaceid}")

    # Get all items for this host
    items = zabbix_call("item.get", {
        "hostids": host["hostid"]
    }, token)

    print(f"   Found {len(items['result'])} items")

    for item in items["result"]:
        # Update item with interface
        result = zabbix_call("item.update", {
            "itemid": item["itemid"],
            "interfaceid": interfaceid
        }, token)

        if "error" in result:
            print(f"   ❌ {item['key_']}: {result['error']}")
        else:
            print(f"   ✅ {item['key_']}")

    print()

print("✅ Done!")

