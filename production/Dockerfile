FROM python:3.11-slim

WORKDIR /app

# Dependências do sistema mínimas
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY config.py sync_prometheus.py scheduler.py ./

# Utilizador não-root
RUN useradd -r -s /bin/false appuser
USER appuser

ENTRYPOINT ["python", "scheduler.py"]
