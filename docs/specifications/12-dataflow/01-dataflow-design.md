# データフロー設計書

## 1. 概要

本文書は、genai-app-docsシステムの主要なデータフローを定義します。
HTTPリクエストからレスポンスまでの処理の流れを詳細に記載します。

### 1.1 データフロー設計方針

- **明確な処理フロー**: 各処理ステップを明示
- **エラーハンドリング**: 異常系の処理フローも記載
- **非同期処理**: async/awaitによる並行処理
- **トランザクション管理**: データ整合性の保証

---

## 2. 標準的なリクエストフロー

### 2.1 GET リクエストフロー（読み取り）

::: mermaid
sequenceDiagram
    autonumber
    participant Client
    participant MW as Middleware Stack
    participant Auth as Authentication
    participant RBAC as RBAC Check
    participant Service
    participant Repo as Repository
    participant Cache
    participant DB as PostgreSQL

    Client->>MW: GET /api/v1/projects<br/>Authorization: Bearer <token>

    Note over MW: 1. CORS<br/>2. Rate Limit<br/>3. Logging<br/>4. Metrics<br/>5. Security Headers

    MW->>Auth: トークン検証

    Auth->>Auth: JWT検証<br/>(Azure AD or Mock)

    Auth->>DB: UserAccount取得<br/>SELECT * FROM users

    DB-->>Auth: UserAccount

    Auth-->>MW: current_user

    MW->>RBAC: 権限チェック

    RBAC->>DB: ProjectMember取得<br/>SELECT * FROM project_members

    DB-->>RBAC: ProjectMember list

    RBAC-->>MW: OK（権限あり）

    MW->>Service: get_projects(current_user)

    Service->>Cache: キャッシュチェック

    alt キャッシュヒット
        Cache-->>Service: キャッシュデータ
    else キャッシュミス
        Service->>Repo: get_multi(filters)

        Repo->>DB: SELECT * FROM projects<br/>WHERE user_id IN (...)

        DB-->>Repo: Project list

        Repo-->>Service: Project objects

        Service->>Cache: キャッシュ保存
    end

    Service-->>MW: ProjectResponse list

    MW-->>Client: 200 OK<br/>{"items": [...], "total": 10}
:::

### 2.2 POST リクエストフロー（作成）

::: mermaid
sequenceDiagram
    autonumber
    participant Client
    participant MW as Middleware Stack
    participant Auth as Authentication
    participant Valid as Pydantic Validation
    participant Service
    participant Repo as Repository
    participant DB as PostgreSQL

    Client->>MW: POST /api/v1/projects<br/>{"name": "New Project", "code": "NEW"}

    MW->>Auth: トークン検証
    Auth-->>MW: current_user

    MW->>Valid: リクエストバリデーション

    Valid->>Valid: 型チェック<br/>形式チェック<br/>必須項目チェック

    alt バリデーションエラー
        Valid-->>Client: 422 Unprocessable Entity<br/>{"errors": [...]}
    end

    Valid-->>MW: ProjectCreate

    MW->>Service: create_project(data, current_user)

    Note over Service: トランザクション開始

    Service->>Repo: create(project_data)

    Repo->>DB: INSERT INTO projects

    DB-->>Repo: project (id付き)

    Service->>Repo: create_member(project_id, user_id)

    Repo->>DB: INSERT INTO project_members

    DB-->>Repo: member

    Note over Service: トランザクションcommit

    Service->>Service: キャッシュ無効化

    Service-->>MW: Project

    MW-->>Client: 201 Created<br/>{"id": "...", "name": "New Project"}
:::

---

## 3. プロジェクト作成フロー

### 3.1 プロジェクト作成（メンバー自動追加）

::: mermaid
graph TB
    Start[クライアント: POST /api/v1/projects] --> Auth[認証チェック]

    Auth --> Valid[Pydanticバリデーション<br/>name, code, description]

    Valid --> CodeCheck{コード重複チェック}

    CodeCheck -->|重複あり| Error409[409 Conflict<br/>Code already exists]

    CodeCheck -->|重複なし| TxStart[トランザクション開始]

    TxStart --> CreateProject[Project作成<br/>INSERT INTO projects]

    CreateProject --> CreateMember[ProjectMember作成<br/>role=PROJECT_MANAGER<br/>INSERT INTO project_members]

    CreateMember --> Commit[commit]

    Commit --> ClearCache[キャッシュ無効化]

    ClearCache --> Response[201 Created<br/>project + member]

    Response --> End[クライアント]

    subgraph "エラー処理"
        Error409
        TxError[Exception発生] --> Rollback[rollback]
        Rollback --> Error500[500 Internal Server Error]
    end

    CreateProject -.->|エラー| TxError
    CreateMember -.->|エラー| TxError

    style Start fill:#E3F2FD
    style Response fill:#C8E6C9
    style Error409 fill:#FFCCBC
    style Error500 fill:#FFCCBC
:::

### 3.2 実装コード

```python
# src/app/services/project/project/crud.py

async def create_project(
    self,
    db: AsyncSession,
    project_data: ProjectCreate,
    creator_id: UUID
) -> Project:
    """プロジェクト作成（メンバー自動追加）"""

    # コード重複チェック
    existing = await self.project_repo.get_by_code(db, project_data.code)
    if existing:
        raise BusinessRuleViolationError(
            f"Project code '{project_data.code}' already exists"
        )

    # プロジェクト作成（flush）
    project = await self.project_repo.create(
        db,
        name=project_data.name,
        code=project_data.code,
        description=project_data.description,
        created_by=creator_id,
        is_active=True
    )

    # メンバー追加（flush）
    await self.member_repo.create(
        db,
        project_id=project.id,
        user_id=creator_id,
        project_role=ProjectRole.PROJECT_MANAGER,
        joined_at=datetime.now(timezone.utc)
    )

    # デコレータが自動commit

    # キャッシュ無効化
    await cache_manager.delete(f"projects:user:{creator_id}")

    return project
```

---

## 4. ファイルアップロードフロー

### 4.1 ファイルアップロード処理

::: mermaid
sequenceDiagram
    autonumber
    participant Client
    participant API
    participant Auth as Authentication
    participant RBAC as RBAC Check
    participant FileService
    participant Storage as StorageService
    participant FileRepo as FileRepository
    participant DB as PostgreSQL

    Client->>API: POST /api/v1/projects/{id}/files/upload<br/>multipart/form-data

    API->>Auth: トークン検証
    Auth-->>API: current_user

    API->>RBAC: プロジェクトメンバーシップ + 権限チェック<br/>(MEMBER以上)

    RBAC->>DB: SELECT * FROM project_members
    DB-->>RBAC: ProjectMember

    alt 権限なし
        RBAC-->>Client: 403 Forbidden
    end

    RBAC-->>API: OK

    API->>API: ファイルバリデーション<br/>- サイズ: 最大100MB<br/>- 拡張子: .csv, .xlsx, etc<br/>- Content-Type

    alt バリデーションエラー
        API-->>Client: 400 Bad Request
    end

    API->>FileService: upload_file(project_id, file, user_id)

    FileService->>FileService: 安全なファイル名生成<br/>UUID + 元の拡張子

    FileService->>Storage: upload(file, path)

    alt STORAGE_BACKEND=local
        Storage->>Storage: aiofiles.open(path, "wb")
        Storage-->>FileService: local_path
    else STORAGE_BACKEND=azure
        Storage->>Storage: BlobClient.upload_blob()
        Storage-->>FileService: blob_url
    end

    FileService->>FileRepo: create(file_metadata)

    FileRepo->>DB: INSERT INTO project_files

    DB-->>FileRepo: ProjectFile

    FileRepo-->>FileService: ProjectFile

    FileService-->>API: ProjectFile

    API-->>Client: 201 Created<br/>{"id": "...", "file_name": "data.csv"}
:::

### 4.2 ファイルダウンロード処理

::: mermaid
sequenceDiagram
    autonumber
    participant Client
    participant API
    participant Auth
    participant RBAC
    participant FileService
    participant FileRepo
    participant Storage
    participant DB

    Client->>API: GET /api/v1/projects/{id}/files/{file_id}/download

    API->>Auth: トークン検証
    Auth-->>API: current_user

    API->>RBAC: プロジェクトメンバーシップチェック

    RBAC-->>API: OK

    API->>FileService: download_file(file_id)

    FileService->>FileRepo: get(file_id)

    FileRepo->>DB: SELECT * FROM project_files
    DB-->>FileRepo: ProjectFile

    alt ファイル未発見
        FileRepo-->>Client: 404 Not Found
    end

    FileRepo-->>FileService: ProjectFile

    FileService->>Storage: download(file_path)

    Storage->>Storage: ファイル読み込み

    Storage-->>FileService: file_content (bytes)

    FileService-->>API: file_content + metadata

    API-->>Client: 200 OK<br/>Content-Type: ...<br/>Content-Disposition: attachment<br/><binary_data>
:::

---

## 5. 分析機能のデータフロー

### 5.1 分析セッション作成〜チャット実行

::: mermaid
graph TB
    Start[1. セッション作成<br/>POST /api/v1/analysis/sessions] --> CreateSession[AnalysisSession作成<br/>INSERT INTO analysis_sessions]

    CreateSession --> SelectFile[2. ファイル選択<br/>original_file_id指定]

    SelectFile --> LoadData[3. データ読み込み<br/>DataManager.load_data\(file_path\)]

    LoadData --> InitAgent[4. エージェント初期化<br/>LangChain AgentExecutor]

    InitAgent --> Chat[5. チャット送信<br/>POST /api/v1/analysis/sessions/{id}/chat]

    Chat --> LLMCall[6. LLM呼び出し<br/>Anthropic/OpenAI/Azure]

    LLMCall --> ToolDecision{7. ツール実行判断}

    ToolDecision -->|ツール実行| ToolExec[8. ツール実行<br/>filter_data/aggregate_data/etc]

    ToolExec --> UpdateData[9. データ更新<br/>DataManager.update_data]

    UpdateData --> SaveStep[10. ステップ保存<br/>INSERT INTO analysis_steps]

    SaveStep --> LLMCall

    ToolDecision -->|完了| SaveChat[11. チャット履歴保存<br/>UPDATE analysis_sessions<br/>SET chat_history = ...]

    SaveChat --> Response[12. レスポンス返却<br/>message + steps_executed]

    Response --> End[クライアント]

    subgraph "オプション: スナップショット"
        Snapshot[POST /api/v1/analysis/sessions/{id}/snapshots]
        Snapshot --> SaveSnapshot[SnapshotManager.create_snapshot]
        SaveSnapshot --> UpdateSession[UPDATE analysis_sessions<br/>SET snapshot_history = ...]
    end

    Response -.->|必要時| Snapshot

    style Start fill:#E3F2FD
    style ToolExec fill:#FFF9C4
    style Response fill:#C8E6C9
:::

### 5.2 分析フロー詳細（シーケンス図）

::: mermaid
sequenceDiagram
    autonumber
    participant Client
    participant API
    participant AnalysisService
    participant Agent as AnalysisAgent
    participant LLM
    participant Tools
    participant State as StateManager
    participant DB

    Client->>API: POST /api/v1/analysis/sessions/{id}/chat<br/>{"message": "売上が100万円以上を抽出"}

    API->>AnalysisService: execute_chat(session_id, message)

    AnalysisService->>Agent: execute(message)

    Agent->>State: get_data_overview()
    State-->>Agent: {"row_count": 1000, "columns": [...]}

    Agent->>Agent: プロンプト構築<br/>データ概要 + ユーザーメッセージ

    Agent->>LLM: ainvoke(prompt)

    LLM->>LLM: 推論<br/>「filter_dataツールを使用」

    LLM-->>Agent: ToolCall<br/>tool="filter_data"<br/>params={...}

    Agent->>Tools: filter_data(column="sales", operator="gte", value=1000000)

    Tools->>State: get_current_data()
    State-->>Tools: DataFrame

    Tools->>Tools: df[df['sales'] >= 1000000]

    Tools->>State: update_data(filtered_df)

    Tools->>DB: INSERT INTO analysis_steps<br/>step_type="filter"

    Tools-->>Agent: "Filtered to 42 rows"

    Agent->>Agent: 会話継続判定<br/>（完了）

    Agent->>LLM: generate_response(tool_result)

    LLM-->>Agent: "売上が100万円以上のデータを42件抽出しました"

    Agent->>DB: UPDATE analysis_sessions<br/>SET chat_history = [...]

    Agent-->>AnalysisService: {"message": "...", "steps_executed": [...]}

    AnalysisService-->>API: result

    API-->>Client: 200 OK<br/>{"message": "...", "steps_executed": [...]}
:::

---

## 6. 認証フロー

### 6.1 初回ログイン（Azure AD）

::: mermaid
sequenceDiagram
    autonumber
    participant User
    participant Browser
    participant AzureAD
    participant API
    participant UserService
    participant DB

    User->>Browser: ログイン要求

    Browser->>AzureAD: Authorization Code Flow開始

    AzureAD->>AzureAD: ユーザー認証<br/>（MFA等）

    AzureAD-->>Browser: Authorization Code

    Browser->>AzureAD: トークン要求<br/>（Authorization Code）

    AzureAD-->>Browser: Access Token (JWT)

    Browser->>API: GET /api/v1/users/me<br/>Authorization: Bearer <JWT>

    API->>API: JWT検証<br/>（署名、有効期限、発行者）

    API->>API: azure_oid抽出

    API->>UserService: get_or_create_by_azure_oid(azure_oid, email, name)

    UserService->>DB: SELECT * FROM users<br/>WHERE azure_oid = ?

    DB-->>UserService: NULL（初回ログイン）

    UserService->>DB: INSERT INTO users<br/>(azure_oid, email, display_name, system_role=USER)

    DB-->>UserService: UserAccount（新規作成）

    UserService->>DB: UPDATE users<br/>SET last_login = NOW()

    UserService-->>API: UserAccount

    API-->>Browser: 200 OK<br/>{"id": "...", "email": "...", "system_role": "user"}

    Browser-->>User: ログイン成功
:::

### 6.2 2回目以降のログイン

::: mermaid
sequenceDiagram
    participant Browser
    participant API
    participant UserService
    participant DB

    Browser->>API: GET /api/v1/projects<br/>Authorization: Bearer <JWT>

    API->>API: JWT検証

    API->>API: azure_oid抽出

    API->>UserService: get_or_create_by_azure_oid(azure_oid)

    UserService->>DB: SELECT * FROM users<br/>WHERE azure_oid = ?

    DB-->>UserService: UserAccount（既存）

    UserService->>UserService: メールアドレス・表示名更新<br/>（変更された場合）

    UserService->>DB: UPDATE users<br/>SET last_login = NOW()

    UserService-->>API: UserAccount

    API->>API: RBAC権限チェック

    API-->>Browser: 200 OK<br/>{"items": [...]}
:::

---

## 7. エラー処理フロー

### 7.1 エラーハンドリングフロー

::: mermaid
graph TB
    Request[HTTPリクエスト] --> MW[Middleware]

    MW --> Auth[Authentication]

    Auth --> AuthError{認証エラー?}

    AuthError -->|Yes| E401[401 Unauthorized<br/>トークン無効]

    AuthError -->|No| RBAC[RBAC Check]

    RBAC --> RBACError{権限エラー?}

    RBACError -->|Yes| E403[403 Forbidden<br/>権限不足]

    RBACError -->|No| Valid[Pydanticバリデーション]

    Valid --> ValidError{バリデーションエラー?}

    ValidError -->|Yes| E422[422 Unprocessable Entity<br/>入力エラー]

    ValidError -->|No| Service[Service Layer]

    Service --> BizError{ビジネスエラー?}

    BizError -->|NotFound| E404[404 Not Found]
    BizError -->|Conflict| E409[409 Conflict]
    BizError -->|BusinessRule| E400[400 Bad Request]

    BizError -->|No| DB[Database Access]

    DB --> DBError{DBエラー?}

    DBError -->|Yes| Rollback[rollback]
    Rollback --> E500[500 Internal Server Error]

    DBError -->|No| Success[200 OK / 201 Created]

    subgraph "RFC 9457準拠エラーレスポンス"
        E401
        E403
        E404
        E409
        E422
        E400
        E500
    end

    style Success fill:#C8E6C9
    style E401 fill:#FFCCBC
    style E403 fill:#FFCCBC
    style E404 fill:#FFCCBC
    style E500 fill:#FFCCBC
:::

---

## 8. キャッシュフロー

### 8.1 キャッシュ利用フロー

::: mermaid
sequenceDiagram
    participant Service
    participant CacheManager
    participant Redis
    participant DB

    Service->>CacheManager: get(key)

    CacheManager->>Redis: GET cache:{key}

    alt キャッシュヒット
        Redis-->>CacheManager: cached_value
        CacheManager-->>Service: value（デシリアライズ）
        Note over Service: DB読み取りスキップ<br/>高速レスポンス
    else キャッシュミス
        Redis-->>CacheManager: NULL

        CacheManager-->>Service: None

        Service->>DB: SELECT ...
        DB-->>Service: data

        Service->>CacheManager: set(key, data, ttl=300)

        CacheManager->>Redis: SETEX cache:{key} 300 <serialized_data>

        Redis-->>CacheManager: OK

        Note over Service: 次回はキャッシュヒット
    end
:::

---

## 9. まとめ

### 9.1 データフロー設計の特徴

✅ **明確な処理フロー**: 各ステップを詳細に定義
✅ **エラーハンドリング**: 異常系の処理も明確化
✅ **非同期処理**: async/awaitによる高性能
✅ **トランザクション管理**: データ整合性の保証
✅ **キャッシュ活用**: パフォーマンス最適化
✅ **RFC 9457準拠**: 統一されたエラーレスポンス

### 9.2 パフォーマンスポイント

| 項目 | 最適化手法 |
|------|----------|
| **認証** | JWT検証（署名検証キャッシュ） |
| **データベース** | N+1対策（selectinload） |
| **キャッシュ** | Redis（TTL付き） |
| **ファイルI/O** | 非同期I/O（aiofiles） |
| **並行処理** | async/await |

---

**ドキュメント管理情報:**

- **作成日**: 2025年（リバースエンジニアリング実施）
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - システムアーキテクチャ設計書: `01-architecture/01-system-architecture.md`
  - API仕様書: `04-api/01-api-specifications.md`
  - コンポーネント設計書: `07-components/01-component-design.md`
