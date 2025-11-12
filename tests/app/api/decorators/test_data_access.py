"""データアクセスデコレータのテスト。

このテストは、data_access.pyのデータアクセス関連デコレータを検証します。
データベース接続を必要としません。
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.api.decorators import cache_result, transactional

# データベース不要のユニットテストとしてマーク
pytestmark = pytest.mark.skip_db


# セッションスコープのフィクスチャをオーバーライドしてデータベースセットアップをスキップ
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """デコレータテストではデータベースセットアップをスキップ。"""
    yield


class TestCacheResult:
    """cache_resultデコレータのテスト。"""

    @pytest.mark.asyncio
    async def test_cache_hit(self):
        """キャッシュヒット時にキャッシュから返却されることをテスト。"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = {"cached": "data"}

        with patch("app.api.decorators.data_access.cache_manager", mock_cache):

            @cache_result(ttl=300, key_prefix="test")
            async def test_func(arg1: int):
                return {"db": "data"}

            result = await test_func(123)

            assert result == {"cached": "data"}
            assert mock_cache.get.called
            # キャッシュヒットなので関数は実行されない（dbデータは返らない）

    @pytest.mark.asyncio
    async def test_cache_miss_and_set(self):
        """キャッシュミス時に関数実行後キャッシュに保存されることをテスト。"""
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None  # キャッシュミス

        with patch("app.api.decorators.data_access.cache_manager", mock_cache):

            @cache_result(ttl=300, key_prefix="test")
            async def test_func(arg1: int):
                return {"db": "data"}

            result = await test_func(123)

            assert result == {"db": "data"}
            assert mock_cache.get.called
            assert mock_cache.set.called
            # setが正しい引数で呼ばれているか確認
            set_call_args = mock_cache.set.call_args
            assert set_call_args[0][1] == {"db": "data"}  # value
            assert set_call_args[0][2] == 300  # ttl


class TestTransactional:
    """transactionalデコレータのテスト。"""

    @pytest.mark.asyncio
    async def test_commit_on_success(self):
        """正常終了時にコミットされることをテスト。"""
        mock_db = AsyncMock()

        class TestService:
            def __init__(self):
                self.db = mock_db

            @transactional
            async def test_method(self):
                return "success"

        service = TestService()
        result = await service.test_method()

        assert result == "success"
        assert mock_db.commit.called
        assert not mock_db.rollback.called

    @pytest.mark.asyncio
    async def test_rollback_on_error(self):
        """例外発生時にロールバックされることをテスト。"""
        mock_db = AsyncMock()

        class TestService:
            def __init__(self):
                self.db = mock_db

            @transactional
            async def test_method(self):
                raise ValueError("エラー")

        service = TestService()

        with pytest.raises(ValueError):
            await service.test_method()

        assert not mock_db.commit.called
        assert mock_db.rollback.called
