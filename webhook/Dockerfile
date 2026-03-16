FROM python:3.11

RUN apt update && apt install -y zabbix-sender

RUN pip install flask

WORKDIR /app

COPY receiver.py .

CMD ["python","receiver.py"]
