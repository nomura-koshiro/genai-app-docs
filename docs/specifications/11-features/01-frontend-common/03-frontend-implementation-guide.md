# フロントエンド実装ガイドライン

## 目的

本ドキュメントは、バックエンド設計書（API仕様・データベース設計）に対して、フロントエンド実装時に必ず従うべきアーキテクチャ・コーディング規約・設計原則を定義します。

すべてのフロントエンド実装は、このガイドラインに厳格に準拠する必要があります。

---

## 1. bulletproof-react アーキテクチャ

### 1.1 Features-based ディレクトリ構造（絶対遵守）

```text
src/
├── features/[feature-name]/     # ビジネス機能別モジュール（必須）
│   ├── api/                    # API層：サーバー通信（必須）
│   │   ├── get-users.ts       # クエリ関数
│   │   ├── create-user.ts     # ミューテーション関数
│   │   └── index.ts           # クリーンなエクスポート
│   ├── components/             # 機能固有コンポーネント（必須）
│   │   ├── user-list.tsx      # ビジネスロジック統合コンポーネント
│   │   ├── user-card.tsx      # 機能固有UI
│   │   └── index.ts           # クリーンなエクスポート
│   ├── hooks/                  # カスタムフック：ビジネスロジック（必須）
│   │   ├── use-user-form.ts   # フォーム管理ロジック
│   │   ├── use-user-filter.ts # フィルタリングロジック
│   │   └── index.ts           # クリーンなエクスポート
│   ├── types/                  # 型定義（必須）
│   │   ├── user.ts            # type定義のみ（interface禁止）
│   │   └── index.ts           # クリーンなエクスポート
│   └── index.ts               # 機能全体のクリーンなエクスポート
│
├── components/                 # 再利用可能UIコンポーネントのみ（必須）
│   ├── sample-ui/             # 基本UIコンポーネント
│   │   ├── button.tsx         # CVAベースのボタン
│   │   ├── input.tsx          # フォーム入力
│   │   ├── card.tsx           # カード
│   │   └── index.ts
│   └── ui/                    # ユーティリティコンポーネント
│       ├── loading.tsx        # ローディング表示
│       ├── error-message.tsx  # エラー表示
│       ├── empty-state.tsx    # 空状態表示
│       └── index.ts
│
├── lib/                       # 共通ライブラリ・設定（必須）
│   ├── api-client.ts         # API通信の基盤
│   ├── query-client.ts       # TanStack Query設定
│   ├── validation.ts         # Zodスキーマ
│   └── utils.ts              # ユーティリティ関数
│
├── stores/                    # Zustand ストア（必須）
│   ├── auth-store.ts         # 認証状態
│   ├── ui-store.ts           # UI状態（モーダル、サイドバー）
│   └── index.ts
│
├── hooks/                     # 汎用カスタムフック（必須）
│   ├── use-debounce.ts       # デバウンス
│   ├── use-pagination.ts     # ページネーション
│   └── index.ts
│
├── utils/                     # 純粋関数ユーティリティ（必須）
│   ├── format.ts             # フォーマット関数
│   ├── date.ts               # 日時処理
│   └── index.ts
│
└── types/                     # アプリ全体の型定義（必須）
    ├── api.ts                # API共通型
    ├── common.ts             # 共通型
    └── index.ts
```

### 1.2 各ディレクトリの責務

| ディレクトリ | 責務 | 配置すべきもの | 配置してはいけないもの |
|------------|------|-------------|---------------------|
| `features/[name]/api/` | API通信 | クエリ関数、ミューテーション関数 | ビジネスロジック、UI処理 |
| `features/[name]/components/` | 機能固有UI | 機能に特化したコンポーネント | 汎用UIコンポーネント |
| `features/[name]/hooks/` | ビジネスロジック | カスタムフック | API呼び出し（api/配下に分離） |
| `features/[name]/types/` | 型定義 | `type` 定義のみ | `interface` 定義（禁止） |
| `components/sample-ui/` | 基本UI | Button、Input、Card等 | ビジネスロジック |
| `components/ui/` | ユーティリティUI | Loading、Error、EmptyState | 機能固有コンポーネント |
| `lib/` | 共通ライブラリ | API Client、設定、ユーティリティ | ビジネスロジック |
| `stores/` | グローバル状態 | Zustand ストア | サーバー状態（TanStack Query使用） |
| `hooks/` | 汎用フック | デバウンス、ページネーション等 | 機能固有ロジック |
| `utils/` | 純粋関数 | フォーマット、計算、変換 | 副作用を持つ関数 |

### 1.3 絶対に作ってはいけない構造

```text
❌ src/pages/              # Next.js App Routerではapp/を使用
❌ src/containers/         # features/で分離する
❌ src/services/           # features/[name]/api/に配置
❌ src/models/             # features/[name]/types/に配置
❌ src/redux/              # Zustand + TanStack Queryを使用
❌ src/actions/            # features/[name]/api/に配置
❌ src/reducers/           # Zustandを使用
❌ src/sagas/              # TanStack Queryを使用
❌ src/contexts/           # Zustand/TanStack Queryを優先
```

---

## 2. 型定義ルール（絶対遵守）

### 2.1 基本ルール

```typescript
// ✅ 良い例：type を使用
export type User = {
  id: string
  email: string
  displayName: string
  isActive: boolean
}

// ❌ 悪い例：interface 禁止
export interface User {  // 禁止
  id: string
  email: string
}
```

### 2.2 アロー関数必須

```typescript
// ✅ 良い例：アロー関数
export const formatDate = (date: Date): string => {
  return date.toISOString()
}

export const UserCard: FC<UserCardProps> = ({ user }) => {
  return <div>{user.displayName}</div>
}

// ❌ 悪い例：function宣言（禁止）
export function formatDate(date: Date): string {  // 禁止
  return date.toISOString()
}

function UserCard({ user }: UserCardProps) {  // 禁止
  return <div>{user.displayName}</div>
}
```

### 2.3 any 禁止

```typescript
// ✅ 良い例：厳密な型定義
export const handleSubmit = (data: UserInput): Promise<User> => {
  return apiClient.post<User>('/users', data)
}

// ❌ 悪い例：any使用（禁止）
export const handleSubmit = (data: any): Promise<any> => {  // 禁止
  return apiClient.post('/users', data)
}

// ✅ unknown を使用して型安全に処理
export const parseApiError = (error: unknown): ApiError => {
  if (error instanceof Error) {
    return { message: error.message }
  }
  return { message: 'Unknown error' }
}
```

### 2.4 CamelCase変換ルール（バックエンド snake_case → フロントエンド camelCase）

```typescript
// バックエンドレスポンス（snake_case）
type UserResponseBackend = {
  user_id: string
  display_name: string
  created_at: string
  is_active: boolean
}

// フロントエンド型定義（camelCase）
export type UserResponse = {
  userId: string
  displayName: string
  createdAt: string
  isActive: boolean
}

// 変換関数
export const convertUserResponse = (backend: UserResponseBackend): UserResponse => ({
  userId: backend.user_id,
  displayName: backend.display_name,
  createdAt: backend.created_at,
  isActive: backend.is_active,
})
```

### 2.5 Enum → type リテラル型の変換例

```typescript
// ❌ 悪い例：Enum使用（非推奨）
export enum UserRole {  // 非推奨
  Admin = 'ADMIN',
  User = 'USER',
}

// ✅ 良い例：type リテラル型
export type UserRole = 'ADMIN' | 'USER'

export type SystemRole = 'system_admin' | 'user'

export type ProjectRole = 'PROJECT_MANAGER' | 'MODERATOR' | 'MEMBER' | 'VIEWER'

// バリデーションヘルパー
export const isValidUserRole = (role: string): role is UserRole => {
  return role === 'ADMIN' || role === 'USER'
}

// 定数オブジェクト（選択肢表示用）
export const USER_ROLES = {
  ADMIN: 'ADMIN',
  USER: 'USER',
} as const

export type UserRole = typeof USER_ROLES[keyof typeof USER_ROLES]
```

---

## 3. 状態管理戦略

### 3.1 状態の分類と管理手法

| 状態の種類 | 管理手法 | 使用ケース | 例 |
|----------|---------|----------|---|
| **グローバル状態** | Zustand | 認証状態、UIフラグ | ユーザー情報、サイドバー開閉 |
| **サーバー状態** | TanStack Query | APIデータ、キャッシュ | ユーザー一覧、プロジェクト詳細 |
| **ローカル状態** | React State | フォーム、モーダル | 入力値、開閉状態 |

### 3.2 Zustand: グローバル状態

```typescript
// stores/auth-store.ts
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

type UserResponse = {
  id: string
  email: string
  displayName: string
  roles: string[]
}

type AuthState = {
  user: UserResponse | null
  isLoading: boolean
  error: string | null

  setUser: (user: UserResponse | null) => void
  setLoading: (loading: boolean) => void
  logout: () => void
  reset: () => void
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        isLoading: false,
        error: null,

        setUser: (user) => set({ user, error: null }),
        setLoading: (loading) => set({ isLoading: loading }),
        logout: () => set({ user: null, error: null }),
        reset: () => set({ user: null, isLoading: false, error: null }),
      }),
      {
        name: 'auth-storage',
        partialize: (state) => ({ user: state.user }), // user のみ永続化
      }
    ),
    { name: 'AuthStore' }
  )
)

// 使用例
export const UserProfile: FC = () => {
  const user = useAuthStore((state) => state.user)
  const logout = useAuthStore((state) => state.logout)

  if (!user) return null

  return (
    <div>
      <p>{user.displayName}</p>
      <button onClick={logout}>ログアウト</button>
    </div>
  )
}
```

### 3.3 TanStack Query: サーバー状態

```typescript
// features/users/api/get-users.ts
import { useQuery } from '@tanstack/react-query'
import type { QueryConfig } from '@/lib/query-client'
import { apiClient } from '@/lib/api-client'

export type User = {
  id: string
  email: string
  displayName: string
  isActive: boolean
}

export type GetUsersResponse = {
  items: User[]
  total: number
  skip: number
  limit: number
}

export const getUsers = async (
  params?: { email?: string; skip?: number; limit?: number }
): Promise<GetUsersResponse> => {
  const response = await apiClient.get<GetUsersResponse>('/api/v1/user_account', {
    params,
  })
  return response.data
}

export type UseUsersOptions = {
  email?: string
  skip?: number
  limit?: number
  config?: QueryConfig<typeof getUsers>
}

export const useUsers = ({ email, skip = 0, limit = 20, config }: UseUsersOptions = {}) => {
  return useQuery({
    queryKey: ['users', { email, skip, limit }],
    queryFn: () => getUsers({ email, skip, limit }),
    staleTime: 1000 * 60, // 1分間キャッシュ
    ...config,
  })
}

// 使用例
export const UserList: FC = () => {
  const { data, isLoading, error } = useUsers({ limit: 20 })

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage error={error} />
  if (!data?.items.length) return <EmptyState message="ユーザーが登録されていません" />

  return (
    <div>
      {data.items.map((user) => (
        <UserCard key={user.id} user={user} />
      ))}
    </div>
  )
}
```

### 3.4 楽観的更新パターンの実装例

```typescript
// features/users/api/update-user.ts
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { MutationConfig } from '@/lib/query-client'
import { apiClient } from '@/lib/api-client'
import type { User } from './get-users'

export type UpdateUserInput = {
  displayName?: string
}

export const updateUser = async ({
  id,
  data,
}: {
  id: string
  data: UpdateUserInput
}): Promise<User> => {
  const response = await apiClient.patch<User>(`/api/v1/user_account/${id}`, data)
  return response.data
}

export const useUpdateUser = (config?: MutationConfig<typeof updateUser>) => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: updateUser,

    // 楽観的更新
    onMutate: async ({ id, data }) => {
      // 進行中のクエリをキャンセル
      await queryClient.cancelQueries({ queryKey: ['users', id] })

      // 以前のデータを保存
      const previousUser = queryClient.getQueryData<User>(['users', id])

      // 楽観的更新
      if (previousUser) {
        queryClient.setQueryData<User>(['users', id], {
          ...previousUser,
          ...data,
        })
      }

      return { previousUser }
    },

    // エラー時のロールバック
    onError: (err, variables, context) => {
      if (context?.previousUser) {
        queryClient.setQueryData(['users', variables.id], context.previousUser)
      }
    },

    // 完了後にキャッシュを無効化
    onSettled: (data, error, variables) => {
      queryClient.invalidateQueries({ queryKey: ['users', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['users'] })
    },

    ...config,
  })
}

// 使用例
export const UserEditForm: FC<{ userId: string }> = ({ userId }) => {
  const updateUser = useUpdateUser()

  const handleSubmit = async (data: UpdateUserInput) => {
    await updateUser.mutateAsync({ id: userId, data })
  }

  return <form onSubmit={handleSubmit}>{/* フォーム */}</form>
}
```

### 3.5 React State: ローカル状態

```typescript
// features/users/components/user-search.tsx
import { useState, useCallback } from 'react'
import { useDebounce } from '@/hooks/use-debounce'
import { useUsers } from '../api/get-users'

export const UserSearch: FC = () => {
  const [searchQuery, setSearchQuery] = useState('')
  const debouncedQuery = useDebounce(searchQuery, 300)

  const { data, isLoading } = useUsers({
    email: debouncedQuery,
    limit: 20,
  })

  const handleSearchChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value)
  }, [])

  return (
    <div>
      <input
        type="text"
        value={searchQuery}
        onChange={handleSearchChange}
        placeholder="メールアドレスで検索"
      />
      {isLoading && <LoadingSpinner />}
      {data && <UserList users={data.items} />}
    </div>
  )
}
```

---

## 4. コンポーネント設計原則

### 4.1 SOLID原則の適用

#### 単一責任の原則（Single Responsibility Principle）

各コンポーネントは単一の責任を持つ。

```typescript
// ❌ 悪い例：複数の責任を持つ
export const UserManagement: FC = () => {
  const { data: users } = useUsers()
  const deleteUser = useDeleteUser()
  const [isModalOpen, setIsModalOpen] = useState(false)

  return (
    <div>
      {/* 一覧表示 */}
      {users?.map((user) => (
        <div key={user.id}>
          <p>{user.displayName}</p>
          <button onClick={() => deleteUser.mutate(user.id)}>削除</button>
        </div>
      ))}
      {/* モーダル */}
      {isModalOpen && <Modal onClose={() => setIsModalOpen(false)} />}
    </div>
  )
}

// ✅ 良い例：責任を分離
export const UserList: FC = () => {
  const { data: users, isLoading, error } = useUsers()

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage error={error} />
  if (!users?.items.length) return <EmptyState message="ユーザーが登録されていません" />

  return (
    <div className="space-y-4">
      {users.items.map((user) => (
        <UserCard key={user.id} user={user} />
      ))}
    </div>
  )
}

export const UserCard: FC<{ user: User }> = ({ user }) => {
  const deleteUser = useDeleteUser()

  const handleDelete = useCallback(() => {
    if (confirm('削除してもよろしいですか？')) {
      deleteUser.mutate(user.id)
    }
  }, [user.id, deleteUser])

  return (
    <div className="p-4 border rounded-lg">
      <h3>{user.displayName}</h3>
      <p>{user.email}</p>
      <button onClick={handleDelete}>削除</button>
    </div>
  )
}
```

#### 開放閉鎖の原則（Open/Closed Principle）

CVAによる拡張、修正に対して閉じる。

```typescript
// components/sample-ui/button.tsx
import { forwardRef, type ButtonHTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline: 'border border-input hover:bg-accent hover:text-accent-foreground',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 px-3',
        lg: 'h-11 px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size }), className)}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = 'Button'

// 使用例：新しいバリアントを追加せずに拡張
<Button variant="destructive" size="sm">削除</Button>
<Button variant="outline" className="custom-class">キャンセル</Button>
```

#### リスコフの置換原則（Liskov Substitution Principle）

Props型の一貫性を保つ。

```typescript
// 基底Props型
export type BaseCardProps = {
  title: string
  description?: string
  className?: string
}

// 拡張Props型（基底型と互換性あり）
export type UserCardProps = BaseCardProps & {
  user: User
  onEdit?: (user: User) => void
  onDelete?: (userId: string) => void
}

export const UserCard: FC<UserCardProps> = ({ title, description, user, onEdit, onDelete }) => {
  return (
    <div className="p-4 border rounded-lg">
      <h3>{title}</h3>
      {description && <p>{description}</p>}
      <p>{user.displayName}</p>
      {onEdit && <button onClick={() => onEdit(user)}>編集</button>}
      {onDelete && <button onClick={() => onDelete(user.id)}>削除</button>}
    </div>
  )
}
```

#### インターフェース分離の原則（Interface Segregation Principle）

必要最小限のPropsを定義。

```typescript
// ❌ 悪い例：不要なPropsを含む
export type UserCardProps = {
  user: User
  onEdit: (user: User) => void
  onDelete: (userId: string) => void
  onActivate: (userId: string) => void  // 使わない場合もある
  onDeactivate: (userId: string) => void  // 使わない場合もある
}

// ✅ 良い例：必要最小限のProps
export type UserCardProps = {
  user: User
  actions?: {
    onEdit?: (user: User) => void
    onDelete?: (userId: string) => void
  }
}

export const UserCard: FC<UserCardProps> = ({ user, actions }) => {
  return (
    <div className="p-4 border rounded-lg">
      <h3>{user.displayName}</h3>
      {actions?.onEdit && <button onClick={() => actions.onEdit(user)}>編集</button>}
      {actions?.onDelete && <button onClick={() => actions.onDelete(user.id)}>削除</button>}
    </div>
  )
}
```

#### 依存性逆転の原則（Dependency Inversion Principle）

カスタムフックによる抽象化。

```typescript
// features/users/hooks/use-user-form.ts
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useCreateUser, useUpdateUser } from '../api'
import type { User } from '../types'

const userInputSchema = z.object({
  displayName: z.string().min(1, '表示名は必須です').max(255, '255文字以内で入力してください'),
  email: z.string().email('有効なメールアドレスを入力してください'),
})

export type UserInput = z.infer<typeof userInputSchema>

export const useUserForm = (initialUser?: User) => {
  const form = useForm<UserInput>({
    resolver: zodResolver(userInputSchema),
    defaultValues: initialUser
      ? {
          displayName: initialUser.displayName,
          email: initialUser.email,
        }
      : {},
  })

  const createUser = useCreateUser()
  const updateUser = useUpdateUser()

  const handleSubmit = form.handleSubmit(async (data) => {
    try {
      if (initialUser) {
        await updateUser.mutateAsync({ id: initialUser.id, data })
      } else {
        await createUser.mutateAsync(data)
      }
      form.reset()
    } catch (error) {
      // エラーハンドリング（api-clientで自動処理）
    }
  })

  return {
    form,
    handleSubmit,
    isSubmitting: createUser.isPending || updateUser.isPending,
  }
}

// 使用例
export const UserForm: FC<{ user?: User }> = ({ user }) => {
  const { form, handleSubmit, isSubmitting } = useUserForm(user)

  return (
    <form onSubmit={handleSubmit}>
      <input {...form.register('displayName')} />
      <input {...form.register('email')} />
      <button type="submit" disabled={isSubmitting}>保存</button>
    </form>
  )
}
```

### 4.2 forwardRef の使用

```typescript
// components/sample-ui/input.tsx
import { forwardRef, type InputHTMLAttributes } from 'react'
import { cn } from '@/lib/utils'

export type InputProps = InputHTMLAttributes<HTMLInputElement> & {
  error?: string
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <div>
        <input
          ref={ref}
          className={cn(
            'flex h-10 w-full rounded-md border border-input bg-background px-3 py-2',
            error && 'border-destructive',
            className
          )}
          {...props}
        />
        {error && <p className="text-sm text-destructive">{error}</p>}
      </div>
    )
  }
)
Input.displayName = 'Input'

// React Hook Form との統合
export const UserForm: FC = () => {
  const { register, formState: { errors } } = useForm()

  return (
    <form>
      <Input
        {...register('email')}
        error={errors.email?.message}
        placeholder="メールアドレス"
      />
    </form>
  )
}
```

### 4.3 Props設計のベストプラクティス

```typescript
// ✅ 良い例：明確で型安全なProps
export type UserCardProps = {
  user: User
  variant?: 'default' | 'compact' | 'detailed'
  showActions?: boolean
  onEdit?: (user: User) => void
  onDelete?: (userId: string) => void
  className?: string
}

export const UserCard: FC<UserCardProps> = ({
  user,
  variant = 'default',
  showActions = true,
  onEdit,
  onDelete,
  className,
}) => {
  return (
    <div className={cn('p-4 border rounded-lg', className)}>
      {/* コンポーネント実装 */}
    </div>
  )
}

// ❌ 悪い例：型が不明確、デフォルト値なし
export type UserCardProps = {
  user: any  // any禁止
  variant: string  // リテラル型にすべき
  showActions: boolean  // デフォルト値なし
  onEdit: Function  // 引数・戻り値が不明確
}
```

---

## 5. パフォーマンス最適化

### 5.1 React.memo の適切な使用

```typescript
// ✅ 良い例：shallow comparison + カスタム比較関数
import { memo, useCallback } from 'react'

type UserCardProps = {
  user: User
  onEdit: (user: User) => void
  onDelete: (userId: string) => void
}

export const UserCard = memo<UserCardProps>(
  ({ user, onEdit, onDelete }) => {
    const handleEdit = useCallback(() => onEdit(user), [user, onEdit])
    const handleDelete = useCallback(() => onDelete(user.id), [user.id, onDelete])

    return (
      <div className="p-4 border rounded-lg">
        <h3>{user.displayName}</h3>
        <p>{user.email}</p>
        <div className="flex gap-2 mt-2">
          <button onClick={handleEdit}>編集</button>
          <button onClick={handleDelete}>削除</button>
        </div>
      </div>
    )
  },
  (prevProps, nextProps) => {
    // カスタム比較：updatedAtが変わっていなければ再レンダリングしない
    return (
      prevProps.user.id === nextProps.user.id &&
      prevProps.user.updatedAt === nextProps.user.updatedAt
    )
  }
)
UserCard.displayName = 'UserCard'
```

### 5.2 useMemo / useCallback

```typescript
// ✅ 良い例：重い計算のメモ化
import { useMemo, useCallback } from 'react'

export const UserStatistics: FC<{ users: User[] }> = ({ users }) => {
  // 重い計算をメモ化
  const statistics = useMemo(() => {
    return {
      total: users.length,
      active: users.filter((user) => user.isActive).length,
      inactive: users.filter((user) => !user.isActive).length,
      averageLoginCount: users.reduce((sum, user) => sum + user.loginCount, 0) / users.length,
    }
  }, [users])

  return (
    <div>
      <p>合計: {statistics.total}</p>
      <p>有効: {statistics.active}</p>
      <p>無効: {statistics.inactive}</p>
      <p>平均ログイン回数: {statistics.averageLoginCount.toFixed(2)}</p>
    </div>
  )
}

// ✅ 良い例：コールバック関数のメモ化
export const UserList: FC = () => {
  const { data: users } = useUsers()
  const deleteUser = useDeleteUser()

  const handleDelete = useCallback(
    (userId: string) => {
      if (confirm('削除してもよろしいですか？')) {
        deleteUser.mutate(userId)
      }
    },
    [deleteUser]
  )

  return (
    <div>
      {users?.items.map((user) => (
        <UserCard key={user.id} user={user} onDelete={handleDelete} />
      ))}
    </div>
  )
}
```

### 5.3 仮想スクロール（大量データ）

```typescript
// features/users/components/user-list-virtual.tsx
import { useVirtualizer } from '@tanstack/react-virtual'
import { useRef } from 'react'

export const UserListVirtual: FC<{ users: User[] }> = ({ users }) => {
  const parentRef = useRef<HTMLDivElement>(null)

  const virtualizer = useVirtualizer({
    count: users.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 80, // 各行の推定高さ
    overscan: 5, // 前後5行を余分にレンダリング
  })

  return (
    <div ref={parentRef} className="h-[600px] overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => {
          const user = users[virtualItem.index]
          return (
            <div
              key={user.id}
              style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width: '100%',
                height: `${virtualItem.size}px`,
                transform: `translateY(${virtualItem.start}px)`,
              }}
            >
              <UserCard user={user} />
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

### 5.4 遅延ロード（Dynamic Import）

```typescript
// app/admin/users/page.tsx
import dynamic from 'next/dynamic'
import { Suspense } from 'react'

// 動的インポート
const UserList = dynamic(() => import('@/features/users/components/user-list'), {
  loading: () => <LoadingSpinner />,
  ssr: false, // CSRのみ（必要に応じて）
})

export default function UsersPage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <UserList />
    </Suspense>
  )
}
```

---

## 6. エラーハンドリング

### 6.1 RFC 9457 エラーレスポンスの処理

```typescript
// types/api.ts
export type ApiErrorResponse = {
  type: string
  title: string
  status: number
  detail: string
  instance: string
  errors?: Array<{
    field: string
    message: string
  }>
}

export type ApiError = Error & {
  response?: {
    status: number
    data: ApiErrorResponse
  }
}
```

### 6.2 API エラー型定義

```typescript
// lib/api-client.ts
import axios, { type AxiosError } from 'axios'
import { useAuthStore } from '@/stores/auth-store'

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
})

// リクエストインターセプター（認証トークン付与）
apiClient.interceptors.request.use((config) => {
  const user = useAuthStore.getState().user
  if (user?.accessToken) {
    config.headers.Authorization = `Bearer ${user.accessToken}`
  }
  return config
})

// レスポンスインターセプター（エラーハンドリング）
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorResponse>) => {
    const apiError = error.response?.data

    // 401: 認証エラー → ログアウト
    if (error.response?.status === 401) {
      useAuthStore.getState().logout()
      window.location.href = '/login'
    }

    // 403: 権限不足 → 通知
    if (error.response?.status === 403) {
      // 通知表示（toast等）
      console.error('アクセス権限がありません:', apiError?.detail)
    }

    // 500: サーバーエラー → 通知
    if (error.response?.status === 500) {
      console.error('サーバーエラーが発生しました:', apiError?.detail)
    }

    return Promise.reject(error)
  }
)
```

### 6.3 統一エラーハンドラー

```typescript
// components/ui/error-message.tsx
import type { FC } from 'react'
import type { ApiError } from '@/types/api'

export type ErrorMessageProps = {
  error: unknown
  retry?: () => void
}

export const ErrorMessage: FC<ErrorMessageProps> = ({ error, retry }) => {
  const getErrorMessage = (error: unknown): string => {
    if (typeof error === 'string') return error

    if (error && typeof error === 'object' && 'response' in error) {
      const apiError = error as ApiError
      return apiError.response?.data?.detail || 'エラーが発生しました'
    }

    if (error instanceof Error) {
      return error.message
    }

    return '不明なエラーが発生しました'
  }

  return (
    <div className="p-4 border border-destructive rounded-lg bg-destructive/10">
      <h3 className="font-semibold text-destructive">エラー</h3>
      <p className="text-sm text-destructive">{getErrorMessage(error)}</p>
      {retry && (
        <button onClick={retry} className="mt-2 text-sm underline">
          再試行
        </button>
      )}
    </div>
  )
}

// 使用例
export const UserList: FC = () => {
  const { data, isLoading, error, refetch } = useUsers()

  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage error={error} retry={refetch} />

  return <div>{/* ユーザー一覧 */}</div>
}
```

---

## 7. テスタビリティ

### 7.1 data-testid の命名規則

```typescript
// 命名規則: [feature]-[component]-[element]-[action?]
export const UserCard: FC<{ user: User }> = ({ user }) => {
  return (
    <div data-testid="user-card" data-user-id={user.id}>
      <h3 data-testid="user-card-name">{user.displayName}</h3>
      <p data-testid="user-card-email">{user.email}</p>
      <button data-testid="user-card-edit-button">編集</button>
      <button data-testid="user-card-delete-button">削除</button>
    </div>
  )
}

// テストコード
import { render, screen } from '@testing-library/react'
import { UserCard } from './user-card'

test('ユーザーカードが正しく表示される', () => {
  const user = { id: '1', displayName: 'テストユーザー', email: 'test@example.com' }
  render(<UserCard user={user} />)

  expect(screen.getByTestId('user-card-name')).toHaveTextContent('テストユーザー')
  expect(screen.getByTestId('user-card-email')).toHaveTextContent('test@example.com')
})
```

### 7.2 テストしやすいコンポーネント設計

```typescript
// ❌ 悪い例：テストしにくい（API呼び出しが内部に）
export const UserList: FC = () => {
  const [users, setUsers] = useState<User[]>([])

  useEffect(() => {
    fetch('/api/users')
      .then((res) => res.json())
      .then((data) => setUsers(data))
  }, [])

  return <div>{users.map((user) => <UserCard key={user.id} user={user} />)}</div>
}

// ✅ 良い例：テストしやすい（データを外部から注入）
export type UserListProps = {
  users: User[]
  isLoading?: boolean
  error?: Error
}

export const UserList: FC<UserListProps> = ({ users, isLoading, error }) => {
  if (isLoading) return <LoadingSpinner />
  if (error) return <ErrorMessage error={error} />
  if (!users.length) return <EmptyState message="ユーザーが登録されていません" />

  return (
    <div data-testid="user-list">
      {users.map((user) => (
        <UserCard key={user.id} user={user} />
      ))}
    </div>
  )
}

// コンテナコンポーネント（API統合）
export const UserListContainer: FC = () => {
  const { data, isLoading, error } = useUsers()

  return <UserList users={data?.items ?? []} isLoading={isLoading} error={error} />
}

// テストコード
test('ユーザー一覧が正しく表示される', () => {
  const users = [
    { id: '1', displayName: 'User 1', email: 'user1@example.com' },
    { id: '2', displayName: 'User 2', email: 'user2@example.com' },
  ]

  render(<UserList users={users} />)
  expect(screen.getByTestId('user-list')).toBeInTheDocument()
})
```

---

## 8. アクセシビリティ

### 8.1 ARIA属性

```typescript
// components/sample-ui/button.tsx
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ children, disabled, ...props }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled}
        aria-disabled={disabled}
        {...props}
      >
        {children}
      </button>
    )
  }
)

// モーダル
export const Modal: FC<{ isOpen: boolean; onClose: () => void; children: ReactNode }> = ({
  isOpen,
  onClose,
  children,
}) => {
  if (!isOpen) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      className="fixed inset-0 z-50"
    >
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />
      <div className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white p-6 rounded-lg">
        <h2 id="modal-title" className="text-lg font-semibold">モーダルタイトル</h2>
        {children}
      </div>
    </div>
  )
}
```

### 8.2 キーボードナビゲーション

```typescript
// components/ui/dropdown.tsx
import { useState, useRef, useEffect } from 'react'

export const Dropdown: FC<{ items: string[] }> = ({ items }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [focusedIndex, setFocusedIndex] = useState(0)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const handleKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setFocusedIndex((prev) => (prev + 1) % items.length)
        break
      case 'ArrowUp':
        e.preventDefault()
        setFocusedIndex((prev) => (prev - 1 + items.length) % items.length)
        break
      case 'Enter':
        e.preventDefault()
        // アイテム選択
        break
      case 'Escape':
        setIsOpen(false)
        break
    }
  }

  return (
    <div ref={dropdownRef} onKeyDown={handleKeyDown}>
      <button onClick={() => setIsOpen(!isOpen)} aria-haspopup="listbox" aria-expanded={isOpen}>
        ドロップダウン
      </button>
      {isOpen && (
        <ul role="listbox" aria-activedescendant={`item-${focusedIndex}`}>
          {items.map((item, index) => (
            <li
              key={index}
              id={`item-${index}`}
              role="option"
              aria-selected={index === focusedIndex}
              tabIndex={index === focusedIndex ? 0 : -1}
            >
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
```

### 8.3 フォーカス管理

```typescript
// features/users/components/user-form-modal.tsx
import { useEffect, useRef } from 'react'
import { Modal } from '@/components/ui/modal'

export const UserFormModal: FC<{ isOpen: boolean; onClose: () => void }> = ({
  isOpen,
  onClose,
}) => {
  const firstInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (isOpen && firstInputRef.current) {
      firstInputRef.current.focus()
    }
  }, [isOpen])

  return (
    <Modal isOpen={isOpen} onClose={onClose}>
      <form>
        <input ref={firstInputRef} placeholder="表示名" />
        <input placeholder="メールアドレス" />
        <button type="submit">保存</button>
        <button type="button" onClick={onClose}>キャンセル</button>
      </form>
    </Modal>
  )
}
```

---

## 9. まとめ

### 9.1 実装前チェックリスト

- [ ] **Features-based構造** に正確に従っているか
- [ ] **bulletproof-react** のディレクトリ構成を守っているか
- [ ] **SOLID/DRY/KISS原則** を適用しているか
- [ ] **型安全性**: `interface`禁止、`type`のみ使用しているか
- [ ] **アロー関数必須**: すべての関数がアロー関数か
- [ ] **any禁止**: 厳密な型定義がされているか
- [ ] **状態管理**: Zustand（グローバル）、TanStack Query（サーバー）、React State（ローカル）を適切に使い分けているか
- [ ] **CVA**: バリアント設計が適切か
- [ ] **forwardRef**: 必要な場所で使用しているか
- [ ] **パフォーマンス**: memo、useMemo、useCallbackを適切に使用しているか
- [ ] **エラーハンドリング**: RFC 9457に準拠したエラー処理を実装しているか
- [ ] **テスタビリティ**: data-testidが適切に設定されているか
- [ ] **アクセシビリティ**: ARIA属性、キーボードナビゲーション、フォーカス管理が実装されているか

### 9.2 関連ドキュメント

- **バックエンドAPI仕様**: [01-api-overview/01-api-overview.md](./01-api-overview/01-api-overview.md)
- **ユーザー管理フロントエンド設計**: [03-user-management/02-user-management-frontend-design.md](./03-user-management/02-user-management-frontend-design.md)
- **プロジェクト管理フロントエンド設計**: [04-project-management/02-project-management-frontend-design.md](./04-project-management/02-project-management-frontend-design.md)

---

**ドキュメント管理情報:**

- **作成日**: 2026年1月3日
- **更新日**: 2026年1月3日
- **対象バージョン**: 現行実装
- **適用範囲**: すべてのフロントエンド実装
