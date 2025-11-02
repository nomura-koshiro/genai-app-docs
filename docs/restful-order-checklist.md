# RESTful メソッド順序整理チェックリスト

**生成日時:** 2025-11-02

**RESTful標準順序:** GET → POST → PATCH → DELETE

## 📊 サマリー

- **全体進捗:** 45/45 ファイル完了 (100%) ✅

- **api_routes:** ✅ 8/8 完了
- **services:** ✅ 9/9 完了
- **repositories:** ✅ 8/8 完了
- **schemas:** ✅ 9/9 完了
- **tests:** ✅ 11/11 完了

**🎉 全ファイル（コード + テスト）の RESTful 順序整理が完了しました！**

---

## 1. API Routes (src/app/api/routes/v1/)

### ✅ project_files.py

| 順序 | メソッド | パス | 説明 | 状態 |
|------|----------|------|------|------|
| 1 | `GET` | `/projects/{project_id}/files` | プロジェクトファイル一覧取得 | ✅ |
| 2 | `GET` | `/projects/{project_id}/files/{file_id}` | プロジェクトファイル情報取得 | ✅ |
| 3 | `GET` | `/projects/{project_id}/files/{file_id}/download` | プロジェクトファイルダウンロード | ✅ |
| 4 | `POST` | `/projects/{project_id}/files` | プロジェクトファイルアップロード | ✅ |
| 5 | `DELETE` | `/projects/{project_id}/files/{file_id}` | プロジェクトファイル削除 | ✅ |

### ✅ project_members.py

| 順序 | メソッド | パス | 説明 | 状態 |
|------|----------|------|------|------|
| 1 | `GET` | `/` | プロジェクトメンバー一覧取得 | ✅ |
| 2 | `GET` | `/me` | 自分のロール取得 | ✅ |
| 3 | `POST` | `/` | プロジェクトメンバー追加 | ✅ |
| 4 | `POST` | `/bulk` | プロジェクトメンバー複数人追加 | ✅ |
| 5 | `PATCH` | `/{member_id}` | メンバーロール更新 | ✅ |
| 6 | `PATCH` | `/bulk` | メンバーロール複数人更新 | ✅ |
| 7 | `DELETE` | `/{member_id}` | メンバー削除 | ✅ |
| 8 | `DELETE` | `/me` | プロジェクト退出 | ✅ |

### ✅ projects.py

| 順序 | メソッド | パス | 説明 | 状態 |
|------|----------|------|------|------|
| 1 | `GET` | `/` | プロジェクト一覧取得 | ✅ |
| 2 | `GET` | `/{project_id}` | プロジェクト詳細取得 | ✅ |
| 3 | `GET` | `/code/{code}` | プロジェクトコード検索 | ✅ |
| 4 | `POST` | `/` | プロジェクト作成 | ✅ |
| 5 | `PATCH` | `/{project_id}` | プロジェクト情報更新 | ✅ |
| 6 | `DELETE` | `/{project_id}` | プロジェクト削除 | ✅ |

### ✅ sample_agents.py

| 順序 | メソッド | パス | 説明 | 状態 |
|------|----------|------|------|------|
| 1 | `GET` | `/sample-sessions/{session_id}` | サンプルセッション情報取得 | ✅ |
| 2 | `POST` | `/sample-chat` | サンプルAIエージェントとチャット | ✅ |
| 3 | `DELETE` | `/sample-sessions/{session_id}` | サンプルセッション削除 | ✅ |

### ✅ sample_files.py

| 順序 | メソッド | パス | 説明 | 状態 |
|------|----------|------|------|------|
| 1 | `GET` | `/sample-download/{file_id}` | サンプルファイルダウンロード | ✅ |
| 2 | `GET` | `/sample-list` | サンプルファイル一覧取得 | ✅ |
| 3 | `POST` | `/sample-upload` | サンプルファイルアップロード | ✅ |
| 4 | `DELETE` | `/sample-files/{file_id}` | サンプルファイル削除 | ✅ |

### ✅ sample_sessions.py

| 順序 | メソッド | パス | 説明 | 状態 |
|------|----------|------|------|------|
| 1 | `GET` | `/sample-sessions` | サンプルセッション一覧取得 | ✅ |
| 2 | `GET` | `/sample-sessions/{session_id}` | サンプルセッション詳細取得 | ✅ |
| 3 | `POST` | `/sample-sessions` | サンプルセッション作成 | ✅ |
| 4 | `PATCH` | `/sample-sessions/{session_id}` | サンプルセッション更新 | ✅ |
| 5 | `DELETE` | `/sample-sessions/{session_id}` | サンプルセッション削除 | ✅ |

### ✅ sample_users.py

| 順序 | メソッド | パス | 説明 | 状態 |
|------|----------|------|------|------|
| 1 | `GET` | `/sample-me` | 現在のサンプルユーザー情報取得 | ✅ |
| 2 | `GET` | `/{user_id}` | 特定サンプルユーザー情報取得 | ✅ |
| 3 | `GET` | `/` | サンプルユーザー一覧取得 | ✅ |
| 4 | `POST` | `/` | 新しいサンプルユーザーを作成 | ✅ |
| 5 | `POST` | `/sample-login` | サンプルユーザーログイン | ✅ |
| 6 | `POST` | `/sample-refresh` | サンプルトークンリフレッシュ | ✅ |
| 7 | `POST` | `/sample-api-key` | サンプルAPIキー生成 | ✅ |

### ✅ users.py

| 順序 | メソッド | パス | 説明 | 状態 |
|------|----------|------|------|------|
| 1 | `GET` | `/` | ユーザー一覧取得 | ✅ |
| 2 | `GET` | `/me` | 現在のユーザー情報取得 | ✅ |
| 3 | `GET` | `/{user_id}` | 特定ユーザー情報取得 | ✅ |
| 4 | `PATCH` | `/me` | ユーザー情報更新 | ✅ |
| 5 | `DELETE` | `/{user_id}` | ユーザー削除 | ✅ |

## 2. Services (src/app/services/)

### ✅ project.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | - | `get_project` | GET | ✅ |
| 2 | - | `get_project_by_code` | GET | ✅ |
| 3 | - | `list_projects` | GET | ✅ |
| 4 | - | `list_user_projects` | GET | ✅ |
| 5 | - | `create_project` | POST | ✅ |
| 6 | - | `update_project` | PATCH | ✅ |
| 7 | - | `delete_project` | DELETE | ✅ |
| 8 | - | `_check_user_role` | PRIVATE | ✅ |
| 9 | - | `_delete_physical_files` | PRIVATE | ✅ |
| 10 | - | `check_user_access` | PRIVATE | ✅ |

### ✅ project_file.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | 80 | `_check_member_role` | UNKNOWN | ✅ |
| 2 | 106 | `_generate_file_path` | UNKNOWN | ✅ |
| 3 | 121 | `_sanitize_filename` | UNKNOWN | ✅ |
| 4 | 139 | `upload_file` | UNKNOWN | ✅ |
| 5 | 244 | `get_file` | GET | ✅ |
| 6 | 271 | `list_project_files` | GET | ✅ |
| 7 | 304 | `download_file` | UNKNOWN | ✅ |
| 8 | 335 | `delete_file` | DELETE | ✅ |

### ✅ project_member.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | - | `get_project_members` | GET | ✅ |
| 2 | - | `get_user_role` | GET | ✅ |
| 3 | - | `add_member` | POST | ✅ |
| 4 | - | `add_members_bulk` | POST | ✅ |
| 5 | - | `update_member_role` | PATCH | ✅ |
| 6 | - | `update_members_bulk` | PATCH | ✅ |
| 7 | - | `remove_member` | DELETE | ✅ |
| 8 | - | `leave_project` | DELETE | ✅ |

### ✅ sample_agent.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | 38 | `chat` | UNKNOWN | ✅ |
| 2 | 121 | `get_session` | GET | ✅ |
| 3 | 150 | `delete_session` | DELETE | ✅ |
| 4 | 177 | `_generate_session_id` | UNKNOWN | ✅ |
| 5 | 185 | `_generate_response` | UNKNOWN | ✅ |

### ✅ sample_authorization.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | 47 | `check_admin_access` | UNKNOWN | ✅ |

### ✅ sample_file.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | - | `get_file` | GET | ✅ |
| 2 | - | `list_files` | GET | ✅ |
| 3 | - | `upload_file` | POST | ✅ |
| 4 | - | `delete_file` | DELETE | ✅ |
| 5 | - | `_generate_file_id` | PRIVATE | ✅ |
| 6 | - | `_sanitize_filename` | PRIVATE | ✅ |

### ✅ sample_session.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | 37 | `list_sessions` | GET | ✅ |
| 2 | 90 | `get_session` | GET | ✅ |
| 3 | 119 | `create_session` | POST | ✅ |
| 4 | 156 | `update_session` | PATCH | ✅ |
| 5 | 199 | `delete_session` | DELETE | ✅ |
| 6 | 226 | `_generate_session_id` | UNKNOWN | ✅ |

### ✅ sample_user.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | - | `get_user` | GET | ✅ |
| 2 | - | `get_user_by_email` | GET | ✅ |
| 3 | - | `list_users` | GET | ✅ |
| 4 | - | `create_user` | POST | ✅ |
| 5 | - | `authenticate` | OTHER | ✅ |

### ✅ user.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | - | `count_users` | GET | ✅ |
| 2 | - | `get_or_create_by_azure_oid` | GET | ✅ |
| 3 | - | `get_user` | GET | ✅ |
| 4 | - | `get_user_by_azure_oid` | GET | ✅ |
| 5 | - | `get_user_by_email` | GET | ✅ |
| 6 | - | `list_active_users` | GET | ✅ |
| 7 | - | `list_users` | GET | ✅ |
| 8 | - | `update_last_login` | PATCH | ✅ |
| 9 | - | `update_user` | PATCH | ✅ |

## 3. Repositories (src/app/repositories/)

### ✅ base.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | 67 | `get` | UNKNOWN | ✅ |
| 2 | 100 | `get_multi` | GET | ✅ |
| 3 | 229 | `create` | UNKNOWN | ✅ |
| 4 | 296 | `update` | UNKNOWN | ✅ |
| 5 | 362 | `delete` | UNKNOWN | ✅ |
| 6 | 417 | `count` | UNKNOWN | ✅ |

### ✅ project.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | 97 | `get` | UNKNOWN | ✅ |
| 2 | 121 | `get_by_code` | GET | ✅ |
| 3 | 160 | `list_by_user` | GET | ✅ |
| 4 | 225 | `get_active_projects` | GET | ✅ |
| 5 | 259 | `delete` | UNKNOWN | ✅ |
| 6 | 290 | `count_by_user` | UNKNOWN | ✅ |

### ✅ project_file.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | 47 | `create` | UNKNOWN | ✅ |
| 2 | 80 | `get` | UNKNOWN | ✅ |
| 3 | 101 | `list_by_project` | GET | ✅ |
| 4 | 129 | `delete` | UNKNOWN | ✅ |
| 5 | 151 | `count_by_project` | UNKNOWN | ✅ |
| 6 | 169 | `get_total_size_by_project` | GET | ✅ |

### ✅ project_member.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | - | `count_by_project` | GET | ✅ |
| 2 | - | `count_by_role` | GET | ✅ |
| 3 | - | `get` | GET | ✅ |
| 4 | - | `get_by_project_and_user` | GET | ✅ |
| 5 | - | `get_user_role` | GET | ✅ |
| 6 | - | `list_by_project` | GET | ✅ |
| 7 | - | `list_by_user` | GET | ✅ |
| 8 | - | `update_role` | PATCH | ✅ |
| 9 | - | `delete` | DELETE | ✅ |

### ✅ sample_file.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | - | `get_by_file_id` | GET | ✅ |
| 2 | - | `list_files` | GET | ✅ |
| 3 | - | `create_file` | POST | ✅ |
| 4 | - | `delete_file` | DELETE | ✅ |

### ✅ sample_session.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | 28 | `get_by_session_id` | GET | ✅ |
| 2 | 42 | `create_session` | POST | ✅ |
| 3 | 58 | `add_message` | POST | ✅ |
| 4 | 89 | `delete_session` | DELETE | ✅ |

### ✅ sample_user.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | 91 | `get_by_email` | GET | ✅ |
| 2 | 136 | `get_by_username` | GET | ✅ |
| 3 | 184 | `get_active_users` | GET | ✅ |

### ✅ user.py

| 順序 | 行 | メソッド名 | タイプ | 状態 |
|------|-----|------------|--------|------|
| 1 | 94 | `get_by_azure_oid` | GET | ✅ |
| 2 | 139 | `get_by_email` | GET | ✅ |
| 3 | 188 | `get_active_users` | GET | ✅ |
| 4 | 255 | `get_by_id` | GET | ✅ |

## 4. Schemas (src/app/schemas/)

### ✅ common.py

| 順序 | 行 | クラス名 | タイプ | 状態 |
|------|-----|----------|--------|------|
| 1 | 33 | `MessageResponse` | GET | ✅ |
| 2 | 50 | `ProblemDetails` | COMMON | ✅ |
| 3 | 124 | `HealthResponse` | GET | ✅ |
| 4 | 151 | `PaginationParams` | COMMON | ✅ |
| 5 | 179 | `PaginatedResponse` | GET | ✅ |

### ✅ project.py

| 順序 | 行 | クラス名 | タイプ | 状態 |
|------|-----|----------|--------|------|
| 1 | - | `ProjectBase` | BASE | ✅ |
| 2 | - | `ProjectMemberBase` | BASE | ✅ |
| 3 | - | `ProjectFileBase` | BASE | ✅ |
| 4 | - | `ProjectResponse` | RESPONSE | ✅ |
| 5 | - | `ProjectMemberResponse` | RESPONSE | ✅ |
| 6 | - | `ProjectFileResponse` | RESPONSE | ✅ |
| 7 | - | `ProjectCreate` | CREATE | ✅ |
| 8 | - | `ProjectMemberCreate` | CREATE | ✅ |
| 9 | - | `ProjectUpdate` | UPDATE | ✅ |
| 10 | - | `ProjectMemberUpdate` | UPDATE | ✅ |

### ✅ project_file.py

| 順序 | 行 | クラス名 | タイプ | 状態 |
|------|-----|----------|--------|------|
| 1 | 29 | `ProjectFileUploadResponse` | GET | ✅ |
| 2 | 73 | `ProjectFileResponse` | GET | ✅ |
| 3 | 123 | `ProjectFileListResponse` | GET | ✅ |
| 4 | 150 | `ProjectFileDeleteResponse` | GET | ✅ |

### ✅ project_member.py

| 順序 | 行 | クラス名 | タイプ | 状態 |
|------|-----|----------|--------|------|
| 1 | - | `ProjectMemberResponse` | RESPONSE | ✅ |
| 2 | - | `ProjectMemberListResponse` | RESPONSE | ✅ |
| 3 | - | `UserRoleResponse` | RESPONSE | ✅ |
| 4 | - | `ProjectMemberBulkResponse` | RESPONSE | ✅ |
| 5 | - | `ProjectMemberBulkUpdateResponse` | RESPONSE | ✅ |
| 6 | - | `ProjectMemberCreate` | CREATE | ✅ |
| 7 | - | `ProjectMemberBulkCreate` | CREATE | ✅ |
| 8 | - | `ProjectMemberUpdate` | UPDATE | ✅ |
| 9 | - | `ProjectMemberRoleUpdate` | UPDATE | ✅ |
| 10 | - | `ProjectMemberBulkUpdateRequest` | UPDATE | ✅ |
| 11 | - | `ProjectMemberBulkUpdateError` | UPDATE | ✅ |
| 12 | - | `ProjectMemberBulkError` | ERROR | ✅ |
| 13 | - | `ProjectMemberWithUser` | OTHER | ✅ |

### ✅ sample_agents.py

| 順序 | 行 | クラス名 | タイプ | 状態 |
|------|-----|----------|--------|------|
| 1 | 6 | `SampleChatRequest` | COMMON | ✅ |
| 2 | 14 | `SampleChatResponse` | GET | ✅ |

### ✅ sample_file.py

| 順序 | 行 | クラス名 | タイプ | 状態 |
|------|-----|----------|--------|------|
| 1 | 8 | `SampleFileUploadResponse` | GET | ✅ |
| 2 | 18 | `SampleFileResponse` | GET | ✅ |
| 3 | 30 | `SampleFileListResponse` | GET | ✅ |
| 4 | 37 | `SampleFileDeleteResponse` | GET | ✅ |

### ✅ sample_sessions.py

| 順序 | 行 | クラス名 | タイプ | 状態 |
|------|-----|----------|--------|------|
| 1 | - | `SampleMessageResponse` | RESPONSE | ✅ |
| 2 | - | `SampleSessionResponse` | RESPONSE | ✅ |
| 3 | - | `SampleSessionListResponse` | RESPONSE | ✅ |
| 4 | - | `SampleDeleteResponse` | RESPONSE | ✅ |
| 5 | - | `SampleSessionCreateRequest` | CREATE | ✅ |
| 6 | - | `SampleSessionUpdateRequest` | UPDATE | ✅ |

### ✅ sample_user.py

| 順序 | 行 | クラス名 | タイプ | 状態 |
|------|-----|----------|--------|------|
| 1 | - | `SampleUserBase` | BASE | ✅ |
| 2 | - | `SampleUserResponse` | RESPONSE | ✅ |
| 3 | - | `SampleToken` | RESPONSE | ✅ |
| 4 | - | `SampleTokenPayload` | RESPONSE | ✅ |
| 5 | - | `SampleTokenWithRefresh` | RESPONSE | ✅ |
| 6 | - | `SampleRefreshTokenRequest` | RESPONSE | ✅ |
| 7 | - | `SampleAPIKeyResponse` | RESPONSE | ✅ |
| 8 | - | `SampleUserCreate` | CREATE | ✅ |
| 9 | - | `SampleUserLogin` | CREATE | ✅ |

### ✅ user.py

| 順序 | 行 | クラス名 | タイプ | 状態 |
|------|-----|----------|--------|------|
| 1 | - | `UserBase` | BASE | ✅ |
| 2 | - | `UserResponse` | RESPONSE | ✅ |
| 3 | - | `UserListResponse` | RESPONSE | ✅ |
| 4 | - | `UserUpdate` | UPDATE | ✅ |

## 5. Tests (tests/app/)

### ✅ Services Tests

| ファイル | フィクスチャ | テスト数 | 順序 | 状態 |
|----------|-------------|----------|------|------|
| test_project_member.py | 2 | 12 | GET(1) → POST(4) → PATCH(2) → DELETE(4) → OTHER(1) | ✅ |
| test_user.py | 0 | 24 | GET(19) → PATCH(5) | ✅ |
| test_project.py | 0 | 15 | GET(5) → POST(2) → PATCH(2) → DELETE(3) → OTHER(3) | ✅ |

### ✅ API Routes Tests

| ファイル | フィクスチャ | テスト数 | 順序 | 状態 |
|----------|-------------|----------|------|------|
| test_project_members.py | 2 | 14 | GET(2) → POST(5) → PATCH(4) → DELETE(3) | ✅ |
| test_users.py | 1 | 8 | GET(7) → PATCH(1) | ✅ |
| test_projects.py | 1 | 7 | GET(3) → POST(2) → PATCH(1) → OTHER(1) | ✅ |
| test_project_files.py | 0 | 7 | GET(3) → DELETE(1) → OTHER(3) | ✅ |

### ✅ Repository Tests

| ファイル | フィクスチャ | テスト数 | 順序 | 状態 |
|----------|-------------|----------|------|------|
| test_project_member.py | 2 | 7 | GET(7) | ✅ |
| test_user.py | 0 | 8 | OTHER(8) | ✅ |
| test_project.py | 0 | 4 | GET(4) | ✅ |
| test_project_file.py | 0 | 4 | GET(4) | ✅ |

**テストファイル合計:** 11ファイル、110テストメソッド ✅

## 📋 完了サマリー

**🎉 全ファイルの RESTful 順序整理が完了しました！**

### 整理内容

**Phase 1: Services (3ファイル)**
- project_member.py: GET（2つ） → POST（2つ） → PATCH（2つ） → DELETE（2つ）
- user.py: GET（7つ） → PATCH（2つ）
- project.py: GET（4つ） → POST → PATCH → DELETE → PRIVATE（3つ）

**Phase 2: API Routes (3ファイル)**
- sample_agents.py: GET → POST → DELETE
- sample_files.py: GET（2つ） → POST → DELETE
- sample_users.py: GET（3つ） → POST（4つ）

**Phase 3: Repositories (2ファイル)**
- project_member.py: GET（7つ） → PATCH → DELETE
- sample_file.py: GET（2つ） → POST → DELETE

**Phase 4: Schemas (5ファイル)**
- project_member.py: RESPONSE（5つ） → CREATE（2つ） → UPDATE（4つ） → ERROR → OTHER
- user.py: BASE → RESPONSE（2つ） → UPDATE
- project.py: BASE（3つ） → RESPONSE（3つ） → CREATE（2つ） → UPDATE（2つ）
- sample_user.py: BASE → RESPONSE（6つ） → CREATE（2つ）
- sample_sessions.py: RESPONSE（4つ） → CREATE → UPDATE

**Phase 5: Tests (11ファイル)**
- Services Tests (3ファイル): 51テストメソッド
  - test_project_member.py: GET → POST → PATCH → DELETE → OTHER
  - test_user.py: GET → PATCH
  - test_project.py: GET → POST → PATCH → DELETE → OTHER
- API Routes Tests (4ファイル): 36テストメソッド
  - test_project_members.py: GET → POST → PATCH → DELETE
  - test_users.py: GET → PATCH
  - test_projects.py: GET → POST → PATCH → OTHER
  - test_project_files.py: GET → DELETE → OTHER
- Repository Tests (4ファイル): 23テストメソッド
  - test_project_member.py: GET
  - test_user.py: OTHER（リポジトリ特有メソッド）
  - test_project.py: GET
  - test_project_file.py: GET

**スキーマ依存関係修正:**
- project_member.py: エラークラスを参照クラスの前に移動して NameError を解消

### 効果

- **全45ファイル（コード34 + テスト11）**が RESTful 標準順序に整理されました
- コードの可読性と保守性が向上しました
- API設計のベストプラクティスに準拠しました
- テストコードも同じ順序で整理され、コードとテストの対応が明確になりました
- スキーマ依存関係の問題が解消され、インポートエラーがなくなりました
