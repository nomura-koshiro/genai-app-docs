"""信頼性デコレータのテスト。

このテストは、reliability.pyの信頼性関連デコレータを検証します。
データベース接続を必要としません。
"""

import pytest

from app.api.decorators import retry_on_error

# データベース不要のユニットテストとしてマーク
pytestmark = pytest.mark.skip_db


# セッションスコープのフィクスチャをオーバーライドしてデータベースセットアップをスキップ
@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """デコレータテストではデータベースセットアップをスキップ。"""
    yield


class TestRetryOnError:
    """retry_on_errorデコレータのテスト。"""

    @pytest.mark.asyncio
    async def test_successful_first_attempt(self):
        """初回実行で成功する場合、リトライしないことをテスト。"""
        call_count = 0

        @retry_on_error(max_retries=3, delay=0.01)
        async def test_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await test_func()

        assert result == "success"
        assert call_count == 1  # 1回だけ実行

    @pytest.mark.asyncio
    async def test_retry_and_success(self):
        """2回失敗後に成功する場合、正しくリトライされることをテスト。"""
        call_count = 0

        @retry_on_error(max_retries=3, delay=0.01, exceptions=(ValueError,))
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("一時的なエラー")
            return "success"

        result = await test_func()

        assert result == "success"
        assert call_count == 3  # 3回目で成功

    @pytest.mark.asyncio
    async def test_all_retries_failed(self):
        """すべてのリトライが失敗した場合、最後の例外が送出されることをテスト。"""
        call_count = 0

        @retry_on_error(max_retries=2, delay=0.01, exceptions=(ValueError,))
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("永続的なエラー")

        with pytest.raises(ValueError, match="永続的なエラー"):
            await test_func()

        assert call_count == 3  # 初回 + 2回リトライ

    @pytest.mark.asyncio
    async def test_non_retryable_exception(self):
        """リトライ対象外の例外は即座に送出されることをテスト。"""
        call_count = 0

        @retry_on_error(max_retries=3, delay=0.01, exceptions=(ValueError,))
        async def test_func():
            nonlocal call_count
            call_count += 1
            raise TypeError("リトライ対象外")

        with pytest.raises(TypeError):
            await test_func()

        assert call_count == 1  # リトライせず即座に失敗
