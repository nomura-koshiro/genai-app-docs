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
    async def test_cache_result_cache_hit_returns_cached_data(self):
        """[test_data_access-001] キャッシュヒット時にキャッシュから返却されることをテスト。"""
        # Arrange
        mock_cache = AsyncMock()
        mock_cache.get.return_value = {"cached": "data"}

        # Act
        with patch("app.api.decorators.data_access.cache_manager", mock_cache):

            @cache_result(ttl=300, key_prefix="test")
            async def test_func(arg1: int):
                return {"db": "data"}

            result = await test_func(123)

            # Assert
            assert result == {"cached": "data"}
            assert mock_cache.get.called
            # キャッシュヒットなので関数は実行されない（dbデータは返らない）

    @pytest.mark.asyncio
    async def test_cache_result_cache_miss_executes_and_stores(self):
        """[test_data_access-002] キャッシュミス時に関数実行後キャッシュに保存されることをテスト。"""
        # Arrange
        mock_cache = AsyncMock()
        mock_cache.get.return_value = None  # キャッシュミス

        # Act
        with patch("app.api.decorators.data_access.cache_manager", mock_cache):

            @cache_result(ttl=300, key_prefix="test")
            async def test_func(arg1: int):
                return {"db": "data"}

            result = await test_func(123)

            # Assert
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
    async def test_transactional_success_commits(self):
        """[test_data_access-003] 正常終了時にコミットされることをテスト。"""
        # Arrange
        mock_db = AsyncMock()

        class TestService:
            def __init__(self):
                self.db = mock_db

            @transactional
            async def test_method(self):
                return "success"

        service = TestService()

        # Act
        result = await service.test_method()

        # Assert
        assert result == "success"
        assert mock_db.commit.called
        assert not mock_db.rollback.called

    @pytest.mark.asyncio
    async def test_transactional_error_rollbacks(self):
        """[test_data_access-004] 例外発生時にロールバックされることをテスト。"""
        # Arrange
        mock_db = AsyncMock()

        class TestService:
            def __init__(self):
                self.db = mock_db

            @transactional
            async def test_method(self):
                raise ValueError("エラー")

        service = TestService()

        # Act
        with pytest.raises(ValueError):
            await service.test_method()

        # Assert
        assert not mock_db.commit.called
        assert mock_db.rollback.called
