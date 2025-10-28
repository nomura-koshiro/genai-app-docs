# Alembicマイグレーション

Alembicを使用したデータベースマイグレーション管理について説明します。

## 初期化

```bash
# Alembicの初期化
alembic init alembic
```

## 設定

```python
# alembic/env.py
from app.database import Base
from app.models import user, session, file  # すべてのモデルをインポート

target_metadata = Base.metadata
```

## マイグレーション作成

```bash
# 自動生成
alembic revision --autogenerate -m "create users table"

# 手動作成
alembic revision -m "add column"
```

## マイグレーション実行

```bash
# 最新バージョンに移行
alembic upgrade head

# 1つ戻す
alembic downgrade -1

# 特定バージョンに移行
alembic upgrade ae1027a6acf

# 履歴表示
alembic history

# 現在のバージョン表示
alembic current
```

## マイグレーションファイル例

```python
"""create users table

Revision ID: abc123
Revises:
Create Date: 2024-01-01 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('ix_sample_users_email', 'users', ['email'])


def downgrade() -> None:
    op.drop_index('ix_sample_users_email')
    op.drop_table('users')
```

## 参考リンク

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
