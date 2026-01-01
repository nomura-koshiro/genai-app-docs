# 個別施策分析 フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|-------|------|------|
| sessions | セッション一覧 | `/projects/{id}/sessions` | セッション一覧表示・検索 |
| session-new | セッション作成 | `/projects/{id}/sessions/new` | 新規セッション作成ウィザード |
| analysis | 分析画面 | `/projects/{id}/sessions/{id}/analysis` | チャット・ステップ・結果表示 |
| snapshots | スナップショット履歴 | `/projects/{id}/sessions/{id}/snapshots` | スナップショットタイムライン・復元 |
| session-detail | セッション詳細 | `/projects/{id}/sessions/{id}` | 完了セッションの結果閲覧 |
| verifications | 検証マスタ管理 | `/admin/verifications` | 検証カテゴリ管理（管理者） |
| issues | 課題マスタ管理 | `/admin/issues` | 分析課題管理（管理者） |
| issue-edit | 課題編集 | `/admin/issues/{id}` | 課題詳細・プロンプト編集 |

### 1.2 コンポーネント構成

```text
pages/projects/[id]/sessions/
├── index.tsx              # セッション一覧
├── new.tsx                # セッション作成ウィザード
└── [sessionId]/
    ├── index.tsx          # セッション詳細（結果閲覧）
    ├── analysis.tsx       # 分析画面
    └── snapshots.tsx      # スナップショット履歴

pages/admin/
├── verifications.tsx      # 検証マスタ管理
├── issues.tsx             # 課題マスタ管理
└── issues/[id].tsx        # 課題編集
```

---

## 2. 画面詳細設計

### 2.1 セッション一覧画面（sessions）

#### 検索・フィルタ項目

| 画面項目 | 入力形式 | APIエンドポイント | クエリパラメータ | 備考 |
|---------|---------|------------------|-----------------|------|
| セッション名検索 | テキスト | `GET .../analysis/session` | - | フロントでフィルタ |
| 課題フィルタ | セレクト | 同上 | - | フロントでフィルタ |

#### 一覧表示項目

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| セッション名 | テキスト(strong) | `GET .../analysis/session` | `sessions[].name` | - |
| 課題 | テキスト | 同上 | `sessions[].issue.name` | - |
| 入力ファイル | テキスト | 同上 | `sessions[].inputFile.filename` | null→"-" |
| スナップショット | 数値 | 同上 | `sessions[].snapshotCount` | - |
| 作成者 | テキスト | 同上 | `sessions[].creator.displayName` | - |
| 更新日時 | 日時 | 同上 | `sessions[].updatedAt` | ISO8601→YYYY/MM/DD HH:mm |
| 開くボタン | ボタン | - | - | analysis画面へ遷移 |
| 複製ボタン | ボタン | `POST .../analysis/session` | - | セッション複製 |

### 2.2 セッション作成画面（session-new）

#### STEP 1: 分析テーマ選択

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | 備考 |
|---------|---------|-----|------------------|---------------------|------|
| 検証カテゴリ | カード選択 | ✓ | `GET /api/v1/analysis/template` | - | カテゴリ一覧から選択 |
| 分析課題 | セレクト | ✓ | `POST .../analysis/session` | `issueId` | カテゴリにより絞り込み |

#### STEP 2: データ準備

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | 備考 |
|---------|---------|-----|------------------|---------------------|------|
| 入力ファイル | セレクト | ✓ | `PUT .../session/{id}` | `inputFileId` | プロジェクトファイルから選択 |
| 対象シート | セレクト | ✓ | 同上 | - | Excelファイルの場合 |
| 時間軸 | セレクト | ✓ | `PATCH .../file/{id}` | `axisConfig.timeAxis` | 列選択 |
| 分析対象値 | セレクト | ✓ | 同上 | `axisConfig.valueAxis` | 列選択 |
| グループ化 | セレクト | - | 同上 | `axisConfig.groupAxis` | 列選択（任意） |

#### STEP 3: 確認

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | 備考 |
|---------|---------|-----|------------------|---------------------|------|
| セッション名 | テキスト | - | `POST .../analysis/session` | `name` | 空白時は自動生成 |

### 2.3 分析画面（analysis）

#### ページヘッダー

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | アクション | 備考 |
|---------|---------|------------------|---------------------|-----------|------|
| セッション名 | テキスト(large) | `GET .../session/{id}` | `name` | - | - |
| スナップショット履歴ボタン | ボタン | - | - | スナップショット履歴画面へ遷移 | - |
| 保存ボタン | ボタン | `POST .../snapshot` | - | 現在のスナップショット保存 | ASN-001 |

#### 情報アラート

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| 現在のスナップショット番号 | バッジ | `GET .../session/{id}` | `currentSnapshot.snapshotOrder` | "スナップショット #N" |
| 入力ファイル名 | テキスト | 同上 | `inputFile.filename` | - |
| 課題名 | テキスト | 同上 | `issue.name` | - |

#### メインエリア（チャット）

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| チャット履歴 | メッセージリスト | `GET .../session/{id}/result` | `chats` | role別スタイル |
| ユーザーメッセージ | 右寄せ | 同上 | `chats[].content` (role=user) | - |
| アシスタント返答 | 左寄せ | 同上 | `chats[].content` (role=assistant) | Markdown対応 |
| メッセージ入力 | テキストエリア | `POST .../session/{id}/chat` | `content` | - |

#### 右サイドバー（ファイル情報・ステップ）

**ファイル情報カード**

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| ファイル名 | テキスト | `GET .../session/{id}` | `inputFile.filename` | - |
| ファイルサイズ | テキスト | 同上 | `inputFile.size` | バイト→KB/MB変換 |
| 行数 | テキスト | 同上 | `inputFile.rows` | - |
| 列数 | テキスト | 同上 | `inputFile.columns` | - |

**ステップリスト**

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| ステップリスト | カードリスト | `GET .../session/{id}/result` | `steps` | ドラッグ並替え可 |
| ステップタイプ | バッジ | 同上 | `steps[].stepType` | - |
| ステップ設定 | 展開パネル | 同上 | `steps[].stepConfig` | JSON表示 |

### 2.4 スナップショット履歴画面（snapshots）

#### ページヘッダー

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | アクション | 備考 |
|---------|---------|------------------|---------------------|-----------|------|
| タイトル | テキスト | - | - | - | "スナップショット履歴" |
| 戻るボタン | ボタン | - | - | 分析画面へ戻る | - |

#### 警告アラート

| 画面項目 | 表示形式 | 備考 |
|---------|---------|------|
| 警告メッセージ | アラート | "スナップショットを復元すると、現在の変更が失われます。" |

#### スナップショットタイムライン

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | アクション | 備考 |
|---------|---------|------------------|---------------------|-----------|------|
| スナップショット番号 | バッジ | `GET .../session/{id}/snapshot` | `snapshots[].snapshotOrder` | - | "#1", "#2", ... |
| 作成日時 | テキスト | 同上 | `snapshots[].createdAt` | - | ISO8601→YYYY/MM/DD HH:mm |
| 説明 | テキスト | 同上 | `snapshots[].description` | - | 自動生成またはユーザー入力 |
| 現在地バッジ | バッジ | 同上 | `snapshots[].id === currentSnapshotId` | - | "現在ここ" |
| 復元ボタン | ボタン | `PUT .../session/{id}` | - | スナップショット復元 | ASN-005 |
| 削除ボタン | アイコンボタン | `DELETE .../snapshot/{id}` | - | スナップショット削除 | ASN-002 |

### 2.5 セッション詳細画面（session-detail）

#### ステータスバナー

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| ステータス | バッジ | `GET .../session/{id}` | `status` | "完了", "進行中", "アーカイブ" |
| 完了日時 | テキスト | 同上 | `completedAt` | status=completedの場合のみ |
| スナップショット数 | テキスト | 同上 | `snapshotCount` | - |

#### 分析結果サマリー

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| 課題名 | テキスト | `GET .../session/{id}/result` | `issue.name` | - |
| 入力ファイル | テキスト | 同上 | `inputFile.filename` | - |
| チャット数 | 数値 | 同上 | `chatCount` | - |
| ステップ数 | 数値 | 同上 | `stepCount` | - |

#### キーインサイト

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| インサイトリスト | リスト | `GET .../session/{id}/result` | `insights` | AIが抽出した主要な発見 |
| インサイトテキスト | テキスト | 同上 | `insights[].text` | Markdown対応 |

#### AI対話履歴（折り畳み可能）

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| チャット履歴 | メッセージリスト | `GET .../session/{id}/messages` | `chats` | 読み取り専用 |
| ユーザーメッセージ | 右寄せ | 同上 | `chats[].content` (role=user) | - |
| アシスタント返答 | 左寄せ | 同上 | `chats[].content` (role=assistant) | Markdown対応 |

#### サイドバー（セッション情報）

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| セッション名 | テキスト | `GET .../session/{id}` | `name` | - |
| 作成者 | テキスト | 同上 | `creator.displayName` | - |
| 作成日時 | テキスト | 同上 | `createdAt` | ISO8601→YYYY/MM/DD HH:mm |
| 最終更新日時 | テキスト | 同上 | `updatedAt` | ISO8601→YYYY/MM/DD HH:mm |

#### サイドバー（アクション）

| 画面項目 | 表示形式 | APIエンドポイント | アクション | 備考 |
|---------|---------|------------------|-----------|------|
| 複製ボタン | ボタン | `POST .../session/{id}/duplicate` | セッション複製 | - |
| エクスポートボタン | ボタン | `GET .../session/{id}/export` | 結果をPDF/CSV出力 | - |
| アーカイブボタン | ボタン | `PUT .../session/{id}` | status=archivedに変更 | - |

---

## 7. ユースケースカバレッジ表

| UC ID | 機能名 | API | 画面コンポーネント | ステータス |
|-------|-------|-----|-------------------|-----------|
| AS-001 | セッション一覧表示 | `GET /project/{id}/analysis/sessions` | sessions | 実装済 |
| AS-002 | セッション作成 | `POST /project/{id}/analysis/session` | session-new | 実装済 |
| AS-003 | セッション詳細取得 | `GET /project/{id}/analysis/session/{id}` | session-detail | 実装済 |
| AS-004 | セッション削除 | `DELETE /project/{id}/analysis/session/{id}` | sessions | 実装済 |
| AF-001 | 分析ファイル一覧 | `GET /session/{id}/files` | analysis | 実装済 |
| AF-002 | 分析ファイル設定 | `PATCH /session/{id}/file/{id}` | analysis | 実装済 |
| ASN-001 | スナップショット作成 | `POST /session/{id}/snapshot` | analysis | 実装済 |
| ASN-002 | スナップショット一覧 | `GET /session/{id}/snapshots` | snapshots | 実装済 |
| ASN-003 | スナップショット復元 | `POST /snapshot/{id}/restore` | snapshots | 実装済 |
| AC-001 | チャット送信 | `POST /session/{id}/chat` | analysis | 実装済 |
| AC-002 | チャット履歴取得 | `GET /session/{id}/messages` | analysis | 実装済 |
| AST-001 | ステップ追加 | `POST /session/{id}/step` | analysis | 実装済 |
| AST-002 | ステップ更新 | `PATCH /step/{id}` | analysis | 実装済 |

---

## 8. 関連ドキュメント

- **バックエンド設計**: [01-analysis-design.md](./01-analysis-design.md)
- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **モックアップ**: [../../03-mockup/pages/sessions.js](../../03-mockup/pages/sessions.js)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 9. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | AN-FRONTEND-001 |
| 対象ユースケース | AS-001〜AS-007, AF-001〜AF-006, ASN-001〜ASN-005, AC-001〜AC-003, AST-001〜AST-006 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `pages/projects/[id]/sessions/` |
|  | `pages/admin/verifications.tsx` |
|  | `pages/admin/issues/` |
