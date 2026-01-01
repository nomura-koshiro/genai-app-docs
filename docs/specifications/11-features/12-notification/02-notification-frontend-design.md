# ユーザー通知 フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| - | ヘッダー通知（コンポーネント） | 全ページ共通 | 通知ベルとドロップダウン |
| notifications | 通知一覧 | /notifications | 全通知一覧ページ（オプション） |

### 1.2 コンポーネント構成

```text
features/notification/
├── components/
│   ├── NotificationBell/
│   │   ├── NotificationBell.tsx
│   │   ├── NotificationBadge.tsx
│   │   └── NotificationDropdown.tsx
│   ├── NotificationList/
│   │   ├── NotificationList.tsx
│   │   └── NotificationItem.tsx
│   └── NotificationEmpty/
│       └── NotificationEmpty.tsx
├── hooks/
│   ├── useNotifications.ts
│   ├── useUnreadCount.ts
│   └── useNotificationPolling.ts
├── api/
│   └── notificationApi.ts
└── types/
    └── notification.ts
```

---

## 2. 画面詳細設計

### 2.1 通知ベルコンポーネント

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| 通知ベルアイコン | アイコンボタン | - | - | 🔔 |
| 未読バッジ | バッジ | GET /notifications | unreadCount | 0の場合非表示、99+表示 |

### 2.2 通知ドロップダウン

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ヘッダータイトル | テキスト | - | - | "通知" |
| すべて既読ボタン | リンクボタン | PATCH /notifications/read-all | - | 未読がある場合のみ表示 |
| 通知アイテム（アイコン） | アイコン | GET /notifications | notifications[].icon | 絵文字表示 |
| 通知アイテム（メッセージ） | テキスト | GET /notifications | notifications[].message | 1行表示、100文字切り詰め |
| 通知アイテム（時間） | テキスト | GET /notifications | notifications[].createdAt | 相対時間表示 |
| 通知アイテム（未読マーク） | スタイル | GET /notifications | notifications[].isRead | 未読時に背景色変更 |
| 空状態 | アイコン+テキスト | - | - | "通知はありません" |
| フッターリンク | リンク | - | - | "すべての通知を見る" |

### 2.3 通知タイプアイコンマッピング

| type | icon | 説明 |
|------|------|------|
| member_added | 👥 | メンバー追加 |
| member_removed | 👤 | メンバー削除 |
| session_complete | ✅ | セッション完了 |
| file_uploaded | 📄 | ファイルアップロード |
| tree_updated | 🌳 | ツリー更新 |
| project_invitation | 📨 | プロジェクト招待 |
| system_announcement | 📢 | システムお知らせ |

---

## 3. インタラクション設計

### 3.1 通知フロー

```text
1. ページロード → 未読件数を取得
2. ベルクリック → ドロップダウン表示、通知一覧取得
3. 通知クリック → 既読にして遷移先URLに移動
4. すべて既読クリック → 全件既読、バッジ非表示
5. フッタークリック → 通知一覧ページに遷移
6. 外部クリック → ドロップダウンを閉じる
```

### 3.2 ポーリング設定

| 設定 | 値 | 説明 |
|------|---|------|
| ポーリング間隔 | 60秒 | 未読件数の定期取得 |
| 初期取得 | ページロード時 | 未読件数を即座に取得 |
| 再取得トリガー | ドロップダウン表示時 | 最新の通知を取得 |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| ページロード | GET /notifications?limit=1 | 未読件数のみ取得 |
| ベルクリック | GET /notifications?limit=10 | ドロップダウン用 |
| 通知クリック | PATCH /notifications/{id}/read | 既読化 |
| すべて既読クリック | PATCH /notifications/read-all | 一括既読 |
| 60秒ごと | GET /notifications?limit=1 | ポーリング（未読件数） |
