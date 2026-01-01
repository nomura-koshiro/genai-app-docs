# ファイルバージョン管理 統合設計書（FV-001〜FV-004）

## 1. 概要

### 1.1 目的

本ドキュメントは、CAMPシステムにおけるファイルバージョン管理機能の統合設計仕様を定義します。本機能は、プロジェクトファイルのバージョン履歴管理、特定バージョンへの復元、バージョン間の比較を提供します。

### 1.2 対象ユースケース

| カテゴリ | UC ID | 機能名 |
|---------|-------|--------|
| **バージョン管理** | FV-001 | ファイルバージョン履歴表示 |
| | FV-002 | 新規バージョンアップロード |
| | FV-003 | 特定バージョンへの復元 |
| | FV-004 | バージョン間比較 |

### 1.3 追加コンポーネント数

| コンポーネント | 数量 | 備考 |
|--------------|------|------|
| データベーステーブル | 1 | 実装済（project_file_versionの代わりにproject_file.parent_file_idで管理） |
| APIエンドポイント | 5 | 実装済: 5/5 |
| Pydanticスキーマ | 8 | 実装済 |
| フロントエンド画面 | 1 | 未実装 |

---

## 2. データベース設計

### 2.1 テーブル一覧

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

| メソッド | パス | 説明 | 実装状況 |
|---------|------|------|----------|
| GET | /api/v1/project/{project_id}/file/{file_id}/versions | バージョン履歴取得 | ✅ 実装済 |
| POST | /api/v1/project/{project_id}/file/{file_id}/version | 新規バージョンアップロード | ✅ 実装済 |
| GET | /api/v1/project/{project_id}/file/{file_id}/version/{version_id} | 特定バージョンダウンロード | ✅ 実装済 |
| POST | /api/v1/project/{project_id}/file/{file_id}/version/{version_id}/restore | バージョン復元 | ✅ 実装済 |
| GET | /api/v1/project/{project_id}/file/{file_id}/version/compare | バージョン比較 | ✅ 実装済 |

### 3.2 リクエスト/レスポンス定義

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

### 4.1 バージョン情報スキーマ

```python
class FileVersionInfo(BaseCamelCaseModel):
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

class FileVersionListResponse(BaseCamelCaseModel):
    """バージョン履歴レスポンス"""
    file_id: UUID
    file_name: str
    current_version: int
    versions: list[FileVersionInfo] = []
    total_versions: int
```

### 4.2 バージョン操作スキーマ

```python
class FileVersionUploadResponse(BaseCamelCaseModel):
    """バージョンアップロードレスポンス"""
    version_id: UUID
    version_number: int
    file_size: int
    comment: str | None = None
    checksum: str | None = None
    created_at: datetime

class FileVersionRestoreRequest(BaseCamelCaseModel):
    """バージョン復元リクエスト"""
    comment: str | None = None

class FileVersionRestoreResponse(BaseCamelCaseModel):
    """バージョン復元レスポンス"""
    file_id: UUID
    new_version_id: UUID
    new_version_number: int
    restored_from_version: int
    comment: str | None = None
    created_at: datetime
```

### 4.3 バージョン比較スキーマ

```python
class SheetChangeInfo(BaseCamelCaseModel):
    """シート変更情報"""
    sheet_name: str
    rows_added: int = 0
    rows_removed: int = 0
    columns_added: int = 0
    columns_removed: int = 0

class VersionComparisonInfo(BaseCamelCaseModel):
    """バージョン比較情報"""
    size_change: int
    size_change_percent: float
    sheet_changes: list[SheetChangeInfo] = []

class FileVersionCompareResponse(BaseCamelCaseModel):
    """バージョン比較レスポンス"""
    file_id: UUID
    file_name: str
    version1: FileVersionInfo
    version2: FileVersionInfo
    comparison: VersionComparisonInfo
```

---

## 5. サービス層設計

### 5.1 サービスクラス

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

    async def download_version(
        self,
        project_id: UUID,
        file_id: UUID,
        version_id: UUID,
        user_id: UUID
    ) -> StreamingResponse:
        """特定バージョンをダウンロード"""
        # 1. バージョンの存在確認
        version = await self._get_version(version_id)

        # 2. ストレージからファイル取得
        file_stream = await self.storage.download(version.storage_path)

        # 3. ファイル名生成（バージョン番号付き）
        file = await self._get_file(file_id)
        filename = self._generate_versioned_filename(file.name, version.version_number)

        return StreamingResponse(
            file_stream,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )

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

### 6.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| file-versions | バージョン履歴 | /projects/{id}/files/{fileId}/versions | バージョン一覧・操作 |

### 6.2 コンポーネント構成

```text
features/file-version/
├── components/
│   ├── VersionList/
│   │   ├── VersionList.tsx
│   │   ├── VersionItem.tsx
│   │   └── VersionTimeline.tsx
│   ├── VersionUpload/
│   │   ├── VersionUploadModal.tsx
│   │   └── VersionCommentInput.tsx
│   ├── VersionCompare/
│   │   ├── VersionCompareModal.tsx
│   │   ├── VersionSelector.tsx
│   │   └── ComparisonResult.tsx
│   └── VersionActions/
│       ├── DownloadButton.tsx
│       └── RestoreButton.tsx
├── hooks/
│   ├── useFileVersions.ts
│   └── useVersionCompare.ts
├── api/
│   └── fileVersionApi.ts
└── types/
    └── fileVersion.ts
```

### 6.3 UI設計

#### バージョン履歴画面

```text
┌────────────────────────────────────────────────────────┐
│  sales_data.xlsx のバージョン履歴                       │
│  現在: v3                                    [新規 ▲]  │
├────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────┐   │
│  │ ● v3 (現在)                     2026/01/01    │   │
│  │   Q4データ追加                                  │   │
│  │   山田 太郎 • 1.0 MB                           │   │
│  │   [ダウンロード]                               │   │
│  └────────────────────────────────────────────────┘   │
│        │                                               │
│  ┌────────────────────────────────────────────────┐   │
│  │ ○ v2                           2025/12/15     │   │
│  │   Q3データ修正                                  │   │
│  │   鈴木 花子 • 512 KB                           │   │
│  │   [ダウンロード] [復元] [比較]                   │   │
│  └────────────────────────────────────────────────┘   │
│        │                                               │
│  ┌────────────────────────────────────────────────┐   │
│  │ ○ v1                           2025/12/01     │   │
│  │   初回アップロード                              │   │
│  │   山田 太郎 • 256 KB                           │   │
│  │   [ダウンロード] [復元] [比較]                   │   │
│  └────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

#### バージョン比較モーダル

```text
┌────────────────────────────────────────────────────────┐
│  バージョン比較                              [×]       │
├────────────────────────────────────────────────────────┤
│  比較元: [v2 ▼]  →  比較先: [v3 ▼]                    │
├────────────────────────────────────────────────────────┤
│  ファイルサイズ: 512 KB → 1.0 MB (+100%)              │
├────────────────────────────────────────────────────────┤
│  シート別変更:                                         │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Sheet1                                           │ │
│  │   行: +150行 / -0行                              │ │
│  │   列: +2列 / -0列                                │ │
│  └──────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐ │
│  │ Sheet2                                           │ │
│  │   行: +50行 / -10行                              │ │
│  │   列: 変更なし                                   │ │
│  └──────────────────────────────────────────────────┘ │
├────────────────────────────────────────────────────────┤
│                                         [閉じる]       │
└────────────────────────────────────────────────────────┘
```

---

## 7. 画面項目・APIマッピング

### 7.1 バージョン履歴画面

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ファイル名 | テキスト | GET /file/{id}/version | fileName | - |
| 現在バージョン | テキスト | GET /file/{id}/version | currentVersion | "v" + n |
| バージョン番号 | テキスト | GET /file/{id}/version | versions[].versionNumber | "v" + n |
| 現在フラグ | バッジ | GET /file/{id}/version | versions[].isCurrent | "現在" バッジ |
| 日時 | 日時 | GET /file/{id}/version | versions[].createdAt | YYYY/MM/DD形式 |
| コメント | テキスト | GET /file/{id}/version | versions[].comment | - |
| アップロード者 | テキスト | GET /file/{id}/version | versions[].uploadedByName | - |
| ファイルサイズ | テキスト | GET /file/{id}/version | versions[].fileSize | KB/MB変換 |
| ダウンロードボタン | ボタン | GET /file/{id}/version/{versionId} | - | ファイルDL |
| 復元ボタン | ボタン | POST /version/{id}/restore | - | 確認ダイアログ |
| 比較ボタン | ボタン | - | - | 比較モーダル表示 |

### 7.2 新規バージョンアップロード

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|------|------------------|---------------------|---------------|
| ファイル | ファイル選択 | ○ | POST /file/{id}/version | file | 同名・同形式のみ |
| コメント | テキスト | - | POST /file/{id}/version | comment | 最大500文字 |
| アップロードボタン | ボタン | - | POST /file/{id}/version | - | - |

### 7.3 バージョン比較

| 画面項目 | 入力/表示形式 | APIエンドポイント | パラメータ/フィールド | 変換処理 |
|---------|-------------|------------------|---------------------|---------|
| 比較元バージョン | セレクト | GET /file/{id}/version/compare | version1 | - |
| 比較先バージョン | セレクト | GET /file/{id}/version/compare | version2 | - |
| サイズ変更 | テキスト | GET /compare | comparison.sizeChange | +n KB / -n KB |
| サイズ変更率 | テキスト | GET /compare | comparison.sizeChangePercent | +n% / -n% |
| シート変更一覧 | リスト | GET /compare | comparison.sheetChanges[] | - |
| 行追加数 | テキスト | GET /compare | sheetChanges[].rowsAdded | +n行 |
| 行削除数 | テキスト | GET /compare | sheetChanges[].rowsRemoved | -n行 |

---

## 8. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面 | ステータス |
|-------|--------|-----|------|-----------|
| FV-001 | ファイルバージョン履歴表示 | GET /file/{id}/versions | file-versions | ✅ 実装済 |
| FV-002 | 新規バージョンアップロード | POST /file/{id}/version | file-versions | ✅ 実装済 |
| FV-003 | 特定バージョンへの復元 | POST /version/{id}/restore | file-versions | ✅ 実装済 |
| FV-004 | バージョン間比較 | GET /file/{id}/version/compare | file-versions | ✅ 実装済 |

カバレッジ: 4/4 = 100%（バックエンドAPI実装済、フロントエンド未実装）

---

## 9. 備考

### 9.1 ストレージ管理

- バージョンファイルは `{storage_root}/versions/{file_id}/{version_number}/` に保存
- 古いバージョンの自動削除ポリシー（例: 10バージョン以上、または1年以上前）
- ストレージ容量の監視とアラート

### 9.2 パフォーマンス考慮

- 大容量ファイルはチャンクアップロード対応
- バージョン比較は非同期処理（Celery等）で実行
- 比較結果のキャッシュ

### 9.3 将来拡張

- 差分バックアップによるストレージ最適化
- バージョン間の差分ダウンロード
- バージョンタグ/ラベル機能
- バージョン承認ワークフロー

---

### ドキュメント管理情報

- **作成日**: 2026年1月1日
- **更新日**: 2026年1月1日
- **バージョン**: 1.0
