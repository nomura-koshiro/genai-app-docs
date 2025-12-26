# テスト戦略書

## 1. 概要

本文書は、CAMP_backシステムのテスト戦略を定義します。
pytest + pytest-asyncioを使用した効率的なテスト戦略により、品質とリグレッション防止を実現します。

### 1.1 テスト設計方針

- **自動化ファースト**: すべてのテストを自動化
- **効率的なテスト**: 冗長なテスト層を排除し、重要な層に集中
- **高速実行**: CI/CDパイプラインでの高速実行
- **独立性**: テストケース間の独立性確保
- **TEST-ID管理**: 各テストに一意のID（`[test_filename-001]`形式）を付与

### 1.2 テスト統計

| 項目 | 値 |
|------|-----|
| テストファイル数 | 24ファイル |
| テスト関数数 | 約232件 |
| TEST-ID形式 | `[test_filename-001]`（ファイル単位で連番管理） |

### 1.3 テスト概要一覧

テスト一覧の詳細は [02-test_list.xlsx](02-test_list.xlsx) を参照してください。

---

## 2. TEST-ID管理

テストの識別と検索を容易にするため、各テストに一意のIDを付与しています。

### 2.1 TEST-ID形式

```text
[test_filename-NNN]

例:
- [test_projects-001] - test_projects.py の1番目のテスト
- [test_user_account-015] - test_user_account.py の15番目のテスト
```

### 2.2 TEST-ID付与ルール

| ルール | 説明 |
|--------|------|
| **ファイル単位連番** | 各ファイル内で001から連番 |
| **docstringに記載** | テスト関数のdocstring冒頭に `[TEST-ID]` 形式で記載 |
| **自動付与スクリプト** | `scripts/add_test_ids.py` で一括付与可能 |

### 2.3 TEST-ID使用例

```python
@pytest.mark.asyncio
async def test_create_project_success(client: AsyncClient, override_auth, regular_user):
    """[test_projects-001] プロジェクト作成の成功ケース。"""
    # Arrange
    override_auth(regular_user)
    # ...
```

### 2.4 TEST-ID管理ツール

```bash
# TEST-IDの一括付与・更新
python scripts/add_test_ids.py

# テスト一覧のExcel出力
python scripts/create_test_excel.py
```

---

## 3. テスト戦略

### 3.1 テスト構成

::: mermaid
graph TB
    subgraph "API Tests 35%"
        API[APIテスト<br/>エンドポイント検証<br/>認証・認可]
    end

    subgraph "Service Tests 65%"
        SVC[サービステスト<br/>ビジネスロジック<br/>DB統合]
    end

    API --> SVC

    style API fill:#2196F3
    style SVC fill:#4CAF50
:::

### 3.2 テストレベル詳細

| レベル | 割合 | 目的 | 対象 |
|-------|------|------|------|
| **APIテスト** | 35% | エンドポイント動作検証、認証・認可 | Routes層 |
| **サービステスト** | 65% | ビジネスロジック検証、DB操作 | Services層 |

### 3.3 テスト対象外の層

以下の層は冗長性回避のため、直接のテスト対象外としています：

| 層 | 理由 |
|----|------|
| **Models** | SQLAlchemyのORM定義のみ。サービステストでDB操作時に間接的に検証 |
| **Repositories** | 汎用CRUD操作のみ。サービステストで間接的にカバー |
| **Schemas** | Pydanticによる自動バリデーション。APIテストで間接的に検証 |

---

## 4. テスト構造

### 4.1 ディレクトリ構成

```text
tests/
├── conftest.py                      # グローバルフィクスチャ
├── fixtures/
│   └── seeders/                     # テストデータシーダー
│       ├── base.py                      # 基底シーダークラス
│       ├── user_account.py              # ユーザーシーダー
│       ├── project.py                   # プロジェクトシーダー
│       ├── project_member.py            # メンバーシーダー
│       ├── project_file.py              # ファイルシーダー
│       └── analysis_session.py          # 分析セッションシーダー
├── app/
│   ├── api/
│   │   ├── core/
│   │   │   └── test_exception_handlers.py # 例外ハンドラテスト
│   │   ├── decorators/
│   │   │   ├── test_basic.py              # 基本デコレータテスト
│   │   │   ├── test_data_access.py        # データアクセステスト
│   │   │   ├── test_error_handling.py     # エラーハンドリングデコレータテスト
│   │   │   └── test_reliability.py        # 信頼性デコレータテスト
│   │   ├── middlewares/
│   │   │   ├── test_logging.py            # ログミドルウェアテスト
│   │   │   ├── test_metrics.py            # メトリクスミドルウェアテスト
│   │   │   ├── test_rate_limit.py         # レート制限テスト
│   │   │   └── test_security_headers.py   # セキュリティヘッダーテスト
│   │   └── routes/
│   │       ├── system/
│   │       │   ├── test_health.py         # ヘルスチェックテスト
│   │       │   ├── test_metrics.py        # メトリクステスト
│   │       │   └── test_root.py           # ルートテスト
│   │       └── v1/
│   │           ├── analysis/
│   │           │   └── test_analysis_sessions.py # 分析セッションAPIテスト
│   │           ├── project/
│   │           │   ├── test_projects.py       # プロジェクトAPIテスト
│   │           │   ├── test_project_members.py # メンバーAPIテスト
│   │           │   └── test_project_files.py   # ファイルAPIテスト
│   │           └── user_accounts/
│   │               └── test_user_accounts.py   # ユーザーAPIテスト
│   ├── core/
│   │   ├── test_config.py                 # 設定テスト
│   │   └── security/
│   │       ├── test_api_key.py            # APIキー認証テスト
│   │       ├── test_jwt.py                # JWT認証テスト
│   │       └── test_password.py           # パスワードテスト
│   └── services/
│       ├── analysis/
│       │   └── test_analysis_session.py   # 分析セッションサービステスト
│       ├── project/
│       │   ├── test_project.py            # プロジェクトサービステスト
│       │   ├── test_project_member.py     # メンバーサービステスト
│       │   └── test_project_file.py       # ファイルサービステスト
│       └── user_account/
│           └── test_user_account.py       # ユーザーサービステスト
```

---

## 5. テストフィクスチャ

### 5.1 フィクスチャとは

**フィクスチャ（fixture）** は、テストの前準備を行うための仕組みです。テストに必要なデータやオブジェクトを自動的に用意してくれます。

```python
# フィクスチャを使わない場合（毎回同じコードを書く必要がある）
async def test_example_without_fixture(db_session):
    # 毎回ユーザーを作成するコードを書く必要がある
    user = UserAccount(azure_oid="test-oid", email="test@example.com", ...)
    db_session.add(user)
    await db_session.commit()
    # テスト処理...

# フィクスチャを使う場合（引数に書くだけでOK）
async def test_example_with_fixture(regular_user):
    # regular_userは自動的に作成済み！
    assert regular_user.email is not None
```

#### 5.1.1 フィクスチャの基本的な使い方

1. **テスト関数の引数にフィクスチャ名を書く** だけで使えます
2. pytestが自動的にフィクスチャを実行し、結果を渡してくれます
3. 複数のフィクスチャを同時に使うこともできます

```python
# 複数のフィクスチャを使う例
@pytest.mark.asyncio
async def test_with_multiple_fixtures(client, override_auth, regular_user, project_with_owner):
    # client: HTTPテストクライアント
    # override_auth: 認証をモックする関数
    # regular_user: 一般ユーザー（自動作成済み）
    # project_with_owner: プロジェクトとオーナー（自動作成済み）

    project, owner = project_with_owner
    override_auth(regular_user)

    response = await client.get(f"/api/v1/project/{project.id}")
    assert response.status_code == 200
```

#### 5.1.2 フィクスチャのスコープ

フィクスチャには「いつ作成・破棄されるか」を決める **スコープ** があります。

| スコープ | 説明 | 使用例 |
|---------|------|--------|
| `function` | 各テスト関数ごとに作成・破棄（デフォルト） | `db_session`, `client` |
| `session` | テストセッション全体で1回だけ作成 | `event_loop`, `setup_test_database` |

```python
# functionスコープ: 各テストで独立したデータ
async def test_1(db_session):  # 新しいdb_sessionが作成される
    ...

async def test_2(db_session):  # また新しいdb_sessionが作成される（test_1とは別）
    ...
```

### 5.2 フィクスチャ階層図

フィクスチャは依存関係を持っています。下位のフィクスチャは上位のフィクスチャに依存しています。

::: mermaid
graph TB
    subgraph "セッションスコープ（テスト全体で1回）"
        EventLoop[event_loop<br/>イベントループ]
        SetupDB[setup_test_database<br/>テストDB作成]
    end

    subgraph "関数スコープ（各テストで毎回）"
        Engine[db_engine<br/>テストエンジン]
        Session[db_session<br/>テストセッション]
        Client[client<br/>HTTPXクライアント]
        Seeder[test_data_seeder<br/>テストデータシーダー]
    end

    subgraph "便利フィクスチャ（よく使うデータ）"
        RegularUser[regular_user<br/>一般ユーザー]
        AdminUser[admin_user<br/>管理者ユーザー]
        ProjectOwner[project_with_owner<br/>オーナー付きプロジェクト]
        ProjectMembers[project_with_members<br/>メンバー付きプロジェクト]
    end

    EventLoop --> Engine
    SetupDB --> Engine
    Engine --> Session
    Session --> Client
    Session --> Seeder
    Seeder --> RegularUser
    Seeder --> AdminUser
    Seeder --> ProjectOwner
    Seeder --> ProjectMembers

    style EventLoop fill:#F44336
    style Engine fill:#FF9800
    style Session fill:#4CAF50
    style Seeder fill:#2196F3
:::

### 5.3 主要フィクスチャ一覧

**実装**: `tests/conftest.py`

#### 5.3.1 インフラ系フィクスチャ

テストの基盤となるフィクスチャです。通常は直接使用せず、他のフィクスチャが内部で使用します。

| フィクスチャ | スコープ | 説明 |
|-------------|---------|------|
| `event_loop` | session | 非同期処理用のイベントループ |
| `setup_test_database` | session | テストDB作成・削除（autouse=自動実行） |
| `db_engine` | function | DBエンジン（各テストでテーブル作成/削除） |

#### 5.3.2 よく使うフィクスチャ

テストコードで頻繁に使用するフィクスチャです。

| フィクスチャ | スコープ | 説明 | 使用場面 |
|-------------|---------|------|---------|
| `db_session` | function | DBセッション | サービステストでDB操作する時 |
| `client` | function | HTTPテストクライアント | APIテストでリクエストを送る時 |
| `override_auth` | function | 認証オーバーライド関数 | APIテストで認証済みユーザーとしてアクセスする時 |
| `test_data_seeder` | function | テストデータ作成ヘルパー | カスタムテストデータを作成する時 |

#### 5.3.3 各フィクスチャの詳細説明

##### db_session

データベースとの接続セッションを提供します。サービステストでDB操作が必要な時に使います。

```python
@pytest.mark.asyncio
async def test_service_example(db_session):
    # db_sessionを使ってサービスを初期化
    service = ProjectService(db_session)

    # サービスのメソッドを呼び出し
    project = await service.create_project(...)

    # 検証
    assert project.id is not None
```

##### client

FastAPIアプリケーションにHTTPリクエストを送信するためのクライアントです。APIテストで使います。

```python
@pytest.mark.asyncio
async def test_api_example(client):
    # GETリクエスト
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    # POSTリクエスト（JSONデータ付き）
    response = await client.post("/api/v1/project", json={
        "name": "Test Project",
        "code": "TEST001"
    })
    assert response.status_code == 201

    # レスポンスのJSONを取得
    data = response.json()
    assert data["name"] == "Test Project"
```

##### override_auth

認証をモックするための関数を提供します。APIテストで「このユーザーとしてログインしている」状態を作れます。

```python
@pytest.mark.asyncio
async def test_authenticated_api(client, override_auth, regular_user):
    # regular_userとして認証された状態にする
    override_auth(regular_user)

    # 認証が必要なAPIにアクセス
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 200
    assert response.json()["id"] == str(regular_user.id)
```

##### test_data_seeder

テストデータを柔軟に作成するためのヘルパーです。便利フィクスチャでは対応できないカスタムデータが必要な時に使います。

```python
@pytest.mark.asyncio
async def test_custom_data(test_data_seeder):
    # 特定の属性を持つユーザーを作成
    user = await test_data_seeder.create_user(
        display_name="特別なユーザー",
        email="special@example.com"
    )

    # プロジェクトを作成してメンバー追加
    project = await test_data_seeder.create_project(
        name="カスタムプロジェクト",
        created_by=user.id
    )

    # 必ずcommitを呼ぶ！
    await test_data_seeder.db.commit()

    # テスト処理...
```

### 5.4 便利フィクスチャ

よく使うテストデータを簡単に取得できる事前定義フィクスチャです。引数に書くだけで使えます。

| フィクスチャ | 説明 | 戻り値 |
|-------------|------|--------|
| `regular_user` | 一般ユーザー（roles=["User"]） | `UserAccount` |
| `admin_user` | 管理者ユーザー（roles=["SystemAdmin"]） | `UserAccount` |
| `project_with_owner` | オーナー付きプロジェクト | `tuple[Project, UserAccount]` |
| `project_with_members` | 全ロールのメンバー付きプロジェクト | `dict` |
| `basic_test_data` | 基本データセット一式 | `dict` |
| `analysis_session_data` | 分析セッション用データ一式 | `dict` |

#### 5.4.1 regular_user / admin_user

```python
@pytest.mark.asyncio
async def test_user_fixtures(regular_user, admin_user):
    # regular_user: 一般ユーザー
    assert "User" in regular_user.roles
    assert regular_user.email is not None

    # admin_user: 管理者ユーザー
    assert "SystemAdmin" in admin_user.roles
```

#### 5.4.2 project_with_owner

プロジェクトとそのオーナーをタプルで返します。

```python
@pytest.mark.asyncio
async def test_project_fixture(project_with_owner):
    # タプルを分解して取得
    project, owner = project_with_owner

    assert project.name is not None
    assert owner.id is not None

    # ownerはPROJECT_MANAGERロールでプロジェクトに参加済み
```

#### 5.4.3 project_with_members

全ロールのメンバーを持つプロジェクトを辞書で返します。権限テストに便利です。

```python
@pytest.mark.asyncio
async def test_project_with_members_fixture(project_with_members):
    # 辞書から各データを取得
    project = project_with_members["project"]
    owner = project_with_members["owner"]          # PROJECT_MANAGER
    moderator = project_with_members["moderator"]  # PROJECT_MODERATOR
    member = project_with_members["member"]        # MEMBER
    viewer = project_with_members["viewer"]        # VIEWER

    # 各ロールでの権限テストに使用
```

#### 5.4.4 analysis_session_data

分析セッション関連のテストデータ一式を返します。

```python
@pytest.mark.asyncio
async def test_analysis_session_fixture(analysis_session_data):
    project = analysis_session_data["project"]
    owner = analysis_session_data["owner"]
    session = analysis_session_data["session"]
    # ... 分析セッション関連のテスト
```

### 5.5 テストデータシーダー

**実装**: `tests/fixtures/seeders/`

テストデータの作成を簡素化するシーダークラス群です。各シーダーは `BaseSeeder` を継承し、ドメインごとに分離されています。

#### 5.5.1 シーダークラス一覧

| シーダークラス | ファイル | 説明 |
|---------------|---------|------|
| `BaseSeeder` | `base.py` | 基底シーダークラス |
| `UserAccountSeeder` | `user_account.py` | ユーザー作成 |
| `ProjectSeeder` | `project.py` | プロジェクト作成 |
| `ProjectMemberSeeder` | `project_member.py` | メンバー追加 |
| `ProjectFileSeeder` | `project_file.py` | ファイル作成 |
| `AnalysisSessionSeeder` | `analysis_session.py` | 分析セッション作成 |

#### 5.5.2 test_data_seederの使い方

`test_data_seeder` フィクスチャは、上記シーダーの機能を統合したヘルパーです。

```python
@pytest.mark.asyncio
async def test_seeder_example(test_data_seeder):
    # ユーザー作成
    user = await test_data_seeder.create_user(display_name="Test User")

    # 管理者ユーザー作成
    admin = await test_data_seeder.create_admin_user()

    # プロジェクト作成（オーナー付き）
    project, owner = await test_data_seeder.create_project_with_owner()

    # メンバー追加
    await test_data_seeder.create_member(
        project=project,
        user=user,
        role=ProjectRole.MEMBER
    )

    # ⚠️ 重要: 最後に必ずcommitを呼ぶ！
    await test_data_seeder.db.commit()
```

> **注意**: `test_data_seeder` を使った場合は、必ず `await test_data_seeder.db.commit()` を呼んでください。便利フィクスチャ（`regular_user` など）は自動的にcommitされます。

### 5.6 認証オーバーライド

APIテストでは `override_auth` フィクスチャを使って認証をモックします。これにより、実際のAzure AD認証をスキップしてテストできます。

#### 5.6.1 基本的な使い方

```python
@pytest.mark.asyncio
async def test_create_project(client, override_auth, regular_user):
    # Step 1: 認証をオーバーライド（regular_userとしてログイン状態にする）
    override_auth(regular_user)

    # Step 2: 認証済みユーザーとしてAPIを呼び出し
    response = await client.post("/api/v1/project", json={
        "name": "Test Project",
        "code": "TEST001"
    })

    # Step 3: 検証
    assert response.status_code == 201
```

#### 5.6.2 異なるユーザーでテスト

```python
@pytest.mark.asyncio
async def test_admin_only_endpoint(client, override_auth, regular_user, admin_user):
    # 一般ユーザーでアクセス → 403 Forbidden
    override_auth(regular_user)
    response = await client.delete("/api/v1/admin/users/123")
    assert response.status_code == 403

    # 管理者ユーザーでアクセス → 200 OK
    override_auth(admin_user)
    response = await client.delete("/api/v1/admin/users/123")
    assert response.status_code == 200
```

#### 5.6.3 未認証状態のテスト

`override_auth` を呼ばなければ、未認証状態としてテストできます。

```python
@pytest.mark.asyncio
async def test_unauthenticated_access(client):
    # override_authを呼ばない → 未認証状態
    response = await client.get("/api/v1/users/me")
    assert response.status_code in [401, 403]
```

### 5.7 フィクスチャ使用のベストプラクティス

#### 5.7.1 適切なフィクスチャを選ぶ

```python
# ✅ Good: 便利フィクスチャで十分な場合はそれを使う
async def test_good(regular_user):
    assert regular_user.email is not None

# ❌ Bad: わざわざシーダーで同じことをする
async def test_bad(test_data_seeder):
    user = await test_data_seeder.create_user()  # regular_userで十分
    await test_data_seeder.db.commit()
    assert user.email is not None
```

#### 5.7.2 必要なフィクスチャだけを使う

```python
# ✅ Good: 必要なものだけ
async def test_user_display_name(regular_user):
    assert regular_user.display_name is not None

# ❌ Bad: 使わないフィクスチャを引数に含める
async def test_user_display_name(client, db_session, regular_user, admin_user):
    assert regular_user.display_name is not None
```

#### 5.7.3 commitを忘れない

```python
# ✅ Good: commitを呼ぶ
async def test_good(test_data_seeder):
    user = await test_data_seeder.create_user()
    await test_data_seeder.db.commit()  # 忘れずに！

# ❌ Bad: commitを忘れる → データが保存されない
async def test_bad(test_data_seeder):
    user = await test_data_seeder.create_user()
    # commitがない → テストが失敗する可能性
```

---

## 6. テストパターン

### 6.1 APIテスト

::: mermaid
graph TB
    API[APIテスト]

    API --> A1[認証・認可テスト]
    API --> A2[CRUD操作テスト]
    API --> A3[エラーレスポンステスト]

    style API fill:#2196F3
:::

#### 6.1.1 APIテスト例

**実装**: `tests/app/api/routes/v1/project/test_projects.py`

```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_project_success(client: AsyncClient, override_auth, regular_user):
    """[test_projects-001] プロジェクト作成の成功ケース。"""
    # Arrange
    override_auth(regular_user)
    project_data = {
        "name": "Test Project",
        "code": f"TEST-{uuid.uuid4().hex[:6]}",
        "description": "Test description",
    }

    # Act
    response = await client.post("/api/v1/project", json=project_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == project_data["name"]

@pytest.mark.asyncio
async def test_create_project_unauthorized(client: AsyncClient):
    """[test_projects-003] 認証なしでのプロジェクト作成失敗。"""
    # Act
    response = await client.post("/api/v1/project", json={"name": "Test", "code": "TEST"})

    # Assert
    assert response.status_code in [401, 403]
```

### 6.2 サービステスト

::: mermaid
graph TB
    SVC[サービステスト]

    SVC --> S1[ビジネスロジック検証]
    SVC --> S2[権限チェック検証]
    SVC --> S3[エラーハンドリング検証]
    SVC --> S4[DB操作検証]

    style SVC fill:#4CAF50
:::

#### 6.2.1 サービステスト例

**実装**: `tests/app/services/project/test_project.py`

```python
import pytest
from app.services import ProjectService
from app.schemas import ProjectCreate, ProjectUpdate
from app.core.exceptions import AuthorizationError, ValidationError

@pytest.mark.asyncio
async def test_create_project_success(db_session):
    """[test_project-001] プロジェクト作成の成功ケース。"""
    # Arrange
    service = ProjectService(db_session)
    project_data = ProjectCreate(name="Test Project", code="TEST-001")

    # Act
    project = await service.create_project(project_data, creator_id)

    # Assert
    assert project.id is not None
    assert project.name == "Test Project"
    assert project.code == "TEST-001"

@pytest.mark.asyncio
async def test_create_project_duplicate_code(db_session):
    """[test_project-002] 重複コードでのプロジェクト作成エラー。"""
    # Arrange
    service = ProjectService(db_session)
    await service.create_project(ProjectCreate(name="First", code="DUP-001"), creator_id)

    # Act & Assert
    with pytest.raises(ValidationError) as exc_info:
        await service.create_project(ProjectCreate(name="Second", code="DUP-001"), creator_id)

    assert "既に使用されています" in str(exc_info.value.message)
```

---

## 7. テストベストプラクティス

### 7.1 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| テストファイル | `test_*.py` | `test_projects.py` |
| テスト関数 | `test_機能_条件_結果` | `test_create_project_success` |
| フィクスチャ | 用途を示す名前 | `regular_user`, `project_with_owner` |

### 7.2 Arrange-Act-Assert（AAA）パターン

```python
@pytest.mark.asyncio
async def test_project_delete_success(db_session, test_project):
    """[test_project-010] プロジェクト削除の成功ケース。"""

    # Arrange（準備）
    service = ProjectService(db_session)
    project_id = test_project.id

    # Act（実行）
    await service.delete_project(project_id, owner_id)

    # Assert（検証）
    deleted = await service.get_project(project_id)
    assert deleted is None
```

### 7.3 避けるべきアンチパターン

❌ **避けるべき:**

```python
# ❌ 複数の検証を1つのテストに詰め込む
async def test_project_operations():
    project = await create_project()
    assert project.id is not None
    updated = await update_project(project.id)
    assert updated.name == "Updated"
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
    project = await create_project()  # 独立して作成
    updated = await update_project(project.id, name="Updated")
    assert updated.name == "Updated"
```

---

## 8. テストカバレッジ

### 8.1 カバレッジ目標

| カテゴリ | 重要度 | カバレッジ目標 |
|---------|-------|--------------|
| **認証・認可** | 最高 | 95% |
| **RBAC** | 最高 | 95% |
| **データ操作（CRUD）** | 高 | 90% |
| **セキュリティ** | 最高 | 95% |
| **ビジネスロジック** | 高 | 85% |
| **ユーティリティ** | 中 | 80% |

### 8.2 カバレッジ計測

```bash
# カバレッジ付きテスト実行
pytest --cov=app --cov-report=html --cov-report=term

# カバレッジレポート表示
open htmlcov/index.html
```

---

## 9. モックとスタブ

### 9.1 モック戦略

| モック対象 | ライブラリ | 用途 |
|-----------|-----------|------|
| 外部API（LLM等） | `unittest.mock` | レスポンスのモック |
| 外部ストレージ | `aioboto3.mock` | ストレージ操作のモック |
| 時間依存 | `freezegun` | 時刻の固定 |

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
    result = await agent.execute("売上が100万円以上のデータを抽出")

    assert result.tool_name == "filter_data"
    mock_llm.ainvoke.assert_called_once()
```

---

**ドキュメント管理情報:**

- **関連ドキュメント**:
  - システムアーキテクチャ設計書: `01-architecture/01-system-architecture.md`
  - API仕様書: `04-api/01-api-specifications.md`
  - データベース設計書: `02-database/01-database-design.md`
