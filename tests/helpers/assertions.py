"""テスト用アサーションヘルパー。

このモジュールは、テストコードで頻繁に使用されるアサーションパターンを
再利用可能な関数として提供します。
"""

from typing import Any

from httpx import Response


def assert_error_response(
    response: Response,
    expected_status: int,
    expected_error_type: str | None = None,
    expected_message_contains: str | None = None,
) -> dict[str, Any]:
    """エラーレスポンスの標準検証。

    Args:
        response: HTTPレスポンス
        expected_status: 期待されるステータスコード
        expected_error_type: 期待されるエラータイプ（オプション）
        expected_message_contains: エラーメッセージに含まれるべき文字列（オプション）

    Returns:
        エラーレスポンスの辞書

    Raises:
        AssertionError: 検証に失敗した場合
    """
    assert response.status_code == expected_status, (
        f"Expected status {expected_status}, got {response.status_code}. "
        f"Response: {response.text}"
    )

    error_data = response.json()
    assert "detail" in error_data, f"Response missing 'detail': {error_data}"

    if expected_error_type:
        assert error_data.get("error_type") == expected_error_type, (
            f"Expected error_type '{expected_error_type}', "
            f"got '{error_data.get('error_type')}'"
        )

    if expected_message_contains:
        detail = error_data.get("detail", "")
        assert expected_message_contains in detail, (
            f"Expected '{expected_message_contains}' in detail, " f"got '{detail}'"
        )

    return error_data


def assert_pagination_response(
    response: Response,
    expected_status: int = 200,
    expected_min_items: int = 0,
    expected_max_items: int | None = None,
    items_key: str | None = None,
) -> dict[str, Any]:
    """ページネーションレスポンスの標準検証。

    Args:
        response: HTTPレスポンス
        expected_status: 期待されるステータスコード
        expected_min_items: 最小アイテム数
        expected_max_items: 最大アイテム数（オプション）
        items_key: アイテムリストのキー名（オプション、自動検出）

    Returns:
        レスポンスデータの辞書

    Raises:
        AssertionError: 検証に失敗した場合
    """
    assert (
        response.status_code == expected_status
    ), f"Expected status {expected_status}, got {response.status_code}"

    data = response.json()

    # 標準フィールドの存在確認
    assert "total" in data, f"Response missing 'total': {data}"
    assert "skip" in data, f"Response missing 'skip': {data}"
    assert "limit" in data, f"Response missing 'limit': {data}"

    # アイテムキーを自動検出または指定
    if items_key is None:
        possible_keys = [
            "items",
            "projects",
            "sessions",
            "users",
            "files",
            "trees",
            "data",
        ]
        items_key = next((k for k in possible_keys if k in data), None)
        assert (
            items_key is not None
        ), f"Could not find items key in response. Available keys: {list(data.keys())}"

    items = data[items_key]
    assert isinstance(
        items, list
    ), f"Expected list for '{items_key}', got {type(items)}"

    # アイテム数の検証
    assert (
        len(items) >= expected_min_items
    ), f"Expected at least {expected_min_items} items, got {len(items)}"

    if expected_max_items is not None:
        assert (
            len(items) <= expected_max_items
        ), f"Expected at most {expected_max_items} items, got {len(items)}"

    return data


def assert_created_response(
    response: Response,
    required_fields: list[str] | None = None,
) -> dict[str, Any]:
    """作成成功レスポンスの標準検証。

    Args:
        response: HTTPレスポンス
        required_fields: 必須フィールドのリスト

    Returns:
        作成されたリソースのデータ

    Raises:
        AssertionError: 検証に失敗した場合
    """
    assert response.status_code == 201, (
        f"Expected status 201, got {response.status_code}. "
        f"Response: {response.text}"
    )

    data = response.json()
    assert "id" in data, f"Response missing 'id': {data}"

    if required_fields:
        for field in required_fields:
            assert field in data, f"Response missing required field '{field}': {data}"

    return data


def assert_ok_response(
    response: Response,
    required_fields: list[str] | None = None,
) -> dict[str, Any]:
    """成功レスポンス (200 OK) の標準検証。

    Args:
        response: HTTPレスポンス
        required_fields: 必須フィールドのリスト

    Returns:
        レスポンスデータ

    Raises:
        AssertionError: 検証に失敗した場合
    """
    assert response.status_code == 200, (
        f"Expected status 200, got {response.status_code}. "
        f"Response: {response.text}"
    )

    data = response.json()

    if required_fields:
        for field in required_fields:
            assert field in data, f"Response missing required field '{field}': {data}"

    return data


def assert_no_content_response(response: Response) -> None:
    """削除成功レスポンス (204 No Content) の検証。

    Args:
        response: HTTPレスポンス

    Raises:
        AssertionError: 検証に失敗した場合
    """
    assert response.status_code == 204, (
        f"Expected status 204, got {response.status_code}. "
        f"Response: {response.text}"
    )


def assert_unauthorized_response(response: Response) -> dict[str, Any]:
    """認証エラーレスポンスの検証。

    Args:
        response: HTTPレスポンス

    Returns:
        エラーレスポンスデータ

    Raises:
        AssertionError: 検証に失敗した場合
    """
    assert response.status_code in [
        401,
        403,
    ], f"Expected status 401 or 403, got {response.status_code}"
    return response.json()


def assert_not_found_response(
    response: Response,
    expected_message_contains: str | None = None,
) -> dict[str, Any]:
    """NotFoundエラーレスポンスの検証。

    Args:
        response: HTTPレスポンス
        expected_message_contains: エラーメッセージに含まれるべき文字列

    Returns:
        エラーレスポンスデータ

    Raises:
        AssertionError: 検証に失敗した場合
    """
    return assert_error_response(
        response,
        expected_status=404,
        expected_message_contains=expected_message_contains,
    )


def assert_csrf_error(
    response: Response,
    expected_message_contains: str = "CSRF token",
) -> dict[str, Any]:
    """CSRFエラーレスポンスの標準検証。

    Args:
        response: HTTPレスポンス
        expected_message_contains: CSRFエラーメッセージに含まれるべき文字列

    Returns:
        エラーレスポンスデータ

    Raises:
        AssertionError: 検証に失敗した場合
    """
    assert response.status_code == 403, (
        f"Expected CSRF error (403), got {response.status_code}. "
        f"Response: {response.text}"
    )

    error_data = response.json()
    detail = error_data.get("detail", "")

    assert expected_message_contains in detail, (
        f"Expected '{expected_message_contains}' in CSRF error, got: {detail}"
    )

    return error_data


def assert_no_csrf_error(response: Response) -> None:
    """CSRFエラーでないことを検証。

    CSRFエラー（403でCSRFトークン関連のメッセージ）が発生していないことを確認します。
    他のエラー（401、422など）は許容されます。

    Args:
        response: HTTPレスポンス

    Raises:
        AssertionError: CSRFエラーが発生した場合
    """
    if response.status_code == 403:
        error_detail = response.json().get("detail", "")
        assert "CSRF" not in error_detail, f"Unexpected CSRF error: {error_detail}"
