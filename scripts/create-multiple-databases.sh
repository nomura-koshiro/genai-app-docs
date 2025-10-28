#!/bin/bash

# 複数のPostgreSQLデータベースを作成するスクリプト
# POSTGRES_MULTIPLE_DATABASES環境変数からカンマ区切りのDB名を読み取る

set -e
set -u

function create_database() {
	local database=$1
	echo "Creating database '$database'"
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
	    CREATE DATABASE $database;
	    GRANT ALL PRIVILEGES ON DATABASE $database TO $POSTGRES_USER;
EOSQL
}

if [ -n "${POSTGRES_MULTIPLE_DATABASES:-}" ]; then
	echo "Multiple database creation requested: $POSTGRES_MULTIPLE_DATABASES"
	for db in $(echo $POSTGRES_MULTIPLE_DATABASES | tr ',' ' '); do
		# デフォルトDBと同じ名前はスキップ
		if [ "$db" != "$POSTGRES_DB" ]; then
			create_database $db
		fi
	done
	echo "Multiple databases created"
fi
