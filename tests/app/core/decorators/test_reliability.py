"""信頼性デコレータのテスト。

このテストは、reliability.pyの信頼性関連デコレータを検証します。
データベース接続を必要としません。
"""

import pytest

from app.core.decorators import retry_on_error

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
    @pytest.mark.parametrize(
        "fail_count,max_retries,should_succeed",
        [
            (2, 3, True),   # 3回目で成功
            (5, 2, False),  # 最大リトライ後失敗
        ],
        ids=["succeeds_after_retries", "fails_max_retries"],
    )
    async def test_retry_on_error_scenarios(self, fail_count, max_retries, should_succeed):
        """[test_reliability-001,002] リトライの動作をテスト（成功/失敗）。"""
        # Arrange
        call_count = 0

        @retry_on_error(max_retries=max_retries, delay=0.01, exceptions=(ValueError,))
        async def test_func():
            nonlocal call_count
            call_count += 1
            if call_count <= fail_count:
                raise ValueError("一時的なエラー" if should_succeed else "永続的なエラー")
            return "success"

        # Act & Assert
        if should_succeed:
            # リトライ後に成功する（Happy Path）
            result = await test_func()
            assert result == "success"
            assert call_count == fail_count + 1  # fail_count回失敗 + 1回成功
        else:
            # すべてのリトライが失敗した場合にエラーが送出される（Error Case）
            with pytest.raises(ValueError, match="永続的なエラー"):
                await test_func()
            assert call_count == max_retries + 1  # 初回 + max_retries回リトライ
