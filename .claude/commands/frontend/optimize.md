---
title: Performance Optimization
description: Reactコンポーネントのパフォーマンスを分析・最適化
tools: [Read, Edit, MultiEdit, Bash, Grep]
---

@frontend-developer

「$ARGUMENTS」のパフォーマンス最適化を行ってください。

## パフォーマンス分析

### 1. 現状分析

以下の観点で現在のパフォーマンス問題を特定してください：

#### 再レンダリング問題

- [ ] 不要な親コンポーネントの再レンダリング
- [ ] Props の参照が変わることによる子コンポーネント再レンダリング
- [ ] Context の過度な使用
- [ ] インライン関数・オブジェクトの作成

#### メモリ使用量

- [ ] 大きなデータセットの処理
- [ ] メモリリークの可能性
- [ ] 不要なデータの保持

#### バンドルサイズ

- [ ] 未使用の依存関係
- [ ] 重い依存関係の不必要な使用
- [ ] Code Splitting の機会

### 2. 最適化戦略

#### React最適化

```typescript
// React.memo の適切な使用
const OptimizedComponent = React.memo(
  ({ data, onAction }) => {
    // コンポーネント実装
  },
  (prevProps, nextProps) => {
    // カスタム比較関数
    return prevProps.data.id === nextProps.data.id && prevProps.data.updatedAt === nextProps.data.updatedAt;
  }
);

// useMemo - 重い計算のメモ化
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(data);
}, [data]);

// useCallback - 関数のメモ化
const handleAction = useCallback(
  (id: string) => {
    onAction(id);
  },
  [onAction]
);
```

#### 状態管理最適化

- **Zustand**: セレクターによる細かい購読
- **TanStack Query**: 適切なキャッシュ戦略
- **React State**: 状態の適切な分離

#### レンダリング最適化

- **条件分岐**: Early Return の活用
- **リスト**: 適切な key の設定
- **仮想化**: 大量データ表示時の react-window/react-virtualized

### 3. 具体的な最適化実装

#### メモ化の適用

```typescript
// ✅ 最適化前
const UserList = ({ users, filter, onUserClick }) => {
  const filteredUsers = users.filter(user =>
    user.name.includes(filter)
  ) // 毎レンダリング時に実行

  return (
    <div>
      {filteredUsers.map(user => (
        <UserCard
          key={user.id}
          user={user}
          onClick={() => onUserClick(user.id)} // 毎回新しい関数
        />
      ))}
    </div>
  )
}

// ✅ 最適化後
const UserList = React.memo(({ users, filter, onUserClick }) => {
  const filteredUsers = useMemo(() =>
    users.filter(user => user.name.includes(filter))
  , [users, filter])

  const handleUserClick = useCallback((userId: string) => {
    onUserClick(userId)
  }, [onUserClick])

  return (
    <div>
      {filteredUsers.map(user => (
        <UserCard
          key={user.id}
          user={user}
          onClick={handleUserClick}
        />
      ))}
    </div>
  )
})
```

#### 遅延ローディングの実装

```typescript
// 重いコンポーネントの遅延読み込み
const HeavyChart = lazy(() => import('./HeavyChart'))

const Dashboard = () => {
  return (
    <Suspense fallback={<ChartSkeleton />}>
      <HeavyChart />
    </Suspense>
  )
}
```

### 4. パフォーマンス測定

#### React DevTools Profiler

```bash
# 開発モードでプロファイリング実行
cd apps/frontend && pnpm dev
```

#### Bundle Analyzer

```bash
# バンドルサイズ分析
cd apps/frontend && ANALYZE=true pnpm build
```

#### Lighthouse / Web Vitals

```bash
# パフォーマンス測定
cd apps/frontend && pnpm build && pnpm start
# Lighthouse で Core Web Vitals を測定
```

### 5. メトリクス目標

#### Core Web Vitals

- **LCP (Largest Contentful Paint)**: < 2.5秒
- **FID (First Input Delay)**: < 100ms
- **CLS (Cumulative Layout Shift)**: < 0.1

#### React固有メトリクス

- **初回レンダリング時間**: < 16ms（60fps維持）
- **再レンダリング回数**: 最小化
- **メモリ使用量**: 安定した推移

### 6. 最適化後の検証

#### パフォーマンステスト

```bash
# テスト実行（パフォーマンスリグレッション検出）
cd apps/frontend && pnpm test

# E2Eテストでのパフォーマンス確認
cd apps/frontend && pnpm test:e2e
```

#### モニタリング

- React DevTools でのレンダリング回数確認
- Chrome DevTools でのメモリ使用量チェック
- Network タブでのバンドルサイズ確認

## 最適化ガイドライン

### やるべき最適化

- [ ] 重いコンポーネントの React.memo 適用
- [ ] 重い計算の useMemo 適用
- [ ] コールバック関数の useCallback 適用
- [ ] 大量データのリスト仮想化
- [ ] 不要な依存関係の除去

### 避けるべき最適化

- [ ] 軽量コンポーネントへの過度なメモ化
- [ ] 全てのオブジェクト・関数のメモ化
- [ ] プレマチュアな最適化

## プロジェクトガイドライン参照

**必ず以下のドキュメントを読んでから最適化してください：**

- `.claude/skills/frontend/state-management.md` - 状態管理戦略
- `.claude/skills/frontend/architecture.md` - アーキテクチャ設計

最適化完了後、Before/Afterの性能比較データを提供してください。
