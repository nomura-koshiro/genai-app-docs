# テスト戦略書

## 1. 概要

本文書は、genai-app-docsシステムのテスト戦略を定義します。
pytest + pytest-asyncioを使用した包括的なテスト戦略により、品質とリグレッション防止を実現します。

### 1.1 テスト設計方針

- **自動化ファースト**: すべてのテストを自動化
- **高カバレッジ**: コードカバレッジ80%以上を目標
- **高速実行**: CI/CDパイプラインでの高速実行
- **独立性**: テストケース間の独立性確保

---

## 2. テストピラミッド

### 2.1 テスト構成

```mermaid
graph TB
    subgraph "E2E Tests 5%"
        E2E[エンドツーエンドテスト<br/>実際のAPI呼び出し<br/>統合シナリオ]
    end

    subgraph "Integration Tests 25%"
        INT[統合テスト<br/>複数コンポーネント<br/>データベース統合]
    end

    subgraph "Unit Tests 70%"
        UNIT[ユニットテスト<br/>単一関数/クラス<br/>モック使用]
    end

    E2E --> INT
    INT --> UNIT

    style E2E fill:#FF9800
    style INT fill:#FFC107
    style UNIT fill:#8BC34A
```

### 2.2 テストレベル詳細

| レベル | 割合 | 実行時間 | 目的 | 対象 |
|-------|------|---------|------|------|
| **ユニットテスト** | 70% | 高速（< 10秒） | 関数・クラスの動作検証 | Services, Repositories, Utilities |
| **統合テスト** | 25% | 中速（10-60秒） | コンポーネント間連携検証 | API + DB, Service + Repository |
| **E2Eテスト** | 5% | 低速（> 60秒） | ビジネスシナリオ検証 | 完全なユーザーフロー |

---

## 3. テスト構造

### 3.1 ディレクトリ構成

```
tests/
├── conftest.py                      # グローバルフィクスチャ
├── app/
│   ├── api/
│   │   ├── core/
│   │   │   ├── test_dependencies.py       # 依存性注入テスト
│   │   │   └── test_exception_handlers.py # 例外ハンドラテスト
│   │   ├── decorators/
│   │   │   ├── test_basic.py              # 基本デコレータテスト
│   │   │   ├── test_data_access.py        # データアクセステスト
│   │   │   ├── test_reliability.py        # 信頼性デコレータテスト
│   │   │   └── test_security.py           # セキュリティデコレータテスト
│   │   ├── middlewares/
│   │   │   ├── test_logging.py            # ログミドルウェアテスト
│   │   │   ├── test_metrics.py            # メトリクスミドルウェアテスト
│   │   │   ├── test_rate_limit.py         # レート制限テスト
│   │   │   ├── test_security_headers.py   # セキュリティヘッダーテスト
│   │   │   └── test_middleware_order.py   # ミドルウェア順序テスト
│   │   └── routes/
│   │       ├── system/
│   │       │   ├── test_health.py         # ヘルスチェックテスト
│   │       │   ├── test_metrics.py        # メトリクステスト
│   │       │   └── test_root.py           # ルートテスト
│   │       └── v1/
│   │           ├── test_users.py          # ユーザーAPIテスト
│   │           ├── test_projects.py       # プロジェクトAPIテスト
│   │           ├── test_project_members.py # メンバーAPIテスト
│   │           ├── test_project_files.py   # ファイルAPIテスト
│   │           └── test_analysis.py        # 分析APIテスト
│   ├── core/
│   │   ├── test_config.py                 # 設定テスト
│   │   ├── test_database.py               # データベーステスト
│   │   └── security/
│   │       ├── test_azure_ad.py           # Azure AD認証テスト
│   │       ├── test_dev_auth.py           # 開発認証テスト
│   │       └── test_password.py           # パスワードテスト
│   ├── models/
│   │   ├── project/
│   │   │   ├── test_project.py            # プロジェクトモデルテスト
│   │   │   ├── test_member.py             # メンバーモデルテスト
│   │   │   └── test_file.py               # ファイルモデルテスト
│   │   └── user_account/
│   │       └── test_user_account.py       # ユーザーモデルテスト
│   ├── repositories/
│   │   ├── test_base.py                   # ベースリポジトリテスト
│   │   ├── project/
│   │   │   ├── test_project.py            # プロジェクトリポジトリテスト
│   │   │   ├── test_member.py             # メンバーリポジトリテスト
│   │   │   └── test_file.py               # ファイルリポジトリテスト
│   │   └── user_account/
│   │       └── test_user_account.py       # ユーザーリポジトリテスト
│   └── services/
│       ├── project/
│       │   ├── test_project.py            # プロジェクトサービステスト
│       │   ├── test_member.py             # メンバーサービステスト
│       │   └── test_file.py               # ファイルサービステスト
│       └── user_account/
│           └── test_user_account.py       # ユーザーサービステスト
```

**テスト統計:**

- **テストファイル数**: 46ファイル
- **テストコード行数**: 10,511行
- **カバレッジ**: `.coverage`ファイル存在（69,632バイト）

---

## 4. テストフィクスチャ

### 4.1 フィクスチャ階層

```mermaid
graph TB
    subgraph "セッションスコープ"
        EventLoop[event_loop<br/>イベントループ]
        SetupDB[setup_test_database<br/>テストDB作成]
    end

    subgraph "モジュールスコープ"
        Engine[db_engine<br/>テストエンジン]
    end

    subgraph "関数スコープ"
        Session[db_session<br/>テストセッション]
        Client[client<br/>HTTPXクライアント]
        User[test_user<br/>テストユーザー]
        Project[test_project<br/>テストプロジェクト]
    end

    EventLoop --> Engine
    SetupDB --> Engine
    Engine --> Session
    Session --> Client
    Session --> User
    User --> Project

    style EventLoop fill:#F44336
    style Engine fill:#FF9800
    style Session fill:#4CAF50
```

### 4.2 主要フィクスチャ

**実装**: `tests/conftest.py`

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.database import Base

@pytest.fixture(scope="session")
def event_loop():
    """セッションスコープのイベントループ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """テストデータベース自動作成・削除"""
    # テストDB作成
    await create_test_database()

    yield

    # テストDB削除
    await drop_test_database()

@pytest.fixture(scope="function")
async def db_engine():
    """テスト用エンジン（各テスト前にテーブル作成）"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # テーブル作成
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # テーブル削除
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()

@pytest.fixture(scope="function")
async def db_session(db_engine):
    """テスト用セッション"""
    async_session = sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

@pytest.fixture(scope="function")
async def client(db_session):
    """HTTPXテストクライアント"""
    app.dependency_overrides[get_db] = lambda: db_session

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

@pytest.fixture
async def test_user(db_session: AsyncSession):
    """テストユーザー作成"""
    user = UserAccount(
        azure_oid="test-azure-oid-12345",
        email="test@example.com",
        display_name="Test User",
        system_role=SystemUserRole.USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_project(db_session: AsyncSession, test_user: UserAccount):
    """テストプロジェクト作成"""
    project = Project(
        name="Test Project",
        code="TEST_PROJECT",
        created_by=test_user.id,
        is_active=True
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    # メンバー追加（PROJECT_MANAGER）
    member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
        project_role=ProjectRole.PROJECT_MANAGER,
        joined_at=datetime.now(timezone.utc)
    )
    db_session.add(member)
    await db_session.commit()

    return project
```

---

## 5. テストパターン

### 5.1 ユニットテスト

```mermaid
graph TB
    UT[ユニットテスト]

    UT --> Repo[リポジトリテスト]
    UT --> Service[サービステスト]
    UT --> Utils[ユーティリティテスト]

    Repo --> R1[CRUD操作検証]
    Repo --> R2[フィルタ検証]
    Repo --> R3[N+1対策検証]

    Service --> S1[ビジネスロジック検証]
    Service --> S2[トランザクション検証]
    Service --> S3[エラーハンドリング検証]

    Utils --> U1[変換関数検証]
    Utils --> U2[バリデーション検証]
    Utils --> U3[ヘルパー関数検証]

    style Repo fill:#4CAF50
    style Service fill:#8BC34A
    style Utils fill:#AED581
```

#### 5.1.1 リポジトリテスト例

**実装**: `tests/app/repositories/project/test_project.py`

```python
import pytest
from app.repositories.project import ProjectRepository
from app.models.project import Project

@pytest.mark.asyncio
async def test_project_create(db_session, test_user):
    """プロジェクト作成テスト"""
    repo = ProjectRepository(Project)

    project = await repo.create(
        db_session,
        name="New Project",
        code="NEW_PROJECT",
        created_by=test_user.id
    )

    assert project.id is not None
    assert project.name == "New Project"
    assert project.code == "NEW_PROJECT"
    assert project.created_by == test_user.id

@pytest.mark.asyncio
async def test_project_get_by_code(db_session, test_project):
    """コードでプロジェクト取得テスト"""
    repo = ProjectRepository(Project)

    project = await repo.get_by_code(db_session, test_project.code)

    assert project is not None
    assert project.id == test_project.id
    assert project.code == test_project.code

@pytest.mark.asyncio
async def test_project_get_multi_with_filters(db_session, test_user):
    """フィルタ付き複数取得テスト"""
    repo = ProjectRepository(Project)

    # 複数プロジェクト作成
    await repo.create(db_session, name="P1", code="P1", created_by=test_user.id)
    await repo.create(db_session, name="P2", code="P2", created_by=test_user.id, is_active=False)

    # アクティブプロジェクトのみ取得
    projects = await repo.get_multi(db_session, is_active=True)

    assert len(projects) == 1
    assert projects[0].code == "P1"
```

#### 5.1.2 サービステスト例

**実装**: `tests/app/services/project/test_project.py`

```python
import pytest
from app.services.project import ProjectService
from app.core.exceptions import BusinessRuleViolationError

@pytest.mark.asyncio
async def test_create_project_with_member(db_session, test_user):
    """プロジェクト作成とメンバー自動追加テスト"""
    service = ProjectService()

    project = await service.create_project_with_member(
        db_session,
        project_data=ProjectCreate(name="Test", code="TEST"),
        creator_id=test_user.id
    )

    # プロジェクト作成確認
    assert project.id is not None
    assert project.created_by == test_user.id

    # メンバー自動追加確認
    members = await service.get_project_members(db_session, project.id)
    assert len(members) == 1
    assert members[0].user_id == test_user.id
    assert members[0].project_role == ProjectRole.PROJECT_MANAGER

@pytest.mark.asyncio
async def test_delete_project_cascades(db_session, test_project):
    """プロジェクト削除でメンバー・ファイルもカスケード削除"""
    service = ProjectService()

    # ファイル追加
    await service.upload_file(db_session, test_project.id, file_data)

    # プロジェクト削除
    await service.delete_project(db_session, test_project.id)

    # プロジェクト削除確認
    project = await service.get_project(db_session, test_project.id)
    assert project is None

    # メンバー削除確認
    members = await service.get_project_members(db_session, test_project.id)
    assert len(members) == 0

@pytest.mark.asyncio
async def test_duplicate_code_raises_error(db_session, test_user, test_project):
    """重複コードでエラー"""
    service = ProjectService()

    with pytest.raises(BusinessRuleViolationError) as exc_info:
        await service.create_project_with_member(
            db_session,
            project_data=ProjectCreate(name="Duplicate", code=test_project.code),
            creator_id=test_user.id
        )

    assert "already exists" in str(exc_info.value).lower()
```

---

### 5.2 統合テスト

```mermaid
graph TB
    IT[統合テスト]

    IT --> API[APIテスト]
    IT --> DB[データベーステスト]
    IT --> MW[ミドルウェアテスト]

    API --> A1[認証フローテスト]
    API --> A2[CRUD操作テスト]
    API --> A3[権限チェックテスト]

    DB --> D1[トランザクションテスト]
    DB --> D2[カスケード削除テスト]
    DB --> D3[リレーションシップテスト]

    MW --> M1[実行順序テスト]
    MW --> M2[エラーハンドリングテスト]
    MW --> M3[パフォーマンステスト]

    style API fill:#2196F3
    style DB fill:#03A9F4
    style MW fill:#00BCD4
```

#### 5.2.1 APIテスト例

**実装**: `tests/app/api/routes/v1/test_projects.py`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_project_success(client: AsyncClient, test_user_token):
    """プロジェクト作成成功"""
    response = await client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {test_user_token}"},
        json={
            "name": "New Project",
            "code": "NEW_PROJECT",
            "description": "Test project"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Project"
    assert data["code"] == "NEW_PROJECT"
    assert "id" in data

@pytest.mark.asyncio
async def test_create_project_unauthorized(client: AsyncClient):
    """認証なしでプロジェクト作成失敗"""
    response = await client.post(
        "/api/v1/projects",
        json={"name": "Test", "code": "TEST"}
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_projects_filters_by_membership(
    client: AsyncClient,
    test_user_token,
    test_project,
    other_user_project
):
    """メンバーのみのプロジェクトを取得"""
    response = await client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {test_user_token}"}
    )

    assert response.status_code == 200
    data = response.json()

    # 自分のプロジェクトのみ取得
    project_ids = [p["id"] for p in data["items"]]
    assert str(test_project.id) in project_ids
    assert str(other_user_project.id) not in project_ids

@pytest.mark.asyncio
async def test_delete_project_forbidden_for_non_manager(
    client: AsyncClient,
    member_user_token,
    test_project
):
    """MEMBER権限でプロジェクト削除失敗"""
    response = await client.delete(
        f"/api/v1/projects/{test_project.id}",
        headers={"Authorization": f"Bearer {member_user_token}"}
    )

    assert response.status_code == 403
    assert "manager" in response.json()["detail"].lower()
```

---

### 5.3 E2Eテスト

```mermaid
sequenceDiagram
    participant Test
    participant API
    participant DB

    Test->>API: 1. ユーザー作成
    API->>DB: INSERT users
    DB-->>API: user_id

    Test->>API: 2. プロジェクト作成
    API->>DB: INSERT projects, project_members
    DB-->>API: project_id

    Test->>API: 3. ファイルアップロード
    API->>DB: INSERT project_files
    DB-->>API: file_id

    Test->>API: 4. 分析セッション作成
    API->>DB: INSERT analysis_sessions
    DB-->>API: session_id

    Test->>API: 5. チャット実行
    API->>DB: UPDATE analysis_sessions<br/>INSERT analysis_steps
    DB-->>API: analysis_result

    Test->>API: 6. プロジェクト削除
    API->>DB: DELETE projects<br/>CASCADE: members, files, sessions
    DB-->>API: success
```

#### 5.3.1 E2Eテスト例

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_complete_analysis_workflow(client: AsyncClient):
    """完全な分析ワークフロー"""

    # 1. ユーザー作成（自動作成）
    # 2. プロジェクト作成
    project_response = await client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Analysis Project", "code": "ANALYSIS"}
    )
    project_id = project_response.json()["id"]

    # 3. ファイルアップロード
    file_response = await client.post(
        f"/api/v1/projects/{project_id}/files/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("data.csv", csv_data, "text/csv")}
    )
    file_id = file_response.json()["id"]

    # 4. 分析セッション作成
    session_response = await client.post(
        "/api/v1/analysis/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={"project_id": project_id, "original_file_id": file_id}
    )
    session_id = session_response.json()["id"]

    # 5. チャット実行
    chat_response = await client.post(
        f"/api/v1/analysis/sessions/{session_id}/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": "売上が100万円以上のデータを抽出してください"}
    )
    assert chat_response.status_code == 200

    # 6. スナップショット作成
    snapshot_response = await client.post(
        f"/api/v1/analysis/sessions/{session_id}/snapshots",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "フィルタ後"}
    )
    assert snapshot_response.status_code == 201

    # 7. プロジェクト削除（カスケード削除）
    delete_response = await client.delete(
        f"/api/v1/projects/{project_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_response.status_code == 204
```

---

## 6. テストカバレッジ

### 6.1 カバレッジ目標

```mermaid
graph LR
    subgraph "カバレッジ目標"
        Overall[全体: 80%以上]
        Critical[重要機能: 90%以上]
        New[新規コード: 100%]
    end

    subgraph "計測項目"
        Line[行カバレッジ]
        Branch[分岐カバレッジ]
        Function[関数カバレッジ]
    end

    Overall --> Line
    Critical --> Branch
    New --> Function

    style Overall fill:#FFC107
    style Critical fill:#FF9800
    style New fill:#F44336
```

### 6.2 重要機能の定義

| カテゴリ | 重要度 | カバレッジ目標 |
|---------|-------|--------------|
| **認証・認可** | 最高 | 95% |
| **RBAC** | 最高 | 95% |
| **データ操作（CRUD）** | 高 | 90% |
| **セキュリティ** | 最高 | 95% |
| **ビジネスロジック** | 高 | 85% |
| **ユーティリティ** | 中 | 80% |
| **UIヘルパー** | 低 | 70% |

### 6.3 カバレッジ計測

```bash
# カバレッジ付きテスト実行
pytest --cov=app --cov-report=html --cov-report=term

# カバレッジレポート表示
open htmlcov/index.html
```

**レポート例:**

```text
Name                                   Stmts   Miss  Cover
----------------------------------------------------------
app/__init__.py                            5      0   100%
app/core/config.py                       158     12    92%
app/core/security/password.py             15      0   100%
app/core/security/azure_ad.py             45      8    82%
app/repositories/base.py                 120     10    92%
app/services/project/project.py          200     25    88%
----------------------------------------------------------
TOTAL                                   5432    445    92%
```

---

## 7. CI/CD統合

### 7.1 CI/CDパイプライン

```mermaid
graph LR
    Push[Git Push] --> Lint[Linting<br/>Ruff]
    Lint --> TypeCheck[Type Check<br/>mypy]
    TypeCheck --> UnitTest[Unit Tests<br/>70%]

    UnitTest --> IntTest[Integration Tests<br/>25%]
    IntTest --> E2E[E2E Tests<br/>5%]

    E2E --> Coverage[Coverage Check<br/>> 80%]
    Coverage --> Build[Build Docker Image]

    Build --> Deploy{Deploy?}
    Deploy -->|Yes| Staging[Staging Environment]
    Deploy -->|No| End[End]

    style UnitTest fill:#4CAF50
    style IntTest fill:#8BC34A
    style E2E fill:#AED581
    style Coverage fill:#FFC107
```

### 7.2 GitHub Actions設定例

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install -r requirements.txt

      - name: Run linter
        run: ruff check .

      - name: Run type check
        run: mypy app/

      - name: Run tests with coverage
        run: |
          pytest --cov=app --cov-report=xml --cov-report=term
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test@localhost/test_db

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

---

## 8. テストベストプラクティス

### 8.1 命名規則

```mermaid
mindmap
  root((命名規則))
    テストファイル
      test_*.py
      *_test.py
    テスト関数
      test_機能名_条件_期待結果
      test_create_project_success
      test_delete_project_forbidden_for_member
    フィクスチャ
      test_*
      test_user
      test_project
    マーカー
      @pytest.mark.asyncio
      @pytest.mark.slow
      @pytest.mark.e2e
```

### 8.2 Arrange-Act-Assert（AAA）パターン

```python
@pytest.mark.asyncio
async def test_project_delete_cascades_members(db_session, test_project):
    """プロジェクト削除でメンバーもカスケード削除"""

    # Arrange（準備）
    repo = ProjectRepository(Project)
    member_repo = ProjectMemberRepository(ProjectMember)

    # メンバー追加
    await member_repo.create(
        db_session,
        project_id=test_project.id,
        user_id=test_user.id,
        project_role=ProjectRole.MEMBER
    )

    # Act（実行）
    await repo.delete(db_session, test_project.id)

    # Assert（検証）
    project = await repo.get(db_session, test_project.id)
    assert project is None

    members = await member_repo.get_by_project(db_session, test_project.id)
    assert len(members) == 0
```

### 8.3 避けるべきアンチパターン

❌ **避けるべき:**

```python
# ❌ 複数の検証を1つのテストに詰め込む
async def test_project_operations():
    # 作成テスト
    project = await create_project()
    assert project.id is not None

    # 更新テスト
    updated = await update_project(project.id)
    assert updated.name == "Updated"

    # 削除テスト
    await delete_project(project.id)
    assert await get_project(project.id) is None

# ❌ テスト間の依存関係
async def test_create_project():
    global project_id
    project = await create_project()
    project_id = project.id

async def test_update_project():
    await update_project(project_id)  # 前のテストに依存
```

✅ **推奨:**

```python
# ✅ 1テスト1検証
async def test_create_project_returns_id():
    project = await create_project()
    assert project.id is not None

async def test_update_project_changes_name():
    project = await create_project()
    updated = await update_project(project.id, name="Updated")
    assert updated.name == "Updated"

async def test_delete_project_removes_from_db():
    project = await create_project()
    await delete_project(project.id)
    assert await get_project(project.id) is None
```

---

## 9. モックとスタブ

### 9.1 モック戦略

```mermaid
graph TB
    Test[テスト]

    Test --> Mock{モック対象}

    Mock -->|外部API| LLM[LLM API<br/>Anthropic/OpenAI]
    Mock -->|外部サービス| Azure[Azure Blob Storage]
    Mock -->|時間依存| Time[datetime.now]

    LLM --> MockLLM[unittest.mock<br/>モックレスポンス]
    Azure --> MockAzure[aioboto3.mock<br/>モックストレージ]
    Time --> MockTime[freezegun<br/>時刻固定]

    style MockLLM fill:#4CAF50
    style MockAzure fill:#8BC34A
    style MockTime fill:#AED581
```

### 9.2 モック実装例

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
@patch("app.services.analysis.agent.llm_client")
async def test_analysis_agent_executes_tool(mock_llm, db_session, test_session):
    """AIエージェントがツールを実行"""

    # モックLLMレスポンス設定
    mock_llm.ainvoke = AsyncMock(return_value={
        "tool": "filter_data",
        "parameters": {"column": "sales", "operator": "gte", "value": 1000000}
    })

    agent = AnalysisAgent(session_id=test_session.id)

    result = await agent.execute("売上が100万円以上のデータを抽出してください")

    assert result.tool_name == "filter_data"
    assert result.affected_rows == 42
    mock_llm.ainvoke.assert_called_once()
```

---

## 10. まとめ

### 10.1 テスト戦略の特徴

✅ **包括的なテストスイート**: 46ファイル、10,511行
✅ **高カバレッジ**: 80%以上を目標
✅ **テストピラミッド**: ユニット70%、統合25%、E2E5%
✅ **自動化**: CI/CDパイプライン統合
✅ **高速実行**: ユニットテスト< 10秒
✅ **独立性**: テストケース間の依存なし
✅ **明確な構造**: AAA パターン、命名規則

### 10.2 今後の改善提案

- **パフォーマンステスト**: ロードテスト、ストレステスト
- **セキュリティテスト**: ペネトレーションテスト
- **変異テスト**: mutation testing
- **ビジュアルリグレッションテスト**: UI変更検出
- **カオスエンジニアリング**: 障害注入テスト

---

**ドキュメント管理情報:**

- **作成日**: 2025年（リバースエンジニアリング実施）
- **対象バージョン**: 現行実装
- **関連ドキュメント**:
  - システムアーキテクチャ設計書: `01-architecture/01-system-architecture.md`
  - API仕様書: `04-api/01-api-specifications.md`
  - データベース設計書: `02-database/01-database-design.md`
