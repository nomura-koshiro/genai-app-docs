---
title: Backend Code Review
description: ベストプラクティスを使用した包括的なFastAPIコードレビュー
tools: [Read, Grep, Glob, Bash]
---

@backend-code-reviewer

バックエンドコードレビューを実行してください。

## レビュー対象
$ARGUMENTS

## FastAPI レビュー観点

### 1. アーキテクチャ・設計品質
- [ ] **レイヤー分離**: API層、CRUD層、モデル層が適切に分離されているか
- [ ] **依存性注入**: FastAPIの依存性注入が適切に活用されているか
- [ ] **設定管理**: 環境変数・設定が適切に分離されているか
- [ ] **エラーハンドリング**: 統一されたエラーハンドリング戦略

#### チェックポイント
```python
# ✅ 良い例：適切なレイヤー分離
@router.post("/", response_model=UserResponse)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    current_user = Depends(deps.get_current_active_user),
) -> User:
    user = crud.user.create(db=db, obj_in=user_in)  # CRUD層を使用
    return user

# ❌ 悪い例：ビジネスロジックがエンドポイントに混在
@router.post("/")
def create_user(user_data: dict):
    # SQLクエリがエンドポイント内に...
    result = db.execute("INSERT INTO users...")
```

### 2. セキュリティ

#### 認証・認可
- [ ] JWT トークンが適切に実装されているか
- [ ] パスワードハッシュ化が適切か（bcrypt等）
- [ ] ロールベースアクセス制御（RBAC）の実装
- [ ] セッション管理の安全性

#### 入力検証
- [ ] Pydantic スキーマによる厳密な入力検証
- [ ] SQLインジェクション対策（ORMの適切な使用）
- [ ] XSS対策（入力値のサニタイゼーション）
- [ ] CSRF対策の実装

```python
# ✅ 良い例：厳密な入力検証
class UserCreate(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v):
            raise ValueError('Password must contain letters')
        return v

# ❌ 悪い例：検証不足
class UserCreate(BaseModel):
    email: str  # メール形式チェックなし
    password: str  # 長さ・複雑さチェックなし
```

### 3. データベース設計・操作

#### モデル設計
- [ ] SQLAlchemy モデルの適切な設計
- [ ] 外部キー・制約の適切な設定
- [ ] インデックスの最適化
- [ ] マイグレーションの安全性

#### クエリ最適化
- [ ] N+1問題の回避（eager loading）
- [ ] 不要なデータ取得の排除
- [ ] ページネーションの実装
- [ ] 複雑なクエリの最適化

```python
# ✅ 良い例：N+1問題を回避
def get_users_with_posts(db: Session) -> List[User]:
    return db.query(User).options(joinedload(User.posts)).all()

# ❌ 悪い例：N+1問題発生
def get_users_with_posts(db: Session) -> List[User]:
    users = db.query(User).all()
    for user in users:
        user.posts  # 各ユーザーごとにクエリ実行
```

### 4. API設計品質

#### RESTful設計
- [ ] HTTPメソッドの適切な使用
- [ ] ステータスコードの適切な返却
- [ ] リソース設計の一貫性
- [ ] エラーレスポンスの統一

#### OpenAPI/Swagger
- [ ] 自動生成ドキュメントの充実
- [ ] 例示データの提供
- [ ] スキーマの詳細説明
- [ ] タグ・説明の適切な設定

```python
# ✅ 良い例：詳細なドキュメンテーション
@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="ユーザー作成",
    description="新しいユーザーアカウントを作成します。",
    response_description="作成されたユーザー情報",
)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
) -> User:
    """
    新しいユーザーを作成
    
    - **email**: 有効なメールアドレス（必須）
    - **password**: 8文字以上のパスワード（必須）
    - **full_name**: フルネーム（必須）
    """
    return crud.user.create(db=db, obj_in=user_in)
```

### 5. エラーハンドリング・ロギング

#### 例外処理
- [ ] 統一された例外ハンドリング
- [ ] 適切なHTTPステータスコード
- [ ] ユーザーフレンドリーなエラーメッセージ
- [ ] セキュアなエラーレスポンス（内部情報の非公開）

#### ロギング
- [ ] 構造化ログ（JSON形式）
- [ ] 適切なログレベル設定
- [ ] 機密情報の非ログ出力
- [ ] 監査ログの実装

```python
# ✅ 良い例：構造化ログ
import structlog

logger = structlog.get_logger(__name__)

@router.post("/")
def create_user(user_in: UserCreate):
    try:
        user = crud.user.create(db=db, obj_in=user_in)
        logger.info(
            "User created successfully",
            user_id=user.id,
            email=user.email,
            action="user_create"
        )
        return user
    except IntegrityError as e:
        logger.error(
            "Failed to create user - email already exists",
            email=user_in.email,
            error=str(e),
            action="user_create_failed"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
```

### 6. パフォーマンス・スケーラビリティ

#### 応答性能
- [ ] データベース接続プールの適切な設定
- [ ] 非同期処理の活用（async/await）
- [ ] キャッシング戦略の実装
- [ ] レスポンス時間の最適化

#### リソース管理
- [ ] メモリ使用量の最適化
- [ ] ファイルハンドル・DB接続のリーク防止
- [ ] バックグラウンドタスクの適切な実装
- [ ] Rate limiting の実装

### 7. テスト品質

#### テストカバレッジ
- [ ] ユニットテストの充実（CRUD操作）
- [ ] 統合テストの実装（API エンドポイント）
- [ ] 認証・認可のテスト
- [ ] エラーケースのテスト

#### テスト設計
- [ ] テストデータの適切な管理
- [ ] モック・スタブの活用
- [ ] テスト環境の分離
- [ ] CI/CDでのテスト自動実行

```python
# ✅ 良い例：包括的なテスト
def test_create_user_success(client: TestClient, db: Session):
    """正常系：ユーザー作成成功"""
    user_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/users/", json=user_data)
    
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "password" not in data  # パスワードが返却されないことを確認

def test_create_user_duplicate_email(client: TestClient, db: Session):
    """異常系：重複メールアドレス"""
    # 事前にユーザー作成
    existing_user = create_random_user(db)
    
    user_data = {
        "email": existing_user.email,
        "password": "testpass123",
        "full_name": "Test User"
    }
    response = client.post("/api/v1/users/", json=user_data)
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]
```

### 8. コード品質・保守性

#### 命名・構造
- [ ] 一貫した命名規則
- [ ] 適切なファイル・ディレクトリ構造
- [ ] 循環インポートの回避
- [ ] 設定ファイルの分離

#### ドキュメンテーション
- [ ] 詳細な docstring
- [ ] 型アノテーションの完備
- [ ] README・設定ガイドの充実
- [ ] API使用例の提供

## レビューフィードバック形式

### 優先度分類
- 🚨 **Critical**: セキュリティ・パフォーマンスの重大な問題
- ⚠️ **Important**: アーキテクチャ・保守性の重要な改善点
- 💡 **Suggestion**: コード品質向上の提案
- ✨ **Enhancement**: より良い実装への改善案

### フィードバック例
```markdown
## 🚨 Critical: SQLインジェクション脆弱性

**ファイル**: `app/api/v1/endpoints/users.py:45`

**問題**: 生のSQLクエリでユーザー入力を使用

**現在のコード**:
```python
result = db.execute(f"SELECT * FROM users WHERE name = '{name}'")
```

**改善案**:
```python
result = db.query(User).filter(User.name == name).first()
```

**理由**: SQLAlchemy ORMを使用することで、SQLインジェクション攻撃を防止できます。
```

## 完了確認項目

### 自動チェック
```bash
# 型チェック
cd apps/backend && mypy .

# リント実行
cd apps/backend && ruff check .

# テスト実行
cd apps/backend && python -m pytest

# セキュリティスキャン
cd apps/backend && bandit -r app/
```

### 手動確認
- [ ] OpenAPI ドキュメント（/docs）の確認
- [ ] 認証フローの動作確認
- [ ] エラーレスポンスの確認
- [ ] パフォーマンステストの実行

具体的なコード例と改善案を含めた建設的なフィードバックを提供してください。