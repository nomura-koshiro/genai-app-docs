# ファイル管理・バージョン管理 バックエンド設計書（FM-001〜FM-004, FV-001〜FV-004）

## 1. 概要

### 1.1 目的

本設計書は、CAMPシステムにおけるファイル管理・バージョン管理機能の統合設計仕様を定義します。本機能は、プロジェクトファイルの一覧表示、アップロード、バージョン履歴管理、特定バージョンへの復元、バージョン間の比較を提供します。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能概要 |
|---------|-------|--------|
| **ファイル管理** | FM-001 | ファイル一覧表示 |
| | FM-002 | ファイル検索・フィルタ |
| | FM-003 | 新規ファイルアップロード |
| | FM-004 | ファイルダウンロード |
| **バージョン管理** | FV-001 | ファイルバージョン履歴表示 |
| | FV-002 | 新規バージョンアップロード |
| | FV-003 | 特定バージョンへの復元 |
| | FV-004 | バージョン間比較 |

### 1.3 コンポーネント数

| レイヤー | 項目数 |
|---------|--------|
| データベーステーブル | 1 |
| APIエンドポイント | 8 |
| Pydanticスキーマ | 11 |
| フロントエンド画面 | 3 |

---

## 2. データベース設計

### 2.1 関連テーブル一覧

| テーブル名 | 説明 |
|-----------|------|
| project_file_version | ファイルバージョン履歴 |

### 2.2 ER図

```text
project_file ──1:N── project_file_version
                           │
                           └── storage_path (ストレージパス)
```

### 2.3 テーブル詳細

#### project_file_version（ファイルバージョン履歴）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| id | UUID | NO | uuid4() | 主キー |
| file_id | UUID | NO | - | ファイルID（FK） |
| version_number | INTEGER | NO | - | バージョン番号 |
| storage_path | VARCHAR(500) | NO | - | ストレージパス |
| file_size | BIGINT | NO | - | ファイルサイズ（バイト） |
| checksum | VARCHAR(64) | YES | NULL | チェックサム（SHA-256） |
| comment | TEXT | YES | NULL | バージョンコメント |
| is_current | BOOLEAN | NO | false | 現在バージョンフラグ |
| uploaded_by | UUID | YES | NULL | アップロード者ID（FK） |
| created_at | TIMESTAMP | NO | now() | 作成日時 |

**インデックス:**

- idx_project_file_version_file_id (file_id)
- idx_project_file_version_current (file_id, is_current)
- idx_project_file_version_number (file_id, version_number) UNIQUE

**制約:**

- uq_file_version: UNIQUE (file_id, version_number)
- ck_version_number: version_number > 0

### 2.4 既存テーブルの拡張

#### project_file（拡張）

| カラム名 | 型 | NULL | デフォルト | 説明 |
|---------|-----|------|-----------|------|
| current_version_id | UUID | YES | NULL | 現在バージョンID（FK） |
| version_count | INTEGER | NO | 1 | バージョン数 |

---

## 3. APIエンドポイント設計

### 3.1 エンドポイント一覧

| メソッド | パス | 説明 |
|---------|------|------|
| GET | /api/v1/project/{project_id}/files | ファイル一覧取得 |
| POST | /api/v1/project/{project_id}/files | 新規ファイルアップロード |
| GET | /api/v1/project/{project_id}/file/{file_id}/download | ファイルダウンロード（現在バージョン） |
| GET | /api/v1/project/{project_id}/file/{file_id}/versions | バージョン履歴取得 |
| POST | /api/v1/project/{project_id}/file/{file_id}/version | 新規バージョンアップロード |
| GET | /api/v1/project/{project_id}/file/{file_id}/version/{version_id} | 特定バージョンダウンロード |
| POST | /api/v1/project/{project_id}/file/{file_id}/version/{version_id}/restore | バージョン復元 |
| GET | /api/v1/project/{project_id}/file/{file_id}/version/compare | バージョン比較 |

### 3.2 リクエスト/レスポンス定義

#### GET /api/v1/project/{project_id}/files（ファイル一覧取得）

**クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| search | string | - | ファイル名検索（部分一致） |
| fileType | string | - | ファイルタイプフィルタ（excel, pdf, image, other） |
| page | int | - | ページ番号（デフォルト: 1） |
| limit | int | - | 1ページあたりの件数（デフォルト: 20） |

**レスポンス (200):**

```json
{
  "files": [
    {
      "fileId": "uuid",
      "name": "sales_data.xlsx",
      "fileType": "excel",
      "fileSize": 1048576,
      "currentVersion": 3,
      "versionCount": 3,
      "updatedBy": "uuid",
      "updatedByName": "山田 太郎",
      "updatedAt": "2026-01-01T10:00:00Z",
      "createdAt": "2025-12-01T00:00:00Z"
    },
    {
      "fileId": "uuid",
      "name": "proposal.pdf",
      "fileType": "pdf",
      "fileSize": 2621440,
      "currentVersion": 1,
      "versionCount": 1,
      "updatedBy": "uuid",
      "updatedByName": "鈴木 花子",
      "updatedAt": "2025-12-28T15:30:00Z",
      "createdAt": "2025-12-28T15:30:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "limit": 20,
  "totalPages": 1
}
```

#### POST /api/v1/project/{project_id}/files（新規ファイルアップロード）

**リクエスト:**

- Content-Type: multipart/form-data
- file: File（必須）
- comment: string（任意）

**レスポンス (201):**

```json
{
  "fileId": "uuid",
  "name": "sales_report_2026.xlsx",
  "fileType": "excel",
  "fileSize": 1258291,
  "currentVersion": 1,
  "versionCount": 1,
  "comment": "2026年売上レポート",
  "uploadedBy": "uuid",
  "uploadedByName": "山田 太郎",
  "createdAt": "2026-01-01T00:00:00Z"
}
```

#### GET /api/v1/project/{project_id}/file/{file_id}/download（現在バージョンダウンロード）

**レスポンス:**

- Content-Type: application/octet-stream
- Content-Disposition: attachment; filename="sales_data.xlsx"

#### GET /project/{project_id}/file/{file_id}/version（バージョン履歴取得）

**レスポンス (200):**

```json
{
  "fileId": "uuid",
  "fileName": "sales_data.xlsx",
  "currentVersion": 3,
  "versions": [
    {
      "versionId": "uuid",
      "versionNumber": 3,
      "fileSize": 1048576,
      "comment": "Q4データ追加",
      "isCurrent": true,
      "uploadedBy": "uuid",
      "uploadedByName": "山田 太郎",
      "createdAt": "2026-01-01T00:00:00Z"
    },
    {
      "versionId": "uuid",
      "versionNumber": 2,
      "fileSize": 524288,
      "comment": "Q3データ修正",
      "isCurrent": false,
      "uploadedBy": "uuid",
      "uploadedByName": "鈴木 花子",
      "createdAt": "2025-12-15T00:00:00Z"
    },
    {
      "versionId": "uuid",
      "versionNumber": 1,
      "fileSize": 262144,
      "comment": "初回アップロード",
      "isCurrent": false,
      "uploadedBy": "uuid",
      "uploadedByName": "山田 太郎",
      "createdAt": "2025-12-01T00:00:00Z"
    }
  ],
  "totalVersions": 3
}
```

#### POST /project/{project_id}/file/{file_id}/version（新規バージョンアップロード）

**リクエスト:**

- Content-Type: multipart/form-data
- file: File（必須）
- comment: string（任意）

**レスポンス (201):**

```json
{
  "versionId": "uuid",
  "versionNumber": 4,
  "fileSize": 2097152,
  "comment": "2026年1月データ追加",
  "checksum": "sha256:abc123...",
  "createdAt": "2026-01-01T00:00:00Z"
}
```

#### GET /project/{project_id}/file/{file_id}/version/{version_id}（特定バージョンダウンロード）

**レスポンス:**

- Content-Type: application/octet-stream
- Content-Disposition: attachment; filename="sales_data_v2.xlsx"

#### POST /project/{project_id}/file/{file_id}/version/{version_id}/restore（バージョン復元）

**リクエスト:**

```json
{
  "comment": "v2に復元"
}
```

**レスポンス (200):**

```json
{
  "fileId": "uuid",
  "newVersionId": "uuid",
  "newVersionNumber": 5,
  "restoredFromVersion": 2,
  "comment": "v2に復元",
  "createdAt": "2026-01-01T00:00:00Z"
}
```

#### GET /project/{project_id}/file/{file_id}/version/compare（バージョン比較）

**クエリパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| version1 | int | ○ | 比較元バージョン番号 |
| version2 | int | ○ | 比較先バージョン番号 |

**レスポンス (200):**

```json
{
  "fileId": "uuid",
  "fileName": "sales_data.xlsx",
  "version1": {
    "versionNumber": 2,
    "fileSize": 524288,
    "createdAt": "2025-12-15T00:00:00Z"
  },
  "version2": {
    "versionNumber": 3,
    "fileSize": 1048576,
    "createdAt": "2026-01-01T00:00:00Z"
  },
  "comparison": {
    "sizeChange": 524288,
    "sizeChangePercent": 100.0,
    "sheetChanges": [
      {
        "sheetName": "Sheet1",
        "rowsAdded": 150,
        "rowsRemoved": 0,
        "columnsAdded": 2,
        "columnsRemoved": 0
      }
    ]
  }
}
```

---

## 4. Pydanticスキーマ設計

### 4.1 Enum定義

```python
from enum import Enum

class FileType(str, Enum):
    """ファイルタイプ"""
    EXCEL = "excel"
    PDF = "pdf"
    IMAGE = "image"
    WORD = "word"
    OTHER = "other"
```

### 4.2 Info/Dataスキーマ

```python
class FileInfo(CamelCaseModel):
    """ファイル情報"""
    file_id: UUID
    name: str
    file_type: FileType
    file_size: int
    current_version: int
    version_count: int
    updated_by: UUID | None = None
    updated_by_name: str | None = None
    updated_at: datetime
    created_at: datetime

class FileVersionInfo(CamelCaseModel):
    """ファイルバージョン情報"""
    version_id: UUID
    version_number: int
    file_size: int
    comment: str | None = None
    checksum: str | None = None
    is_current: bool = False
    uploaded_by: UUID | None = None
    uploaded_by_name: str | None = None
    created_at: datetime

class SheetChangeInfo(CamelCaseModel):
    """シート変更情報"""
    sheet_name: str
    rows_added: int = 0
    rows_removed: int = 0
    columns_added: int = 0
    columns_removed: int = 0

class VersionComparisonInfo(CamelCaseModel):
    """バージョン比較情報"""
    size_change: int
    size_change_percent: float
    sheet_changes: list[SheetChangeInfo] = []
```

### 4.3 Request/Responseスキーマ

```python
# Request スキーマ
class FileVersionRestoreRequest(CamelCaseModel):
    """バージョン復元リクエスト"""
    comment: str | None = None

# Response スキーマ
class FileListResponse(CamelCaseModel):
    """ファイル一覧レスポンス"""
    files: list[FileInfo] = []
    total: int
    page: int = 1
    limit: int = 20
    total_pages: int

class FileUploadResponse(CamelCaseModel):
    """ファイルアップロードレスポンス"""
    file_id: UUID
    name: str
    file_type: FileType
    file_size: int
    current_version: int
    version_count: int
    comment: str | None = None
    uploaded_by: UUID
    uploaded_by_name: str
    created_at: datetime

class FileVersionListResponse(CamelCaseModel):
    """バージョン履歴レスポンス"""
    file_id: UUID
    file_name: str
    current_version: int
    versions: list[FileVersionInfo] = []
    total_versions: int

class FileVersionUploadResponse(CamelCaseModel):
    """バージョンアップロードレスポンス"""
    version_id: UUID
    version_number: int
    file_size: int
    comment: str | None = None
    checksum: str | None = None
    created_at: datetime

class FileVersionRestoreResponse(CamelCaseModel):
    """バージョン復元レスポンス"""
    file_id: UUID
    new_version_id: UUID
    new_version_number: int
    restored_from_version: int
    comment: str | None = None
    created_at: datetime

class FileVersionCompareResponse(CamelCaseModel):
    """バージョン比較レスポンス"""
    file_id: UUID
    file_name: str
    version1: FileVersionInfo
    version2: FileVersionInfo
    comparison: VersionComparisonInfo
```

---

## 5. サービス層設計

### 5.1 サービスクラス構成

| サービス | 責務 |
|---------|------|
| FileManagementService | ファイル管理（一覧・アップロード・ダウンロード） |
| FileVersionService | バージョン管理（履歴・アップロード・復元・比較） |

### 5.2 主要メソッド

#### FileManagementService

```python
class FileManagementService:
    """ファイル管理サービス（一覧・アップロード）"""

    def __init__(self, db: AsyncSession, storage: StorageService):
        self.db = db
        self.storage = storage

    async def list_files(
        self,
        project_id: UUID,
        user_id: UUID,
        search: str | None = None,
        file_type: str | None = None,
        page: int = 1,
        limit: int = 20
    ) -> FileListResponse:
        """プロジェクト内のファイル一覧を取得"""
        # 1. プロジェクトの存在確認と権限チェック
        await self._check_project_access(project_id, user_id)

        # 2. クエリ構築
        query = select(ProjectFile).where(ProjectFile.project_id == project_id)

        if search:
            query = query.where(ProjectFile.name.ilike(f"%{search}%"))

        if file_type:
            query = query.where(ProjectFile.file_type == file_type)

        # 3. ページネーション
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))

        query = query.offset((page - 1) * limit).limit(limit)
        query = query.order_by(ProjectFile.updated_at.desc())

        # 4. ファイル取得
        result = await self.db.execute(query)
        files = result.scalars().all()

        return FileListResponse(
            files=[FileInfo.from_orm(f) for f in files],
            total=total,
            page=page,
            limit=limit,
            total_pages=math.ceil(total / limit)
        )

    async def upload_file(
        self,
        project_id: UUID,
        file: UploadFile,
        comment: str | None,
        user_id: UUID
    ) -> FileUploadResponse:
        """新規ファイルをアップロード"""
        # 1. プロジェクト権限チェック
        await self._check_project_access(project_id, user_id)

        # 2. ファイルバリデーション
        await self._validate_file(file)

        # 3. ストレージに保存
        storage_path = await self.storage.upload(
            file,
            f"projects/{project_id}/files"
        )

        # 4. チェックサム計算
        checksum = await self._calculate_checksum(file)

        # 5. ファイルレコード作成
        new_file = ProjectFile(
            project_id=project_id,
            name=file.filename,
            file_type=self._detect_file_type(file.filename),
            file_size=file.size,
            storage_path=storage_path,
            checksum=checksum,
            current_version=1,
            version_count=1,
            uploaded_by=user_id
        )

        self.db.add(new_file)
        await self.db.commit()
        await self.db.refresh(new_file)

        # 6. 初回バージョン作成
        await self._create_initial_version(new_file, comment, user_id)

        return FileUploadResponse.from_orm(new_file)

    async def download_file(
        self,
        project_id: UUID,
        file_id: UUID,
        user_id: UUID
    ) -> StreamingResponse:
        """現在バージョンのファイルをダウンロード"""
        # 1. ファイル取得
        file = await self._get_file(file_id)

        # 2. 権限チェック
        await self._check_project_access(project_id, user_id)

        # 3. ストレージからファイル取得
        file_stream = await self.storage.download(file.storage_path)

        return StreamingResponse(
            file_stream,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{file.name}"'}
        )
```

#### FileVersionService

```python
class FileVersionService:
    """ファイルバージョン管理サービス"""

    def __init__(self, db: AsyncSession, storage: StorageService):
        self.db = db
        self.storage = storage

    async def list_versions(
        self,
        project_id: UUID,
        file_id: UUID,
        user_id: UUID
    ) -> FileVersionListResponse:
        """バージョン履歴を取得"""
        # 1. ファイルの存在確認と権限チェック
        file = await self._get_file(file_id)

        # 2. バージョン一覧の取得
        versions = await self._get_versions(file_id)

        return FileVersionListResponse(
            file_id=file_id,
            file_name=file.name,
            current_version=file.version_count,
            versions=versions,
            total_versions=len(versions)
        )

    async def upload_version(
        self,
        project_id: UUID,
        file_id: UUID,
        file: UploadFile,
        comment: str | None,
        user_id: UUID
    ) -> FileVersionUploadResponse:
        """新規バージョンをアップロード"""
        # 1. ファイルの存在確認
        existing_file = await self._get_file(file_id)

        # 2. ファイルをストレージに保存
        storage_path = await self.storage.upload(file, f"versions/{file_id}")

        # 3. チェックサム計算
        checksum = await self._calculate_checksum(file)

        # 4. バージョンレコード作成
        new_version_number = existing_file.version_count + 1
        version = await self._create_version(
            file_id=file_id,
            version_number=new_version_number,
            storage_path=storage_path,
            file_size=file.size,
            checksum=checksum,
            comment=comment,
            uploaded_by=user_id
        )

        # 5. 現在バージョンフラグ更新
        await self._set_current_version(file_id, version.id)

        return FileVersionUploadResponse(...)

    async def restore_version(
        self,
        project_id: UUID,
        file_id: UUID,
        version_id: UUID,
        comment: str | None,
        user_id: UUID
    ) -> FileVersionRestoreResponse:
        """特定バージョンに復元"""
        # 1. 復元元バージョンの取得
        source_version = await self._get_version(version_id)

        # 2. ストレージからファイルコピー
        new_storage_path = await self.storage.copy(
            source_version.storage_path,
            f"versions/{file_id}"
        )

        # 3. 新規バージョンとして登録
        file = await self._get_file(file_id)
        new_version_number = file.version_count + 1

        restore_comment = comment or f"v{source_version.version_number}から復元"
        new_version = await self._create_version(
            file_id=file_id,
            version_number=new_version_number,
            storage_path=new_storage_path,
            file_size=source_version.file_size,
            checksum=source_version.checksum,
            comment=restore_comment,
            uploaded_by=user_id
        )

        # 4. 現在バージョン更新
        await self._set_current_version(file_id, new_version.id)

        return FileVersionRestoreResponse(...)

    async def compare_versions(
        self,
        project_id: UUID,
        file_id: UUID,
        version1: int,
        version2: int,
        user_id: UUID
    ) -> FileVersionCompareResponse:
        """バージョン間を比較"""
        # 1. 両バージョンの取得
        v1 = await self._get_version_by_number(file_id, version1)
        v2 = await self._get_version_by_number(file_id, version2)

        # 2. ファイル内容の取得
        content1 = await self.storage.download(v1.storage_path)
        content2 = await self.storage.download(v2.storage_path)

        # 3. 比較実行（Excel/CSVの場合はシート・行・列の比較）
        comparison = await self._compare_files(content1, content2)

        return FileVersionCompareResponse(
            file_id=file_id,
            file_name=file.name,
            version1=v1,
            version2=v2,
            comparison=comparison
        )
```

---

## 6. フロントエンド設計

フロントエンド設計の詳細は、別ドキュメントを参照してください。

- **フロントエンド設計書**: [02-file-version-frontend-design.md](02-file-version-frontend-design.md)

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 |
|-------|--------|-----|------|
| FM-001 | ファイル一覧表示 | GET /project/{id}/files | files |
| FM-002 | ファイル検索・フィルタ | GET /project/{id}/files?search= | files |
| FM-003 | 新規ファイルアップロード | POST /project/{id}/files | upload |
| FM-004 | ファイルダウンロード | GET /file/{id}/download | files |
| FV-001 | ファイルバージョン履歴表示 | GET /file/{id}/versions | file-versions |
| FV-002 | 新規バージョンアップロード | POST /file/{id}/version | file-versions |
| FV-003 | 特定バージョンへの復元 | POST /version/{id}/restore | file-versions |
| FV-004 | バージョン間比較 | GET /file/{id}/version/compare | file-versions |

カバレッジ: 8/8 = 100%

---

## 8. 関連ドキュメント

- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **プロジェクト管理設計書**: [../04-project-management/01-project-management-design.md](../04-project-management/01-project-management-design.md)
- **API共通仕様**: [../02-api-overview/01-api-overview.md](../02-api-overview/01-api-overview.md)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | FV-DESIGN-001 |
| 対象ユースケース | FM-001〜FM-004, FV-001〜FV-004 |
| 最終更新日 | 2026-01-01 |
| 対象ソースコード | `src/app/models/project/project_file.py` |
|  | `src/app/schemas/project/file.py` |
|  | `src/app/api/routes/v1/project/file.py` |
