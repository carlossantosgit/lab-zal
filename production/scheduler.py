#!/usr/bin/env python3
"""
Scheduler do sincronizador Prometheus -> Zabbix.

Intervalos configuráveis via env vars:
  SYNC_INTERVAL_MINUTES  (default: 5)  -- cria/actualiza items e triggers (--all)
  PUSH_INTERVAL_MINUTES  (default: 1)  -- envia valores dos alertas activos (--push)
"""

import os
import subprocess
import sys
import time

import schedule

SCRIPT = os.path.join(os.path.dirname(__file__), "sync_prometheus.py")
SYNC_INTERVAL = int(os.getenv("SYNC_INTERVAL_MINUTES", "5"))
PUSH_INTERVAL = int(os.getenv("PUSH_INTERVAL_MINUTES", "1"))


def _run(flag):
    result = subprocess.run(
        [sys.executable, SCRIPT, flag],
        capture_output=False,
    )
    if result.returncode != 0:
        print("WARN: %s terminou com codigo %d" % (flag, result.returncode),
              flush=True)


def run_sync():
    _run("--all")


def run_push():
    _run("--push")


if __name__ == "__main__":
    print("Scheduler iniciado  (sync=%dm  push=%dm)" % (SYNC_INTERVAL, PUSH_INTERVAL),
          flush=True)

    # Executar imediatamente no arranque
    run_sync()
    run_push()

    schedule.every(SYNC_INTERVAL).minutes.do(run_sync)
    schedule.every(PUSH_INTERVAL).minutes.do(run_push)

    while True:
        schedule.run_pending()
        time.sleep(10)
