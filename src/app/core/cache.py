"""Redisキャッシュ管理。"""

import json
from typing import Any

from redis.asyncio import Redis

from app.config import settings


class CacheManager:
    """Redisキャッシュマネージャー。"""

    def __init__(self):
        """初期化."""
        self._redis: Redis | None = None

    async def connect(self) -> None:
        """Redis接続を確立."""
        if settings.REDIS_URL:
            self._redis = await Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )

    async def disconnect(self) -> None:
        """Redis接続を閉じる."""
        if self._redis:
            await self._redis.aclose()

    async def get(self, key: str) -> Any | None:
        """キャッシュからデータを取得.

        Args:
            key: キャッシュキー

        Returns:
            キャッシュされたデータ、存在しない場合はNone
        """
        if not self._redis:
            return None

        value = await self._redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: int | None = None,
    ) -> None:
        """データをキャッシュに保存.

        Args:
            key: キャッシュキー
            value: キャッシュするデータ
            expire: 有効期限（秒）、Noneの場合は無期限
        """
        if not self._redis:
            return

        serialized = json.dumps(value, ensure_ascii=False, default=str)
        if expire:
            await self._redis.setex(key, expire, serialized)
        else:
            await self._redis.set(key, serialized)

    async def delete(self, key: str) -> None:
        """キャッシュからデータを削除.

        Args:
            key: キャッシュキー
        """
        if not self._redis:
            return

        await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        """キャッシュキーが存在するかチェック.

        Args:
            key: キャッシュキー

        Returns:
            存在する場合True
        """
        if not self._redis:
            return False

        return await self._redis.exists(key) > 0

    async def clear(self, pattern: str = "*") -> None:
        """パターンに一致するキャッシュをすべて削除.

        Args:
            pattern: キーパターン（デフォルト: "*" すべて）
        """
        if not self._redis:
            return

        async for key in self._redis.scan_iter(match=pattern):
            await self._redis.delete(key)


# グローバルキャッシュマネージャーインスタンス
cache_manager = CacheManager()


async def get_cache_manager() -> CacheManager:
    """キャッシュマネージャーを取得.

    Returns:
        CacheManagerインスタンス
    """
    return cache_manager
