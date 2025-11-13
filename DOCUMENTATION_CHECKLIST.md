# ドキュメント整合性チェックリスト

**作成日**: 2025-11-13
**調査対象**: genai-app-docs プロジェクト全ドキュメント
**調査方法**: 実装を正として、ドキュメントとの整合性を確認

---

## 📊 進捗サマリー

- **総調査カテゴリ数**: 7
- **発見された問題数**: 52件
  - 🔴 **高優先度**: 18件
  - 🟡 **中優先度**: 25件
  - 🟢 **低優先度**: 9件

---

## 🔴 高優先度（早急な対応が必要）

### Getting Started

- [x] `.env.local.example`にAzure AD開発モード設定を追加（DEV_MOCK_TOKEN, DEV_MOCK_USER_EMAIL, DEV_MOCK_USER_OID, DEV_MOCK_USER_NAME）
- [x] `config.py`のデフォルトデータベース名を`camp_backend_db`に統一
- [x] プロジェクト概要（06-project-overview.md）の機能モジュール説明を更新（user_accounts, project, analysis, driver_tree, ppt_generatorの追加）
- [x] データベース基礎（07-database-basics.md）のテーブル構成を更新（UserAccountモデルの追加）

### Architecture

- [x] **新規追加されたモジュールの記載漏れ**
  - `models/user_account/` - Azure AD対応のUserAccountモデル
  - `api/routes/v1/user_accounts/` - UserAccountエンドポイント
  - `repositories/user_account/` - UserAccountリポジトリ
  - `schemas/user_account/` - UserAccountスキーマ
  - `services/user/` - UserService (Azure AD対応)
- [x] **分析機能(analysis)のAPI構造の不一致** - ドキュメントには`chat.py`, `files.py`, `snapshots.py`, `steps.py`が記載されているが実装されていない
- [x] **依存性注入の型アノテーション** - Azure AD認証用の依存性(`AzureUserServiceDep`, `CurrentUserAzureDep`)が説明されていない
- [x] **認証フローの説明不足** - Azure AD認証フロー(`AUTH_MODE`による切り替え）が完全に説明されていない
- [x] **LangGraphエージェント実装の説明** - 既に実装済みなのに「将来実装」と記載されている

### Core Concepts

- [x] **Database Design - データベース環境の説明が古い** - SQLiteの記載を削除し、PostgreSQL 16に統一
- [x] **Database Design - UserAccountモデルの説明不足** - `users`テーブル（UserAccountモデル）の追加と、SampleUserとの使い分けを明記
- [x] **Security - Azure AD認証の記載漏れ** - Azure AD認証（本番環境）と開発モード認証の説明を追加

### Development

- [x] **依存性注入の型アノテーション不一致** - `UserServiceDep` vs `AzureUserServiceDep`、`CurrentUserDep` vs `CurrentUserAzureDep`の説明
- [x] **2つの認証システムの共存** - JWT認証（SampleUser用）とAzure AD認証（UserAccount用）が並行稼働していることを説明
- [x] **UserAccount vs User モデル名の不一致** - ドキュメント内の`User`を`UserAccount`に統一、ファイルパスも修正

### Testing

- [x] **テストディレクトリ構造の記述が古い** - sample_agents、sample_files、sample_sessions、sample_usersのテストは存在せず、実際はproject、analysis、driver_tree、ppt_generator、user_accountsのテストが存在

### Reference

- [x] **Database Schema - id型の不一致** - usersとsessionsテーブルのid型がINTEGERと記載されているが、実装ではUUID
- [x] **Database Schema - session_id型の不一致** - messagesテーブルのsession_idがINTEGERと記載されているが、実装ではUUID
- [x] **Database Schema - セキュリティ監査フィールドの記載漏れ** - 8つの追加フィールド（last_login_at, last_login_ip, failed_login_attempts, locked_until, refresh_token_hash, refresh_token_expires_at, api_key_hash, api_key_created_at）
- [x] **Environment Variables - Azure AD認証設定の記載漏れ** - 9つの環境変数（AUTH_MODE, AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_OPENAPI_CLIENT_ID, DEV_MOCK_TOKEN, DEV_MOCK_USER_EMAIL, DEV_MOCK_USER_OID, DEV_MOCK_USER_NAME）
- [x] **Utils - ストレージバックエンドの場所** - ドキュメントに記載されている`app/storage/`が実装に存在しない

---

## 🟡 中優先度（改善推奨）

### Getting Started

- [ ] プロジェクト構造にdata/とutils/ディレクトリを追加

### Architecture

- [ ] **モデル名・ファイル名の記載誤り**
  - `models/sample/user.py` → `models/sample/sample_user.py`
  - リポジトリのファイル名に`sample/`サブディレクトリが抜けている
- [ ] **API routes構造の不一致** - すべてのファイル名に`sample_`プレフィックスが付いている（agents.py → sample_agents.py）
- [ ] **モデル名のプレフィックス** - Session → SampleSession、Message → SampleMessage
- [ ] **dependenciesの実装場所の誤記** - `api/dependencies.py` → `api/core/dependencies.py`

### Core Concepts

- [ ] **Tech Stack - line-length設定の不一致** - Ruffのline-length設定を100から140に修正
- [ ] **Database Design - Session/Messageモデルのクラス名** - `Session` → `SampleSession`、`Message` → `SampleMessage`
- [ ] **Security - fastapi-azure-authの記載漏れ** - セキュリティ依存関係リストに追加
- [ ] **Security - AUTH_MODEの説明不一致** - 開発モードは「JWT」ではなく「Mock Auth」
- [ ] **Security - レガシーJWT認証の位置づけ** - 「SampleUser用JWT認証（レガシー、移行予定）」と明記

### Development

- [ ] **クラス名のプレフィックス規則** - `Sample`プレフィックスの使用ルールが不明確
- [ ] **@transactionalデコレータの実装状況** - 「将来の実装」とされているが既に実装済み
- [ ] **エンドポイントパスの全体構造** - ルーター階層が不明確
- [ ] **トランザクション管理の説明** - `@transactional`デコレータが既に実装されていることを明記

### Guides

- [ ] **架空のエンティティを例に使用** - "Product"モデルを例に使用しているが、実際の実装では使われていない
- [ ] **ガイドの実例更新** - user_account、project、analysis、driver_tree、ppt_generatorの実例に更新

### Specifications

- [ ] **テーブル数の記述** - 「16テーブル」という記述が正確かどうか未確認
- [ ] **API設計のエンドポイント例** - 実際のエンドポイント（analysis、driver_tree、ppt_generator、project、user_accounts）と例示の乖離
- [ ] **インフラ設計** - docker-compose.ymlファイルの存在と整合性の確認

### Reference

- [ ] **API Specification - ファイル削除エンドポイント** - エンドポイントパスの確認が必要
- [ ] **Database Schema - クエリ例のモデル名** - `Message` → `SampleMessage`、`Session` → `SampleSession`、`File` → `SampleFile`
- [ ] **Environment Variables - 新しいセキュリティ設定** - BCRYPT_ROUNDS、ENABLE_CSP、WORKERSの記載漏れ
- [ ] **Utils - セキュリティモジュールの構造** - 単一ファイルからディレクトリ構造（password.py, jwt.py, api_key.py, azure_ad.py, dev_auth.py）への変更を反映
- [ ] **Utils - リフレッシュトークン関数** - create_refresh_token、decode_refresh_tokenの記載漏れ

---

## 🟢 低優先度（時間があれば修正）

### Getting Started

- [ ] 前提条件のPythonバージョン - 問題なし（確認済み）

### Architecture

- [ ] 型エイリアスの命名規則の統一 - `Sample`プレフィックスの有無を統一

### Core Concepts

- [ ] **Tech Stack - Pydanticバージョン表記** - 「Pydantic: 2.0.0+」「Pydantic Settings: 2.6.0+」と区別して記載

### Development

- [ ] **Python 3.12+ジェネリック構文の要件** - バージョン要件の明記が望ましい
- [ ] **ログ実装の例** - 実装と密接に連携した例の追加

### Guides

- [ ] **Analysis機能のファイル数** - 「42ファイル」という具体的な記述が将来的に陳腐化する可能性

### Specifications

- [ ] **RBAC設計** - 基本的に一致しているが、詳細な権限マトリックスの整合性は未確認

### Reference

- [ ] **Environment Variables - MAX_FILE_SIZE_MB** - 新しい環境変数の記載漏れ
- [ ] **Utils - validate_password_strength** - パスワード強度検証関数の記載漏れ
- [ ] **Resources - 外部リンク** - 実際のリンク確認は行っていない

---

## 📋 カテゴリ別完了状況

### 01. Getting Started
- **調査完了**: ✅
- **問題数**: 4件（高: 4, 中: 1, 低: 0）
- **修正状況**: 0/5

### 02. Architecture
- **調査完了**: ✅
- **問題数**: 10件（高: 5, 中: 4, 低: 1）
- **修正状況**: 0/10

### 03. Core Concepts
- **調査完了**: ✅
- **問題数**: 9件（高: 3, 中: 5, 低: 1）
- **修正状況**: 0/9

### 04. Development
- **調査完了**: ✅
- **問題数**: 9件（高: 3, 中: 4, 低: 2）
- **修正状況**: 0/9

### 05. Testing
- **調査完了**: ✅
- **問題数**: 1件（高: 1, 中: 0, 低: 0）
- **修正状況**: 0/1

### 06. Guides
- **調査完了**: ✅
- **問題数**: 3件（高: 0, 中: 2, 低: 1）
- **修正状況**: 0/3

### 07. Specifications
- **調査完了**: ✅
- **問題数**: 3件（高: 0, 中: 3, 低: 1）
- **修正状況**: 0/4

### 08. Reference
- **調査完了**: ✅
- **問題数**: 13件（高: 5, 中: 5, 低: 3）
- **修正状況**: 0/13

---

## 🎯 推奨アクション

### フェーズ1: 高優先度対応（1-2週間）

1. **Azure AD認証の完全なドキュメント化**
   - UserAccountモデルの追加
   - Azure AD認証フローの説明
   - AUTH_MODE環境変数の設定方法
   - 依存性注入パターンの更新

2. **データベース設計の更新**
   - UUID型の使用を明記
   - セキュリティ監査フィールドの追加
   - UserAccount vs SampleUserの使い分けを明記

3. **テストドキュメントの更新**
   - 実際のテスト構造に合わせた修正
   - 実在する機能モジュールのテスト例に更新

### フェーズ2: 中優先度対応（2-4週間）

1. **ファイル名・パスの正確な記載**
   - すべてのドキュメントでファイル名とパスを確認し修正

2. **実装状況の反映**
   - 既に実装済みの機能を「将来実装」としている箇所を修正
   - @transactionalデコレータ、LangGraphエージェントなど

3. **設定ファイルの完全な記載**
   - すべての環境変数をドキュメント化
   - config.pyの設定項目を網羅

### フェーズ3: 低優先度対応（時間があれば）

1. **細かい不一致の修正**
   - バージョン表記の統一
   - 命名規則の明確化
   - 外部リンクの確認

---

## 📝 メモ

- この調査は2025-11-13時点の実装を基準にしています
- 実装が変更された場合は、このチェックリストも更新する必要があります
- 高優先度の問題から順に対応することを推奨します
- ドキュメント修正後は、実装との整合性を再確認してください

---

## 🔄 更新履歴

- 2025-11-13: 初回作成（全カテゴリ調査完了）
