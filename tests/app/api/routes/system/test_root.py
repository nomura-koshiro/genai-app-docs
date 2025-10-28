"""ルートエンドポイントのテスト。

このモジュールは、ルートパス（/）が正しくウェルカムメッセージと
バージョン情報を返すことを検証します。
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_returns_200(client: AsyncClient):
    """ルートエンドポイントが200を返すことを確認。"""
    response = await client.get("/")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_root_returns_json(client: AsyncClient):
    """ルートエンドポイントがJSON形式を返すことを確認。"""
    response = await client.get("/")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]

    # JSONとしてパース可能
    data = response.json()
    assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_root_contains_message(client: AsyncClient):
    """レスポンスにウェルカムメッセージが含まれることを確認。"""
    response = await client.get("/")
    data = response.json()

    assert "message" in data
    assert isinstance(data["message"], str)
    assert len(data["message"]) > 0
    # "Welcome" という文字列が含まれる
    assert "welcome" in data["message"].lower()


@pytest.mark.asyncio
async def test_root_contains_version(client: AsyncClient):
    """レスポンスにバージョン情報が含まれることを確認。"""
    response = await client.get("/")
    data = response.json()

    assert "version" in data
    assert isinstance(data["version"], str)
    # バージョン形式（例: 0.1.0）
    assert len(data["version"]) > 0


@pytest.mark.asyncio
async def test_root_contains_docs_link(client: AsyncClient):
    """レスポンスにドキュメントリンクが含まれることを確認。"""
    response = await client.get("/")
    data = response.json()

    assert "docs" in data
    assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_root_no_auth_required(client: AsyncClient):
    """ルートエンドポイントが認証不要であることを確認。"""
    # 認証なしでアクセス
    response = await client.get("/")

    # 401や403ではなく200が返る
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_root_response_structure(client: AsyncClient):
    """レスポンスが期待される構造を持つことを確認。"""
    response = await client.get("/")
    data = response.json()

    # 必須フィールドが全て含まれている
    required_fields = ["message", "version", "docs"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # 各フィールドが空でない
    for field in required_fields:
        assert data[field], f"Field {field} is empty"
