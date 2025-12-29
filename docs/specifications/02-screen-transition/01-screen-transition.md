# CAMPシステム 画面遷移図

本文書は、CAMPシステムの画面構成と遷移を定義するものです。

---

## 1. 全体画面構成

### 1.1 レイアウト構造

```text
┌─────────────────────────────────────────────────────────────┐
│                        ヘッダー                              │
│  [ロゴ]                              [通知] [ユーザーメニュー] │
├────────────┬────────────────────────────────────────────────┤
│            │                                                │
│            │                                                │
│  サイド    │              メインコンテンツ                    │
│  バー      │                                                │
│  メニュー  │                                                │
│            │                                                │
│            │                                                │
│            │                                                │
├────────────┴────────────────────────────────────────────────┤
│                        フッター                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 サイドバーメニュー構成

```text
📁 ダッシュボード
├─ ホーム

📁 プロジェクト管理
├─ プロジェクト一覧
├─ プロジェクト作成
└─ メンバー管理

📁 個別施策分析
├─ 分析セッション一覧
├─ 新規セッション作成
└─ スナップショット履歴

📁 ドライバーツリー
├─ ツリー一覧
├─ ツリー作成
├─ 数式マスタ管理
└─ カテゴリマスタ管理

📁 ファイル管理
├─ ファイル一覧
└─ アップロード

📁 システム管理（Admin）
├─ ユーザー管理
├─ ロール管理
├─ 検証マスタ管理
└─ 課題マスタ管理
```

---

## 2. 画面一覧

### 2.1 認証系画面

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| AUTH-001 | ログイン画面 | /login | Azure AD認証画面 |
| AUTH-002 | ログアウト確認 | /logout | ログアウト確認ダイアログ |

### 2.2 ダッシュボード系画面

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| DASH-001 | ダッシュボード | /dashboard | ホーム画面、概要表示 |

### 2.3 プロジェクト管理系画面

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| PROJ-001 | プロジェクト一覧 | /projects | プロジェクト一覧表示 |
| PROJ-002 | プロジェクト作成 | /projects/new | 新規プロジェクト作成フォーム |
| PROJ-003 | プロジェクト詳細 | /projects/:id | プロジェクト詳細・編集 |
| PROJ-004 | メンバー管理 | /projects/:id/members | メンバー追加・削除・ロール変更 |
| PROJ-005 | ファイル管理 | /projects/:id/files | プロジェクトファイル一覧 |

### 2.4 個別施策分析系画面

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| ANAL-001 | セッション一覧 | /projects/:id/sessions | 分析セッション一覧 |
| ANAL-002 | セッション作成 | /projects/:id/sessions/new | 新規セッション作成 |
| ANAL-003 | 分析画面 | /sessions/:id | チャット＆ステップ操作画面 |
| ANAL-004 | スナップショット履歴 | /sessions/:id/snapshots | スナップショット一覧・分岐 |

### 2.5 ドライバーツリー系画面

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| TREE-001 | ツリー一覧 | /projects/:id/trees | ドライバーツリー一覧 |
| TREE-002 | ツリー作成 | /projects/:id/trees/new | 新規ツリー作成 |
| TREE-003 | ツリー編集 | /trees/:id | ノード・リレーション編集 |
| TREE-004 | 施策設定 | /trees/:id/policies | 施策の追加・編集 |
| TREE-005 | 数式マスタ一覧 | /admin/formulas | 数式マスタ管理 |
| TREE-006 | カテゴリマスタ一覧 | /admin/categories | カテゴリマスタ管理 |

### 2.6 システム管理系画面

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| ADMIN-001 | ユーザー一覧 | /admin/users | ユーザー一覧・検索 |
| ADMIN-002 | ユーザー詳細 | /admin/users/:id | ユーザー詳細・ロール管理 |
| ADMIN-003 | 検証マスタ一覧 | /admin/verifications | 検証マスタ管理 |
| ADMIN-004 | 課題マスタ一覧 | /admin/issues | 課題マスタ管理 |
| ADMIN-005 | 課題マスタ詳細 | /admin/issues/:id | プロンプト・初期メッセージ設定 |

---

## 3. 画面遷移図

### 3.1 認証フロー

::: mermaid
graph TD
    subgraph 認証
        LOGIN[AUTH-001: ログイン画面]
        LOGOUT[AUTH-002: ログアウト確認]
    end

    subgraph メイン
        DASH[DASH-001: ダッシュボード]
    end

    LOGIN -->|Azure AD認証成功| DASH
    LOGIN -->|初回ログイン| DASH
    DASH -->|ログアウト| LOGOUT
    LOGOUT -->|確認| LOGIN
    LOGOUT -->|キャンセル| DASH
:::

### 3.2 プロジェクト管理フロー

::: mermaid
graph TD
    subgraph プロジェクト管理
        PLIST[PROJ-001: プロジェクト一覧]
        PNEW[PROJ-002: プロジェクト作成]
        PDETAIL[PROJ-003: プロジェクト詳細]
        PMEMBER[PROJ-004: メンバー管理]
        PFILE[PROJ-005: ファイル管理]
    end

    DASH[ダッシュボード] -->|サイドメニュー| PLIST
    PLIST -->|新規作成ボタン| PNEW
    PLIST -->|行クリック| PDETAIL
    PNEW -->|作成完了| PDETAIL
    PNEW -->|キャンセル| PLIST
    PDETAIL -->|タブ: メンバー| PMEMBER
    PDETAIL -->|タブ: ファイル| PFILE
    PMEMBER -->|タブ: 詳細| PDETAIL
    PFILE -->|タブ: 詳細| PDETAIL
:::

### 3.3 個別施策分析フロー

::: mermaid
graph TD
    subgraph 個別施策分析
        SLIST[ANAL-001: セッション一覧]
        SNEW[ANAL-002: セッション作成]
        SDETAIL[ANAL-003: 分析画面]
        SSNAP[ANAL-004: スナップショット履歴]
    end

    PDETAIL[プロジェクト詳細] -->|分析タブ| SLIST
    SLIST -->|新規作成| SNEW
    SLIST -->|行クリック| SDETAIL
    SNEW -->|作成完了| SDETAIL
    SDETAIL -->|履歴ボタン| SSNAP
    SSNAP -->|スナップショット選択| SDETAIL
    SSNAP -->|戻る| SDETAIL

    subgraph 分析画面内操作
        CHAT[チャットパネル]
        STEP[ステップパネル]
        FILE[ファイル選択]
    end

    SDETAIL --> CHAT
    SDETAIL --> STEP
    SDETAIL --> FILE
    CHAT -->|AI応答| STEP
:::

### 3.4 ドライバーツリーフロー

::: mermaid
graph TD
    subgraph ドライバーツリー
        TLIST[TREE-001: ツリー一覧]
        TNEW[TREE-002: ツリー作成]
        TEDIT[TREE-003: ツリー編集]
        TPOLICY[TREE-004: 施策設定]
    end

    PDETAIL[プロジェクト詳細] -->|ツリータブ| TLIST
    TLIST -->|新規作成| TNEW
    TLIST -->|行クリック| TEDIT
    TNEW -->|作成完了| TEDIT
    TEDIT -->|施策タブ| TPOLICY
    TPOLICY -->|ツリータブ| TEDIT

    subgraph ツリー編集内操作
        NODE[ノード追加/編集]
        REL[リレーション定義]
        DATA[データ紐付け]
    end

    TEDIT --> NODE
    TEDIT --> REL
    TEDIT --> DATA
:::

### 3.5 システム管理フロー

::: mermaid
graph TD
    subgraph ユーザー管理
        ULIST[ADMIN-001: ユーザー一覧]
        UDETAIL[ADMIN-002: ユーザー詳細]
    end

    subgraph マスタ管理
        VLIST[ADMIN-003: 検証マスタ一覧]
        ILIST[ADMIN-004: 課題マスタ一覧]
        IDETAIL[ADMIN-005: 課題マスタ詳細]
        FLIST[TREE-005: 数式マスタ一覧]
        CLIST[TREE-006: カテゴリマスタ一覧]
    end

    DASH[ダッシュボード] -->|サイドメニュー| ULIST
    ULIST -->|行クリック| UDETAIL
    UDETAIL -->|戻る| ULIST

    DASH -->|サイドメニュー| VLIST
    DASH -->|サイドメニュー| ILIST
    ILIST -->|行クリック| IDETAIL
    IDETAIL -->|戻る| ILIST

    VLIST -->|課題作成| ILIST
:::

### 3.6 全体遷移図

::: mermaid
graph LR
    subgraph 認証
        LOGIN[ログイン]
    end

    subgraph メイン
        DASH[ダッシュボード]
    end

    subgraph プロジェクト
        PROJ[プロジェクト管理]
        MEMBER[メンバー管理]
        FILE[ファイル管理]
    end

    subgraph 分析
        SESSION[セッション]
        CHAT[チャット分析]
        SNAP[スナップショット]
    end

    subgraph ツリー
        TREE[ツリー編集]
        POLICY[施策設定]
    end

    subgraph 管理
        USER[ユーザー管理]
        MASTER[マスタ管理]
    end

    LOGIN --> DASH
    DASH --> PROJ
    PROJ --> MEMBER
    PROJ --> FILE
    PROJ --> SESSION
    SESSION --> CHAT
    CHAT --> SNAP
    PROJ --> TREE
    TREE --> POLICY
    DASH --> USER
    DASH --> MASTER
:::

---

## 4. 画面遷移マトリクス

### 4.1 主要画面間の遷移

| 遷移元 ＼ 遷移先 | ダッシュボード | プロジェクト一覧 | プロジェクト詳細 | セッション一覧 | 分析画面 | ツリー一覧 | ツリー編集 |
|-----------------|---------------|-----------------|-----------------|---------------|---------|-----------|-----------|
| ログイン | ✓ | - | - | - | - | - | - |
| ダッシュボード | - | ✓ | ✓ | - | - | - | - |
| プロジェクト一覧 | ✓ | - | ✓ | - | - | - | - |
| プロジェクト詳細 | ✓ | ✓ | - | ✓ | - | ✓ | - |
| セッション一覧 | ✓ | - | ✓ | - | ✓ | - | - |
| 分析画面 | ✓ | - | - | ✓ | - | - | - |
| ツリー一覧 | ✓ | - | ✓ | - | - | - | ✓ |
| ツリー編集 | ✓ | - | - | - | - | ✓ | - |

### 4.2 遷移アクション一覧

| アクション | 遷移元 | 遷移先 | トリガー |
|-----------|--------|--------|---------|
| サイドメニュークリック | 任意 | 対象画面 | メニュー項目クリック |
| 一覧行クリック | 一覧画面 | 詳細画面 | テーブル行クリック |
| 新規作成ボタン | 一覧画面 | 作成画面 | ボタンクリック |
| タブ切り替え | 詳細画面 | 同画面別タブ | タブクリック |
| 戻るボタン | 詳細/作成画面 | 一覧画面 | ボタンクリック |
| パンくずリスト | 任意 | 上位階層 | リンククリック |

---

## 5. コンポーネント構成

### 5.1 共通コンポーネント

```text
components/
├── layout/
│   ├── Header.tsx           # ヘッダー
│   ├── Sidebar.tsx          # サイドバーメニュー
│   ├── Footer.tsx           # フッター
│   └── MainLayout.tsx       # メインレイアウト
├── common/
│   ├── Breadcrumb.tsx       # パンくずリスト
│   ├── DataTable.tsx        # データテーブル
│   ├── Modal.tsx            # モーダルダイアログ
│   ├── Tabs.tsx             # タブコンポーネント
│   ├── Form/                # フォーム系
│   │   ├── Input.tsx
│   │   ├── Select.tsx
│   │   ├── Button.tsx
│   │   └── FileUpload.tsx
│   └── Notification.tsx     # 通知
└── features/
    ├── project/             # プロジェクト関連
    ├── analysis/            # 分析関連
    ├── driver-tree/         # ドライバーツリー関連
    └── admin/               # 管理画面関連
```

---

#### ドキュメント管理情報

- **作成日**: 2025年12月25日
- **関連文書**: 02-usecase-flow-analysis.md
- **目的**: 画面構成と遷移の定義
