# Testing ドキュメント更新の必要性

## 現状の問題点

現在のTestingドキュメント（docs/05-testing/）では、架空のsample_*機能（sample_users、sample_files、sample_sessions、sample_agents）を例として使用しています。しかし、実際のプロジェクトでは以下の機能が実装されています：

## 実際のプロジェクト構造

### 実装されているAPI機能

1. **user_accounts** - ユーザーアカウント管理（Azure AD認証）
2. **project** - プロジェクト管理（CRUD、ファイル、メンバー）
3. **analysis** - 分析機能（テンプレート、セッション）
4. **driver_tree** - ドライバーツリー管理
5. **ppt_generator** - PPTファイル生成

### 実際のテストディレクトリ構造

```text
tests/
├── conftest.py                     # 共通フィクスチャ
└── app/
    ├── api/
    │   ├── core/                   # 依存性注入、例外ハンドラー
    │   ├── decorators/             # デコレータのテスト
    │   ├── middlewares/            # ミドルウェアのテスト
    │   └── routes/
    │       ├── system/             # ヘルスチェック、メトリクス
    │       └── v1/
    │           ├── user_accounts/  # ユーザーアカウントAPI
    │           ├── project/        # プロジェクトAPI
    │           ├── analysis/       # 分析API
    │           ├── driver_tree/    # ドライバーツリーAPI
    │           └── ppt_generator/  # PPT生成API
    ├── models/                     # モデル層のテスト
    │   ├── user_account/
    │   └── project/
    ├── repositories/               # リポジトリ層のテスト
    │   ├── user_account/
    │   ├── project/
    │   ├── analysis/
    │   └── driver_tree/
    └── services/                   # サービス層のテスト
        ├── user_account/
        ├── project/
        ├── analysis/
        ├── driver_tree/
        └── ppt_generator/
```

## 実際のconftest.pyのフィクスチャ

```python
# tests/conftest.py の主要なフィクスチャ

@pytest.fixture
async def test_user(db_session):
    """テスト用ユーザーアカウントを作成"""
    user = UserAccount(
        azure_oid="test-azure-oid",
        email="test@example.com",
        display_name="Test User",
        roles=["User"],
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest.fixture
async def test_project(db_session, test_user):
    """テスト用プロジェクトを作成"""
    project = Project(
        name="テストプロジェクト",
        code="TEST001",
        description="テスト用プロジェクト",
    )
    db_session.add(project)
    await db_session.flush()

    # プロジェクトマネージャーとして追加
    member = ProjectMember(
        project_id=project.id,
        user_id=test_user.id,
        role=ProjectRole.PROJECT_MANAGER,
    )
    db_session.add(member)
    await db_session.commit()
    await db_session.refresh(project)
    return project

@pytest.fixture
async def seeded_templates(db_session):
    """分析テンプレートデータをシード"""
    from app.utils.template_seeder import seed_templates
    result = await seed_templates(db_session, clear_existing=True)
    return result

@pytest.fixture
def override_auth(request):
    """認証依存性をオーバーライド"""
    from app.api.core.dependencies import get_current_active_user_azure
    from app.main import app

    def _override(user):
        app.dependency_overrides[get_current_active_user_azure] = lambda: user
        return user

    yield _override
    app.dependency_overrides.clear()
```

## 実際のテスト例

### UserAccountのテスト (tests/app/api/routes/v1/user_accounts/test_user_accounts.py)

```python
@pytest.mark.asyncio
async def test_list_users_success(client: AsyncClient, override_auth, mock_admin_user):
    """ユーザー一覧取得の正常系テスト（管理者権限）"""
    # Arrange
    override_auth(mock_admin_user)

    # Act
    response = await client.get("/api/v1/users")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "total" in data
```

### Projectのテスト (tests/app/api/routes/v1/project/test_project.py)

```python
@pytest.mark.asyncio
async def test_create_project_endpoint_success(client: AsyncClient, override_auth, mock_current_user):
    """プロジェクト作成エンドポイントの成功ケース"""
    # Arrange
    override_auth(mock_current_user)

    project_data = {
        "name": "Test Project",
        "code": f"TEST-{uuid.uuid4().hex[:6]}",
        "description": "Test description",
    }

    # Act
    response = await client.post("/api/v1/projects", json=project_data)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == project_data["name"]
```

### モデル制約のテスト (tests/app/models/user_account/test_user_account.py)

```python
@pytest.mark.asyncio
async def test_user_unique_azure_oid(db_session):
    """Azure OIDの一意性制約のテスト"""
    # Arrange
    user1 = UserAccount(
        azure_oid="unique-oid-12345",
        email="user1@company.com",
        display_name="User 1",
    )
    db_session.add(user1)
    await db_session.commit()

    # Act & Assert - 同じAzure OIDで作成しようとするとエラー
    user2 = UserAccount(
        azure_oid="unique-oid-12345",  # 同じOID
        email="user2@company.com",
        display_name="User 2",
    )
    db_session.add(user2)

    with pytest.raises(IntegrityError):
        await db_session.commit()
```

## 推奨される修正内容

### 1. 01-testing-strategy/index.md

- テストディレクトリ構造を実際の構造に更新
- sample_* の例を user_accounts, project, analysis 等に変更
- v1/ 配下のAPI説明を実際の機能に更新

### 2. 02-unit-testing/index.md

- SampleUser を UserAccount に変更
- 実際のモデル構造に基づく例に更新

### 3. 03-api-testing/index.md

- sample-files, sample-users の例を実際のエンドポイントに変更
- /api/v1/users, /api/v1/projects 等の実例を追加
- 認証テストの例を override_auth フィクスチャを使用した例に更新

### 4. 05-mocks-fixtures/index.md

- 実際の conftest.py のフィクスチャ例を追加
- test_user, test_project, seeded_templates, override_auth の説明を追加

## 影響範囲

これらの変更により、開発者は以下のメリットを享受できます：

1. **実際のコードベースとの整合性** - ドキュメントが実際の実装と一致
2. **即座に使える例** - コピー&ペーストで動作するテストコード
3. **正確なパス情報** - 実際のテストファイルの場所が明確
4. **プロジェクト固有の知識** - Azure AD認証、ProjectRole等の実際の実装に基づく

## 注意事項

- sample_* の例をすべて削除するのではなく、「教育目的のシンプルな例」として一部残すことも検討
- 実際のプロジェクト構造を反映しつつ、学習しやすい構成を維持
- conftest.pyの重要なフィクスチャ（test_user, test_project等）を明示的に文書化
