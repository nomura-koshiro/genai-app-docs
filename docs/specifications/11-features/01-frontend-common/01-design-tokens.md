# デザイントークン設計書

## 概要

本ドキュメントは、CAMPシステムのデザイントークン（CSS変数）を定義します。
フロントエンド実装では、これらのトークンをTailwind CSSの設定およびCSS変数として使用します。

> **参照元**: `docs/specifications/03-mockup/design-system.css`

---

## 1. カラーパレット

### 1.1 プライマリカラー（Blue）

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| primary-50 | `--color-primary-50` | `#eff6ff` | 背景（ホバー、選択状態） |
| primary-100 | `--color-primary-100` | `#dbeafe` | 背景（アクティブ状態） |
| primary-200 | `--color-primary-200` | `#bfdbfe` | ボーダー（アクセント） |
| primary-300 | `--color-primary-300` | `#93c5fd` | ボーダー（フォーカス） |
| primary-400 | `--color-primary-400` | `#60a5fa` | アイコン（セカンダリ） |
| primary-500 | `--color-primary-500` | `#3b82f6` | ブランドカラー（基準） |
| primary-600 | `--color-primary-600` | `#2563eb` | ボタン背景、リンク |
| primary-700 | `--color-primary-700` | `#1d4ed8` | ボタンホバー |
| primary-800 | `--color-primary-800` | `#1e40af` | テキスト（強調） |
| primary-900 | `--color-primary-900` | `#1e3a8a` | テキスト（最強調） |

### 1.2 ニュートラルカラー（Gray）

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| neutral-50 | `--color-neutral-50` | `#f8fafc` | 背景（ページ全体） |
| neutral-100 | `--color-neutral-100` | `#f1f5f9` | 背景（セクション、ホバー） |
| neutral-200 | `--color-neutral-200` | `#e2e8f0` | ボーダー（デフォルト） |
| neutral-300 | `--color-neutral-300` | `#cbd5e1` | ボーダー（ホバー） |
| neutral-400 | `--color-neutral-400` | `#94a3b8` | テキスト（プレースホルダー） |
| neutral-500 | `--color-neutral-500` | `#64748b` | テキスト（セカンダリ） |
| neutral-600 | `--color-neutral-600` | `#475569` | テキスト（サブ） |
| neutral-700 | `--color-neutral-700` | `#334155` | テキスト（本文） |
| neutral-800 | `--color-neutral-800` | `#1e293b` | テキスト（プライマリ） |
| neutral-900 | `--color-neutral-900` | `#0f172a` | テキスト（見出し） |

### 1.3 セマンティックカラー

#### Success（Green）

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| success-50 | `--color-success-50` | `#f0fdf4` | Alert背景 |
| success-100 | `--color-success-100` | `#dcfce7` | Badge背景 |
| success-500 | `--color-success-500` | `#22c55e` | ボタン背景 |
| success-600 | `--color-success-600` | `#16a34a` | テキスト、アイコン |
| success-700 | `--color-success-700` | `#15803d` | ホバー状態 |

#### Warning（Amber）

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| warning-50 | `--color-warning-50` | `#fffbeb` | Alert背景 |
| warning-100 | `--color-warning-100` | `#fef3c7` | Badge背景 |
| warning-500 | `--color-warning-500` | `#f59e0b` | ボタン背景 |
| warning-600 | `--color-warning-600` | `#d97706` | テキスト、アイコン |
| warning-700 | `--color-warning-700` | `#b45309` | ホバー状態 |

#### Danger（Red）

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| danger-50 | `--color-danger-50` | `#fef2f2` | Alert背景 |
| danger-100 | `--color-danger-100` | `#fee2e2` | Badge背景 |
| danger-500 | `--color-danger-500` | `#ef4444` | ボタン背景 |
| danger-600 | `--color-danger-600` | `#dc2626` | テキスト、アイコン |
| danger-700 | `--color-danger-700` | `#b91c1c` | ホバー状態 |

#### Info（Blue - Primary と同一）

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| info-50 | `--color-info-50` | `#eff6ff` | Alert背景 |
| info-100 | `--color-info-100` | `#dbeafe` | Badge背景 |
| info-500 | `--color-info-500` | `#3b82f6` | ボタン背景 |
| info-600 | `--color-info-600` | `#2563eb` | テキスト、アイコン |
| info-700 | `--color-info-700` | `#1d4ed8` | ホバー状態 |

### 1.4 エイリアス（意味的カラー）

| エイリアス | CSS変数 | ライトモード | ダークモード | 用途 |
|-----------|--------|-------------|-------------|------|
| background | `--color-background` | `neutral-50` (#f8fafc) | `neutral-900` (#0f172a) | ページ背景 |
| surface | `--color-surface` | `#ffffff` | `neutral-800` (#1e293b) | カード、モーダル背景 |
| surface-elevated | `--color-surface-elevated` | `#ffffff` | `neutral-700` (#334155) | 浮き上がった要素 |
| border | `--color-border` | `neutral-200` (#e2e8f0) | `neutral-700` (#334155) | デフォルトボーダー |
| border-light | `--color-border-light` | `neutral-100` (#f1f5f9) | `neutral-800` (#1e293b) | 軽いボーダー |
| text-primary | `--color-text-primary` | `neutral-800` (#1e293b) | `neutral-100` (#f1f5f9) | 本文テキスト |
| text-secondary | `--color-text-secondary` | `neutral-500` (#64748b) | `neutral-400` (#94a3b8) | 補助テキスト |
| text-muted | `--color-text-muted` | `neutral-400` (#94a3b8) | `neutral-500` (#64748b) | プレースホルダー |
| text-inverse | `--color-text-inverse` | `#ffffff` | `neutral-900` (#0f172a) | 反転テキスト |

### 1.5 ダークモード カラーパレット

ダークモードでは、ライトモードのカラースケールを反転させるのではなく、視認性とコントラストを考慮した専用の配色を使用します。

#### ダークモード用プライマリカラー調整

| トークン名 | ライトモード | ダークモード | 用途 |
|-----------|-------------|-------------|------|
| primary-hover-bg | `primary-50` | `primary-900/30` | ホバー背景 |
| primary-active-bg | `primary-100` | `primary-800/40` | アクティブ背景 |
| primary-button | `primary-600` | `primary-500` | ボタン背景 |
| primary-button-hover | `primary-700` | `primary-400` | ボタンホバー |
| primary-text | `primary-600` | `primary-400` | リンク、強調テキスト |

#### ダークモード用セマンティックカラー調整

| セマンティック | ライトモード背景 | ダークモード背景 | ライトモードテキスト | ダークモードテキスト |
|---------------|-----------------|-----------------|---------------------|---------------------|
| success | `success-50` | `success-900/20` | `success-700` | `success-400` |
| warning | `warning-50` | `warning-900/20` | `warning-700` | `warning-400` |
| danger | `danger-50` | `danger-900/20` | `danger-700` | `danger-400` |
| info | `info-50` | `info-900/20` | `info-700` | `info-400` |

---

## 2. タイポグラフィ

### 2.1 フォントファミリー

| トークン名 | CSS変数 | 値 |
|-----------|--------|-----|
| font-base | `--font-family-base` | `'Segoe UI', 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif` |
| font-mono | `--font-family-mono` | `'Consolas', 'Monaco', 'Menlo', monospace` |

### 2.2 フォントサイズ

| トークン名 | CSS変数 | 値 | px換算 | 用途 |
|-----------|--------|-----|--------|------|
| text-xs | `--font-size-xs` | `0.75rem` | 12px | キャプション、ラベル |
| text-sm | `--font-size-sm` | `0.875rem` | 14px | 補助テキスト、ボタン |
| text-base | `--font-size-base` | `1rem` | 16px | 本文 |
| text-lg | `--font-size-lg` | `1.125rem` | 18px | 小見出し |
| text-xl | `--font-size-xl` | `1.25rem` | 20px | 見出し4 |
| text-2xl | `--font-size-2xl` | `1.5rem` | 24px | 見出し3 |
| text-3xl | `--font-size-3xl` | `1.875rem` | 30px | 見出し2 |
| text-4xl | `--font-size-4xl` | `2.25rem` | 36px | 見出し1 |

### 2.3 フォントウェイト

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| font-normal | `--font-weight-normal` | `400` | 本文 |
| font-medium | `--font-weight-medium` | `500` | ボタン、ラベル |
| font-semibold | `--font-weight-semibold` | `600` | 見出し、強調 |
| font-bold | `--font-weight-bold` | `700` | 大見出し |

### 2.4 行高

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| leading-tight | `--line-height-tight` | `1.25` | 見出し |
| leading-normal | `--line-height-normal` | `1.5` | 本文 |
| leading-relaxed | `--line-height-relaxed` | `1.75` | 長文 |

### 2.5 字間

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| tracking-tight | `--letter-spacing-tight` | `-0.025em` | 見出し |
| tracking-normal | `--letter-spacing-normal` | `0` | 本文 |
| tracking-wide | `--letter-spacing-wide` | `0.025em` | ラベル |
| tracking-wider | `--letter-spacing-wider` | `0.05em` | キャプション |

### 2.6 見出しスタイル

```typescript
// Tailwind CSS クラス定義
export const headingStyles = {
  h1: 'text-3xl font-bold leading-tight tracking-tight',     // 30px
  h2: 'text-2xl font-semibold leading-tight',                // 24px
  h3: 'text-xl font-semibold leading-tight',                 // 20px
  h4: 'text-lg font-semibold leading-tight',                 // 18px
} as const;

// CSSクラス対応
// .heading-1: h1相当
// .heading-2: h2相当
// .heading-3: h3相当
// .heading-4: h4相当
```

---

## 3. スペーシング

### 3.1 スペーシングスケール

| トークン名 | CSS変数 | 値 | px換算 | 用途 |
|-----------|--------|-----|--------|------|
| spacing-0 | `--spacing-0` | `0` | 0px | なし |
| spacing-1 | `--spacing-1` | `0.25rem` | 4px | 極小間隔 |
| spacing-2 | `--spacing-2` | `0.5rem` | 8px | 小間隔 |
| spacing-3 | `--spacing-3` | `0.75rem` | 12px | 中小間隔 |
| spacing-4 | `--spacing-4` | `1rem` | 16px | 標準間隔 |
| spacing-5 | `--spacing-5` | `1.25rem` | 20px | 中間隔 |
| spacing-6 | `--spacing-6` | `1.5rem` | 24px | 中大間隔 |
| spacing-8 | `--spacing-8` | `2rem` | 32px | 大間隔 |
| spacing-10 | `--spacing-10` | `2.5rem` | 40px | 特大間隔 |
| spacing-12 | `--spacing-12` | `3rem` | 48px | セクション間 |
| spacing-16 | `--spacing-16` | `4rem` | 64px | 大セクション間 |
| spacing-20 | `--spacing-20` | `5rem` | 80px | ページ間 |

### 3.2 用途別ガイドライン

| 用途 | 推奨スペーシング | Tailwind クラス |
|------|------------------|-----------------|
| アイコンとテキスト間 | spacing-2 | `gap-2` |
| フォームフィールド間 | spacing-5 | `space-y-5` |
| カード内パディング | spacing-5 | `p-5` |
| セクション間 | spacing-8〜spacing-12 | `mt-8`〜`mt-12` |
| ボタン内パディング | spacing-2 × spacing-4 | `py-2 px-4` |

---

## 4. シャドウ

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| shadow-xs | `--shadow-xs` | `0 1px 2px 0 rgba(0, 0, 0, 0.05)` | 微小な浮き上がり |
| shadow-sm | `--shadow-sm` | `0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)` | カード、ドロップダウン |
| shadow-md | `--shadow-md` | `0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)` | 浮遊要素 |
| shadow-lg | `--shadow-lg` | `0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)` | モーダル、ポップオーバー |
| shadow-xl | `--shadow-xl` | `0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)` | 大きなモーダル |
| shadow-2xl | `--shadow-2xl` | `0 25px 50px -12px rgba(0, 0, 0, 0.25)` | 最大の浮き上がり |
| shadow-inner | `--shadow-inner` | `inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)` | 凹み効果 |
| shadow-focus | `--shadow-focus` | `0 0 0 3px rgba(59, 130, 246, 0.3)` | フォーカスリング |

---

## 5. ボーダー半径

| トークン名 | CSS変数 | 値 | px換算 | 用途 |
|-----------|--------|-----|--------|------|
| radius-none | `--radius-none` | `0` | 0px | 角なし |
| radius-sm | `--radius-sm` | `0.25rem` | 4px | Badge、小ボタン |
| radius-md | `--radius-md` | `0.375rem` | 6px | ボタン、入力フィールド |
| radius-lg | `--radius-lg` | `0.5rem` | 8px | カード |
| radius-xl | `--radius-xl` | `0.75rem` | 12px | モーダル |
| radius-2xl | `--radius-2xl` | `1rem` | 16px | 大きなカード |
| radius-full | `--radius-full` | `9999px` | - | 円形、ピル型 |

---

## 6. トランジション

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| transition-fast | `--transition-fast` | `150ms ease` | ホバー、フォーカス |
| transition-base | `--transition-base` | `200ms ease` | 標準アニメーション |
| transition-slow | `--transition-slow` | `300ms ease` | 大きな変化 |
| transition-colors | `--transition-colors` | `color 150ms ease, background-color 150ms ease, border-color 150ms ease` | カラー変化 |

---

## 7. Z-Index スケール

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| z-dropdown | `--z-dropdown` | `100` | ドロップダウンメニュー |
| z-sticky | `--z-sticky` | `200` | スティッキー要素 |
| z-fixed | `--z-fixed` | `300` | 固定要素 |
| z-sidebar | `--z-sidebar` | `400` | サイドバー |
| z-header | `--z-header` | `500` | ヘッダー |
| z-modal-backdrop | `--z-modal-backdrop` | `600` | モーダル背景 |
| z-modal | `--z-modal` | `700` | モーダル |
| z-popover | `--z-popover` | `800` | ポップオーバー |
| z-tooltip | `--z-tooltip` | `900` | ツールチップ |
| z-toast | `--z-toast` | `1000` | トースト通知 |

---

## 8. レイアウト定数

| トークン名 | CSS変数 | 値 | 用途 |
|-----------|--------|-----|------|
| header-height | `--header-height` | `60px` | ヘッダー高さ |
| sidebar-width | `--sidebar-width` | `260px` | サイドバー幅（展開時） |
| sidebar-width-collapsed | `--sidebar-width-collapsed` | `60px` | サイドバー幅（折りたたみ時） |
| footer-height | `--footer-height` | `40px` | フッター高さ |
| content-max-width | `--content-max-width` | `1200px` | コンテンツ最大幅 |

---

## 9. ダークモード実装

### 9.1 テーマ切り替え方式

CAMPシステムでは以下の3つのテーマモードをサポートします。

| モード | 説明 |
|--------|------|
| `light` | ライトモード（明るい背景） |
| `dark` | ダークモード（暗い背景） |
| `system` | OSの設定に従う |

### 9.2 実装アーキテクチャ

```text
src/
├── lib/
│   └── theme.ts              # テーマユーティリティ
├── stores/
│   └── theme-store.ts        # テーマ状態管理（Zustand）
├── components/
│   └── ui/
│       └── theme-toggle.tsx  # テーマ切り替えコンポーネント
└── app/
    └── providers.tsx         # ThemeProvider設定
```

### 9.3 テーマストア（Zustand）

```typescript
// src/stores/theme-store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type Theme = 'light' | 'dark' | 'system';

type ThemeState = {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
};

const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      resolvedTheme: getSystemTheme(),
      setTheme: (theme) => {
        const resolvedTheme = theme === 'system' ? getSystemTheme() : theme;
        set({ theme, resolvedTheme });

        // DOMにクラスを適用
        if (resolvedTheme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      },
    }),
    {
      name: 'camp-theme',
      onRehydrateStorage: () => (state) => {
        // 初期化時にテーマを適用
        if (state) {
          state.setTheme(state.theme);
        }
      },
    }
  )
);
```

### 9.4 テーマトグルコンポーネント

```typescript
// src/components/ui/theme-toggle.tsx
import { Moon, Sun, Monitor } from 'lucide-react';
import { useThemeStore } from '@/stores/theme-store';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export const ThemeToggle = () => {
  const { theme, setTheme, resolvedTheme } = useThemeStore();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" data-testid="theme-toggle">
          {resolvedTheme === 'dark' ? (
            <Moon className="h-5 w-5" />
          ) : (
            <Sun className="h-5 w-5" />
          )}
          <span className="sr-only">テーマを切り替え</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem
          onClick={() => setTheme('light')}
          data-testid="theme-light"
        >
          <Sun className="mr-2 h-4 w-4" />
          ライト
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setTheme('dark')}
          data-testid="theme-dark"
        >
          <Moon className="mr-2 h-4 w-4" />
          ダーク
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => setTheme('system')}
          data-testid="theme-system"
        >
          <Monitor className="mr-2 h-4 w-4" />
          システム
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
```

### 9.5 OS設定変更の監視

```typescript
// src/hooks/use-system-theme.ts
import { useEffect } from 'react';
import { useThemeStore } from '@/stores/theme-store';

export const useSystemThemeListener = () => {
  const { theme, setTheme } = useThemeStore();

  useEffect(() => {
    if (theme !== 'system') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = () => {
      setTheme('system'); // 再計算をトリガー
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme, setTheme]);
};
```

### 9.6 サーバー連携（ユーザー設定API）

テーマ設定はサーバーの `user_settings` テーブルに永続化され、ログイン時に復元されます。

#### 関連API

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/user_account/me/settings` | ユーザー設定取得 |
| PATCH | `/api/v1/user_account/me/settings` | ユーザー設定更新 |

> 詳細は [03-user-management/01-user-management-design.md](./03-user-management/01-user-management-design.md) を参照

#### APIレスポンス型定義

```typescript
// src/features/user/types/user-settings.ts
type ThemeType = 'light' | 'dark' | 'system';

type UserSettingsResponse = {
  theme: ThemeType;
  language: 'ja' | 'en';
  timezone: string;
  notifications: {
    emailEnabled: boolean;
    projectInvite: boolean;
    sessionComplete: boolean;
    treeUpdate: boolean;
    systemAnnouncement: boolean;
  };
  display: {
    itemsPerPage: number;
    defaultProjectView: 'grid' | 'list';
    showWelcomeMessage: boolean;
  };
};

type UserSettingsUpdateRequest = {
  theme?: ThemeType;
  language?: 'ja' | 'en';
  timezone?: string;
  notifications?: Partial<UserSettingsResponse['notifications']>;
  display?: Partial<UserSettingsResponse['display']>;
};
```

#### テーマ同期フック

```typescript
// src/features/user/hooks/use-theme-sync.ts
import { useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useThemeStore } from '@/stores/theme-store';
import { getUserSettings, updateUserSettings } from '../api/user-settings';

/**
 * サーバーとローカルのテーマ設定を同期するフック
 */
export const useThemeSync = () => {
  const queryClient = useQueryClient();
  const { theme, setTheme } = useThemeStore();

  // サーバーから設定を取得
  const { data: settings } = useQuery({
    queryKey: ['user', 'settings'],
    queryFn: getUserSettings,
    staleTime: 5 * 60 * 1000, // 5分
  });

  // サーバーに設定を保存
  const { mutate: saveTheme } = useMutation({
    mutationFn: (newTheme: ThemeType) =>
      updateUserSettings({ theme: newTheme }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['user', 'settings'] });
    },
  });

  // 初回ログイン時：サーバー設定をローカルに反映
  useEffect(() => {
    if (settings?.theme && settings.theme !== theme) {
      setTheme(settings.theme);
    }
  }, [settings?.theme]);

  // テーマ変更時：サーバーに保存
  const updateTheme = (newTheme: ThemeType) => {
    setTheme(newTheme);      // ローカル即時反映
    saveTheme(newTheme);     // サーバーに非同期保存
  };

  return { theme, updateTheme };
};
```

#### API関数

```typescript
// src/features/user/api/user-settings.ts
import { api } from '@/lib/api-client';

export const getUserSettings = async (): Promise<UserSettingsResponse> => {
  const response = await api.get('/user_account/me/settings');
  return response.data;
};

export const updateUserSettings = async (
  data: UserSettingsUpdateRequest
): Promise<UserSettingsResponse> => {
  const response = await api.patch('/user_account/me/settings', data);
  return response.data;
};
```

#### ThemeToggle（サーバー連携版）

```typescript
// src/components/ui/theme-toggle.tsx
import { Moon, Sun, Monitor } from 'lucide-react';
import { useThemeSync } from '@/features/user/hooks/use-theme-sync';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export const ThemeToggle = () => {
  const { theme, updateTheme } = useThemeSync();
  const resolvedTheme = theme === 'system'
    ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
    : theme;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" data-testid="theme-toggle">
          {resolvedTheme === 'dark' ? (
            <Moon className="h-5 w-5" />
          ) : (
            <Sun className="h-5 w-5" />
          )}
          <span className="sr-only">テーマを切り替え</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        <DropdownMenuItem
          onClick={() => updateTheme('light')}
          data-testid="theme-light"
        >
          <Sun className="mr-2 h-4 w-4" />
          ライト
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => updateTheme('dark')}
          data-testid="theme-dark"
        >
          <Moon className="mr-2 h-4 w-4" />
          ダーク
        </DropdownMenuItem>
        <DropdownMenuItem
          onClick={() => updateTheme('system')}
          data-testid="theme-system"
        >
          <Monitor className="mr-2 h-4 w-4" />
          システム
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
};
```

#### データフロー

```text
┌─────────────────────────────────────────────────────────────────┐
│                        テーマ設定フロー                           │
└─────────────────────────────────────────────────────────────────┘

【初回ログイン時】
  ┌──────────┐     GET /settings      ┌──────────┐
  │  Server  │ ────────────────────► │  Client  │
  │  (API)   │   theme: "dark"       │ (Zustand)│
  └──────────┘                        └──────────┘
                                           │
                                           ▼
                                    setTheme("dark")
                                           │
                                           ▼
                              document.classList.add("dark")

【ユーザー操作時】
  ┌──────────┐    PATCH /settings     ┌──────────┐
  │  Server  │ ◄──────────────────── │  Client  │
  │  (API)   │   theme: "light"      │ (Zustand)│
  └──────────┘                        └──────────┘
       │                                   │
       ▼                                   ▼
  user_settings                    setTheme("light")
  テーブル更新                            │
                                          ▼
                             document.classList.remove("dark")
```

#### 設定画面での表示

テーマ設定はヘッダーのトグルボタン以外に、ユーザー設定画面（プロフィール）でも変更可能です。

**対応ユースケース**: U-012（ユーザー設定取得）、U-013（ユーザー設定更新）

---

## 10. Tailwind CSS 設定

### 10.1 tailwind.config.ts

```typescript
import type { Config } from 'tailwindcss';

export default {
  content: ['./src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class', // クラスベースのダークモード
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        neutral: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          500: '#f59e0b',
          600: '#d97706',
          700: '#b45309',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        },
        info: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
      fontFamily: {
        sans: ['Segoe UI', 'Hiragino Kaku Gothic ProN', 'Meiryo', 'sans-serif'],
        mono: ['Consolas', 'Monaco', 'Menlo', 'monospace'],
      },
      fontSize: {
        xs: ['0.75rem', { lineHeight: '1rem' }],
        sm: ['0.875rem', { lineHeight: '1.25rem' }],
        base: ['1rem', { lineHeight: '1.5rem' }],
        lg: ['1.125rem', { lineHeight: '1.75rem' }],
        xl: ['1.25rem', { lineHeight: '1.75rem' }],
        '2xl': ['1.5rem', { lineHeight: '2rem' }],
        '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
        '4xl': ['2.25rem', { lineHeight: '2.5rem' }],
      },
      spacing: {
        '0': '0',
        '1': '0.25rem',
        '2': '0.5rem',
        '3': '0.75rem',
        '4': '1rem',
        '5': '1.25rem',
        '6': '1.5rem',
        '8': '2rem',
        '10': '2.5rem',
        '12': '3rem',
        '16': '4rem',
        '20': '5rem',
      },
      borderRadius: {
        none: '0',
        sm: '0.25rem',
        DEFAULT: '0.375rem',
        md: '0.375rem',
        lg: '0.5rem',
        xl: '0.75rem',
        '2xl': '1rem',
        full: '9999px',
      },
      boxShadow: {
        xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
        DEFAULT: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
        md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
        lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
        xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)',
        '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
        inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.05)',
        focus: '0 0 0 3px rgba(59, 130, 246, 0.3)',
      },
      transitionDuration: {
        fast: '150ms',
        DEFAULT: '200ms',
        slow: '300ms',
      },
      zIndex: {
        dropdown: '100',
        sticky: '200',
        fixed: '300',
        sidebar: '400',
        header: '500',
        'modal-backdrop': '600',
        modal: '700',
        popover: '800',
        tooltip: '900',
        toast: '1000',
      },
    },
  },
  plugins: [],
} satisfies Config;
```

### 10.2 グローバルCSS変数（globals.css）

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Layout */
    --header-height: 60px;
    --sidebar-width: 260px;
    --sidebar-width-collapsed: 60px;
    --footer-height: 40px;
    --content-max-width: 1200px;

    /* ライトモード カラー */
    --color-background: #f8fafc;
    --color-surface: #ffffff;
    --color-surface-elevated: #ffffff;
    --color-border: #e2e8f0;
    --color-border-light: #f1f5f9;
    --color-text-primary: #1e293b;
    --color-text-secondary: #64748b;
    --color-text-muted: #94a3b8;
    --color-text-inverse: #ffffff;

    /* Focus Ring */
    --shadow-focus: 0 0 0 3px rgba(59, 130, 246, 0.3);

    /* コンポーネント固有 */
    --card-background: #ffffff;
    --input-background: #ffffff;
    --sidebar-background: #ffffff;
    --header-background: #ffffff;
    --dropdown-background: #ffffff;
    --modal-backdrop: rgba(0, 0, 0, 0.5);
  }

  .dark {
    /* ダークモード カラー */
    --color-background: #0f172a;
    --color-surface: #1e293b;
    --color-surface-elevated: #334155;
    --color-border: #334155;
    --color-border-light: #1e293b;
    --color-text-primary: #f1f5f9;
    --color-text-secondary: #94a3b8;
    --color-text-muted: #64748b;
    --color-text-inverse: #0f172a;

    /* Focus Ring（ダークモード調整） */
    --shadow-focus: 0 0 0 3px rgba(96, 165, 250, 0.4);

    /* コンポーネント固有 */
    --card-background: #1e293b;
    --input-background: #0f172a;
    --sidebar-background: #1e293b;
    --header-background: #1e293b;
    --dropdown-background: #334155;
    --modal-backdrop: rgba(0, 0, 0, 0.75);
  }

  /* フラッシュ防止（初期読み込み時） */
  html {
    color-scheme: light;
  }

  html.dark {
    color-scheme: dark;
  }

  body {
    background-color: var(--color-background);
    color: var(--color-text-primary);
    transition: background-color 0.2s ease, color 0.2s ease;
  }
}
```

### 10.3 フラッシュ防止スクリプト

ページ読み込み時のテーマフラッシュ（FOUC）を防ぐため、`<head>`内に以下のスクリプトを配置します。

```html
<!-- app/layout.tsx の <head> 内 -->
<script dangerouslySetInnerHTML={{
  __html: `
    (function() {
      try {
        var stored = localStorage.getItem('camp-theme');
        var theme = stored ? JSON.parse(stored).state.theme : 'system';
        var isDark = theme === 'dark' ||
          (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
        if (isDark) {
          document.documentElement.classList.add('dark');
        }
      } catch (e) {}
    })();
  `
}} />
```

---

## 11. CSSクラス・Reactコンポーネント対応表

| モックアップCSSクラス | 用途 | Reactコンポーネント | CVA Variant |
|----------------------|------|---------------------|-------------|
| `.btn` | ボタン基本 | `<Button>` | - |
| `.btn-primary` | プライマリボタン | `<Button>` | `variant="primary"` |
| `.btn-secondary` | セカンダリボタン | `<Button>` | `variant="secondary"` |
| `.btn-success` | 成功ボタン | `<Button>` | `variant="success"` |
| `.btn-warning` | 警告ボタン | `<Button>` | `variant="warning"` |
| `.btn-danger` | 危険ボタン | `<Button>` | `variant="danger"` |
| `.btn-ghost` | ゴーストボタン | `<Button>` | `variant="ghost"` |
| `.btn-link` | リンクボタン | `<Button>` | `variant="link"` |
| `.btn-xs` | 極小ボタン | `<Button>` | `size="xs"` |
| `.btn-sm` | 小ボタン | `<Button>` | `size="sm"` |
| `.btn-lg` | 大ボタン | `<Button>` | `size="lg"` |
| `.btn-xl` | 特大ボタン | `<Button>` | `size="xl"` |
| `.btn-icon` | アイコンボタン | `<IconButton>` | - |
| `.form-input` | テキスト入力 | `<Input>` | - |
| `.form-select` | セレクト | `<Select>` | - |
| `.form-textarea` | テキストエリア | `<Textarea>` | - |
| `.form-check` | チェックボックス/ラジオ | `<Checkbox>`, `<RadioGroup>` | - |
| `.toggle` | トグルスイッチ | `<Switch>` | - |
| `.form-error` | エラーメッセージ | `<FormField>` | - |
| `.card` | カード | `<Card>` | - |
| `.card-hoverable` | ホバー可能カード | `<Card>` | `hoverable={true}` |
| `.stat-card` | 統計カード | `<StatCard>` | - |
| `.data-table` | データテーブル | `<DataTable>` | - |
| `.badge` | バッジ | `<Badge>` | - |
| `.badge-primary` | プライマリバッジ | `<Badge>` | `variant="primary"` |
| `.badge-success` | 成功バッジ | `<Badge>` | `variant="success"` |
| `.badge-warning` | 警告バッジ | `<Badge>` | `variant="warning"` |
| `.badge-danger` | 危険バッジ | `<Badge>` | `variant="danger"` |
| `.tag` | タグ | `<Tag>` | - |
| `.alert` | アラート | `<Alert>` | - |
| `.alert-info` | 情報アラート | `<Alert>` | `variant="info"` |
| `.alert-success` | 成功アラート | `<Alert>` | `variant="success"` |
| `.alert-warning` | 警告アラート | `<Alert>` | `variant="warning"` |
| `.alert-danger` | 危険アラート | `<Alert>` | `variant="danger"` |
| `.modal` | モーダル | `<Modal>` | - |
| `.modal-sm` | 小モーダル | `<Modal>` | `size="sm"` |
| `.modal-lg` | 大モーダル | `<Modal>` | `size="lg"` |
| `.modal-xl` | 特大モーダル | `<Modal>` | `size="xl"` |
| `.tabs` | タブ | `<Tabs>` | - |
| `.pills` | ピル | `<Tabs>` | `variant="pills"` |
| `.breadcrumb` | パンくずリスト | `<Breadcrumb>` | - |
| `.pagination` | ページネーション | `<Pagination>` | - |
| `.spinner` | スピナー | `<Spinner>` | - |
| `.progress` | プログレスバー | `<Progress>` | - |
| `.skeleton` | スケルトン | `<Skeleton>` | - |
| `.empty-state` | 空状態 | `<EmptyState>` | - |
| `.file-upload` | ファイルアップロード | `<FileUpload>` | - |

---

## 関連ドキュメント

- [フロントエンド実装ガイドライン](./03-frontend-implementation-guide.md)
- [共通UIコンポーネント設計](./02-shared-ui-components.md)
- [モックアップ](../03-mockup/)

---

### ドキュメント管理情報

- **作成日**: 2026年1月3日
- **更新日**: 2026年1月3日
- **変更履歴**:
  - 2026/01/03: ダークモード対応を追加（セクション9）
