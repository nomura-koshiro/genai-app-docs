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

### 1.2 共通UIコンポーネント参照

本機能で使用する共通UIコンポーネント（`components/ui/`）:

| コンポーネント | 用途 | 参照元 |
|--------------|------|-------|
| `Card` | セッションカード、ステップカード | [02-shared-ui-components.md](../01-frontend-common/02-shared-ui-components.md) |
| `DataTable` | セッション一覧、スナップショット一覧 | 同上 |
| `Badge` | ステータスバッジ | 同上 |
| `Button` | 操作ボタン | 同上 |
| `Input` | 検索・フォーム入力 | 同上 |
| `Select` | 課題選択、フィルタ | 同上 |
| `Textarea` | プロンプト入力 | 同上 |
| `Modal` | 確認ダイアログ | 同上 |
| `Alert` | 警告・エラー表示 | 同上 |
| `Tabs` | 結果表示タブ | 同上 |
| `Progress` | 分析進捗表示 | 同上 |
| `Skeleton` | 読み込み中表示 | 同上 |
| `EmptyState` | データなし表示 | 同上 |

### 1.3 コンポーネント構成

```text
features/analysis/
├── api/
│   ├── get-sessions.ts              # GET /project/{id}/analysis/session
│   ├── get-session.ts               # GET /session/{id}
│   ├── create-session.ts            # POST /project/{id}/analysis/session
│   ├── update-session.ts            # PUT /session/{id}
│   ├── delete-session.ts            # DELETE /session/{id}
│   ├── get-result.ts                # GET /session/{id}/result
│   ├── send-chat.ts                 # POST /session/{id}/chat
│   ├── get-messages.ts              # GET /session/{id}/messages
│   ├── get-snapshots.ts             # GET /session/{id}/snapshot
│   ├── create-snapshot.ts           # POST /session/{id}/snapshot
│   ├── restore-snapshot.ts          # POST /snapshot/{id}/restore
│   ├── delete-snapshot.ts           # DELETE /snapshot/{id}
│   ├── create-step.ts               # POST /session/{id}/step
│   ├── update-step.ts               # PATCH /step/{id}
│   └── index.ts
├── components/
│   ├── session-card/
│   │   ├── session-card.tsx         # セッションカード（Card使用）
│   │   └── index.ts
│   ├── session-filters/
│   │   ├── session-filters.tsx      # フィルター（Select使用）
│   │   └── index.ts
│   ├── session-wizard/
│   │   ├── session-wizard.tsx       # 作成ウィザード
│   │   ├── step-theme-select.tsx    # STEP1: テーマ選択
│   │   ├── step-data-prep.tsx       # STEP2: データ準備
│   │   ├── step-confirm.tsx         # STEP3: 確認
│   │   └── index.ts
│   ├── analysis-chat/
│   │   ├── analysis-chat.tsx        # チャット形式表示
│   │   └── index.ts
│   ├── analysis-steps/
│   │   ├── analysis-steps.tsx       # ステップ表示
│   │   └── index.ts
│   ├── analysis-results/
│   │   ├── analysis-results.tsx     # 結果表示（Tabs使用）
│   │   └── index.ts
│   ├── snapshot-timeline/
│   │   ├── snapshot-timeline.tsx    # スナップショットタイムライン
│   │   └── index.ts
│   ├── snapshot-card/
│   │   ├── snapshot-card.tsx        # スナップショットカード
│   │   └── index.ts
│   └── index.ts
├── routes/
│   ├── session-list/
│   │   ├── session-list.tsx         # セッション一覧コンテナ
│   │   ├── session-list.hook.ts     # セッション一覧用hook
│   │   └── index.ts
│   ├── session-new/
│   │   ├── session-new.tsx          # セッション作成コンテナ
│   │   ├── session-new.hook.ts      # セッション作成用hook
│   │   └── index.ts
│   ├── session-detail/
│   │   ├── session-detail.tsx       # セッション詳細コンテナ
│   │   ├── session-detail.hook.ts   # セッション詳細用hook
│   │   └── index.ts
│   ├── analysis/
│   │   ├── analysis.tsx             # 分析画面コンテナ
│   │   ├── analysis.hook.ts         # 分析画面用hook
│   │   └── index.ts
│   └── snapshots/
│       ├── snapshots.tsx            # スナップショット履歴コンテナ
│       ├── snapshots.hook.ts        # スナップショット履歴用hook
│       └── index.ts
├── types/
│   ├── api.ts                       # API入出力の型
│   ├── domain.ts                    # ドメインモデル（Session, Snapshot, Chat, Step等）
│   └── index.ts
└── index.ts

app/projects/[id]/sessions/
├── page.tsx               # セッション一覧ページ → SessionList
├── new/
│   └── page.tsx           # セッション作成ウィザードページ → SessionNew
└── [sessionId]/
    ├── page.tsx           # セッション詳細ページ → SessionDetail
    ├── analysis/
    │   └── page.tsx       # 分析画面ページ → Analysis
    └── snapshots/
        └── page.tsx       # スナップショット履歴ページ → Snapshots

app/admin/
├── verifications/
│   └── page.tsx           # 検証マスタ管理ページ
└── issues/
    ├── page.tsx           # 課題マスタ管理ページ
    └── [id]/
        └── page.tsx       # 課題編集ページ
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

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 検証カテゴリ | カード選択 | ✓ | `GET /api/v1/analysis/template` | - | カテゴリ一覧から選択 |
| 分析課題 | セレクト | ✓ | `POST .../analysis/session` | `issueId` | カテゴリにより絞り込み |

#### STEP 2: データ準備

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 入力ファイル | セレクト | ✓ | `PUT .../session/{id}` | `inputFileId` | プロジェクトファイルから選択 |
| 対象シート | セレクト | ✓ | 同上 | - | Excelファイルの場合 |
| 時間軸 | セレクト | ✓ | `PATCH .../file/{id}` | `axisConfig.timeAxis` | 列選択 |
| 分析対象値 | セレクト | ✓ | 同上 | `axisConfig.valueAxis` | 列選択 |
| グループ化 | セレクト | - | 同上 | `axisConfig.groupAxis` | 列選択（任意） |

#### STEP 3: 確認

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
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

##### ファイル情報カード

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 備考 |
|---------|---------|------------------|---------------------|------|
| ファイル名 | テキスト | `GET .../session/{id}` | `inputFile.filename` | - |
| ファイルサイズ | テキスト | 同上 | `inputFile.size` | バイト→KB/MB変換 |
| 行数 | テキスト | 同上 | `inputFile.rows` | - |
| 列数 | テキスト | 同上 | `inputFile.columns` | - |

##### ステップリスト

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

## 3. 画面項目・APIマッピング

### 3.1 セッション一覧取得

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| 課題フィルタ | セレクト | - | `GET /project/{id}/analysis/session` | `issue_id` | UUID |
| スキップ | 数値 | - | 同上 | `skip` | ≥0 |
| 取得件数 | 数値 | - | 同上 | `limit` | デフォルト20、最大100 |

### 3.2 セッション作成

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| セッション名 | テキスト | - | `POST /project/{id}/analysis/session` | `name` | 空白時は自動生成 |
| 分析課題 | セレクト | ✓ | 同上 | `issueId` | UUID |
| 入力ファイル | セレクト | ✓ | `PUT /session/{id}` | `inputFileId` | UUID |

### 3.3 チャット送信

| 画面項目 | 入力形式 | 必須 | APIエンドポイント | リクエストフィールド | バリデーション |
|---------|---------|-----|------------------|---------------------|---------------|
| メッセージ | テキストエリア | ✓ | `POST /session/{id}/chat` | `content` | 1文字以上 |

---

## 4. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| セッション一覧ページ表示 | `GET /project/{id}/analysis/session` | 初期ロード |
| 検証カテゴリ選択 | `GET /api/v1/analysis/template` | 課題リスト取得 |
| セッション作成ボタン | `POST /project/{id}/analysis/session` | ウィザード完了時 |
| 分析画面表示 | `GET /session/{id}`, `GET /session/{id}/result` | 並列取得 |
| メッセージ送信 | `POST /session/{id}/chat` | - |
| スナップショット保存 | `POST /session/{id}/snapshot` | - |
| スナップショット履歴表示 | `GET /session/{id}/snapshot` | - |
| スナップショット復元 | `POST /snapshot/{id}/restore` | 確認後 |
| ファイル軸設定変更 | `PATCH /file/{id}` | - |
| ステップ追加 | `POST /session/{id}/step` | - |
| ステップ更新 | `PATCH /step/{id}` | - |

---

## 5. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | アクセス権限がありませんメッセージ表示 |
| 404 Not Found | セッションが見つかりませんメッセージ表示 |
| 409 Conflict | 復元先のスナップショットが存在しませんメッセージ表示 |
| 422 Validation Error | フォームエラー表示 |
| 500 Server Error | エラー画面を表示、リトライボタン |
| AI API Error | "分析中にエラーが発生しました。再試行してください"メッセージ表示 |

---

## 6. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| 一覧取得 | ページネーションで件数制限（デフォルト20件） |
| チャット履歴 | 仮想スクロールで大量メッセージを効率的に表示 |
| チャット送信 | オプティミスティック更新で即座にUIに反映 |
| ステップリスト | useMemo でステップ表示を最適化 |
| キャッシュ | React Query でセッションデータを5分間キャッシュ |
| ファイル情報 | 遅延ロードでサイドバー表示を高速化 |

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

## 8. Storybook対応

### 8.1 ストーリー一覧

| コンポーネント | ストーリー名 | 説明 | 状態バリエーション |
|--------------|-------------|------|-------------------|
| SessionCard | Default | 分析セッションカード表示 | 通常、進行中、完了、アーカイブ済み |
| SessionFilters | Default | セッションフィルタ | 通常、課題フィルタ適用済み |
| SessionWizard | Step1 | セッション作成ウィザード | Step1、Step2、Step3、送信中 |
| AnalysisChat | Default | 分析チャット表示 | 通常、空、ローディング、メッセージあり |
| AnalysisSteps | Default | 分析ステップ表示 | 通常、空、ドラッグ中 |
| AnalysisResults | Default | 分析結果表示 | 通常、ローディング、インサイトあり |
| SnapshotTimeline | Default | スナップショットタイムライン | 通常、空、現在のスナップショットあり |
| SnapshotCard | Default | スナップショットカード表示 | 通常、現在、復元中 |

### 8.2 ストーリー実装例

```tsx
// features/analysis/components/session-card/session-card.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { fn } from "@storybook/test";

import { SessionCard } from "./session-card";
import type { Session } from "../../types";

const baseSession: Session = {
  id: "1",
  name: "売上分析セッション",
  issue: { id: "i1", name: "売上トレンド分析" },
  inputFile: { id: "f1", filename: "sales_data.xlsx" },
  snapshotCount: 3,
  creator: { id: "u1", displayName: "山田太郎" },
  updatedAt: "2024-01-15T10:30:00Z",
  status: "in_progress",
};

const meta = {
  title: "features/analysis/components/session-card",
  component: SessionCard,
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component: "分析セッションカードコンポーネント。",
      },
    },
  },
  tags: ["autodocs"],
  args: {
    onOpen: fn(),
    onDuplicate: fn(),
  },
} satisfies Meta<typeof SessionCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    session: baseSession,
  },
};

export const InProgress: Story = {
  args: {
    session: { ...baseSession, status: "in_progress" },
  },
};

export const Completed: Story = {
  args: {
    session: { ...baseSession, status: "completed" },
  },
};

export const Archived: Story = {
  args: {
    session: { ...baseSession, status: "archived" },
  },
};
```

```tsx
// features/analysis/components/analysis-chat/analysis-chat.stories.tsx
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { fn } from "@storybook/test";

import { AnalysisChat } from "./analysis-chat";
import type { ChatMessage } from "../../types";

const mockMessages: ChatMessage[] = [
  { id: "1", role: "user", content: "売上の傾向を分析してください", createdAt: "2024-01-15T10:00:00Z" },
  {
    id: "2",
    role: "assistant",
    content:
      "データを分析した結果、以下の傾向が見られます:\n\n1. **月間成長率**: 平均5%の成長\n2. **季節変動**: Q4に売上がピーク\n3. **地域差**: 関東エリアが全体の40%を占める",
    createdAt: "2024-01-15T10:01:00Z",
  },
  { id: "3", role: "user", content: "地域別の詳細を教えてください", createdAt: "2024-01-15T10:02:00Z" },
];

const meta = {
  title: "features/analysis/components/analysis-chat",
  component: AnalysisChat,
  parameters: {
    layout: "padded",
    docs: {
      description: {
        component: "分析チャットコンポーネント。AIとの対話UIを提供。",
      },
    },
  },
  tags: ["autodocs"],
  args: {
    onSendMessage: fn(),
  },
} satisfies Meta<typeof AnalysisChat>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    messages: mockMessages,
  },
};

export const Empty: Story = {
  args: {
    messages: [],
  },
};

export const Loading: Story = {
  args: {
    messages: mockMessages,
    isLoading: true,
  },
};
```

---

## 9. テスト戦略

### 9.1 テスト対象・カバレッジ目標

| レイヤー | テスト種別 | カバレッジ目標 | 主な検証内容 |
|---------|----------|---------------|-------------|
| コンポーネント | ユニットテスト | 80%以上 | セッションカード、チャット、結果表示 |
| ユーティリティ | ユニットテスト | 90%以上 | hooks, utils, バリデーション |
| API連携 | 統合テスト | 70%以上 | API呼び出し、状態管理、エラーハンドリング |
| E2E | E2Eテスト | 主要フロー100% | セッション作成、分析実行、スナップショット管理 |

### 9.2 ユニットテスト例

```typescript
// features/analysis/hooks/__tests__/use-analysis-chat.test.ts
import { renderHook, act } from "@testing-library/react";
import { useAnalysisChat } from "../use-analysis-chat";

describe("useAnalysisChat", () => {
  it("メッセージ送信後に入力がクリアされる", async () => {
    const { result } = renderHook(() =>
      useAnalysisChat({ sessionId: "test-session" })
    );

    act(() => {
      result.current.setMessage("テストメッセージ");
    });

    expect(result.current.message).toBe("テストメッセージ");

    await act(async () => {
      await result.current.sendMessage();
    });

    expect(result.current.message).toBe("");
  });

  it("空メッセージは送信されない", async () => {
    const { result } = renderHook(() =>
      useAnalysisChat({ sessionId: "test-session" })
    );

    await act(async () => {
      await result.current.sendMessage();
    });

    expect(result.current.error).toBe("メッセージを入力してください");
  });
});
```

### 9.3 コンポーネントテスト例

```tsx
// features/analysis/components/session-card/__tests__/session-card.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";

import { SessionCard } from "../session-card";
import type { Session } from "../../../types";

const mockSession: Session = {
  id: "1",
  name: "テストセッション",
  issue: { id: "i1", name: "売上分析" },
  inputFile: { id: "f1", filename: "data.xlsx" },
  snapshotCount: 2,
  creator: { id: "u1", displayName: "テストユーザー" },
  updatedAt: "2024-01-01T00:00:00Z",
  status: "in_progress",
};

describe("SessionCard", () => {
  it("セッション情報を正しく表示する", () => {
    render(<SessionCard session={mockSession} />);

    expect(screen.getByText("テストセッション")).toBeInTheDocument();
    expect(screen.getByText("売上分析")).toBeInTheDocument();
    expect(screen.getByText("data.xlsx")).toBeInTheDocument();
  });

  it("開くボタンクリックでonOpenが呼ばれる", async () => {
    const user = userEvent.setup();
    const onOpen = vi.fn();
    render(<SessionCard session={mockSession} onOpen={onOpen} />);

    await user.click(screen.getByRole("button", { name: /開く/i }));
    expect(onOpen).toHaveBeenCalledWith(mockSession.id);
  });

  it("完了ステータスで完了バッジを表示", () => {
    render(
      <SessionCard session={{ ...mockSession, status: "completed" }} />
    );

    expect(screen.getByText("完了")).toBeInTheDocument();
  });
});
```

### 9.4 E2Eテスト例

```typescript
// e2e/analysis.spec.ts
import { test, expect } from "@playwright/test";

test.describe("個別施策分析", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/projects/1/sessions");
  });

  test("セッション一覧が表示される", async ({ page }) => {
    await expect(
      page.getByRole("heading", { name: "セッション" })
    ).toBeVisible();
    await expect(page.getByTestId("session-list")).toBeVisible();
  });

  test("新規セッションを作成できる", async ({ page }) => {
    await page.getByRole("button", { name: "新規作成" }).click();

    // STEP1: テーマ選択
    await page.getByTestId("category-card-sales").click();
    await page.getByLabel("分析課題").selectOption("売上トレンド分析");
    await page.getByRole("button", { name: "次へ" }).click();

    // STEP2: データ準備
    await page.getByLabel("入力ファイル").selectOption("sales_data.xlsx");
    await page.getByLabel("時間軸").selectOption("date");
    await page.getByLabel("分析対象値").selectOption("amount");
    await page.getByRole("button", { name: "次へ" }).click();

    // STEP3: 確認
    await page.getByLabel("セッション名").fill("E2Eテストセッション");
    await page.getByRole("button", { name: "作成" }).click();

    await expect(page.getByText("セッションを作成しました")).toBeVisible();
  });

  test("チャットでAIと対話できる", async ({ page }) => {
    await page.getByTestId("session-card").first().click();
    await page.getByRole("link", { name: "分析開始" }).click();

    await page.getByPlaceholder("メッセージを入力").fill("売上の傾向を分析してください");
    await page.getByRole("button", { name: "送信" }).click();

    await expect(page.getByText("売上の傾向を分析してください")).toBeVisible();
    await expect(page.getByTestId("assistant-message")).toBeVisible();
  });

  test("スナップショットを保存・復元できる", async ({ page }) => {
    await page.getByTestId("session-card").first().click();
    await page.getByRole("link", { name: "分析開始" }).click();

    // スナップショット保存
    await page.getByRole("button", { name: "保存" }).click();
    await expect(page.getByText("スナップショットを保存しました")).toBeVisible();

    // スナップショット履歴へ移動
    await page.getByRole("button", { name: "履歴" }).click();
    await expect(page.getByTestId("snapshot-timeline")).toBeVisible();

    // 復元
    await page.getByTestId("snapshot-card").first().getByRole("button", { name: "復元" }).click();
    await page.getByRole("button", { name: "確認" }).click();
    await expect(page.getByText("スナップショットを復元しました")).toBeVisible();
  });
});
```

### 9.5 モックデータ

```typescript
// features/analysis/__mocks__/handlers.ts
import { http, HttpResponse } from "msw";

export const analysisHandlers = [
  http.get("/api/v1/project/:projectId/analysis/session", () => {
    return HttpResponse.json({
      sessions: [
        {
          id: "1",
          name: "売上分析セッション",
          issue: { id: "i1", name: "売上トレンド分析" },
          inputFile: { filename: "sales_data.xlsx" },
          snapshotCount: 3,
          creator: { displayName: "山田太郎" },
          updatedAt: "2024-01-15T10:30:00Z",
          status: "in_progress",
        },
      ],
      total: 1,
    });
  }),

  http.get("/api/v1/session/:id", ({ params }) => {
    return HttpResponse.json({
      id: params.id,
      name: "テストセッション",
      status: "in_progress",
      issue: { id: "i1", name: "売上トレンド分析" },
      inputFile: { filename: "data.xlsx", size: 1024, rows: 100, columns: 5 },
      currentSnapshot: { snapshotOrder: 2 },
      snapshotCount: 2,
    });
  }),

  http.post("/api/v1/session/:id/chat", async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      id: "new-msg",
      role: "assistant",
      content: `「${body.content}」について分析しました。結果は以下の通りです...`,
      createdAt: new Date().toISOString(),
    });
  }),

  http.get("/api/v1/session/:id/snapshot", () => {
    return HttpResponse.json({
      snapshots: [
        {
          id: "s1",
          snapshotOrder: 1,
          description: "初期状態",
          createdAt: "2024-01-15T09:00:00Z",
        },
        {
          id: "s2",
          snapshotOrder: 2,
          description: "売上分析完了後",
          createdAt: "2024-01-15T10:00:00Z",
        },
      ],
    });
  }),
];
```

---

## 10. 関連ドキュメント

- **バックエンド設計**: [01-analysis-design.md](./01-analysis-design.md)
- **ユースケース一覧**: [../../01-usercases/01-usecases.md](../../01-usercases/01-usecases.md)
- **モックアップ**: [../../03-mockup/pages/sessions.js](../../03-mockup/pages/sessions.js)
- **API共通仕様**: [../01-api-overview/01-api-overview.md](../01-api-overview/01-api-overview.md)

---

## 11. ドキュメント管理情報

| 項目 | 内容 |
|------|------|
| ドキュメントID | AN-FRONTEND-001 |
| 対象ユースケース | AS-001〜AS-007, AF-001〜AF-006, ASN-001〜ASN-005, AC-001〜AC-003, AST-001〜AST-006 |
| 最終更新日 | 2026-01-01 |
| 対象フロントエンド | `app/projects/[id]/sessions/` |
