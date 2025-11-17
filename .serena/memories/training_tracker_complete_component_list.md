# Training Tracker - 完全なページ・コンポーネント一覧

## 🏗️ Feature-based Directory Structure

```
src/
├── app/                    # Next.js 15 App Router
│   ├── (auth)/
│   │   ├── login/
│   │   └── register/
│   ├── dashboard/
│   ├── training/
│   ├── menu/
│   ├── history/
│   ├── stats/
│   └── settings/
├── features/              # 機能別モジュール
├── components/           # 共通UIコンポーネント
├── types/               # TypeScript型定義（完了）
├── hooks/               # カスタムフック
├── stores/              # Zustand状態管理
└── utils/               # ユーティリティ
```

## 📱 Pages & Route Structure

### Authentication Routes
- `/` - ランディングページ
- `/login` - ログイン画面
- `/register` - アカウント登録
- `/forgot-password` - パスワードリセット

### Main Application Routes
- `/dashboard` - ダッシュボード
- `/training` - トレーニング記録
- `/training/[sessionId]` - 記録詳細
- `/menu` - メニュー管理
- `/menu/create` - メニュー作成
- `/menu/[menuId]/edit` - メニュー編集
- `/history` - 履歴一覧
- `/history/calendar` - カレンダー表示
- `/stats` - 統計・グラフ
- `/settings` - 設定
- `/settings/profile` - プロフィール設定
- `/settings/integrations` - 外部連携

## 🎯 Phase 1: Core Components (最優先)

### 1. Authentication Feature (`src/features/auth/`)

#### Components
```typescript
// src/features/auth/components/
├── LoginForm.tsx              // ログインフォーム
├── RegisterForm.tsx           // 登録フォーム
├── ForgotPasswordForm.tsx     // パスワードリセット
├── GoogleAuthButton.tsx       // Google OAuth
└── AuthLayout.tsx            // 認証画面共通レイアウト
```

#### Hooks & API
```typescript
// src/features/auth/hooks/
├── useAuth.ts                // 認証状態管理
├── useLogin.ts               // ログイン処理
├── useRegister.ts            // 登録処理
└── useGoogleAuth.ts          // Google認証

// src/features/auth/api/
├── authApi.ts                // 認証API
└── authSchema.ts             // Zodスキーマ
```

#### Types Used
- `User`, `LoginRequest`, `RegisterRequest`, `AuthResponse`

### 2. Dashboard Feature (`src/features/dashboard/`)

#### Components
```typescript
// src/features/dashboard/components/
├── DashboardLayout.tsx       // ダッシュボードレイアウト
├── TodayStats.tsx           // 今日の統計
├── ScheduledMenus.tsx       // 本日のメニュー
├── RecentPRCard.tsx         // 最新PR表示
├── QuickStartButtons.tsx    // クイックアクション
└── WeeklyProgress.tsx       // 週間進捗
```

#### Types Used
- `DashboardStats`, `TodaySchedule`, `RecentPR`

### 3. Training Feature (`src/features/training/`)

#### Components
```typescript
// src/features/training/components/
├── TrainingSession/
│   ├── SessionHeader.tsx    // セッション情報
│   ├── ExerciseCard.tsx     // 種目カード
│   ├── SetInput.tsx         // セット入力
│   ├── TimerControls.tsx    // タイマー操作
│   └── SessionControls.tsx  // セッション制御
├── ExerciseSelector/
│   ├── ExerciseList.tsx     // 種目一覧
│   ├── ExerciseFilter.tsx   // フィルター
│   └── ExerciseSearch.tsx   // 検索
└── RecordInput/
    ├── WeightInput.tsx      // 重量入力
    ├── RepsInput.tsx        // 回数入力
    └── RPESelector.tsx      // RPE選択
```

#### Types Used
- `TrainingSession`, `TrainingRecord`, `SetRecord`, `Exercise`

### 4. Common UI Components (`src/components/ui/`)

#### Basic Components (shadcn/ui based)
```typescript
├── Button.tsx               // ボタン
├── Input.tsx               // 入力フィールド
├── Card.tsx                // カード
├── Modal.tsx               // モーダル
├── Toast.tsx               // トースト通知
├── Skeleton.tsx            // スケルトン
├── Spinner.tsx             // ローディング
└── ErrorBoundary.tsx       // エラーハンドリング
```

#### Complex Components
```typescript
├── form/
│   ├── Form.tsx            // フォームラッパー
│   ├── FormField.tsx       // フィールド
│   └── FormError.tsx       // エラー表示
├── layout/
│   ├── Header.tsx          // ヘッダー
│   ├── Navigation.tsx      // ナビゲーション
│   ├── Sidebar.tsx         // サイドバー
│   └── Layout.tsx          // 基本レイアウト
└── data-display/
    ├── Table.tsx           // テーブル
    ├── Pagination.tsx      // ページネーション
    └── EmptyState.tsx      // 空状態
```

## 🎯 Phase 2: Extended Features (中優先)

### 5. Menu Feature (`src/features/menu/`)

#### Components
```typescript
// src/features/menu/components/
├── MenuList/
│   ├── MenuCard.tsx        // メニューカード
│   ├── MenuFilter.tsx      // フィルター
│   └── MenuSearch.tsx      // 検索
├── MenuBuilder/
│   ├── MenuForm.tsx        // メニューフォーム
│   ├── ExerciseSelector.tsx // 種目選択
│   ├── OrderManager.tsx    // 順序管理
│   └── MenuPreview.tsx     // プレビュー
└── Schedule/
    ├── ScheduleCalendar.tsx // スケジュールカレンダー
    ├── ScheduleForm.tsx     // スケジュール設定
    └── WeeklySchedule.tsx   // 週間スケジュール
```

#### Types Used
- `Menu`, `MenuExercise`, `Schedule`, `CreateMenuRequest`

### 6. History Feature (`src/features/history/`)

#### Components
```typescript
// src/features/history/components/
├── HistoryList/
│   ├── HistoryItem.tsx     // 履歴アイテム
│   ├── HistoryFilter.tsx   // フィルター
│   └── HistorySearch.tsx   // 検索
├── Calendar/
│   ├── TrainingCalendar.tsx // トレーニングカレンダー
│   ├── CalendarDay.tsx     // カレンダー日付
│   └── CalendarLegend.tsx  // 凡例
└── SessionDetail/
    ├── SessionSummary.tsx   // セッション概要
    ├── ExerciseDetail.tsx   // 種目詳細
    └── PRHighlights.tsx     // PR達成ハイライト
```

#### Types Used
- `TrainingHistory`, `TrainingCalendarData`, `TrainingDay`

### 7. Stats Feature (`src/features/stats/`)

#### Components
```typescript
// src/features/stats/components/
├── Charts/
│   ├── ProgressChart.tsx   // 進捗チャート
│   ├── VolumeChart.tsx     // ボリュームチャート
│   ├── StrengthChart.tsx   // 筋力チャート
│   └── ComparisonChart.tsx // 比較チャート
├── Statistics/
│   ├── StatCard.tsx        // 統計カード
│   ├── TrendIndicator.tsx  // トレンド指標
│   └── PRTracker.tsx       // PR追跡
└── Filters/
    ├── PeriodSelector.tsx  // 期間選択
    ├── ExerciseSelector.tsx // 種目選択
    └── MetricSelector.tsx  // 指標選択
```

#### Types Used
- `ProgressStats`, `PersonalRecord`, `StatsSummary`

## 🎯 Phase 3: Advanced Features (低優先)

### 8. Settings Feature (`src/features/settings/`)

#### Components
```typescript
// src/features/settings/components/
├── Profile/
│   ├── ProfileForm.tsx     // プロフィール編集
│   ├── AvatarUpload.tsx    // アバター設定
│   └── PasswordChange.tsx  // パスワード変更
├── Preferences/
│   ├── ThemeSelector.tsx   // テーマ選択
│   ├── UnitSelector.tsx    // 単位設定
│   └── NotificationSettings.tsx // 通知設定
├── Integrations/
│   ├── ServiceList.tsx     // サービス一覧
│   ├── ConnectionCard.tsx  // 連携カード
│   └── SyncStatus.tsx      // 同期状態
└── Export/
    ├── ExportForm.tsx      // エクスポート設定
    ├── ExportHistory.tsx   // エクスポート履歴
    └── DownloadButton.tsx  // ダウンロード
```

#### Types Used
- `User`, `AppSettings`, `ExternalIntegration`, `ExportRequest`

## 🔧 Global State & Hooks

### Zustand Stores
```typescript
// src/stores/
├── authStore.ts           // 認証状態
├── trainingStore.ts       // トレーニング状態
├── menuStore.ts           // メニュー状態
└── settingsStore.ts       // 設定状態
```

### Common Hooks
```typescript
// src/hooks/
├── useLocalStorage.ts     // ローカルストレージ
├── useDebounce.ts        // デバウンス
├── useInfiniteScroll.ts  // 無限スクロール
├── useTimer.ts           // タイマー機能
└── useNotification.ts    // 通知機能
```

## 📊 Implementation Priority Matrix

| Feature | Priority | Dependencies | Complexity |
|---------|----------|--------------|------------|
| Auth | P0 | None | Low |
| Dashboard | P0 | Auth | Medium |
| Training | P0 | Auth, Dashboard | High |
| Common UI | P0 | None | Low |
| Menu | P1 | Training | Medium |
| History | P1 | Training | Medium |
| Stats | P2 | Training, History | High |
| Settings | P2 | Auth | Low |

## 🎨 Design System Integration

すべてのコンポーネントは以下に準拠:
- Tailwind CSS + CVA for styling
- shadcn/ui component library
- 統一されたデザイントークン
- アクセシビリティ対応
- レスポンシブデザイン

この構造により、スケーラブルで保守性の高いアプリケーションを構築できます。
