# セキュリティ実装詳細設計書

## 📋 文書管理情報

| 項目 | 内容 |
|------|------|
| **文書名** | セキュリティ実装詳細設計書 |
| **バージョン** | 1.0.0 |
| **作成日** | 2025-01-11 |
| **最終更新日** | 2025-01-11 |
| **作成者** | Claude Code |
| **対象システム** | genai-app-docs (camp-backend) |
| **関連文書** | [RBAC設計書](./01-rbac-design.md), [認証設計書](./02-authentication-design.md) |

---

## 📑 目次

1. [概要](#1-概要)
2. [OWASP Top 10 対策](#2-owasp-top-10-対策)
3. [認証セキュリティ実装](#3-認証セキュリティ実装)
4. [パスワードセキュリティ](#4-パスワードセキュリティ)
5. [セッション管理](#5-セッション管理)
6. [入力検証とサニタイゼーション](#6-入力検証とサニタイゼーション)
7. [APIセキュリティ](#7-apiセキュリティ)
8. [データ保護](#8-データ保護)
9. [監査ログとモニタリング](#9-監査ログとモニタリング)
10. [セキュリティテスト](#10-セキュリティテスト)
11. [付録](#11-付録)

---

## 1. 概要

### 1.1 目的

本設計書は、genai-app-docsプロジェクトのセキュリティ実装の詳細を文書化し、以下を達成することを目的とします：

- **セキュリティベストプラクティスの適用**: OWASP Top 10対策の実装方法を明確化
- **実装ガイドの提供**: 開発者がセキュアなコードを書くための具体的な指針
- **セキュリティ監査の支援**: セキュリティレビューとペネトレーションテストの準備
- **コンプライアンス対応**: セキュリティ標準への準拠を証明

### 1.2 適用範囲

本設計書は以下を対象とします：

- ✅ OWASP Top 10セキュリティリスク対策
- ✅ 認証・認可メカニズムの実装
- ✅ パスワードハッシュ化とストレージ
- ✅ トークン管理とセッションセキュリティ
- ✅ 入力検証とサニタイゼーション
- ✅ APIセキュリティ（レート制限、CORS、ヘッダー）
- ✅ データ暗号化と保護
- ✅ 監査ログとセキュリティモニタリング

### 1.3 セキュリティ原則

本システムは以下のセキュリティ原則に基づいて設計されています：

```mermaid
graph TB
    subgraph "セキュリティ設計原則"
        A[Defense in Depth<br/>多層防御]
        B[Least Privilege<br/>最小権限の原則]
        C[Fail Secure<br/>セキュアな失敗]
        D[Complete Mediation<br/>完全な調停]
        E[Separation of Duties<br/>職務分離]

        A --> A1[複数のセキュリティ層]
        A --> A2[単一障害点の排除]

        B --> B1[必要最小限の権限付与]
        B --> B2[デフォルト拒否]

        C --> C1[エラー時は安全側に倒す]
        C --> C2[詳細エラーの非公開]

        D --> D1[すべてのアクセスをチェック]
        D --> D2[権限キャッシュの適切な管理]

        E --> E1[管理者権限の分離]
        E --> E2[監査の独立性]
    end

    style A fill:#ff6b6b
    style B fill:#51cf66
    style C fill:#339af0
    style D fill:#ffd43b
    style E fill:#ff6b6b
```

### 1.4 セキュリティスタック

```text
┌─────────────────────────────────────────────────────┐
│ Application Layer                                   │
│ - Input Validation (Pydantic)                       │
│ - RBAC Authorization                                │
│ - Output Encoding                                   │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ API Layer                                           │
│ - Rate Limiting (Redis)                             │
│ - Security Headers (HSTS, CSP, X-Frame-Options)     │
│ - CORS Policy                                       │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Authentication Layer                                │
│ - Azure AD / JWT                                    │
│ - Token Validation                                  │
│ - Password Hashing (bcrypt)                         │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Data Layer                                          │
│ - SQL Injection Prevention (SQLAlchemy)             │
│ - Encrypted Storage (Azure Blob)                    │
│ - Database Access Control                           │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│ Infrastructure Layer                                │
│ - TLS/HTTPS                                         │
│ - Network Segmentation                              │
│ - Firewall Rules                                    │
└─────────────────────────────────────────────────────┘
```

---

## 2. OWASP Top 10 対策

### 2.1 OWASP Top 10 (2021) 対策サマリー

| # | リスク | 対策状況 | 実装方法 |
|---|--------|----------|----------|
| A01 | Broken Access Control | ✅ 実装済み | RBAC、ProjectRole権限チェック |
| A02 | Cryptographic Failures | ✅ 実装済み | bcrypt + SHA-256、HTTPS、Azure Blob暗号化 |
| A03 | Injection | ✅ 実装済み | SQLAlchemy ORM、Pydantic検証 |
| A04 | Insecure Design | ✅ 実装済み | セキュアな設計原則、脅威モデリング |
| A05 | Security Misconfiguration | ✅ 実装済み | セキュリティヘッダー、環境別設定 |
| A06 | Vulnerable Components | ⚠️ 継続監視 | Dependabot、定期的な依存関係更新 |
| A07 | Identification and Authentication Failures | ✅ 実装済み | Azure AD、JWT、MFA対応 |
| A08 | Software and Data Integrity Failures | ✅ 実装済み | 署名検証、監査ログ |
| A09 | Security Logging and Monitoring Failures | ✅ 実装済み | structlog、Prometheus、監査ログ |
| A10 | Server-Side Request Forgery (SSRF) | ✅ 実装済み | URL検証、ホワイトリスト |

### 2.2 A01: Broken Access Control（アクセス制御の不備）

#### 2.2.1 対策概要

**脆弱性の説明**:

- 適切な権限チェックがなく、他のユーザーのデータにアクセスできる
- 権限昇格攻撃（一般ユーザーが管理者権限を取得）
- IDOR (Insecure Direct Object Reference) 攻撃

**実装されている対策**:

```mermaid
graph LR
    A[HTTPリクエスト] --> B{認証チェック}
    B -->|失敗| C[401 Unauthorized]
    B -->|成功| D{システムロールチェック}
    D -->|SYSTEM_ADMIN| E[全アクセス許可]
    D -->|USER| F{プロジェクトロールチェック}
    F -->|PROJECT_MANAGER| G[プロジェクト管理]
    F -->|MEMBER| H[リソース編集]
    F -->|VIEWER| I[リソース閲覧]
    F -->|権限なし| J[403 Forbidden]

    style C fill:#ff6b6b
    style E fill:#51cf66
    style J fill:#ff6b6b
```

#### 2.2.2 実装詳細

**RBAC権限チェック実装**:

```python
# src/app/api/core/dependencies/auth.py
from app.core.rbac import require_project_role
from app.models.enums import ProjectRole

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    user_data = Depends(get_current_user_data),
) -> User:
    """認証済みユーザーを取得（必須）"""
    user = await user_service.get_by_azure_oid(db, user_data.oid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

# エンドポイントでの使用例
@router.put("/projects/{project_id}/files/{file_id}")
async def update_project_file(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    file_update: ProjectFileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """プロジェクトファイル更新（MEMBER以上の権限が必要）"""
    # プロジェクトメンバーシップと権限チェック
    member = await project_member_service.get_by_user_and_project(
        db, current_user.id, project_id
    )
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a member of this project"
        )

    # 権限チェック（VIEWERは編集不可）
    if member.role == ProjectRole.VIEWER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # リソース所有権チェック
    file = await project_file_service.get_by_id(db, file_id)
    if file.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="File does not belong to this project"
        )

    return await project_file_service.update(db, file_id, file_update)
```

**セキュリティチェックリスト**:

- ✅ すべてのAPIエンドポイントで認証を強制（オプショナルなゲストアクセスは明示的に許可）
- ✅ リソースアクセス時にプロジェクトメンバーシップを検証
- ✅ 権限レベルに応じた操作制限（VIEWER/MEMBER/PROJECT_MANAGER）
- ✅ リソース所有権の検証（project_id一致チェック）
- ✅ SYSTEM_ADMINによるバイパスは監査ログに記録

#### 2.2.3 IDOR対策

**IDOR (Insecure Direct Object Reference) 攻撃の防止**:

```python
# ❌ 脆弱な実装例（使用しない）
@router.get("/files/{file_id}")
async def get_file_bad(file_id: int, db: AsyncSession = Depends(get_db)):
    # 権限チェックなし - 他のユーザーのファイルにアクセス可能
    return await file_service.get_by_id(db, file_id)

# ✅ セキュアな実装例
@router.get("/projects/{project_id}/files/{file_id}")
async def get_file_secure(
    project_id: uuid.UUID,
    file_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. プロジェクトメンバーシップチェック
    member = await project_member_service.get_by_user_and_project(
        db, current_user.id, project_id
    )
    if not member:
        raise HTTPException(403, "Not a project member")

    # 2. ファイル存在確認
    file = await project_file_service.get_by_id(db, file_id)
    if not file:
        raise HTTPException(404, "File not found")

    # 3. リソース所有権チェック
    if file.project_id != project_id:
        raise HTTPException(403, "File does not belong to this project")

    return file
```

**IDOR対策のベストプラクティス**:

- UUID v4を主キーとして使用（連番IDは予測可能）
- リソースアクセス時にプロジェクトIDとリソースIDの関連性を検証
- エラーメッセージで存在の有無を漏らさない（404 vs 403の使い分けに注意）

### 2.3 A02: Cryptographic Failures（暗号化の失敗）

#### 2.3.1 対策概要

**脆弱性の説明**:

- 機密データの平文保存
- 弱い暗号化アルゴリズムの使用
- 不適切な鍵管理

**実装されている対策**:

```mermaid
graph TB
    subgraph "暗号化実装"
        A[パスワード] --> B[SHA-256事前ハッシュ]
        B --> C[bcrypt ハッシュ化<br/>コスト: 12ラウンド]
        C --> D[データベース保存]

        E[ファイル] --> F[Azure Blob Storage]
        F --> G[サーバーサイド暗号化<br/>AES-256]

        H[通信] --> I[TLS 1.2/1.3]
        I --> J[HTTPS強制<br/>HSTS]

        K[APIキー] --> L[環境変数]
        L --> M[Azure Key Vault<br/>本番環境]
    end

    style C fill:#51cf66
    style G fill:#51cf66
    style I fill:#51cf66
    style M fill:#51cf66
```

#### 2.3.2 パスワードハッシュ化実装

**bcrypt + SHA-256ハイブリッド方式**:

```python
# src/app/core/security/password.py
import hashlib
import bcrypt

def hash_password(password: str) -> str:
    """パスワードをbcryptでハッシュ化します。

    セキュリティ特性:
        - SHA-256事前ハッシュ化: bcryptの72バイト制限に対処
        - bcryptアルゴリズム: コスト12ラウンド（2^12 = 4096回のハッシュ計算）
        - ランダムsalt自動生成: レインボーテーブル攻撃耐性
        - ブルートフォース攻撃耐性: 1パスワードあたり約0.1秒の計算時間

    なぜSHA-256を使用するか:
        1. bcryptは72バイトまでしか処理できない
        2. 日本語などのマルチバイト文字対応
        3. SHA-256は常に64文字（64バイト < 72バイト）を出力
        4. 長いパスワードでも安全に処理可能

    Args:
        password: ハッシュ化する平文パスワード

    Returns:
        str: bcrypt形式のハッシュ（$2b$12$...）
    """
    # ステップ1: SHA-256で事前ハッシュ化（72バイト制限対策）
    password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

    # ステップ2: bcryptでハッシュ化（ランダムsalt自動生成）
    hashed = bcrypt.hashpw(password_hash.encode("utf-8"), bcrypt.gensalt())

    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証します。

    セキュリティ特性:
        - 定時間比較: タイミング攻撃対策
        - bcryptの内部実装により安全な比較を保証

    Args:
        plain_password: ユーザー入力の平文パスワード
        hashed_password: データベースに保存されたハッシュ

    Returns:
        bool: パスワードが一致すればTrue
    """
    password_hash = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    return bcrypt.checkpw(
        password_hash.encode("utf-8"),
        hashed_password.encode("utf-8")
    )
```

**bcrypt設定の根拠**:

| 項目 | 設定値 | 根拠 |
|------|--------|------|
| **コストファクター** | 12ラウンド | OWASP推奨（2^12 = 4096回の計算）、1パスワードあたり約0.1秒の処理時間 |
| **事前ハッシュ** | SHA-256 | bcryptの72バイト制限に対処、マルチバイト文字対応 |
| **Salt** | 自動生成 | bcrypt.gensalt()が毎回ランダムなsaltを生成、レインボーテーブル攻撃を防止 |

#### 2.3.3 ファイル暗号化

**Azure Blob Storage暗号化**:

```python
# src/app/core/storage/azure_blob.py
from azure.storage.blob.aio import BlobServiceClient

class AzureBlobStorage:
    """Azure Blob Storageクライアント（暗号化対応）"""

    def __init__(self):
        # サーバーサイド暗号化（SSE）は自動的に有効
        # Azure Blob Storageはデフォルトで以下を使用:
        # - 暗号化: AES-256
        # - 鍵管理: Microsoft管理キー（デフォルト）または顧客管理キー
        self.client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONNECTION_STRING
        )

    async def upload_file(
        self,
        container: str,
        blob_name: str,
        data: bytes,
        content_type: str | None = None,
    ) -> str:
        """ファイルをアップロード（自動暗号化）

        セキュリティ:
            - サーバーサイド暗号化（AES-256）
            - HTTPS転送（TLS 1.2+）
            - アクセス制御（SASトークン）
        """
        container_client = self.client.get_container_client(container)
        blob_client = container_client.get_blob_client(blob_name)

        await blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings={"content_type": content_type} if content_type else None,
        )

        return blob_client.url
```

**暗号化仕様**:

- **転送中**: TLS 1.2/1.3、HTTPS強制
- **保存時**: AES-256サーバーサイド暗号化（Azure Blob Storage標準）
- **鍵管理**: Microsoft管理キー（デフォルト）、顧客管理キー対応可能

#### 2.3.4 通信暗号化（TLS/HTTPS）

**HSTS（HTTP Strict Transport Security）強制**:

```python
# src/app/api/middlewares/security_headers.py
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 本番環境のみ: HSTS (HTTP Strict Transport Security)
        if not settings.DEBUG:
            # max-age=31536000: 1年間HSTSポリシーを記憶
            # includeSubDomains: すべてのサブドメインにも適用
            response.headers["Strict-Transport-Security"] = \
                "max-age=31536000; includeSubDomains"

        return response
```

**TLS設定**:

- **プロトコル**: TLS 1.2以上（TLS 1.0/1.1は無効化）
- **暗号スイート**: 強力な暗号スイートのみ許可（AES-GCM優先）
- **証明書**: Let's EncryptまたはAzure証明書
- **HSTS**: 1年間のmax-age設定

### 2.4 A03: Injection（インジェクション）

#### 2.4.1 SQLインジェクション対策

**SQLAlchemy ORMによる自動エスケープ**:

```python
# ✅ セキュア: SQLAlchemy ORM（パラメータ化クエリ）
from sqlalchemy import select

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """メールアドレスでユーザーを検索（SQLインジェクション対策済み）"""
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

# SQLAlchemyが生成するクエリ（内部）:
# SELECT * FROM users WHERE email = :email_1
# パラメータ: {'email_1': 'user@example.com'}
```

**生SQLの禁止**:

```python
# ❌ 脆弱: 生SQL（絶対に使用しない）
async def get_user_by_email_bad(db: AsyncSession, email: str):
    # SQLインジェクション脆弱性！
    query = f"SELECT * FROM users WHERE email = '{email}'"
    result = await db.execute(query)
    return result.fetchone()

# 攻撃例:
# email = "'; DROP TABLE users; --"
# 生成されるSQL: SELECT * FROM users WHERE email = ''; DROP TABLE users; --'
```

**セキュアなクエリパターン**:

```python
# パターン1: 等価比較
stmt = select(User).where(User.email == email)

# パターン2: LIKE検索（ワイルドカードエスケープ）
search_term = f"%{search.replace('%', '\\%').replace('_', '\\_')}%"
stmt = select(User).where(User.name.like(search_term, escape="\\"))

# パターン3: IN句
stmt = select(User).where(User.id.in_(user_ids))

# パターン4: 複雑な条件
from sqlalchemy import and_, or_
stmt = select(User).where(
    and_(
        User.is_active == True,
        or_(User.role == "admin", User.role == "manager")
    )
)
```

#### 2.4.2 NoSQLインジェクション対策

**Redisコマンドの安全な使用**:

```python
# src/app/core/cache.py
class CacheManager:
    async def set(self, key: str, value: Any, ttl: int | None = None):
        """キャッシュに値を設定（安全な実装）"""
        # キーのサニタイゼーション
        safe_key = self._sanitize_key(key)

        # redis-pyライブラリは自動的にエスケープを処理
        await self._redis.set(
            safe_key,
            json.dumps(value),
            ex=ttl or self.default_ttl
        )

    def _sanitize_key(self, key: str) -> str:
        """Redisキーをサニタイズ"""
        # スペース、改行、特殊文字を削除
        return re.sub(r'[^a-zA-Z0-9:_-]', '', key)
```

#### 2.4.3 コマンドインジェクション対策

**外部コマンド実行の禁止**:

本プロジェクトでは以下のポリシーを適用：

- ❌ `os.system()` の使用禁止
- ❌ `subprocess.call()` の直接使用禁止
- ✅ 必要な場合は `subprocess.run()` with `shell=False`
- ✅ 入力値の厳密なバリデーション

```python
# ❌ 脆弱な実装（使用禁止）
import os
def process_file_bad(filename: str):
    os.system(f"convert {filename} output.pdf")  # コマンドインジェクション脆弱性

# ✅ セキュアな実装
import subprocess
from pathlib import Path

def process_file_secure(filename: str):
    # 入力検証
    if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
        raise ValueError("Invalid filename")

    # ファイルの存在確認
    filepath = Path(filename)
    if not filepath.exists():
        raise FileNotFoundError()

    # shell=Falseで安全に実行
    subprocess.run(
        ["convert", str(filepath), "output.pdf"],
        shell=False,  # シェル経由の実行を無効化
        check=True,
        timeout=30,
    )
```

### 2.5 A04: Insecure Design（安全でない設計）

#### 2.5.1 セキュアな設計原則の適用

**実装されているセキュア設計パターン**:

1. **認証と認可の分離**:

   ```python
   # 認証: ユーザーが誰かを確認
   user = await get_current_user(token)

   # 認可: ユーザーが何をできるかを確認
   await check_project_permission(user, project, "write")
   ```

2. **デフォルト拒否**:

   ```python
   # すべてのエンドポイントはデフォルトで認証が必要
   # ゲストアクセスは明示的に許可
   @router.get("/public-data", dependencies=[])  # 明示的な許可
   async def get_public_data():
       return {"data": "public"}
   ```

3. **セキュアなデフォルト設定**:

   ```python
   # src/app/core/config.py
   class Settings(BaseSettings):
       # セキュアなデフォルト値
       DEBUG: bool = False  # 本番環境ではFalse
       RATE_LIMIT_CALLS: int = 100  # レート制限を有効化
       ALLOWED_ORIGINS: list[str] = []  # CORSはデフォルトで制限

       @model_validator(mode="before")
       @classmethod
       def validate_production_security(cls, values):
           """本番環境でのセキュリティ設定を検証"""
           if values.get("ENVIRONMENT") == "production":
               # 本番環境では厳格なチェック
               if values.get("DEBUG") is True:
                   raise ValueError("DEBUG must be False in production")
               if not values.get("SECRET_KEY") or len(values.get("SECRET_KEY", "")) < 32:
                   raise ValueError("SECRET_KEY must be at least 32 characters")
               if not values.get("ALLOWED_ORIGINS"):
                   raise ValueError("ALLOWED_ORIGINS must be set in production")
           return values
   ```

#### 2.5.2 脅威モデリング

**STRIDE脅威分析**:

| 脅威 | 説明 | 対策 |
|------|------|------|
| **S**poofing (なりすまし) | 他のユーザーになりすます | Azure AD認証、JWT署名検証、MFA対応 |
| **T**ampering (改ざん) | データを不正に変更 | JWT署名、HTTPS、監査ログ |
| **R**epudiation (否認) | 操作を否認 | 監査ログ、タイムスタンプ、ユーザー追跡 |
| **I**nformation Disclosure (情報漏洩) | 機密情報の漏洩 | RBAC、暗号化、セキュリティヘッダー |
| **D**enial of Service (サービス拒否) | サービスを利用不能にする | レート制限、タイムアウト、リソース制限 |
| **E**levation of Privilege (権限昇格) | 権限を不正に昇格 | RBAC厳格チェック、最小権限の原則 |

### 2.6 A05: Security Misconfiguration（セキュリティ設定ミス）

#### 2.6.1 セキュリティヘッダー

**実装されているセキュリティヘッダー**:

```python
# src/app/api/middlewares/security_headers.py
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 1. X-Content-Type-Options: MIMEスニッフィング防止
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 2. X-Frame-Options: クリックジャッキング防止
        response.headers["X-Frame-Options"] = "DENY"

        # 3. X-XSS-Protection: XSS攻撃防止（レガシーブラウザ向け）
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 4. Strict-Transport-Security: HTTPS強制（本番環境のみ）
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = \
                "max-age=31536000; includeSubDomains"

        # 5. Content-Security-Policy（オプション）
        # より厳密なセキュリティが必要な場合
        # response.headers["Content-Security-Policy"] = (
        #     "default-src 'self'; "
        #     "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        #     "style-src 'self' 'unsafe-inline'; "
        # )

        return response
```

**セキュリティヘッダーの効果**:

| ヘッダー | 目的 | 効果 |
|----------|------|------|
| `X-Content-Type-Options: nosniff` | MIMEスニッフィング防止 | ブラウザがContent-Typeを無視してファイルタイプを判定するのを防ぐ |
| `X-Frame-Options: DENY` | クリックジャッキング防止 | iframe内でのページ表示を完全に禁止 |
| `X-XSS-Protection: 1; mode=block` | XSS攻撃防止 | ブラウザのXSSフィルターを有効化（レガシーブラウザ向け） |
| `Strict-Transport-Security` | HTTPS強制 | 1年間HTTPSを強制、中間者攻撃を防止 |

#### 2.6.2 環境別設定管理

**環境変数による設定分離**:

```text
project_root/
├── .env.local          # 開発環境設定
├── .env.staging        # ステージング環境設定
├── .env.production     # 本番環境設定（Git管理外）
└── .env.example        # サンプル設定
```

**環境別セキュリティ設定**:

```bash
# .env.local（開発環境）
ENVIRONMENT=development
DEBUG=True
AUTH_MODE=development
SECRET_KEY=dev-secret-key-change-me-in-production
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# .env.production（本番環境）
ENVIRONMENT=production
DEBUG=False
AUTH_MODE=production
SECRET_KEY=<32文字以上のランダム文字列>
ALLOWED_ORIGINS=["https://example.com"]
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
DATABASE_URL=postgresql+asyncpg://prod-user:strong-password@prod-db:5432/prod_db
```

**設定バリデーション**:

```python
# src/app/core/config.py
@model_validator(mode="before")
@classmethod
def validate_production_security(cls, values: dict[str, Any]) -> dict[str, Any]:
    """本番環境でのセキュリティ設定を検証"""
    if values.get("ENVIRONMENT") == "production":
        # 1. DEBUGモード禁止
        if values.get("DEBUG") is True:
            raise ValueError(
                "DEBUG=True is not allowed in production. "
                "Set DEBUG=False for production environment."
            )

        # 2. SECRET_KEY必須（32文字以上）
        secret_key = values.get("SECRET_KEY")
        if not secret_key or len(secret_key) < 32:
            raise ValueError(
                "SECRET_KEY must be at least 32 characters in production. "
                "Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )

        # 3. ALLOWED_ORIGINS必須
        if not values.get("ALLOWED_ORIGINS"):
            raise ValueError(
                "ALLOWED_ORIGINS must be set in production. "
                "Example: ALLOWED_ORIGINS=[\"https://example.com\"]"
            )

        # 4. 開発モード認証禁止
        if values.get("AUTH_MODE") == "development":
            raise ValueError(
                "AUTH_MODE=development is not allowed in production. "
                "Set AUTH_MODE=production and configure Azure AD."
            )

    return values
```

### 2.7 A07: Identification and Authentication Failures

#### 2.7.1 認証メカニズム

**多層認証アーキテクチャ**:

```mermaid
graph TB
    subgraph "認証層"
        A[HTTPリクエスト] --> B{認証モード}
        B -->|production| C[Azure AD認証]
        B -->|development| D[モック認証]

        C --> E{トークン検証}
        E --> F[JWT署名検証]
        F --> G[有効期限チェック]
        G --> H[発行者検証]
        H --> I[オーディエンス検証]
        I --> J[スコープ検証]
        J --> K[認証成功]

        E -->|失敗| L[401 Unauthorized]

        D --> M{モックトークン}
        M -->|一致| K
        M -->|不一致| L
    end

    style C fill:#51cf66
    style K fill:#51cf66
    style L fill:#ff6b6b
```

#### 2.7.2 トークンセキュリティ

**JWT実装の詳細**:

```python
# src/app/core/security/jwt.py
from datetime import UTC, datetime, timedelta
from jose import ExpiredSignatureError, JWTError, jwt

def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """JWTアクセストークンを生成

    トークンに含まれるクレーム:
        - sub: Subject（user_id）
        - exp: 有効期限（UTC）
        - iat: 発行時刻（UTC）
        - type: トークンタイプ（"access"）

    アルゴリズム: HS256（HMAC-SHA256）
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt

def decode_access_token(token: str) -> dict[str, Any] | None:
    """JWTトークンをデコードし検証

    検証項目:
        - 署名の検証（SECRET_KEYとの一致）
        - 有効期限の検証（exp）
        - アルゴリズムの検証（HS256）
        - subフィールドの存在確認
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "verify_exp": True,  # 有効期限を検証
                "verify_signature": True,
            },
        )

        # subフィールド必須
        if "sub" not in payload:
            logger.warning("JWT検証失敗: subフィールドがありません")
            return None

        return payload

    except ExpiredSignatureError:
        logger.warning("JWTトークン有効期限切れ")
        return None
    except JWTError as e:
        logger.warning(f"JWTデコードエラー: {e}")
        return None
```

**トークンセキュリティのベストプラクティス**:

- ✅ 短い有効期限（デフォルト: 30分）
- ✅ リフレッシュトークンの実装（有効期限: 7日間）
- ✅ トークンの署名検証（HMAC-SHA256）
- ✅ トークンの有効期限検証（自動）
- ✅ HTTPSでの送信（平文での送信禁止）
- ✅ HttpOnlyクッキーの使用（XSS対策）

#### 2.7.3 ブルートフォース攻撃対策

**アカウントロックアウト機能**:

```python
# src/app/models/user.py（将来実装）
class User(Base):
    __tablename__ = "users"

    # ログイン試行回数追跡
    failed_login_attempts: Mapped[int] = mapped_column(default=0)
    last_failed_login: Mapped[datetime | None] = mapped_column(nullable=True)
    account_locked_until: Mapped[datetime | None] = mapped_column(nullable=True)

    @property
    def is_locked(self) -> bool:
        """アカウントがロックされているかチェック"""
        if not self.account_locked_until:
            return False
        return datetime.now(UTC) < self.account_locked_until

# src/app/services/auth.py（将来実装）
async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User | None:
    """ユーザー認証（ブルートフォース対策付き）"""
    user = await user_service.get_by_email(db, email)

    if not user:
        # タイミング攻撃対策: 存在しないユーザーでもハッシュ計算
        verify_password("dummy", "$2b$12$dummy...")
        return None

    # アカウントロックチェック
    if user.is_locked:
        logger.warning(
            "ロックされたアカウントへのログイン試行",
            user_id=user.id,
            email=email,
        )
        return None

    # パスワード検証
    if not verify_password(password, user.hashed_password):
        # 失敗回数をインクリメント
        user.failed_login_attempts += 1
        user.last_failed_login = datetime.now(UTC)

        # 5回失敗でアカウントロック（1時間）
        if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            user.account_locked_until = datetime.now(UTC) + timedelta(
                hours=settings.ACCOUNT_LOCK_DURATION_HOURS
            )
            logger.warning(
                "アカウントロック",
                user_id=user.id,
                failed_attempts=user.failed_login_attempts,
            )

        await db.commit()
        return None

    # 認証成功: カウンターをリセット
    user.failed_login_attempts = 0
    user.last_failed_login = None
    user.account_locked_until = None
    await db.commit()

    return user
```

**設定値**:

- `MAX_LOGIN_ATTEMPTS`: 5回（デフォルト）
- `ACCOUNT_LOCK_DURATION_HOURS`: 1時間（デフォルト）

### 2.8 A09: Security Logging and Monitoring Failures

#### 2.8.1 監査ログ実装

**構造化ログ（structlog）**:

```python
# src/app/core/logging.py
import structlog

def setup_logging():
    """構造化ログを設定"""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer() if not settings.DEBUG
                else structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

# 使用例
logger = structlog.get_logger(__name__)

# セキュリティイベントのログ記録
logger.warning(
    "認証失敗",
    event="authentication_failed",
    user_email=email,
    ip_address=request.client.host,
    user_agent=request.headers.get("User-Agent"),
    timestamp=datetime.now(UTC).isoformat(),
)
```

#### 2.8.2 セキュリティイベントの記録

**記録すべきセキュリティイベント**:

| イベント | ログレベル | 含めるべき情報 |
|----------|------------|----------------|
| **認証成功** | INFO | user_id, email, ip_address, timestamp |
| **認証失敗** | WARNING | email, ip_address, reason, timestamp |
| **アカウントロック** | WARNING | user_id, failed_attempts, timestamp |
| **権限エラー** | WARNING | user_id, resource, required_permission, timestamp |
| **不正なトークン** | WARNING | token_type, error_reason, ip_address, timestamp |
| **レート制限超過** | WARNING | client_id, limit, current_count, timestamp |
| **データアクセス** | INFO | user_id, resource_type, resource_id, action, timestamp |
| **設定変更** | INFO | admin_id, setting_key, old_value, new_value, timestamp |
| **エラー** | ERROR | error_type, error_message, stack_trace, timestamp |

**実装例**:

```python
# src/app/api/core/dependencies/auth.py
async def get_current_user(
    db: AsyncSession = Depends(get_db),
    user_data = Depends(get_current_user_data),
    request: Request = None,
) -> User:
    """認証済みユーザーを取得"""
    try:
        user = await user_service.get_by_azure_oid(db, user_data.oid)

        if not user:
            # 認証失敗をログ記録
            logger.warning(
                "ユーザーが見つかりません",
                event="user_not_found",
                azure_oid=user_data.oid,
                ip_address=request.client.host if request else "unknown",
                timestamp=datetime.now(UTC).isoformat(),
            )
            raise HTTPException(404, "User not found")

        # 認証成功をログ記録
        logger.info(
            "ユーザー認証成功",
            event="authentication_success",
            user_id=str(user.id),
            email=user.email,
            ip_address=request.client.host if request else "unknown",
            timestamp=datetime.now(UTC).isoformat(),
        )

        return user

    except Exception as e:
        logger.error(
            "認証エラー",
            event="authentication_error",
            error_type=type(e).__name__,
            error_message=str(e),
            timestamp=datetime.now(UTC).isoformat(),
        )
        raise
```

#### 2.8.3 ログの保護

**機密情報のマスキング**:

```python
# src/app/core/logging.py
def mask_sensitive_data(event_dict):
    """機密情報をマスク"""
    sensitive_keys = [
        "password",
        "token",
        "api_key",
        "secret",
        "authorization",
        "credit_card",
    ]

    for key in sensitive_keys:
        if key in event_dict:
            event_dict[key] = "***MASKED***"

    return event_dict

structlog.configure(
    processors=[
        mask_sensitive_data,  # 機密情報マスキング
        # ... その他のプロセッサ
    ]
)
```

---

## 3. 認証セキュリティ実装

### 3.1 Azure AD認証実装

**Azure AD認証フロー**:

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Frontend as フロントエンド
    participant Backend as バックエンド
    participant AzureAD as Azure AD

    User->>Frontend: ログインボタンクリック
    Frontend->>AzureAD: 認証リクエスト
    AzureAD->>User: ログイン画面表示
    User->>AzureAD: 資格情報入力
    AzureAD->>AzureAD: MFA検証（オプション）
    AzureAD->>Frontend: 認証コード返却
    Frontend->>AzureAD: トークンリクエスト
    AzureAD->>Frontend: アクセストークン発行
    Frontend->>Backend: API呼び出し（Bearer Token）
    Backend->>Backend: トークン検証
    Backend->>Backend: ユーザー情報取得/作成
    Backend->>Frontend: APIレスポンス
    Frontend->>User: コンテンツ表示
```

**実装コード**:

```python
# src/app/core/security/azure_ad.py
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer
from fastapi_azure_auth.user import User as AzureUser

# Azure AD認証スキーム初期化
azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.AZURE_CLIENT_ID,
    tenant_id=settings.AZURE_TENANT_ID,
    scopes={
        f"api://{settings.AZURE_CLIENT_ID}/access_as_user": "Access API as user",
    },
    allow_guest_users=False,  # ゲストユーザーを拒否
)

async def get_current_azure_user(
    user: Annotated[AzureUser, Security(get_azure_scheme_dependency, scopes=["access_as_user"])],
) -> AzureUser:
    """Azure ADから認証済みユーザーを取得

    トークン検証内容:
        - JWT署名検証（Azure AD公開鍵）
        - 有効期限チェック（exp）
        - 発行者検証（iss）
        - オーディエンス検証（aud）
        - スコープ検証（scp）
    """
    if not user:
        raise HTTPException(401, "Azure AD authentication failed")
    return user
```

### 3.2 開発モック認証

**開発環境用モック認証**:

```python
# src/app/core/security/dev_auth.py
class DevUser:
    """開発モード用モックユーザー"""

    def __init__(self):
        self.oid = settings.DEV_MOCK_USER_OID
        self.email = settings.DEV_MOCK_USER_EMAIL
        self.name = settings.DEV_MOCK_USER_NAME
        self.roles = []

async def get_current_dev_user(
    credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())
) -> DevUser:
    """開発モード認証（固定トークンチェック）"""
    token = credentials.credentials

    if token != settings.DEV_MOCK_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid development token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return DevUser()
```

**開発トークンの取得方法**:

```bash
# .env.local
DEV_MOCK_TOKEN=mock-access-token-dev-12345

# curlでの使用例
curl -H "Authorization: Bearer mock-access-token-dev-12345" \
     http://localhost:8000/api/v1/users/me
```

### 3.3 認証統合レイヤー

**環境に応じた認証の自動切り替え**:

```python
# src/app/api/core/dependencies/auth.py
from app.core.config import settings

# 認証モードに応じて依存関係を切り替え
if settings.AUTH_MODE == "production":
    from app.core.security.azure_ad import get_current_azure_user as get_user_data
else:
    from app.core.security.dev_auth import get_current_dev_user as get_user_data

async def get_current_user_data():
    """現在の認証モードに応じたユーザーデータ取得"""
    return await get_user_data()

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    user_data = Depends(get_current_user_data),
) -> User:
    """認証済みユーザーをデータベースから取得"""
    if settings.AUTH_MODE == "production":
        # Azure AD OIDでユーザー取得
        user = await user_service.get_by_azure_oid(db, user_data.oid)
    else:
        # 開発モード: メールでユーザー取得
        user = await user_service.get_by_email(db, user_data.email)

    if not user:
        raise HTTPException(404, "User not found")

    return user
```

---

## 4. パスワードセキュリティ

### 4.1 パスワードポリシー

**パスワード強度要件**:

```python
# src/app/core/security/password.py
def validate_password_strength(password: str) -> tuple[bool, str]:
    """パスワード強度を検証

    要件（必須）:
        - 最小8文字
        - 大文字を1つ以上（A-Z）
        - 小文字を1つ以上（a-z）
        - 数字を1つ以上（0-9）

    推奨:
        - 特殊文字を1つ以上（!@#$%^&*(),.?":{}|<>）
        - 12文字以上
    """
    if len(password) < 8:
        return False, "パスワードは8文字以上である必要があります"

    if not re.search(r"[A-Z]", password):
        return False, "パスワードには大文字を含めてください"

    if not re.search(r"[a-z]", password):
        return False, "パスワードには小文字を含めてください"

    if not re.search(r"\d", password):
        return False, "パスワードには数字を含めてください"

    # 特殊文字は推奨（警告のみ）
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        logger.warning("パスワードに特殊文字が含まれていません（推奨）")

    return True, ""
```

### 4.2 パスワードハッシュ化

**bcrypt + SHA-256ハイブリッド方式の詳細**:

```text
┌─────────────────────────────────────────┐
│ 平文パスワード                           │
│ "MySecurePassword123!"                  │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ ステップ1: SHA-256ハッシュ化              │
│ hashlib.sha256(password.encode())       │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ SHA-256ハッシュ（64文字）                 │
│ "a3c5e6f7d8b9a1c2..."                  │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ ステップ2: bcryptハッシュ化               │
│ bcrypt.hashpw(hash, bcrypt.gensalt())   │
│ - ランダムsalt生成                       │
│ - 12ラウンド（2^12 = 4096回計算）        │
└─────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────┐
│ bcryptハッシュ（60文字）                  │
│ "$2b$12$KIX...hash...salt..."          │
└─────────────────────────────────────────┘
                ↓
        データベース保存
```

**なぜSHA-256を使うのか？**:

1. **bcryptの72バイト制限対策**:
   - bcryptは最初の72バイトしか処理しない
   - 日本語などのマルチバイト文字は1文字3-4バイト
   - SHA-256は常に64文字（64バイト）を出力

2. **長いパスワードの安全な処理**:
   - 100文字のパスワードでも安全に処理可能
   - パスワード長によるハッシュの違いを排除

3. **均一な入力長**:
   - bcryptへの入力が常に64文字で一定
   - ハッシュ計算時間の予測可能性

**セキュリティ上の懸念と対応**:

| 懸念 | 対応 |
|------|------|
| SHA-256は高速すぎる | bcryptで2^12回の再ハッシュ化（遅延効果） |
| レインボーテーブル | bcryptのランダムsaltで無効化 |
| 衝突攻撃 | SHA-256の衝突耐性 + bcryptの追加保護 |

### 4.3 パスワードリセット

**セキュアなパスワードリセットフロー**:

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Frontend as フロントエンド
    participant Backend as バックエンド
    participant Email as メールサービス
    participant DB as データベース

    User->>Frontend: パスワードリセット要求
    Frontend->>Backend: POST /api/v1/auth/reset-password
    Backend->>DB: ユーザー存在確認
    Backend->>Backend: リセットトークン生成<br/>（UUID v4, 1時間有効）
    Backend->>DB: トークン保存（ハッシュ化）
    Backend->>Email: リセットリンク送信
    Email->>User: メール受信
    User->>Frontend: リセットリンククリック
    Frontend->>Backend: POST /api/v1/auth/reset-password/confirm
    Backend->>Backend: トークン検証
    Backend->>Backend: 新パスワードハッシュ化
    Backend->>DB: パスワード更新
    Backend->>DB: トークン無効化
    Backend->>Frontend: 成功レスポンス
    Frontend->>User: パスワード変更完了
```

**実装例（将来実装）**:

```python
# src/app/api/routes/v1/auth.py
import secrets
from datetime import timedelta

@router.post("/auth/reset-password")
async def request_password_reset(
    email: EmailStr,
    db: AsyncSession = Depends(get_db),
):
    """パスワードリセット要求"""
    user = await user_service.get_by_email(db, email)

    # タイミング攻撃対策: 常に同じ時間かかるようにする
    if not user:
        await asyncio.sleep(0.1)  # ダミー処理
        return {"message": "If the email exists, a reset link has been sent"}

    # リセットトークン生成（暗号学的に安全）
    reset_token = secrets.token_urlsafe(32)
    reset_token_hash = hashlib.sha256(reset_token.encode()).hexdigest()

    # トークンをデータベースに保存（ハッシュ化）
    user.password_reset_token = reset_token_hash
    user.password_reset_expires = datetime.now(UTC) + timedelta(hours=1)
    await db.commit()

    # リセットリンク送信
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    await email_service.send_password_reset_email(user.email, reset_link)

    logger.info(
        "パスワードリセット要求",
        user_id=str(user.id),
        email=user.email,
    )

    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/auth/reset-password/confirm")
async def confirm_password_reset(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db),
):
    """パスワードリセット確認"""
    # トークンをハッシュ化して検索
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    user = await user_service.get_by_reset_token(db, token_hash)

    if not user or user.password_reset_expires < datetime.now(UTC):
        raise HTTPException(400, "Invalid or expired reset token")

    # パスワード強度検証
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(400, error_msg)

    # 新パスワードをハッシュ化
    user.hashed_password = hash_password(new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    await db.commit()

    logger.info(
        "パスワードリセット完了",
        user_id=str(user.id),
    )

    return {"message": "Password reset successful"}
```

---

## 5. セッション管理

### 5.1 トークンライフサイクル

**トークンの種類と有効期限**:

| トークン種類 | 有効期限 | 用途 | ストレージ |
|-------------|---------|------|-----------|
| **アクセストークン** | 30分 | API呼び出し | メモリ/LocalStorage |
| **リフレッシュトークン** | 7日間 | トークン更新 | HttpOnlyクッキー |
| **パスワードリセット** | 1時間 | パスワードリセット | データベース |
| **メール確認** | 24時間 | メール確認 | データベース |

**トークン更新フロー**:

```mermaid
sequenceDiagram
    participant Client as クライアント
    participant API as API

    Client->>API: リクエスト（アクセストークン）
    API->>API: トークン検証
    API-->>Client: 401 Unauthorized<br/>（トークン期限切れ）
    Client->>API: POST /auth/refresh<br/>（リフレッシュトークン）
    API->>API: リフレッシュトークン検証
    API-->>Client: 新アクセストークン + 新リフレッシュトークン
    Client->>API: リクエスト（新アクセストークン）
    API-->>Client: 成功レスポンス
```

### 5.2 トークン無効化

**トークンブラックリスト実装（Redis使用）**:

```python
# src/app/core/cache.py
class CacheManager:
    async def blacklist_token(self, token: str, ttl: int):
        """トークンをブラックリストに追加"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        await self._redis.setex(
            f"blacklist:token:{token_hash}",
            ttl,
            "1"
        )

    async def is_token_blacklisted(self, token: str) -> bool:
        """トークンがブラックリストにあるかチェック"""
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        result = await self._redis.get(f"blacklist:token:{token_hash}")
        return result is not None

# 使用例: ログアウト
@router.post("/auth/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    token: str = Depends(get_current_token),
    cache: CacheManager = Depends(get_cache),
):
    """ログアウト（トークン無効化）"""
    # トークンをブラックリストに追加（残り有効期限分）
    payload = decode_access_token(token)
    if payload:
        ttl = int(payload["exp"] - datetime.now(UTC).timestamp())
        await cache.blacklist_token(token, ttl)

    logger.info("ログアウト", user_id=str(current_user.id))
    return {"message": "Logged out successfully"}
```

---

## 6. 入力検証とサニタイゼーション

### 6.1 Pydanticによる入力検証

**基本的な検証パターン**:

```python
# src/app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field, ConfigDict
import uuid

class UserCreate(BaseModel):
    """ユーザー作成スキーマ（入力検証）"""

    # メールアドレス: 自動フォーマット検証
    email: EmailStr = Field(
        description="メールアドレス",
        examples=["user@example.com"],
    )

    # パスワード: 長さ制限
    password: str = Field(
        min_length=8,
        max_length=128,
        description="パスワード（8文字以上）",
    )

    # 表示名: 長さ制限、パターン
    display_name: str = Field(
        min_length=1,
        max_length=100,
        description="表示名",
        pattern=r"^[a-zA-Z0-9\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+$",
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,  # 前後の空白を自動削除
        str_min_length=1,  # 空文字列を拒否
    )
```

**高度な検証パターン**:

```python
from pydantic import field_validator, model_validator
from typing import Annotated

class ProjectFileCreate(BaseModel):
    """プロジェクトファイル作成スキーマ"""

    filename: str = Field(min_length=1, max_length=255)
    file_size: int = Field(gt=0, le=100*1024*1024)  # 最大100MB
    file_type: str
    project_id: uuid.UUID

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        """ファイル名の安全性を検証"""
        # パストラバーサル攻撃対策
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Filename contains invalid characters")

        # 許可された拡張子のチェック
        allowed_extensions = {".pdf", ".docx", ".xlsx", ".txt", ".csv"}
        ext = Path(v).suffix.lower()
        if ext not in allowed_extensions:
            raise ValueError(f"File type {ext} is not allowed")

        return v

    @field_validator("file_type")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        """MIMEタイプを検証"""
        allowed_types = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "text/plain",
            "text/csv",
        }
        if v not in allowed_types:
            raise ValueError(f"File type {v} is not allowed")
        return v

    @model_validator(mode="after")
    def validate_file_size_by_type(self) -> "ProjectFileCreate":
        """ファイルタイプに応じたサイズ制限"""
        max_sizes = {
            "application/pdf": 50 * 1024 * 1024,  # 50MB
            "text/plain": 10 * 1024 * 1024,  # 10MB
            "text/csv": 10 * 1024 * 1024,  # 10MB
        }

        max_size = max_sizes.get(self.file_type, 5 * 1024 * 1024)
        if self.file_size > max_size:
            raise ValueError(
                f"File size {self.file_size} exceeds limit {max_size} for type {self.file_type}"
            )

        return self
```

### 6.2 パストラバーサル対策

**安全なファイルパス処理**:

```python
from pathlib import Path

def safe_join_path(base_path: str, *paths: str) -> Path:
    """安全にパスを結合（パストラバーサル対策）

    Args:
        base_path: ベースディレクトリ
        *paths: 結合するパス要素

    Returns:
        Path: 安全に結合されたパス

    Raises:
        ValueError: パストラバーサル攻撃を検出した場合
    """
    base = Path(base_path).resolve()
    target = (base / Path(*paths)).resolve()

    # ベースパスの外にあるかチェック
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError("Path traversal attempt detected")

    return target

# 使用例
@router.get("/files/{filename}")
async def download_file(filename: str):
    try:
        # ❌ 脆弱: file_path = f"/data/{filename}"
        # ✅ セキュア:
        file_path = safe_join_path("/data", filename)

        if not file_path.exists():
            raise HTTPException(404, "File not found")

        return FileResponse(file_path)

    except ValueError as e:
        logger.warning(
            "パストラバーサル攻撃検出",
            filename=filename,
            error=str(e),
        )
        raise HTTPException(400, "Invalid filename")
```

### 6.3 XSS対策

**HTMLエスケープ**:

```python
import html

def sanitize_html_output(text: str) -> str:
    """HTMLを安全にエスケープ（XSS対策）"""
    return html.escape(text)

# 使用例
class MessageResponse(BaseModel):
    message: str

    @field_validator("message")
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        """メッセージをサニタイズ"""
        return html.escape(v)
```

**Content-Security-Policy（CSP）ヘッダー**:

```python
# src/app/api/middlewares/security_headers.py
response.headers["Content-Security-Policy"] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data: https:; "
    "font-src 'self' data:; "
    "connect-src 'self'"
)
```

---

## 7. APIセキュリティ

### 7.1 レート制限

**Redis Sorted Setによるスライディングウィンドウ実装**:

```python
# src/app/api/middlewares/rate_limit.py
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Redisベースのレート制限ミドルウェア

    アルゴリズム: スライディングウィンドウ
    - デフォルト: 100リクエスト/60秒
    - クライアント識別: user_id > API key > IP address
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_id = self._get_client_identifier(request)
        cache_key = f"rate_limit:{client_id}"

        current_time = int(time.time())
        window_start = current_time - self.period

        # 古いエントリを削除
        await cache_manager._redis.zremrangebyscore(cache_key, 0, window_start)

        # 現在のリクエスト数をカウント
        request_count = await cache_manager._redis.zcard(cache_key)

        if request_count >= self.calls:
            # レート制限超過
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "details": {
                        "limit": self.calls,
                        "period": self.period,
                        "retry_after": self.period,
                    },
                },
                headers={"Retry-After": str(self.period)},
            )

        # 新しいリクエストを追加
        request_id = f"{current_time}:{hashlib.sha256(str(time.time()).encode()).hexdigest()}"
        await cache_manager._redis.zadd(cache_key, {request_id: current_time})
        await cache_manager._redis.expire(cache_key, self.period)

        # リクエストを処理
        response = await call_next(request)

        # レート制限ヘッダーを追加
        remaining = max(0, self.calls - request_count - 1)
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(current_time + self.period)

        return response
```

**レート制限のカスタマイズ**:

```python
# src/app/core/config.py
class Settings(BaseSettings):
    # レート制限設定
    RATE_LIMIT_CALLS: int = Field(default=100, description="リクエスト制限数")
    RATE_LIMIT_PERIOD: int = Field(default=60, description="制限期間（秒）")

    # 環境別設定
    # 開発: 1000req/min（緩い制限）
    # ステージング: 100req/min
    # 本番: 100req/min（厳格な制限）
```

### 7.2 CORS設定

**CORSポリシーの実装**:

```python
# src/app/core/app_factory.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # 許可するオリジン
    allow_credentials=True,  # クッキー送信を許可
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],  # 許可するメソッド
    allow_headers=[
        "Accept",
        "Content-Type",
        "Authorization",
        "X-API-Key",
    ],  # 許可するヘッダー
)
```

**環境別CORS設定**:

```bash
# .env.local（開発環境）
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:5173"]

# .env.production（本番環境）
ALLOWED_ORIGINS=["https://example.com", "https://app.example.com"]
```

### 7.3 APIバージョニング

**バージョニング戦略**:

```python
# URLパスベースのバージョニング
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(projects.router, prefix="/api/v1/projects", tags=["projects"])

# 将来のバージョン
# app.include_router(users_v2.router, prefix="/api/v2/users", tags=["users-v2"])
```

**非推奨エンドポイントの処理**:

```python
from fastapi import Header

@router.get("/legacy-endpoint", deprecated=True)
async def legacy_endpoint(
    warning: str = Header(default=None, alias="X-API-Warning")
):
    """非推奨エンドポイント（v2で削除予定）

    警告ヘッダーを返却:
        X-API-Warning: This endpoint is deprecated. Use /api/v2/new-endpoint instead.
    """
    return Response(
        content=json.dumps({"data": "legacy"}),
        headers={
            "X-API-Warning": "This endpoint is deprecated. Use /api/v2/new-endpoint instead.",
            "X-API-Sunset": "2025-12-31",  # 廃止予定日
        },
    )
```

---

## 8. データ保護

### 8.1 データベースセキュリティ

**SQLAlchemyセキュリティ設定**:

```python
# src/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

# セキュアな接続設定
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 本番環境ではFalse
    pool_pre_ping=True,  # 接続健全性チェック
    pool_size=settings.DB_POOL_SIZE,  # 接続プールサイズ
    max_overflow=settings.DB_MAX_OVERFLOW,  # 最大追加接続数
    pool_recycle=settings.DB_POOL_RECYCLE,  # 接続の再利用期限（秒）
    connect_args={
        "ssl": "require" if settings.ENVIRONMENT == "production" else None,
        "server_settings": {
            "application_name": f"{settings.APP_NAME}-{settings.ENVIRONMENT}",
        },
    },
)
```

**データベース接続文字列のセキュリティ**:

```bash
# ❌ 脆弱: パスワードが平文
DATABASE_URL=postgresql://user:password@localhost:5432/db

# ✅ セキュア: 環境変数または Azure Key Vault
DATABASE_URL=${DB_CONNECTION_STRING}
```

### 8.2 機密データの保護

**機密データのフィールドレベル暗号化**（将来実装）:

```python
# src/app/models/mixins/encryption.py
from cryptography.fernet import Fernet

class EncryptedFieldMixin:
    """フィールドレベル暗号化ミックスイン"""

    @staticmethod
    def encrypt_value(value: str) -> str:
        """値を暗号化"""
        f = Fernet(settings.ENCRYPTION_KEY)
        return f.encrypt(value.encode()).decode()

    @staticmethod
    def decrypt_value(encrypted: str) -> str:
        """値を復号化"""
        f = Fernet(settings.ENCRYPTION_KEY)
        return f.decrypt(encrypted.encode()).decode()

# 使用例
class SensitiveData(Base, EncryptedFieldMixin):
    __tablename__ = "sensitive_data"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    _encrypted_field: Mapped[str] = mapped_column("encrypted_field")

    @property
    def encrypted_field(self) -> str:
        """暗号化フィールドを復号化して取得"""
        return self.decrypt_value(self._encrypted_field)

    @encrypted_field.setter
    def encrypted_field(self, value: str):
        """値を暗号化して保存"""
        self._encrypted_field = self.encrypt_value(value)
```

### 8.3 データマスキング

**ログ出力時のデータマスキング**:

```python
def mask_sensitive_fields(data: dict) -> dict:
    """機密フィールドをマスク"""
    sensitive_keys = {
        "password",
        "token",
        "api_key",
        "secret",
        "authorization",
        "ssn",  # 社会保障番号
        "credit_card",
        "cvv",
    }

    masked_data = data.copy()
    for key in masked_data:
        if key.lower() in sensitive_keys:
            masked_data[key] = "***MASKED***"
        elif isinstance(masked_data[key], dict):
            masked_data[key] = mask_sensitive_fields(masked_data[key])

    return masked_data

# API レスポンスのマスキング
class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    display_name: str
    # パスワードフィールドは含めない（モデルから除外）

    model_config = ConfigDict(
        from_attributes=True,
        # 機密フィールドを除外
        json_schema_extra={
            "exclude": {"hashed_password", "password_reset_token"}
        }
    )
```

---

## 9. 監査ログとモニタリング

### 9.1 監査ログの実装

**監査ログテーブル設計**（将来実装）:

```python
# src/app/models/audit_log.py
from sqlalchemy.dialects.postgresql import JSONB

class AuditLog(Base):
    """監査ログテーブル"""
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    timestamp: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))

    # アクション情報
    event_type: Mapped[str] = mapped_column(String(50))  # 例: "user.login", "project.delete"
    action: Mapped[str] = mapped_column(String(20))  # 例: "create", "read", "update", "delete"
    resource_type: Mapped[str] = mapped_column(String(50))  # 例: "user", "project", "file"
    resource_id: Mapped[str | None] = mapped_column(String(100))

    # ユーザー情報
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    user_email: Mapped[str | None] = mapped_column(String(255))
    user_ip: Mapped[str | None] = mapped_column(String(45))  # IPv6対応
    user_agent: Mapped[str | None] = mapped_column(Text)

    # リクエスト情報
    http_method: Mapped[str | None] = mapped_column(String(10))
    endpoint: Mapped[str | None] = mapped_column(String(255))
    status_code: Mapped[int | None] = mapped_column()

    # 詳細情報
    details: Mapped[dict | None] = mapped_column(JSONB)  # 追加のコンテキスト情報

    # 結果
    success: Mapped[bool] = mapped_column(default=True)
    error_message: Mapped[str | None] = mapped_column(Text)
```

**監査ログ記録関数**:

```python
# src/app/core/audit.py
async def create_audit_log(
    db: AsyncSession,
    event_type: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    user: User | None = None,
    request: Request | None = None,
    success: bool = True,
    error_message: str | None = None,
    details: dict | None = None,
):
    """監査ログを作成"""
    audit_log = AuditLog(
        event_type=event_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user.id if user else None,
        user_email=user.email if user else None,
        user_ip=request.client.host if request else None,
        user_agent=request.headers.get("User-Agent") if request else None,
        http_method=request.method if request else None,
        endpoint=str(request.url.path) if request else None,
        success=success,
        error_message=error_message,
        details=details,
    )

    db.add(audit_log)
    await db.commit()

    # 構造化ログにも記録
    logger.info(
        "監査ログ",
        event_type=event_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=str(user.id) if user else None,
        success=success,
    )

# 使用例
@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None,
):
    """プロジェクト削除"""
    project = await project_service.get_by_id(db, project_id)

    # 権限チェック
    # ...

    try:
        await project_service.delete(db, project_id)

        # 監査ログ記録（成功）
        await create_audit_log(
            db=db,
            event_type="project.delete",
            action="delete",
            resource_type="project",
            resource_id=str(project_id),
            user=current_user,
            request=request,
            success=True,
            details={"project_name": project.name},
        )

        return {"message": "Project deleted"}

    except Exception as e:
        # 監査ログ記録（失敗）
        await create_audit_log(
            db=db,
            event_type="project.delete",
            action="delete",
            resource_type="project",
            resource_id=str(project_id),
            user=current_user,
            request=request,
            success=False,
            error_message=str(e),
        )
        raise
```

### 9.2 セキュリティモニタリング

**Prometheusメトリクス**:

```python
# src/app/api/middlewares/metrics.py
from prometheus_client import Counter, Histogram

# セキュリティ関連メトリクス
security_events_total = Counter(
    "security_events_total",
    "セキュリティイベント総数",
    ["event_type", "severity"],
)

authentication_attempts_total = Counter(
    "authentication_attempts_total",
    "認証試行総数",
    ["result", "method"],
)

authorization_failures_total = Counter(
    "authorization_failures_total",
    "認可失敗総数",
    ["resource_type", "required_permission"],
)

# 使用例
async def get_current_user(...):
    try:
        user = await user_service.get_by_azure_oid(db, user_data.oid)

        # 認証成功メトリクス
        authentication_attempts_total.labels(
            result="success",
            method="azure_ad"
        ).inc()

        return user

    except HTTPException:
        # 認証失敗メトリクス
        authentication_attempts_total.labels(
            result="failure",
            method="azure_ad"
        ).inc()

        security_events_total.labels(
            event_type="authentication_failure",
            severity="warning"
        ).inc()

        raise
```

**アラート設定（Prometheus AlertManager）**:

```yaml
# prometheus/alerts.yml
groups:
  - name: security_alerts
    interval: 1m
    rules:
      # 認証失敗率が高い
      - alert: HighAuthenticationFailureRate
        expr: |
          rate(authentication_attempts_total{result="failure"}[5m]) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "高頻度の認証失敗を検出"
          description: "過去5分間で{{ $value }}回/秒の認証失敗が発生しています"

      # レート制限超過が多い
      - alert: HighRateLimitExceeded
        expr: |
          rate(http_requests_total{status_code="429"}[5m]) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "レート制限超過が頻発"
          description: "過去5分間で{{ $value }}回/秒のレート制限超過が発生しています"

      # 権限エラーが多い
      - alert: HighAuthorizationFailureRate
        expr: |
          rate(authorization_failures_total[5m]) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "権限エラーが頻発"
          description: "過去5分間で{{ $value }}回/秒の権限エラーが発生しています"
```

---

## 10. セキュリティテスト

### 10.1 セキュリティテスト戦略

**テストピラミッド**:

```text
         △
        /|△\
       / | △ \
      /  |  △  \
     /   |   △   \
    /____|____△____\

   △ ペネトレーションテスト（手動）
   △ セキュリティスキャン（OWASP ZAP）
   △ 統合テスト（認証・認可フロー）
   △ ユニットテスト（個別セキュリティ機能）
```

### 10.2 ユニットテスト

**パスワードハッシュ化のテスト**:

```python
# tests/app/core/security/test_password.py
import pytest
from app.core.security.password import hash_password, verify_password, validate_password_strength

def test_hash_password():
    """パスワードハッシュ化のテスト"""
    password = "SecurePass123!"
    hashed = hash_password(password)

    # ハッシュがbcrypt形式であることを確認
    assert hashed.startswith("$2b$")
    assert len(hashed) == 60

    # 同じパスワードでも異なるハッシュが生成される（salt）
    hashed2 = hash_password(password)
    assert hashed != hashed2

def test_verify_password():
    """パスワード検証のテスト"""
    password = "SecurePass123!"
    hashed = hash_password(password)

    # 正しいパスワード
    assert verify_password(password, hashed) is True

    # 間違ったパスワード
    assert verify_password("WrongPassword", hashed) is False

def test_validate_password_strength():
    """パスワード強度検証のテスト"""
    # 弱いパスワード
    is_valid, error = validate_password_strength("pass")
    assert is_valid is False
    assert "8文字以上" in error

    # 大文字なし
    is_valid, error = validate_password_strength("password123")
    assert is_valid is False
    assert "大文字" in error

    # 強いパスワード
    is_valid, error = validate_password_strength("SecurePass123!")
    assert is_valid is True
    assert error == ""

def test_long_password_with_multibyte():
    """長いパスワードとマルチバイト文字のテスト"""
    # 日本語を含む長いパスワード
    password = "これは非常に長いパスワードですSecure123!あいうえお" * 3
    hashed = hash_password(password)

    # 正しく検証できることを確認
    assert verify_password(password, hashed) is True
```

**認証テスト**:

```python
# tests/app/api/test_auth.py
import pytest
from httpx import AsyncClient
from app.core.security.jwt import create_access_token

@pytest.mark.asyncio
async def test_get_current_user_success(client: AsyncClient, test_user):
    """認証済みユーザー取得のテスト（成功）"""
    # アクセストークン生成
    token = create_access_token({"sub": str(test_user.id)})

    # 認証ヘッダー付きでリクエスト
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(client: AsyncClient):
    """無効なトークンのテスト"""
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer invalid-token"}
    )

    assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_expired_token(client: AsyncClient, test_user):
    """期限切れトークンのテスト"""
    from datetime import timedelta

    # 期限切れトークン（-1秒）
    token = create_access_token(
        {"sub": str(test_user.id)},
        expires_delta=timedelta(seconds=-1)
    )

    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 401
```

**RBAC権限テスト**:

```python
# tests/app/api/test_rbac.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_project_access_with_viewer_role(
    client: AsyncClient,
    test_user,
    test_project,
    test_project_member_viewer,
):
    """VIEWER権限のテスト（読み取りのみ）"""
    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # 読み取り: 成功
    response = await client.get(
        f"/api/v1/projects/{test_project.id}",
        headers=headers
    )
    assert response.status_code == 200

    # 更新: 失敗（権限不足）
    response = await client.put(
        f"/api/v1/projects/{test_project.id}",
        headers=headers,
        json={"name": "Updated Name"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_project_access_without_membership(
    client: AsyncClient,
    test_user,
    other_project,
):
    """プロジェクトメンバー以外のアクセステスト"""
    token = create_access_token({"sub": str(test_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # メンバーでないプロジェクトへのアクセス: 失敗
    response = await client.get(
        f"/api/v1/projects/{other_project.id}",
        headers=headers
    )
    assert response.status_code == 403
```

### 10.3 セキュリティスキャン

**OWASP ZAP統合**:

```bash
# scripts/security-scan.sh
#!/bin/bash

# OWASP ZAPを使用した自動セキュリティスキャン
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://localhost:8000 \
  -r zap-report.html \
  -J zap-report.json
```

**依存関係の脆弱性スキャン**:

```bash
# Pipenvによる脆弱性チェック
pipenv check

# Safety（PyPIパッケージの脆弱性チェック）
safety check --file requirements.txt

# Bandit（Pythonコードの静的解析）
bandit -r src/ -f json -o bandit-report.json
```

### 10.4 ペネトレーションテスト

**テストシナリオ**:

| シナリオ | 目的 | 期待結果 |
|----------|------|----------|
| **SQLインジェクション** | ORMの安全性確認 | すべてのクエリがパラメータ化されている |
| **XSS攻撃** | 入力検証とエスケープ確認 | HTMLタグがエスケープされている |
| **CSRF攻撃** | トークン検証確認 | 無効なトークンでリクエスト拒否 |
| **権限昇格** | RBAC実装確認 | 下位ロールが上位権限操作を拒否される |
| **パストラバーサル** | ファイルパス検証確認 | ベースディレクトリ外へのアクセス拒否 |
| **ブルートフォース** | レート制限確認 | 連続失敗でアカウントロック |

---

## 11. 付録

### 11.1 セキュリティチェックリスト

**デプロイ前チェックリスト**:

- [ ] **認証**
  - [ ] Azure AD認証が正しく設定されている
  - [ ] トークンの有効期限が適切（30分以内）
  - [ ] リフレッシュトークンが実装されている
  - [ ] 開発モード認証が無効化されている（本番環境）

- [ ] **認可**
  - [ ] すべてのAPIエンドポイントで権限チェックが実装されている
  - [ ] RBACが正しく機能している
  - [ ] IDOR脆弱性が存在しない

- [ ] **データ保護**
  - [ ] パスワードがbcryptでハッシュ化されている
  - [ ] 機密データが暗号化されている
  - [ ] HTTPS/TLSが強制されている（HSTS）
  - [ ] データベース接続がSSLで暗号化されている

- [ ] **入力検証**
  - [ ] すべての入力がPydanticで検証されている
  - [ ] SQLインジェクション対策が実装されている
  - [ ] XSS対策が実装されている
  - [ ] パストラバーサル対策が実装されている

- [ ] **APIセキュリティ**
  - [ ] レート制限が有効化されている
  - [ ] CORSが適切に設定されている
  - [ ] セキュリティヘッダーが設定されている
  - [ ] APIキーが環境変数で管理されている

- [ ] **監視**
  - [ ] 監査ログが実装されている
  - [ ] セキュリティイベントがログ記録されている
  - [ ] アラートが設定されている
  - [ ] ログが適切に保護されている

- [ ] **設定**
  - [ ] DEBUGモードが無効化されている
  - [ ] SECRET_KEYが32文字以上でランダム
  - [ ] 環境変数が適切に設定されている
  - [ ] デフォルトパスワードが変更されている

### 11.2 インシデント対応手順

**セキュリティインシデント発生時の手順**:

1. **検出と評価**（0-15分）
   - アラート確認
   - 影響範囲の特定
   - 重要度の評価（Critical/High/Medium/Low）

2. **封じ込め**（15-60分）
   - 攻撃の遮断（ファイアウォールルール、IPブロック）
   - 侵害されたアカウントの無効化
   - 影響を受けたサービスの隔離

3. **根絶**（1-4時間）
   - 脆弱性の修正
   - マルウェアの削除
   - 侵入経路の特定と閉鎖

4. **復旧**（4-24時間）
   - サービスの段階的復旧
   - データの復元（必要な場合）
   - 監視の強化

5. **事後分析**（1-7日）
   - インシデントレポート作成
   - 再発防止策の策定
   - セキュリティ対策の改善

### 11.3 セキュリティ連絡先

**セキュリティ問題の報告**:

- **メール**: <security@example.com>
- **PGP公開鍵**: <https://example.com/.well-known/pgp-key.txt>
- **バグバウンティ**: <https://example.com/security/bounty>

**報告テンプレート**:

```markdown
# セキュリティ脆弱性報告

## 報告者情報
- 氏名: [氏名]
- メール: [メールアドレス]
- 報告日: [YYYY-MM-DD]

## 脆弱性の詳細
- **タイトル**: [脆弱性の簡潔な説明]
- **重要度**: [Critical/High/Medium/Low]
- **影響を受けるバージョン**: [バージョン番号]
- **脆弱性の種類**: [SQLインジェクション、XSS、など]

## 再現手順
1. [ステップ1]
2. [ステップ2]
3. [ステップ3]

## 影響
[この脆弱性による影響の説明]

## 推奨される修正方法
[修正方法の提案（オプション）]

## スクリーンショット/ログ
[証拠となるスクリーンショットやログ（オプション）]
```

### 11.4 参考資料

**セキュリティ標準とベストプラクティス**:

- [OWASP Top 10 (2021)](https://owasp.org/Top10/)
- [OWASP Application Security Verification Standard (ASVS)](https://owasp.org/www-project-application-security-verification-standard/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/controls)
- [SANS Top 25](https://www.sans.org/top25-software-errors/)

**Python/FastAPIセキュリティリソース**:

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Python Security](https://owasp.org/www-project-python-security/)
- [Pydantic Security Best Practices](https://docs.pydantic.dev/latest/security/)

**Azure AD セキュリティ**:

- [Microsoft Identity Platform Best Practices](https://docs.microsoft.com/en-us/azure/active-directory/develop/identity-platform-integration-checklist)
- [Azure Security Best Practices](https://docs.microsoft.com/en-us/azure/security/fundamentals/best-practices-and-patterns)

---

## 変更履歴

| バージョン | 日付 | 変更内容 | 作成者 |
|-----------|------|----------|--------|
| 1.0.0 | 2025-01-11 | 初版作成 | Claude Code |

---
