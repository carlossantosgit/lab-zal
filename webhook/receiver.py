from flask import Flask, request
import subprocess
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

ZABBIX_SERVER = "zabbix-server"

@app.route("/alerts", methods=["POST"])
def alerts():
    data = request.json

    logging.info(f"📬 Received {len(data.get('alerts', []))} alerts")

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

        # Extra: enviar severity se existir
        severity = labels.get("severity", "unknown")

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

