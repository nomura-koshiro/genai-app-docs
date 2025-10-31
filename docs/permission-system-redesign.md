# 権限システム再設計ドキュメント

## 概要

プロジェクト権限システムを4段階から3段階に簡素化し、システムレベルとプロジェクトレベルの権限を明確に分離しました。

**実装日**: 2025-10-31
**コミットID**: dee03f2
**ブランチ**: claude/create-api-011CUfG6ZYaP2bo3FVMsXtNr

---

## 1. 権限モデルの変更

### 1.1 新旧比較

```mermaid
graph TB
    subgraph "旧システム"
        Old_User[User]
        Old_PM[ProjectMember]

        Old_User --> Old_PM

        Old_PM --> Old_Owner[OWNER<br/>全権限]
        Old_PM --> Old_Admin[ADMIN<br/>管理権限]
        Old_PM --> Old_Member[MEMBER<br/>編集権限]
        Old_PM --> Old_Viewer[VIEWER<br/>閲覧のみ]
    end

    subgraph "新システム"
        New_User[User]
        New_SR[SystemRole]
        New_PM[ProjectMember]
        New_PR[ProjectRole]

        New_User --> New_SR
        New_User --> New_PM
        New_PM --> New_PR

        New_SR --> Sys_Admin[SYSTEM_ADMIN<br/>全プロジェクトアクセス]
        New_SR --> Sys_User[USER<br/>通常ユーザー]

        New_PR --> Proj_Admin[PROJECT_ADMIN<br/>プロジェクト全権限<br/>旧OWNER+ADMIN統合]
        New_PR --> Proj_Member[MEMBER<br/>編集権限]
        New_PR --> Proj_Viewer[VIEWER<br/>閲覧のみ]
    end

    style Old_Owner fill:#ff6b6b
    style Old_Admin fill:#ff6b6b
    style Proj_Admin fill:#51cf66
    style Sys_Admin fill:#339af0
```

### 1.2 権限マトリックス

| 操作 | SYSTEM_ADMIN | PROJECT_ADMIN | MEMBER | VIEWER |
|------|--------------|---------------|--------|--------|
| 全プロジェクト閲覧 | ✅ | ❌ | ❌ | ❌ |
| プロジェクト閲覧 | ✅ | ✅ | ✅ | ✅ |
| プロジェクト編集 | ✅ | ✅ | ✅ | ❌ |
| メンバー追加/削除 | ✅ | ✅ | ❌ | ❌ |
| ロール変更 | ✅ | ✅ | ❌ | ❌ |
| プロジェクト削除 | ✅ | ✅ | ❌ | ❌ |

---

## 2. システムアーキテクチャ

### 2.1 レイヤー構成と変更箇所

```mermaid
graph TD
    Client[Client Application]

    subgraph "API Layer"
        API[project_members.py<br/>✅ ドキュメント更新<br/>✅ 権限要件明確化]
    end

    subgraph "Service Layer"
        Service[ProjectMemberService<br/>✅ 6メソッド更新<br/>✅ 権限チェック変更]
    end

    subgraph "Repository Layer"
        Repo[ProjectMemberRepository<br/>変更なし]
    end

    subgraph "Model Layer"
        User[User Model<br/>✅ SystemRole追加]
        ProjectMember[ProjectMember Model<br/>✅ ProjectRole簡素化]
    end

    subgraph "Schema Layer"
        Schema[Pydantic Schemas<br/>✅ 全スキーマ更新<br/>✅ ドキュメント更新]
    end

    subgraph "Database"
        DB[(PostgreSQL)]
    end

    Client --> API
    API --> Service
    Service --> Repo
    Repo --> User
    Repo --> ProjectMember
    User --> DB
    ProjectMember --> DB
    API -.uses.-> Schema
    Service -.uses.-> Schema

    style User fill:#ffd43b
    style ProjectMember fill:#ffd43b
    style Service fill:#ffd43b
    style API fill:#ffd43b
    style Schema fill:#ffd43b
```

### 2.2 データモデル（ER図）

```mermaid
erDiagram
    User ||--o{ ProjectMember : "has many"
    Project ||--o{ ProjectMember : "has many"
    User ||--|| SystemRole : "has"
    ProjectMember ||--|| ProjectRole : "has"

    User {
        uuid id PK
        string azure_oid UK
        string email UK
        string display_name
        json roles "SystemRole配列"
        timestamp created_at
        timestamp updated_at
    }

    SystemRole {
        enum SYSTEM_ADMIN "全プロジェクトアクセス"
        enum USER "通常ユーザー(デフォルト)"
    }

    Project {
        uuid id PK
        string name
        string code UK
        string description
        uuid created_by FK
        timestamp created_at
        timestamp updated_at
    }

    ProjectMember {
        uuid id PK
        uuid project_id FK
        uuid user_id FK
        enum role "ProjectRole"
        uuid added_by FK
        timestamp joined_at
    }

    ProjectRole {
        enum PROJECT_ADMIN "OWNER+ADMIN統合"
        enum MEMBER "編集権限"
        enum VIEWER "閲覧のみ"
    }
```

---

## 3. 権限チェックフロー

### 3.1 メンバー追加フロー

```mermaid
sequenceDiagram
    participant Client
    participant API as API Layer
    participant Service as ProjectMemberService
    participant Repo as Repository
    participant DB as Database

    Client->>API: POST /projects/{id}/members
    API->>Service: add_member(project_id, member_data, added_by)

    Service->>Repo: get_member(project_id, added_by)
    Repo->>DB: SELECT * FROM project_members
    DB-->>Repo: adder_member
    Repo-->>Service: adder_member

    alt adder is not PROJECT_ADMIN
        Service-->>API: AuthorizationError("権限不足")
        API-->>Client: 403 Forbidden
    else adder is PROJECT_ADMIN
        Service->>Repo: create(project_id, user_id, role)
        Repo->>DB: INSERT INTO project_members
        DB-->>Repo: new_member
        Repo-->>Service: new_member
        Service-->>API: new_member
        API-->>Client: 201 Created
    end
```

### 3.2 ロール更新フロー（最後のPROJECT_ADMIN保護）

```mermaid
sequenceDiagram
    participant Client
    participant Service as ProjectMemberService
    participant Repo as Repository

    Client->>Service: update_member_role(member_id, new_role, requester_id)

    Service->>Repo: get_by_id(member_id)
    Repo-->>Service: target_member

    Service->>Repo: get_member(project_id, requester_id)
    Repo-->>Service: requester_member

    alt requester is not PROJECT_ADMIN
        Service-->>Client: AuthorizationError("権限不足")
    else target is PROJECT_ADMIN and new_role != PROJECT_ADMIN
        Service->>Repo: count_admins(project_id)
        Repo-->>Service: admin_count

        alt admin_count <= 1
            Service-->>Client: ValidationError("最後のPROJECT_ADMINは降格不可")
        else admin_count > 1
            Service->>Repo: update(member_id, new_role)
            Repo-->>Service: updated_member
            Service-->>Client: updated_member
        end
    else normal update
        Service->>Repo: update(member_id, new_role)
        Repo-->>Service: updated_member
        Service-->>Client: updated_member
    end
```

---

## 4. 実装の詳細

### 4.1 変更ファイル一覧

```mermaid
mindmap
  root((権限システム再設計))
    モデル層
      src/app/models/user.py
        SystemRole enum追加
        has_system_role()メソッド
        is_system_admin()メソッド
      src/app/models/project_member.py
        ProjectRole簡素化
        OWNER + ADMIN → PROJECT_ADMIN
    スキーマ層
      src/app/schemas/project_member.py
        全スキーマクラス更新
        Field description更新
        UserRoleResponse後方互換性維持
    サービス層
      src/app/services/project_member.py
        add_member()
        add_members_bulk()
        update_member_role()
        update_members_bulk()
        remove_member()
        leave_project()
    API層
      src/app/api/routes/v1/project_members.py
        全エンドポイントドキュメント更新
        権限要件明確化
        サンプルレスポンス更新
    テスト層
      10ファイル一括更新
        models 2ファイル
        services 3ファイル
        repositories 3ファイル
        api 2ファイル
```

### 4.2 サービス層の主要変更

#### 権限チェックロジック（Before → After）

**Before（旧システム）:**
```python
# OWNER または ADMIN が必要
if adder_role not in [ProjectRole.OWNER, ProjectRole.ADMIN]:
    raise AuthorizationError("権限不足")

# OWNER ロールの追加は OWNER のみ可能
if member_data.role == ProjectRole.OWNER and adder_role != ProjectRole.OWNER:
    raise AuthorizationError("OWNER追加にはOWNER権限が必要")
```

**After（新システム）:**
```python
# PROJECT_ADMIN が必要
if adder_role != ProjectRole.PROJECT_ADMIN:
    raise AuthorizationError("権限不足")

# OWNER特別扱いを削除（PROJECT_ADMINで統一）
```

#### 最後の管理者保護（Before → After）

**Before（旧システム）:**
```python
# 最後のOWNERチェック
if target_member.role == ProjectRole.OWNER:
    owner_count = await self._count_members_by_role(
        target_member.project_id, ProjectRole.OWNER
    )
    if owner_count <= 1:
        raise ValidationError("最後のOWNERは変更/削除できません")
```

**After（新システム）:**
```python
# 最後のPROJECT_ADMINチェック
if target_member.role == ProjectRole.PROJECT_ADMIN:
    admin_count = await self._count_members_by_role(
        target_member.project_id, ProjectRole.PROJECT_ADMIN
    )
    if admin_count <= 1:
        raise ValidationError("最後のPROJECT_ADMINは変更/削除できません")
```

---

## 5. API エンドポイント

### 5.1 エンドポイント一覧と権限要件

```mermaid
graph LR
    subgraph "Project Members API"
        A[POST /members<br/>メンバー追加<br/>👤 PROJECT_ADMIN]
        B[POST /members/bulk<br/>一括追加<br/>👤 PROJECT_ADMIN]
        C[GET /members<br/>一覧取得<br/>👤 MEMBER以上]
        D[GET /members/me<br/>自分のロール取得<br/>👤 MEMBER以上]
        E[PATCH /members/:id<br/>ロール更新<br/>👤 PROJECT_ADMIN]
        F[PATCH /members/bulk<br/>一括ロール更新<br/>👤 PROJECT_ADMIN]
        G[DELETE /members/:id<br/>メンバー削除<br/>👤 PROJECT_ADMIN]
        H[DELETE /members/me<br/>プロジェクト退出<br/>👤 任意のメンバー]
    end

    style A fill:#4dabf7
    style B fill:#4dabf7
    style E fill:#4dabf7
    style F fill:#4dabf7
    style G fill:#4dabf7
    style C fill:#51cf66
    style D fill:#51cf66
    style H fill:#ffd43b
```

### 5.2 一括操作のレスポンス構造

```mermaid
classDiagram
    class ProjectMemberBulkResponse {
        +UUID project_id
        +List~ProjectMemberWithUser~ added
        +List~ProjectMemberBulkError~ failed
        +int total_requested
        +int total_added
        +int total_failed
    }

    class ProjectMemberBulkUpdateResponse {
        +UUID project_id
        +List~ProjectMemberWithUser~ updated
        +List~ProjectMemberBulkUpdateError~ failed
        +int total_requested
        +int total_updated
        +int total_failed
    }

    class ProjectMemberWithUser {
        +UUID id
        +UUID project_id
        +UUID user_id
        +ProjectRole role
        +datetime joined_at
        +UUID added_by
        +UserResponse user
    }

    class ProjectMemberBulkError {
        +UUID user_id
        +ProjectRole role
        +string error
    }

    class ProjectMemberBulkUpdateError {
        +UUID member_id
        +ProjectRole role
        +string error
    }

    ProjectMemberBulkResponse --> ProjectMemberWithUser
    ProjectMemberBulkResponse --> ProjectMemberBulkError
    ProjectMemberBulkUpdateResponse --> ProjectMemberWithUser
    ProjectMemberBulkUpdateResponse --> ProjectMemberBulkUpdateError
```

---

## 6. テスト更新

### 6.1 更新したテストファイル

```mermaid
graph TD
    subgraph "テストファイル（10ファイル）"
        M1[test_project_member.py<br/>models]
        M2[test_project.py<br/>models]

        S1[test_project_member.py<br/>services]
        S2[test_project_file.py<br/>services]
        S3[test_project.py<br/>services]

        R1[test_project_member.py<br/>repositories]
        R2[test_user.py<br/>repositories]
        R3[test_project.py<br/>repositories]

        A1[test_project_members.py<br/>api]
        A2[test_project_files.py<br/>api]
    end

    M1 --> Change[ProjectRole.OWNER/ADMIN<br/>↓<br/>ProjectRole.PROJECT_ADMIN]
    M2 --> Change
    S1 --> Change
    S2 --> Change
    S3 --> Change
    R1 --> Change
    R2 --> Change
    R3 --> Change
    A1 --> Change
    A2 --> Change

    style Change fill:#ffd43b
```

### 6.2 テスト更新の詳細

**変更パターン:**
- `ProjectRole.OWNER` → `ProjectRole.PROJECT_ADMIN`
- `ProjectRole.ADMIN` → `ProjectRole.PROJECT_ADMIN`
- フィクスチャ名: `test_project_with_owner` は維持（意味的に正しいため）
- コメント: "OWNER" → "PROJECT_ADMIN" に更新

**影響を受けたテストケース数:** 約80+

---

## 7. 後方互換性

### 7.1 維持されている機能

```mermaid
graph LR
    subgraph "後方互換性"
        A[UserRoleResponse]
        B[is_owner フィールド]
        C[is_admin フィールド]
        D[既存APIエンドポイント]
        E[リクエスト/レスポンス形式]
    end

    A --> B
    A --> C

    B -.動作.-> F[PROJECT_ADMIN の場合 true]
    C -.動作.-> F

    style A fill:#51cf66
    style B fill:#51cf66
    style C fill:#51cf66
    style D fill:#51cf66
    style E fill:#51cf66
```

### 7.2 非推奨フィールドの動作

| フィールド | 旧動作 | 新動作 |
|-----------|--------|--------|
| `is_owner` | `role == OWNER` の場合 `true` | `role == PROJECT_ADMIN` の場合 `true` |
| `is_admin` | `role in [OWNER, ADMIN]` の場合 `true` | `role == PROJECT_ADMIN` の場合 `true` |

**注意:** これらのフィールドは将来のバージョンで削除される可能性があります。

---

## 8. データベース移行（TODO）

### 8.1 必要な移行作業

```mermaid
graph TD
    A[現状のデータ] --> B{role カラム}

    B -->|owner| C[project_admin に変換]
    B -->|admin| C
    B -->|member| D[member のまま]
    B -->|viewer| E[viewer のまま]

    C --> F[Alembic Migration]
    D --> F
    E --> F

    F --> G[新システムのデータ]

    style A fill:#ff6b6b
    style G fill:#51cf66
    style F fill:#ffd43b
```

### 8.2 移行スクリプト例（未実装）

```sql
-- 既存データの変換
UPDATE project_members
SET role = 'project_admin'
WHERE role IN ('owner', 'admin');

-- インデックスの再作成（必要に応じて）
CREATE INDEX idx_project_members_role ON project_members(role);
```

### 8.3 移行チェックリスト

- [ ] Alembic マイグレーションファイル作成
- [ ] `owner` → `project_admin` 変換クエリ
- [ ] `admin` → `project_admin` 変換クエリ
- [ ] データ整合性チェック
- [ ] ロールバックスクリプト準備
- [ ] 本番環境移行手順書作成

---

## 9. 変更の影響範囲

### 9.1 ファイル変更サマリー

```mermaid
pie title "変更ファイルの分布（12ファイル）"
    "テストファイル" : 10
    "サービス層" : 1
    "スキーマ層" : 1
```

### 9.2 変更行数

- **追加**: 81行
- **削除**: 89行
- **純増減**: -8行（コードの簡素化）

### 9.3 影響を受けるコンポーネント

```mermaid
graph TD
    A[権限システム再設計] --> B[直接影響]
    A --> C[間接影響]
    A --> D[影響なし]

    B --> B1[ProjectMemberService]
    B --> B2[ProjectMember Model]
    B --> B3[User Model]
    B --> B4[Schemas]
    B --> B5[API Routes]
    B --> B6[Tests 10ファイル]

    C --> C1[プロジェクト作成時のOWNER割り当て]
    C --> C2[権限チェックミドルウェア]
    C --> C3[フロントエンドの表示ロジック]

    D --> D1[ProjectFileService]
    D --> D2[Repository層]
    D --> D3[Database接続]
    D --> D4[認証システム]

    style B1 fill:#ffd43b
    style B2 fill:#ffd43b
    style B3 fill:#ffd43b
    style B4 fill:#ffd43b
    style B5 fill:#ffd43b
    style B6 fill:#ffd43b
    style C1 fill:#74c0fc
    style C2 fill:#74c0fc
    style C3 fill:#74c0fc
    style D1 fill:#51cf66
    style D2 fill:#51cf66
    style D3 fill:#51cf66
    style D4 fill:#51cf66
```

---

## 10. まとめ

### 10.1 主な改善点

1. **シンプル化**: 4段階 → 3段階のプロジェクト権限
2. **明確化**: システムレベルとプロジェクトレベルの分離
3. **一貫性**: OWNER/ADMIN の二重管理を排除
4. **拡張性**: 将来的なシステム管理機能の追加が容易

### 10.2 新システムの利点

```mermaid
graph LR
    A[新権限システム] --> B[シンプル]
    A --> C[明確]
    A --> D[拡張可能]
    A --> E[保守しやすい]

    B --> B1[管理者ロールが1つ]
    C --> C1[システム/プロジェクトの分離]
    D --> D1[SystemRole で機能追加可能]
    E --> E1[権限チェックのコード削減]

    style A fill:#339af0
    style B fill:#51cf66
    style C fill:#51cf66
    style D fill:#51cf66
    style E fill:#51cf66
```

### 10.3 次のアクション

1. **即時**: データベース移行スクリプトの作成
2. **短期**: フロントエンドの表示ロジック更新
3. **中期**: `is_owner`/`is_admin` フィールドの廃止検討
4. **長期**: システム管理機能の追加実装

---

## 付録

### A. 参考リンク

- コミット: `dee03f2`
- ブランチ: `claude/create-api-011CUfG6ZYaP2bo3FVMsXtNr`
- 関連Issue: （該当する場合記載）

### B. 用語集

| 用語 | 説明 |
|------|------|
| SystemRole | ユーザーのシステムレベル権限（SYSTEM_ADMIN/USER） |
| ProjectRole | プロジェクトメンバーのロール（PROJECT_ADMIN/MEMBER/VIEWER） |
| PROJECT_ADMIN | 旧OWNER+ADMINを統合した新しいプロジェクト管理者ロール |
| 最後の管理者保護 | プロジェクトに最低1人のPROJECT_ADMINを維持する制約 |

### C. 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-10-31 | 1.0 | 初版作成 - 権限システム再設計完了 |

---

**作成者**: Claude Code
**最終更新**: 2025-10-31
