# 認証実装

JWT、OAuth2、パスワードハッシュを使用した認証について説明します。

## パスワードハッシュ化

```python
# src/app/core/security.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """パスワードをハッシュ化。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """パスワードを検証。"""
    return pwd_context.verify(plain_password, hashed_password)


# 使用例
hashed = hash_password("mypassword123")
is_valid = verify_password("mypassword123", hashed)  # True
```

## JWTトークン生成

```python
from datetime import datetime, timedelta, timezone
from jose import jwt

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """JWTアクセストークンを作成。"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict | None:
    """JWTトークンをデコード。"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.JWTError:
        return None
```

## 認証エンドポイント

```python
# src/app/api/routes/auth.py
from fastapi import APIRouter, Depends
from app.schemas.user import UserLogin, Token
from app.api.dependencies import UserServiceDep
from app.core.security import create_access_token

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(
    login_data: UserLogin,
    user_service: UserServiceDep,
) -> Token:
    """ログイン。"""
    # ユーザー認証
    user = await user_service.authenticate(
        login_data.email,
        login_data.password
    )

    # トークン生成
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return Token(access_token=access_token, token_type="bearer")
```

## 認証依存性

```python
# src/app/api/dependencies.py
from fastapi import Depends, Header, HTTPException
from app.core.security import decode_access_token


async def get_current_user(
    authorization: str | None = Header(None),
    user_service: UserServiceDep = None,
) -> User:
    """現在の認証済みユーザーを取得。"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # "Bearer <token>" から token を抽出
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    # トークンデコード
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    # ユーザー取得
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = await user_service.get_user(int(user_id))
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


# 使用例
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUserDep) -> UserResponse:
    """現在のユーザー情報を取得。"""
    return UserResponse.model_validate(current_user)
```

## 参考リンク

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/)
- [Passlib Documentation](https://passlib.readthedocs.io/)
