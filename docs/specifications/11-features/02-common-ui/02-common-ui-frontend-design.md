# 共通UI フロントエンド設計書（UI-001〜UI-011）

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| header | ヘッダー | 全ページ共通 | グローバルナビゲーション（検索、通知、ユーザーメニュー） |
| sidebar | サイドバー | 全ページ共通 | サイドナビゲーション（権限ベース表示） |
| notifications | 通知一覧 | /notifications | 全通知一覧ページ（オプション） |

### 1.2 コンポーネント構成

```text
features/common/
├── components/
│   ├── Header/
│   │   ├── Header.tsx
│   │   ├── UserMenu.tsx
│   │   ├── NotificationBell.tsx
│   │   ├── NotificationBadge.tsx
│   │   ├── NotificationDropdown.tsx
│   │   ├── GlobalSearch.tsx
│   │   ├── SearchInput.tsx
│   │   ├── SearchDropdown.tsx
│   │   └── SearchResultItem.tsx
│   ├── Sidebar/
│   │   ├── Sidebar.tsx
│   │   ├── SidebarSection.tsx
│   │   ├── SidebarItem.tsx
│   │   └── ProjectNavigator.tsx
│   └── Layout/
│       └── AppLayout.tsx
├── hooks/
│   ├── useUserContext.ts
│   ├── usePermissions.ts
│   ├── useNavigation.ts
│   ├── useGlobalSearch.ts
│   ├── useSearchDebounce.ts
│   ├── useNotifications.ts
│   ├── useUnreadCount.ts
│   └── useNotificationPolling.ts
├── contexts/
│   └── UserContextProvider.tsx
├── api/
│   ├── userContextApi.ts
│   ├── searchApi.ts
│   └── notificationApi.ts
└── types/
    ├── userContext.ts
    ├── search.ts
    └── notification.ts
```

---

## 2. 画面詳細設計

### 2.1 サイドバー（sidebar）

#### セクション構成

| セクションID | セクション名 | 必要権限 | メニュー項目 |
|-------------|-------------|---------|------------|
| dashboard | ダッシュボード | user | ホーム |
| project | プロジェクト管理 | user | プロジェクト、プロジェクト作成 |
| analysis | 個別施策分析 | user | 分析セッション一覧、新規セッション作成 |
| driver-tree | ドライバーツリー | user | ツリー一覧、新規ツリー作成、カテゴリマスタ |
| file | ファイル管理 | user | ファイル一覧、アップロード |
| system-admin | システム管理 | system_admin | ユーザー管理、ロール管理、検証カテゴリ、課題マスタ |
| monitoring | 監視・運用 | system_admin | システム統計、操作履歴、監査ログ、全プロジェクト |
| operations | システム運用 | system_admin | システム設定、通知管理、セキュリティ、一括操作 |

#### 表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 表示セクション | セクション群 | `GET /api/v1/user_account/me/context` | `sidebar.visibleSections` | 配列→セクション表示判定 |
| プロジェクトリンク | ナビゲーション | 同上 | `navigation.projectNavigationType` | `detail`→詳細直接遷移, `list`→一覧遷移 |
| プロジェクト名 | テキスト | 同上 | `navigation.defaultProjectName` | 1件時のみ表示 |

#### 動的遷移ルール

| 条件 | 遷移先 | URL |
|-----|-------|-----|
| プロジェクト数 = 0 | プロジェクト一覧（空状態） | `/projects` |
| プロジェクト数 = 1 | プロジェクト詳細 | `/projects/{projectId}` |
| プロジェクト数 > 1 | プロジェクト一覧 | `/projects` |

### 2.2 ヘッダー（header）

#### 表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ユーザー名 | テキスト | `GET /api/v1/user_account/me/context` | `user.displayName` | - |
| ユーザーアバター | イニシャル | 同上 | `user.displayName` | 先頭2文字 |
| 通知バッジ | バッジ | 同上 | `notifications.unreadCount` | 0の場合非表示、99+表示 |
| 管理者バッジ | バッジ | 同上 | `permissions.isSystemAdmin` | `true`の場合のみ表示 |

#### ユーザーメニュー

| メニュー項目 | 表示条件 | 遷移先 |
|------------|---------|-------|
| プロフィール | 常時 | `/settings/profile` |
| 設定 | 常時 | `/settings` |
| 管理パネル | isSystemAdmin = true | `/admin` |
| ログアウト | 常時 | Azure AD logout |

### 2.3 グローバル検索（GlobalSearch）

#### 検索入力

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 検索ボックス | テキスト入力 | - | `GET /api/v1/search` | `q` | 2文字以上で検索実行 |
| タイプフィルタ | セレクト | - | 同上 | `type` | project/session/file/tree |

#### 検索結果表示

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 検索結果件数 | テキスト | `GET /api/v1/search` | `total` | "n件" 形式 |
| 結果アイテム（アイコン） | アイコン | 同上 | `results[].type` | type→絵文字マッピング |
| 結果アイテム（名前） | テキスト | 同上 | `results[].highlightedText` | HTMLとしてレンダリング |
| 結果アイテム（説明） | テキスト | 同上 | `results[].description` | 50文字で切り詰め |
| 結果アイテム（プロジェクト名） | テキスト | 同上 | `results[].projectName` | 親プロジェクト表示 |
| 結果アイテム（更新日時） | テキスト | 同上 | `results[].updatedAt` | 相対時間表示 |
| 空状態 | アイコン+テキスト | - | - | "検索結果がありません" |

#### タイプアイコンマッピング

| type | アイコン | 説明 |
|------|---------|------|
| project | 📁 | プロジェクト |
| session | 📊 | 分析セッション |
| file | 📄 | ファイル |
| tree | 🌳 | ドライバーツリー |

#### キーボードショートカット

| キー | 動作 |
|------|------|
| Ctrl+K / Cmd+K | 検索ボックスにフォーカス |
| ↑ | 前の結果を選択 |
| ↓ | 次の結果を選択 |
| Enter | 選択中の結果に遷移 |
| Esc | ドロップダウンを閉じる |

### 2.4 通知ベル（NotificationBell）

#### 通知ベルコンポーネント

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 通知ベルアイコン | アイコンボタン | - | - | 🔔 |
| 未読バッジ | バッジ | `GET /api/v1/user_account/me/context` | `notifications.unreadCount` | 0の場合非表示、99+表示 |

#### 通知ドロップダウン表示

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ヘッダータイトル | テキスト | - | - | "通知" |
| すべて既読ボタン | リンクボタン | `PATCH /api/v1/notifications/read-all` | - | 未読がある場合のみ表示 |
| 通知アイテム（アイコン） | アイコン | `GET /api/v1/notifications` | `items[].icon` | 絵文字表示 |
| 通知アイテム（タイトル） | テキスト | 同上 | `items[].title` | 1行表示 |
| 通知アイテム（メッセージ） | テキスト | 同上 | `items[].message` | 100文字切り詰め |
| 通知アイテム（時間） | テキスト | 同上 | `items[].createdAt` | 相対時間表示 |
| 通知アイテム（未読マーク） | スタイル | 同上 | `items[].isRead` | 未読時に背景色変更 |
| 空状態 | アイコン+テキスト | - | - | "通知はありません" |
| フッターリンク | リンク | - | - | "すべての通知を見る" |

#### 通知タイプアイコンマッピング

| type | icon | 説明 |
|------|------|------|
| member_added | 👥 | メンバー追加 |
| member_removed | 👤 | メンバー削除 |
| session_complete | ✅ | セッション完了 |
| file_uploaded | 📄 | ファイルアップロード |
| tree_updated | 🌳 | ツリー更新 |
| project_invitation | 📨 | プロジェクト招待 |
| system_announcement | 📢 | システムお知らせ |

#### アクション

| 画面項目 | 操作 | APIエンドポイント | 備考 |
|---------|-----|------------------|------|
| 通知アイテムクリック | 既読化+遷移 | `PATCH /api/v1/notifications/{id}/read` | 関連画面へ遷移 |
| すべて既読ボタン | クリック | `PATCH /api/v1/notifications/read-all` | 確認なしで実行 |
| 削除ボタン | クリック | `DELETE /api/v1/notifications/{id}` | 確認ダイアログ表示 |

### 2.5 通知一覧ページ（notifications）

#### 一覧表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 通知アイコン | アイコン | `GET /api/v1/notifications` | `items[].icon` | 絵文字表示 |
| 通知タイトル | テキスト | 同上 | `items[].title` | - |
| 通知メッセージ | テキスト | 同上 | `items[].message` | - |
| 通知日時 | 日時 | 同上 | `items[].createdAt` | YYYY/MM/DD HH:mm |
| 既読状態 | バッジ | 同上 | `items[].isRead` | `true`→"既読", `false`→"未読" |
| 関連リソース | リンク | 同上 | `items[].linkUrl` | 遷移リンク表示 |

#### ページネーション

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| ページ番号 | ボタン群 | `GET /api/v1/notifications` | `total`, `skip`, `limit` | `Math.ceil(total / limit)` でページ数計算 |

---

## 3. 画面項目・APIマッピング

### 3.1 コンテキスト取得

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ユーザーID | - | `GET /api/v1/user_account/me/context` | `user.id` | 内部使用 |
| ユーザー名 | テキスト | 同上 | `user.displayName` | - |
| メール | テキスト | 同上 | `user.email` | - |
| ロール | 配列 | 同上 | `user.roles` | - |
| システム管理者フラグ | boolean | 同上 | `permissions.isSystemAdmin` | - |
| 表示セクション | 配列 | 同上 | `sidebar.visibleSections` | - |
| プロジェクト数 | 数値 | 同上 | `navigation.projectCount` | - |
| 遷移タイプ | enum | 同上 | `navigation.projectNavigationType` | `list` or `detail` |
| デフォルトプロジェクトID | UUID | 同上 | `navigation.defaultProjectId` | 1件時のみ |
| 未読通知数 | 数値 | 同上 | `notifications.unreadCount` | - |

### 3.2 グローバル検索

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 検索キーワード | テキスト | ✓ | `GET /api/v1/search` | `q` | 2文字以上 |
| タイプフィルタ | セレクト | - | 同上 | `type` | project/session/file/tree |
| 取得件数 | 数値 | - | 同上 | `limit` | デフォルト10 |

### 3.3 通知管理

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 既読フィルタ | セレクト | - | `GET /api/v1/notifications` | `is_read` | true/false |
| スキップ | 数値 | - | 同上 | `skip` | ≥0 |
| 取得件数 | 数値 | - | 同上 | `limit` | デフォルト20、最大100 |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| アプリ初期化 | `GET /api/v1/user_account/me/context` | 1回のみ |
| ページリロード | `GET /api/v1/user_account/me/context` | キャッシュ無効時 |
| ログイン成功後 | `GET /api/v1/user_account/me/context` | 強制リフレッシュ |
| プロジェクト参加/離脱後 | refetch() | ナビゲーション更新 |
| 検索入力変更 | `GET /api/v1/search` | 300msデバウンス、2文字以上 |
| ベルクリック | `GET /api/v1/notifications?limit=10` | ドロップダウン用 |
| 通知クリック | `PATCH /api/v1/notifications/{id}/read` | 既読化 |
| すべて既読クリック | `PATCH /api/v1/notifications/read-all` | 一括既読 |
| 60秒ごと | `GET /api/v1/user_account/me/context` | ポーリング（未読件数更新） |

---

## 5. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | アクセス拒否画面を表示 |
| 500 Server Error | エラー画面を表示、リトライボタン |
| Network Error | オフライン表示、リトライボタン |

---

## 6. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| 初期ロード | コンテキストAPIは軽量（1KB未満） |
| キャッシュ | React Query で5分間キャッシュ |
| 再レンダリング | useMemo でセクション表示を最適化 |
| バンドルサイズ | セクションコンポーネントは遅延ロード |
| 検索 | 300msデバウンスでAPI呼び出しを最適化 |
| 通知 | 60秒ポーリングで負荷軽減 |

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| UI-001 | 権限に応じたメニューを表示する | `GET /user_account/me/context` | Sidebar | 設計済 |
| UI-002 | 参画プロジェクト数に応じて遷移先を切り替える | `GET /user_account/me/context` | ProjectNavigator | 設計済 |
| UI-003 | ユーザーコンテキスト情報を取得する | `GET /user_account/me/context` | UserContextProvider | 設計済 |
| UI-004 | プロジェクト・セッション・ファイル・ツリーを横断検索する | `GET /search` | GlobalSearch | 設計済 |
| UI-005 | 検索結果をフィルタリングする | `GET /search?type=` | SearchDropdown | 設計済 |
| UI-006 | 未読通知一覧を取得する | `GET /notifications` | NotificationDropdown | 設計済 |
| UI-007 | 通知詳細を取得する | `GET /notifications/{id}` | NotificationDropdown | 設計済 |
| UI-008 | 通知を既読にする | `PATCH /notifications/{id}/read` | NotificationDropdown | 設計済 |
| UI-009 | すべての通知を既読にする | `PATCH /notifications/read-all` | NotificationDropdown | 設計済 |
| UI-010 | 通知を削除する | `DELETE /notifications/{id}` | NotificationDropdown | 設計済 |
| UI-011 | 未読通知バッジを表示する | `GET /user_account/me/context` | NotificationBadge | 設計済 |

---

## 8. 関連ドキュメント

- **バックエンド設計書**: [01-common-ui-design.md](./01-common-ui-design.md)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)
- **ユーザー管理設計書**: [../03-user-management/01-user-management-design.md](../03-user-management/01-user-management-design.md)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|-----|------|
| ドキュメントID | COMMON-UI-FRONTEND-DESIGN-001 |
| 対象ユースケース | UI-001〜UI-011 |
| 最終更新日 | 2026-01-01 |
| 作成者 | 開発チーム |
| レビュー状態 | 設計済 |
