# セキュリティベストプラクティス

APIのセキュリティ対策について説明します。

## OWASP Top 10対策

### 1. インジェクション対策

```python
# ✅ SQLAlchemyのORMを使用（自動エスケープ）
query = select(SampleUser).where(SampleUser.email == email)

# ❌ 生SQL（SQLインジェクションの危険）
query = f"SELECT * FROM users WHERE email = '{email}'"
```

### 2. 認証の実装

```python
# JWT認証を実装
# パスワードはbcryptでハッシュ化
# トークンの有効期限を設定
```

### 3. 機密データの保護

```python
# ✅ パスワードは返さない
class SampleUserResponse(BaseModel):
    id: int
    email: str
    username: str
    # hashed_password は含めない

# ✅ 環境変数で機密情報を管理
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
```

## CORS設定

```python
# src/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://example.com"],  # 本番環境では特定のオリジンのみ
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## レート制限

```python
# src/app/api/middlewares/rate_limit.py
from fastapi import Request, HTTPException
from collections import defaultdict
import time

# シンプルなレート制限実装
request_counts = defaultdict(list)
RATE_LIMIT = 100  # 1分間に100リクエスト
TIME_WINDOW = 60  # 60秒


async def rate_limit_middleware(request: Request, call_next):
    """レート制限ミドルウェア。"""
    client_ip = request.client.host
    current_time = time.time()

    # 古いリクエストを削除
    request_counts[client_ip] = [
        t for t in request_counts[client_ip]
        if current_time - t < TIME_WINDOW
    ]

    # レート制限チェック
    if len(request_counts[client_ip]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Too many requests"
        )

    # リクエストを記録
    request_counts[client_ip].append(current_time)

    return await call_next(request)
```

## 入力バリデーション

```python
from pydantic import BaseModel, Field, field_validator


class SampleUserCreate(BaseModel):
    email: EmailStr  # メール形式を検証
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """パスワード強度を検証。"""
        if not any(c.isdigit() for c in v):
            raise ValueError("数字を含める必要があります")
        if not any(c.isupper() for c in v):
            raise ValueError("大文字を含める必要があります")
        return v
```

## HTTPSの使用

```powershell
# 本番環境ではHTTPSを使用
uvicorn app.main:app --host 0.0.0.0 --port 443 --ssl-keyfile key.pem --ssl-certfile cert.pem
```

## セキュリティヘッダー

```python
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """セキュリティヘッダーを追加。"""

    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)
```

## 環境変数管理

```python
# .env ファイル（gitignoreに追加）
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30


# src/app/core/config.py
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """環境変数から設定を読み込み。"""
    SECRET_KEY: str
    DATABASE_URL: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = ConfigDict(env_file=".env")


settings = Settings()
```

## セキュリティチェックリスト

- [ ] パスワードはbcryptでハッシュ化
- [ ] JWT認証を実装
- [ ] HTTPS を使用
- [ ] CORS を適切に設定
- [ ] レート制限を実装
- [ ] 入力バリデーションを徹底
- [ ] 機密情報を環境変数で管理
- [ ] SQLインジェクション対策（ORMを使用）
- [ ] XSS対策（自動エスケープ）
- [ ] CSRF対策（必要に応じて）
- [ ] セキュリティヘッダーを設定
- [ ] エラーメッセージで内部情報を漏らさない
- [ ] ログに機密情報を含めない

## 参考リンク

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Best Practices](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
