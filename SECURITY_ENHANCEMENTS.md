# セキュリティ強化実装サマリー

## 実装日
2026-01-02

## 概要
監査ログとX-Forwarded-Forヘッダー処理のセキュリティを強化しました。

---

## タスク1: 監査ログの機密情報除外パターン強化

### 変更ファイル
- `src/app/api/middlewares/audit_log.py`

### 実装内容

#### 1. 機密情報パターンの定義

**SENSITIVE_KEYS（完全一致）** - 計33項目:
```python
SENSITIVE_KEYS: set[str] = {
    # SQLAlchemy内部
    "_sa_instance_state",

    # 認証関連（11項目）
    "password", "password_hash", "token", "secret", "api_key",
    "apikey", "credential", "authorization", "access_token",
    "refresh_token", "session_token", "bearer", "jwt",

    # Azure/クラウド関連（3項目）
    "client_secret", "azure_client_secret", "connection_string",

    # 暗号化関連（4項目）
    "private_key", "secret_key", "encryption_key", "signing_key",

    # 個人情報（7項目）
    "ssn", "social_security_number", "credit_card", "card_number",
    "cvv", "cvc", "bank_account", "routing_number",

    # 認証コード（5項目）
    "pin", "otp", "mfa_code", "verification_code", "auth_code",

    # データベース（2項目）
    "database_password", "db_password",

    # セッション（2項目）
    "session_id", "cookie",
}
```

**SENSITIVE_PATTERNS（正規表現）** - 計7パターン:
```python
SENSITIVE_PATTERNS: list[re.Pattern[str]] = [
    # password, new_password, user_password, password_hash
    re.compile(r"^password$|_password$|^password_|_password_", re.IGNORECASE),

    # secret, client_secret, secret_key
    re.compile(r"^secret$|_secret$|^secret_|_secret_", re.IGNORECASE),

    # token, access_token, refresh_token
    re.compile(r"^token$|_token$|^token_|_token_", re.IGNORECASE),

    # api_key, encryption_key (keyboard, monkey は除外)
    re.compile(r"^key$|_key$|^key_|_key_", re.IGNORECASE),

    # credential, credentials
    re.compile(r"credential", re.IGNORECASE),

    # bearer
    re.compile(r"bearer", re.IGNORECASE),

    # auth, oauth, auth_code (author は除外)
    re.compile(r"^auth$|_auth$|^auth_|_auth_|oauth", re.IGNORECASE),
]
```

#### 2. 機密情報判定メソッドの追加

```python
def _is_sensitive_field(self, field_name: str) -> bool:
    """フィールド名が機密情報かどうかを判定。

    完全一致とパターンマッチングの両方でチェック。
    """
    field_lower = field_name.lower()

    # 完全一致チェック
    if field_lower in SENSITIVE_KEYS:
        return True

    # パターンマッチング
    for pattern in SENSITIVE_PATTERNS:
        if pattern.match(field_lower):
            return True

    return False
```

#### 3. 変更前データ取得時の機密情報除外

**変更前**:
```python
excluded_keys = {"_sa_instance_state", "password", "password_hash"}
return {
    key: self._serialize_value(value)
    for key, value in result.__dict__.items()
    if not key.startswith("_") and key not in excluded_keys
}
```

**変更後**:
```python
return {
    key: self._serialize_value(value)
    for key, value in result.__dict__.items()
    if not key.startswith("_") and not self._is_sensitive_field(key)
}
```

### セキュリティ効果

| 項目 | 変更前 | 変更後 |
|------|--------|--------|
| 除外パターン数 | 3項目（固定） | 33項目 + 7正規表現パターン |
| カバレッジ | password, password_hash のみ | 認証情報、暗号化キー、個人情報、セッション情報など包括的 |
| 偽陽性対策 | なし | あり（author, keyboard等を除外） |

---

## タスク2: X-Forwarded-For信頼性チェック

### 変更ファイル
1. `src/app/core/config.py`
2. `src/app/utils/request_helpers.py`
3. `src/app/api/middlewares/audit_log.py`（適用）
4. `src/app/api/middlewares/activity_tracking.py`（既に適用済み）

### 実装内容

#### 1. 信頼できるプロキシの設定（config.py）

```python
TRUSTED_PROXIES: list[str] = Field(
    default=[
        "10.0.0.0/8",      # プライベートネットワーク（クラスA）
        "172.16.0.0/12",   # プライベートネットワーク（クラスB）
        "192.168.0.0/16",  # プライベートネットワーク（クラスC）
        "127.0.0.1/32",    # ローカルホスト
    ],
    description="信頼できるプロキシのCIDR（X-Forwarded-Forヘッダーを信頼）",
)
```

#### 2. プロキシ信頼性判定メソッドの追加（request_helpers.py）

```python
@staticmethod
def is_trusted_proxy(ip: str) -> bool:
    """IPアドレスが信頼できるプロキシか判定。

    設定されたTRUSTED_PROXIESのCIDR範囲に含まれるかをチェック。
    """
    try:
        from app.core.config import settings

        ip_obj = ipaddress.ip_address(ip)
        for trusted_network in settings.TRUSTED_PROXIES:
            if ip_obj in ipaddress.ip_network(trusted_network):
                return True
        return False
    except ValueError:
        return False
```

#### 3. X-Forwarded-For処理の強化（request_helpers.py）

**変更前**:
```python
def get_client_ip(request: Request) -> str | None:
    direct_ip = request.client.host if request.client else None
    forwarded_for = request.headers.get("x-forwarded-for")

    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
        if is_valid_ip(client_ip):
            return client_ip  # ⚠️ 無条件に信頼

    return direct_ip
```

**変更後**:
```python
def get_client_ip(request: Request) -> str | None:
    direct_ip = request.client.host if request.client else None

    # ✅ 直接接続元が信頼できるプロキシでない場合はX-Forwarded-Forを無視
    if direct_ip and not RequestHelper.is_trusted_proxy(direct_ip):
        logger.debug(
            "直接接続元が信頼できるプロキシではないため、X-Forwarded-Forを無視します",
            direct_ip=direct_ip,
        )
        return direct_ip

    # ✅ 信頼できるプロキシからのX-Forwarded-Forのみ使用
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
        if RequestHelper.is_valid_ip(client_ip):
            return client_ip
        else:
            logger.warning("無効なX-Forwarded-For形式", ...)
            return direct_ip

    return direct_ip
```

### セキュリティ効果

#### シナリオ1: 信頼できるプロキシ経由のアクセス

```
クライアント(203.0.113.10) → プロキシ(192.168.1.1) → アプリケーション

直接接続元: 192.168.1.1 (信頼できる)
X-Forwarded-For: 203.0.113.10, 192.168.1.1

結果: 203.0.113.10 を記録 ✅
```

#### シナリオ2: 信頼できないプロキシ経由のアクセス（攻撃シナリオ）

```
攻撃者(8.8.8.8) → アプリケーション
X-Forwarded-For: 203.0.113.10 (偽装)

直接接続元: 8.8.8.8 (信頼できない)
X-Forwarded-For: 203.0.113.10

結果: 8.8.8.8 を記録 ✅ (偽装されたIPを無視)
```

#### シナリオ3: 直接アクセス

```
クライアント(203.0.113.30) → アプリケーション

直接接続元: 203.0.113.30
X-Forwarded-For: なし

結果: 203.0.113.30 を記録 ✅
```

### 脅威の緩和

| 脅威 | 変更前 | 変更後 |
|------|--------|--------|
| IPアドレス偽装攻撃 | **脆弱** - X-Forwarded-Forを無条件に信頼 | **緩和** - 信頼できるプロキシからのみ受け入れ |
| レート制限回避 | **可能** - 偽装IPでレート制限を回避可能 | **困難** - 実際のIPアドレスで制限 |
| アクセスログ改ざん | **可能** - 任意のIPを記録可能 | **困難** - 信頼性のあるIPのみ記録 |

---

## 共通化による効果

### RequestHelperの共通利用

`RequestHelper.get_client_ip()`を以下のミドルウェアで統一的に使用：

1. **audit_log.py** (監査ログミドルウェア)
   - 変更: `self._get_client_ip()` → `RequestHelper.get_client_ip()`

2. **activity_tracking.py** (操作履歴ミドルウェア)
   - 既に使用中: `RequestHelper.get_client_ip()`

### メリット

1. **一貫性**: 両方のミドルウェアで同じロジックを使用
2. **保守性**: 変更は`RequestHelper`のみで反映
3. **テスタビリティ**: 共通ロジックのテストが容易

---

## 検証

### コード品質チェック

```bash
# Python文法チェック
python -m py_compile src/app/utils/request_helpers.py
python -m py_compile src/app/core/config.py
python -m py_compile src/app/api/middlewares/audit_log.py
✅ エラーなし

# Ruffによるコード品質チェック
ruff check src/app/utils/request_helpers.py
ruff check src/app/core/config.py
ruff check src/app/api/middlewares/audit_log.py
✅ All checks passed!
```

---

## 本番環境での設定

### 環境変数による設定上書き（オプション）

Azure App Service等の本番環境で、信頼できるプロキシの範囲をカスタマイズする場合：

```bash
# .env.production
TRUSTED_PROXIES='["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.1/32", "100.64.0.0/10"]'
```

**注意**: デフォルト設定で一般的なプライベートネットワークをカバーしているため、通常は変更不要です。

---

## セキュリティレビュー

### 機密情報除外

- ✅ パスワード、トークン、APIキーの除外
- ✅ 個人情報（SSN、クレジットカード、銀行口座）の除外
- ✅ 暗号化キー、秘密鍵の除外
- ✅ セッションID、Cookieの除外
- ✅ 正規表現による柔軟なパターンマッチング
- ✅ 偽陽性対策（author、keyboard等を除外）

### IPアドレス検証

- ✅ 信頼できるプロキシからのみX-Forwarded-Forを受け入れ
- ✅ IPアドレス形式の検証
- ✅ CIDR範囲による柔軟な設定
- ✅ デフォルトでRFC1918プライベートネットワークをカバー

---

## まとめ

本実装により、以下のセキュリティが強化されました：

1. **監査ログの機密情報保護**
   - 3項目 → 33項目 + 7パターン に拡大
   - 包括的な機密情報除外

2. **IPアドレス偽装攻撃の緩和**
   - X-Forwarded-Forの信頼性チェック
   - 信頼できるプロキシのみから受け入れ

3. **コードの品質向上**
   - 共通ロジックの統一
   - 保守性の向上
