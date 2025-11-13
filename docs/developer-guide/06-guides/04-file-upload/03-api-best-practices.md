# ステップ4-5: APIとベストプラクティス

このドキュメントでは、APIエンドポイント、スキーマ、チェックリスト、よくある落とし穴、ベストプラクティスについて説明します。

[← 前へ: バリデーションとサービス](./04-file-upload-validation-service.md) | [↑ ファイルアップロード実装](./04-file-upload.md)

## 目次

- [ステップ4: APIエンドポイントの実装](#ステップ4-apiエンドポイントの実装)
- [ステップ5: スキーマの追加](#ステップ5-スキーマの追加)
- [チェックリスト](#チェックリスト)
- [よくある落とし穴](#よくある落とし穴)
- [ベストプラクティス](#ベストプラクティス)

## ステップ4: APIエンドポイントの実装

`src/app/api/routes/files.py`：

```python
"""ファイルアップロード/ダウンロードAPIルート。"""

from io import BytesIO

from fastapi import APIRouter, File, Query, UploadFile
from fastapi.responses import StreamingResponse

from app.api.core import CurrentUserOptionalDep, SampleFileServiceDep
from app.schemas.file import (
    FileDeleteResponse,
    FileInfo,
    FileListResponse,
    FileUploadResponse,
    FileUrlResponse,
)

router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(..., description="アップロードするファイル"),
    file_service: SampleFileServiceDep = None,
    current_user: CurrentUserOptionalDep = None,
) -> FileUploadResponse:
    """
    ファイルをアップロードします。

    - **file**: アップロードするファイル
    - 最大サイズ: 10MB（設定可能）
    - 許可される形式: jpg, png, pdf, txt など
    """
    user_id = current_user.id if current_user else None
    db_file = await file_service.upload_file(file, user_id)

    return FileUploadResponse(
        file_id=db_file.file_id,
        filename=db_file.original_filename,
        size=db_file.size,
        content_type=db_file.content_type,
        message="File uploaded successfully",
    )


@router.post("/upload/chunked", response_model=FileUploadResponse)
async def upload_file_chunked(
    file: UploadFile = File(..., description="大きなファイル"),
    file_service: SampleFileServiceDep = None,
    current_user: CurrentUserOptionalDep = None,
) -> FileUploadResponse:
    """
    チャンク形式でファイルをアップロードします（大きなファイル用）。

    - メモリ効率的なアップロード
    - 大きなファイルに推奨
    """
    user_id = current_user.id if current_user else None
    db_file = await file_service.upload_chunked(file, user_id)

    return FileUploadResponse(
        file_id=db_file.file_id,
        filename=db_file.original_filename,
        size=db_file.size,
        content_type=db_file.content_type,
        message="File uploaded successfully (chunked)",
    )


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    file_service: SampleFileServiceDep = None,
) -> StreamingResponse:
    """
    ファイルをダウンロードします。

    - ストリーミングレスポンスで効率的に配信
    """
    contents, filename, content_type = await file_service.download_file(file_id)

    return StreamingResponse(
        BytesIO(contents),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{file_id}/url", response_model=FileUrlResponse)
async def get_file_url(
    file_id: str,
    expires_in: int = Query(3600, ge=60, le=86400, description="有効期限（秒）"),
    file_service: SampleFileServiceDep = None,
) -> FileUrlResponse:
    """
    ファイルの署名付きURLを取得します。

    - 一時的なアクセスURLを生成
    - Azure Blob使用時に署名付きURLを返す
    """
    url = await file_service.get_file_url(file_id, expires_in)

    return FileUrlResponse(
        file_id=file_id,
        url=url,
        expires_in=expires_in,
    )


@router.delete("/{file_id}", response_model=FileDeleteResponse)
async def delete_file(
    file_id: str,
    file_service: SampleFileServiceDep = None,
) -> FileDeleteResponse:
    """
    ファイルを削除します。
    """
    await file_service.delete_file(file_id)

    return FileDeleteResponse(
        file_id=file_id,
        message=f"File {file_id} deleted successfully",
    )


@router.get("/list", response_model=FileListResponse)
async def list_files(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    file_service: SampleFileServiceDep = None,
    current_user: CurrentUserOptionalDep = None,
) -> FileListResponse:
    """
    アップロードされたファイルのリストを取得します。
    """
    user_id = current_user.id if current_user else None
    files = await file_service.list_files(user_id=user_id, skip=skip, limit=limit)

    file_infos = [
        FileInfo(
            file_id=f.file_id,
            filename=f.original_filename,
            size=f.size,
            content_type=f.content_type,
            created_at=f.created_at,
        )
        for f in files
    ]

    return FileListResponse(files=file_infos, total=len(file_infos))
```

## ステップ5: スキーマの追加

`src/app/schemas/file.py`に追加：

```python
class FileUrlResponse(BaseModel):
    """ファイルURL取得レスポンス。"""

    file_id: str = Field(..., description="ファイルID")
    url: str = Field(..., description="ファイルURL")
    expires_in: int = Field(..., description="有効期限（秒）")
```

## チェックリスト

ファイルアップロード実装のチェックリスト：

- [ ] ストレージバックエンドインターフェースの定義
- [ ] ローカルストレージの実装
- [ ] Azure Blobストレージの実装（必要な場合）
- [ ] ストレージファクトリの実装
- [ ] ファイルバリデーションの実装
- [ ] 許可されるファイルタイプの定義
- [ ] ファイルサイズ制限の実装
- [ ] ファイル名のサニタイゼーション
- [ ] チャンクアップロードの実装（大きなファイル用）
- [ ] ストリーミングダウンロードの実装
- [ ] 署名付きURL生成（Azure用）
- [ ] ファイル削除機能
- [ ] エラーハンドリング
- [ ] セキュリティ対策
- [ ] テストの作成

## よくある落とし穴

### 1. メモリの過剰使用

```python
# 悪い例（大きなファイルでメモリ不足）
contents = await file.read()  # ファイル全体をメモリに読み込む

# 良い例（チャンク単位で処理）
async def upload_chunked(file: UploadFile, chunk_size: int = 1024 * 1024):
    while chunk := await file.read(chunk_size):
        # チャンクを処理
        pass
```

### 2. ファイル名のセキュリティ

```python
# 悪い例（パストラバーサル攻撃の可能性）
filename = file.filename  # "../../../etc/passwd"

# 良い例
filename = sanitize_filename(file.filename)
```

### 3. Content-Typeの検証不足

```python
# 悪い例
# Content-Typeをチェックしない

# 良い例
if file.content_type not in ALLOWED_MIME_TYPES:
    raise ValidationError("Content type not allowed")
```

### 4. ファイルポインタのリセット忘れ

```python
# 悪い例
contents = await file.read()
# ファイルポインタが末尾のまま
validate_file(file)  # 空のファイルとして検証される

# 良い例
contents = await file.read()
await file.seek(0)  # ポインタをリセット
```

### 5. エラー時のクリーンアップ忘れ

```python
# 悪い例
await storage.save(filename, contents)
# エラーが発生してもファイルが残る
await repository.create(...)

# 良い例
try:
    storage_path = await storage.save(filename, contents)
    await repository.create(...)
except Exception:
    await storage.delete(storage_path)  # クリーンアップ
    raise
```

## ベストプラクティス

### 1. ストレージの抽象化

```python
# 抽象インターフェースを使用
storage: StorageBackend = get_storage_backend()

# 環境に応じて実装を切り替え
# 開発: ローカルストレージ
# 本番: Azure Blob
```

### 2. ファイルバリデーション

```python
# 複数のレイヤーでバリデーション
# 1. 拡張子チェック
# 2. MIMEタイプチェック
# 3. ファイルサイズチェック
# 4. ファイル内容チェック（オプション）
```

### 3. セキュアなファイル名

```python
# ユニークIDを使用
file_id = str(uuid.uuid4())
storage_filename = f"{file_id}{file_extension}"

# 元のファイル名は別途保存
original_filename = sanitize_filename(file.filename)
```

### 4. 効率的なストリーミング

```python
# StreamingResponseを使用
return StreamingResponse(
    BytesIO(contents),
    media_type=content_type,
    headers={"Content-Disposition": f'attachment; filename="{filename}"'},
)
```

### 5. 環境変数の活用

```python
# .env
STORAGE_TYPE=local  # または azure
MAX_UPLOAD_SIZE=10485760  # 10MB
AZURE_STORAGE_CONNECTION_STRING=...
```

## 完了

おめでとうございます！ファイルアップロード機能の実装が完了しました。

**[← ファイルアップロード実装に戻る](./04-file-upload.md)**

## 参考リンク

### 公式ドキュメント

- [FastAPI File Uploads](https://fastapi.tiangolo.com/tutorial/request-files/)
- [Azure Blob Storage Python SDK](https://learn.microsoft.com/en-us/azure/storage/blobs/storage-quickstart-blobs-python)
- [aiofiles Documentation](https://github.com/Tinche/aiofiles)

### プロジェクト内リンク

- [ストレージ設定](../03-core-concepts/06-storage.md)
- [セキュリティ](../03-core-concepts/05-security.md)
- [エラーハンドリング](../03-core-concepts/04-error-handling.md)

### 関連ガイド

- [新しいエンドポイント追加](./01-add-endpoint.md)
- [バックグラウンドタスク](./05-background-tasks.md)
