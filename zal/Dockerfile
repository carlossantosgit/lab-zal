FROM --platform=linux/arm64 golang:1.16-alpine AS builder

RUN apk add --no-cache git

RUN git clone https://github.com/devopyio/zabbix-alertmanager.git /src && \
    cd /src && git checkout v1.2.0 && \
    go build -o /zal ./cmd/zal

FROM --platform=linux/arm64 alpine:3.18
COPY --from=builder /zal /usr/local/bin/zal
COPY hosts.yml /etc/zal/hosts.yml
COPY zal-config.yaml /etc/zal/zal-config.yaml

EXPOSE 9095
CMD ["zal", "send", \
     "--zabbix-addr=zabbix-server:10051", \
     "--default-host=prometheus-lab", \
     "--hosts-path=/etc/zal/hosts.yml", \
     "--addr=0.0.0.0:9095", \
     "--key-prefix=prometheus", \
     "--log.level=info"]
