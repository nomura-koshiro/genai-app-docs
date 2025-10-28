#!/bin/bash
# PostgreSQL & Redis起動スクリプト

# スクリプトの場所から1階層上がプロジェクトルート
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"

echo "=== Docker起動 ==="
sudo service docker start

echo "=== PostgreSQL & Redis コンテナ起動 ==="
docker compose up -d postgres redis

echo "=== PostgreSQL healthcheckを待機中 ==="
for i in {1..30}; do
    if docker inspect --format='{{.State.Health.Status}}' backend-postgres 2>/dev/null | grep -q "healthy"; then
        echo "PostgreSQL is healthy!"
        break
    fi
    echo "待機中... ($i/30)"
    sleep 1
done

echo "=== Redis healthcheckを待機中 ==="
for i in {1..30}; do
    if docker inspect --format='{{.State.Health.Status}}' backend-redis 2>/dev/null | grep -q "healthy"; then
        echo "Redis is healthy!"
        break
    fi
    echo "待機中... ($i/30)"
    sleep 1
done

echo "=== 起動確認 ==="
docker ps | grep -E "postgres|redis"

echo "=== データベース準備完了 ==="
