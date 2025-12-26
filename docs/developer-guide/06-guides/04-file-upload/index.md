# ファイルアップロード実装

このガイドでは、ローカルストレージとAzure Blobストレージを使用したファイルアップロード機能の実装方法を説明します。

## 目次

- [概要](#概要)
- [ファイルアップロードフロー](#ファイルアップロードフロー)
- [前提条件](#前提条件)
- [実装ステップ](#実装ステップ)
- [参考リンク](#参考リンク)

## 概要

ファイルアップロード機能の主要コンポーネント：

```text
ファイルアップロード機能
├── ストレージバックエンド（storage/）
│   ├── base.py - 抽象インターフェース
│   ├── local.py - ローカルストレージ実装
│   └── azure_blob.py - Azure Blob実装
├── ファイルモデル（models/sample_file.py）
├── ファイルリポジトリ（repositories/sample_file.py）
├── ファイルサービス（services/sample_file.py）
└── ファイルAPI（api/routes/v1/sample_files.py）
```

## ファイルアップロードフロー

以下の図は、ファイルアップロードの全体的な処理フローを示しています。

::: mermaid
sequenceDiagram
    participant C as クライアント
    participant API as FastAPI<br/>Router
    participant FS as FileService
    participant V as Validator
    participant S as Storage<br/>(Local/Azure)
    participant FR as FileRepository
    participant DB as PostgreSQL

    Note over C,DB: ファイルアップロードフロー

    C->>+API: POST /api/sample-files/upload<br/>multipart/form-data
    API->>+FS: upload_file(file, user_id)

    FS->>+V: validate_file(file)

    alt ファイル検証
        V->>V: ファイル名チェック
        V->>V: 拡張子チェック<br/>(.jpg, .png, .pdf等)
        V->>V: MIMEタイプチェック
        V->>V: ファイルサイズチェック<br/>(MAX_UPLOAD_SIZE)
        V-->>-FS: 検証成功
    else 検証失敗
        V-->>FS: ValidationError
        FS-->>API: ValidationError
        API-->>C: 422 Unprocessable Entity
    end

    FS->>FS: ファイル内容読込<br/>await file.read()
    FS->>FS: UUID生成<br/>file_id = uuid4()
    FS->>FS: ファイル名サニタイズ<br/>sanitize_filename()
    FS->>FS: ストレージ用ファイル名生成<br/>{file_id}.{ext}

    FS->>+S: save(filename, contents)

    alt ストレージタイプ
        S->>S: ローカル: uploads/ に保存
        S->>S: Azure: Blob Storage に保存
    end

    S-->>-FS: storage_path

    FS->>+FR: create(file_id, filename,<br/>size, content_type, storage_path)
    FR->>+DB: INSERT INTO files<br/>VALUES (...)
    DB-->>-FR: File record
    FR-->>-FS: File object

    FS-->>-API: File object
    API-->>-C: 200 OK<br/>{file_id, filename,<br/>size, content_type}

    Note over C,DB: ファイルダウンロードフロー

    C->>+API: GET /api/sample-files/download/{file_id}
    API->>+FS: download_file(file_id)
    FS->>+FR: get(file_id)
    FR->>+DB: SELECT * FROM files<br/>WHERE file_id = ?
    DB-->>-FR: File record
    FR-->>-FS: File object

    FS->>+S: load(storage_path)

    alt ストレージタイプ
        S->>S: ローカル: ファイル読込
        S->>S: Azure: Blob ダウンロード
    end

    S-->>-FS: contents (bytes)

    FS-->>-API: (contents, filename,<br/>content_type)
    API-->>-C: StreamingResponse<br/>Content-Disposition: attachment

    style C fill:#81d4fa,stroke:#01579b,stroke-width:3px,color:#000,stroke-width:3px
    style API fill:#ffb74d,stroke:#e65100,stroke-width:3px,color:#000,stroke-width:3px
    style FS fill:#ce93d8,stroke:#4a148c,stroke-width:3px,color:#000,stroke-width:3px
    style V fill:#f06292,stroke:#880e4f,stroke-width:3px,color:#000,stroke-width:3px
    style S fill:#fff176,stroke:#f57f17,stroke-width:3px,color:#000,stroke-width:3px
    style FR fill:#81c784,stroke:#1b5e20,stroke-width:3px,color:#000,stroke-width:3px
    style DB fill:#64b5f6,stroke:#01579b,stroke-width:3px,color:#000,stroke-width:3px
:::

### 処理フローの詳細

#### 1. ファイルアップロード

1. **クライアント** → **API**: `multipart/form-data` 形式でファイル送信
2. **API** → **FileService**: アップロード処理を依頼
3. **FileService** → **Validator**: ファイル検証
   - ファイル名の存在確認
   - 拡張子チェック（許可リスト）
   - MIMEタイプチェック
   - ファイルサイズチェック（10MB制限等）
4. **検証成功時**:
   - ファイル内容を読み込み
   - UUID でユニークなファイルIDを生成
   - ファイル名をサニタイズ
   - ストレージ用のファイル名を生成（`{uuid}.{ext}`）
5. **FileService** → **Storage**: ファイル保存
   - 開発環境: `uploads/` ディレクトリに保存
   - 本番環境: Azure Blob Storage に保存
6. **FileService** → **FileRepository** → **PostgreSQL**: メタデータを保存
   - file_id, filename, size, content_type, storage_path, user_id
7. **API** → **クライアント**: アップロード成功レスポンス

#### 2. ファイルダウンロード

1. **クライアント** → **API**: ファイルIDを指定してダウンロード
2. **API** → **FileService**: ダウンロード処理を依頼
3. **FileService** → **FileRepository** → **PostgreSQL**: メタデータ取得
4. **FileService** → **Storage**: ファイル内容を読み込み
5. **API** → **クライアント**: `StreamingResponse` で効率的に配信

### セキュリティとベストプラクティス

- **ファイル名のサニタイズ**: パストラバーサル攻撃を防止
- **UUID使用**: ファイル名の衝突を回避
- **拡張子とMIMEタイプの二重チェック**: 不正ファイルの検出
- **ファイルサイズ制限**: DoS攻撃の防止
- **ストレージの抽象化**: 環境に応じてLocal/Azureを切り替え
- **StreamingResponse**: メモリ効率的なダウンロード

## 前提条件

- FastAPIの基礎知識
- ストレージシステムの理解
- 非同期I/Oの理解
- ファイル処理のセキュリティ知識

## 実装ステップ

ファイルアップロード機能の実装は以下の手順で行います：

### ステップ1: ストレージバックエンドの実装

ストレージの抽象化とローカル/Azureストレージの実装について詳しく知りたい場合は、以下のドキュメントを参照してください：

**[→ ステップ1: ストレージバックエンド](./04-file-upload-storage.md)**

- 1.1 抽象インターフェースの定義
- 1.2 ローカルストレージの実装
- 1.3 Azure Blobストレージの実装
- 1.4 ストレージバックエンドのファクトリ

### ステップ2-3: バリデーションとサービス

ファイル検証とファイルサービスの実装について詳しく知りたい場合は、以下のドキュメントを参照してください：

**[→ ステップ2-3: バリデーションとサービス](./04-file-upload-validation-service.md)**

- ステップ2: ファイルバリデーション（ファイル検証ユーティリティ、サニタイゼーション）
- ステップ3: ファイルサービスの拡張（upload_file、upload_chunked、get_file_url）

### ステップ4-5: APIとベストプラクティス

APIエンドポイント、スキーマ、ベストプラクティスについて詳しく知りたい場合は、以下のドキュメントを参照してください：

**[→ ステップ4-5: APIとベストプラクティス](./04-file-upload-api-best-practices.md)**

- ステップ4: APIエンドポイントの実装
- ステップ5: スキーマの追加
- チェックリスト
- よくある落とし穴
- ベストプラクティス

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
