#!/usr/bin/env bash
# Auto-generated install script from Doramagic seed resources.packages
set -e

echo 'Installing Doramagic skill dependencies...'

python3 -m pip install github.com/jackc/pgx/v5
python3 -m pip install github.com/uptrace/bun
python3 -m pip install github.com/formancehq/go-libs/v4
python3 -m pip install github.com/nats-io/nats.go
python3 -m pip install github.com/formancehq/numscript
python3 -m pip install go.opentelemetry.io/otel
python3 -m pip install github.com/ThreeDotsLabs/watermill
python3 -m pip install github.com/ClickHouse/clickhouse-go/v2
python3 -m pip install github.com/olivere/elastic/v7
python3 -m pip install github.com/spf13/viper

echo 'Done. Skill ready to use.'