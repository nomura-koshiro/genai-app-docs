# 共通UI フロントエンド設計書

## 1. フロントエンド設計

### 1.1 画面一覧

| 画面ID | 画面名 | パス | 説明 |
|--------|--------|------|------|
| - | ヘッダー | 全ページ共通 | グローバルナビゲーション |
| - | サイドバー | 全ページ共通 | サイドナビゲーション |

### 1.2 コンポーネント構成

```text
features/common/
├── components/
│   ├── Header/
│   │   ├── Header.tsx
│   │   ├── UserMenu.tsx
│   │   ├── NotificationBell.tsx
│   │   └── GlobalSearch.tsx
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
│   └── useNavigation.ts
├── contexts/
│   └── UserContextProvider.tsx
├── api/
│   └── userContextApi.ts
└── types/
    └── userContext.ts
```

---

## 2. サイドバー設計

### 2.1 セクション構成

| セクションID | セクション名 | 必要権限 | メニュー項目 |
|-------------|-------------|---------|------------|
| dashboard | ダッシュボード | user | ホーム |
| project | プロジェクト管理 | user | プロジェクト、プロジェクト作成 |
| analysis | 個別施策分析 | user | 分析セッション一覧、新規セッション作成 |
| driver-tree | ドライバーツリー | user | ツリー一覧、新規ツリー作成、カテゴリマスタ |
| file | ファイル管理 | user | ファイル一覧、アップロード |
| system-admin | システム管理 | system_admin | ユーザー管理、ロール管理、検証カテゴリ、課題マスタ |
| monitoring | 監視・運用 | system_admin | システム統計、操作履歴、監査ログ、全プロジェクト |
| operations | システム運用 | system_admin | システム設定、通知管理、セキュリティ、一括操作、データ管理、サポートツール |

### 2.2 権限ベース表示ロジック

```typescript
// hooks/usePermissions.ts
export function usePermissions() {
  const { userContext } = useUserContext();

  return {
    isSystemAdmin: userContext?.permissions.isSystemAdmin ?? false,
    canAccessAdminPanel: userContext?.permissions.canAccessAdminPanel ?? false,
    // ...
  };
}

// components/Sidebar/Sidebar.tsx
export function Sidebar() {
  const { userContext } = useUserContext();
  const visibleSections = userContext?.sidebar.visibleSections ?? [];

  return (
    <aside className="sidebar">
      {visibleSections.includes('dashboard') && <DashboardSection />}
      {visibleSections.includes('project') && <ProjectSection />}
      {visibleSections.includes('analysis') && <AnalysisSection />}
      {visibleSections.includes('driver-tree') && <DriverTreeSection />}
      {visibleSections.includes('file') && <FileSection />}
      {visibleSections.includes('system-admin') && <SystemAdminSection />}
      {visibleSections.includes('monitoring') && <MonitoringSection />}
      {visibleSections.includes('operations') && <OperationsSection />}
    </aside>
  );
}
```

### 2.3 プロジェクト動的遷移

| 条件 | 遷移先 | URL |
|-----|-------|-----|
| プロジェクト数 = 0 | プロジェクト一覧（空状態） | /projects |
| プロジェクト数 = 1 | プロジェクト詳細 | /projects/{projectId} |
| プロジェクト数 > 1 | プロジェクト一覧 | /projects |

```typescript
// components/Sidebar/ProjectNavigator.tsx
export function ProjectNavigator() {
  const { userContext } = useUserContext();
  const router = useRouter();

  const handleProjectClick = () => {
    const nav = userContext?.navigation;

    if (nav?.projectNavigationType === 'detail' && nav.defaultProjectId) {
      // 1つのプロジェクトのみ → 詳細画面へ
      router.push(`/projects/${nav.defaultProjectId}`);
    } else {
      // 0または複数 → 一覧画面へ
      router.push('/projects');
    }
  };

  return (
    <SidebarItem
      icon="📁"
      label={
        userContext?.navigation.projectNavigationType === 'detail'
          ? userContext.navigation.defaultProjectName ?? 'プロジェクト'
          : 'プロジェクト一覧'
      }
      onClick={handleProjectClick}
    />
  );
}
```

---

## 3. ヘッダー設計

### 3.1 コンポーネント構成

| 画面項目 | 表示形式 | APIエンドポイント | レスポンスフィールド | 変換処理 |
|---------|---------|------------------|---------------------|---------|
| ユーザー名 | テキスト | GET /user_account/me/context | user.displayName | - |
| ユーザーアバター | イニシャル | GET /user_account/me/context | user.displayName | 先頭2文字 |
| 通知バッジ | バッジ | GET /user_account/me/context | notifications.unreadCount | 0の場合非表示 |
| 管理者バッジ | バッジ | GET /user_account/me/context | permissions.isSystemAdmin | trueの場合表示 |

### 3.2 ユーザーメニュー

| メニュー項目 | 表示条件 | 遷移先 |
|------------|---------|-------|
| プロフィール | 常時 | /settings/profile |
| 設定 | 常時 | /settings |
| 管理パネル | isSystemAdmin | /admin |
| ログアウト | 常時 | Azure AD logout |

---

## 4. コンテキスト管理

### 4.1 UserContextProvider

```typescript
// contexts/UserContextProvider.tsx
interface UserContextState {
  userContext: UserContextResponse | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

export function UserContextProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<UserContextState>({
    userContext: null,
    isLoading: true,
    error: null,
    refetch: async () => {},
  });

  useEffect(() => {
    fetchUserContext();
  }, []);

  const fetchUserContext = async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true }));
      const response = await userContextApi.getContext();
      setState({
        userContext: response,
        isLoading: false,
        error: null,
        refetch: fetchUserContext,
      });
    } catch (error) {
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: error as Error,
      }));
    }
  };

  return (
    <UserContext.Provider value={state}>
      {children}
    </UserContext.Provider>
  );
}
```

### 4.2 初期化フロー

```text
1. アプリ起動 / ページリロード
2. UserContextProvider が GET /user_account/me/context を呼び出し
3. レスポンスを state に保存
4. Header, Sidebar が state を参照して表示を切り替え
5. 権限がない場合はセクションを非表示
6. プロジェクト数に応じてナビゲーションを切り替え
```

---

## 5. API呼び出しタイミング

| トリガー | API呼び出し | 備考 |
|---------|------------|------|
| アプリ初期化 | GET /user_account/me/context | 1回のみ |
| ページリロード | GET /user_account/me/context | キャッシュ無効時 |
| ログイン成功後 | GET /user_account/me/context | 強制リフレッシュ |
| プロジェクト参加/離脱後 | refetch() | ナビゲーション更新 |
| 通知既読後 | 部分更新 | unreadCount のみ |

---

## 6. エラーハンドリング

| エラー | 対応 |
|-------|------|
| 401 Unauthorized | ログイン画面にリダイレクト |
| 403 Forbidden | アクセス拒否画面を表示 |
| 500 Server Error | エラー画面を表示、リトライボタン |
| Network Error | オフライン表示、リトライボタン |

---

## 7. パフォーマンス考慮

| 項目 | 対策 |
|-----|------|
| 初期ロード | コンテキストAPIは軽量（1KB未満） |
| キャッシュ | React Query で5分間キャッシュ |
| 再レンダリング | useMemo でセクション表示を最適化 |
| バンドルサイズ | セクションコンポーネントは遅延ロード |
