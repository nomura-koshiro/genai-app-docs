# 共通UIコンポーネント設計仕様

## 概要

本ドキュメントは、`components/ui/` に配置する再利用可能な共通UIコンポーネントの設計を定義します。
bulletproof-react アーキテクチャに準拠し、全機能で一貫性のあるUIを提供します。

## モックアップ参照

本ドキュメントのコンポーネントは `docs/specifications/03-mockup/design-system.css` に定義されたCSSクラスを基に設計されています。

| モックアップCSSクラス | 対応コンポーネント |
|----------------------|-------------------|
| `.form-input`, `.form-input-sm`, `.form-input-lg` | `<Input>` |
| `.form-textarea` | `<Textarea>` |
| `.form-select` | `<Select>` |
| `.form-check`, `.form-check-input` | `<Checkbox>`, `<RadioGroup>` |
| `.toggle`, `.toggle-slider` | `<Switch>` |
| `.form-group`, `.form-label`, `.form-error`, `.form-help` | `<FormField>` |
| `.btn`, `.btn-*` | `<Button>` |
| `.btn-icon` | `<IconButton>` |
| `.spinner`, `.spinner-sm`, `.spinner-lg` | `<Spinner>` |
| `.alert`, `.alert-*` | `<Alert>` |
| `.badge`, `.badge-*` | `<Badge>` |
| `.modal`, `.modal-*` | `<Modal>` |
| `.card`, `.card-*` | `<Card>` |
| `.data-table`, `.table-container` | `<DataTable>` |
| `.pagination`, `.pagination-btn` | `<Pagination>` |
| `.tabs`, `.tab`, `.tab-content` | `<Tabs>` |
| `.breadcrumb`, `.breadcrumb-item` | `<Breadcrumb>` |
| `.skeleton`, `.skeleton-*` | `<Skeleton>` |
| `.progress`, `.progress-bar` | `<Progress>` |
| `.empty-state` | `<EmptyState>` |
| `.file-upload` | `<FileUpload>` |
| `.tag`, `.tag-remove` | `<Tag>` |
| `.stat-card` | `<StatCard>` |

詳細なデザイントークン（カラー、スペーシング、タイポグラフィ）は [01-design-tokens.md](./01-design-tokens.md) を参照してください。

---

## 設計原則

### 1. アーキテクチャ準拠

- `components/ui/` にのみ配置（features配下には置かない）
- 機能固有のロジックを含まない純粋なUI層
- ビジネスロジックはカスタムフックで分離

### 2. 型安全性

- **interface禁止**: すべて `type` を使用
- **アロー関数必須**: すべての関数コンポーネントはアロー関数
- **any禁止**: 厳密な型定義を徹底

### 3. スタイリング戦略

- CVAによるバリアント管理
- Tailwind CSS によるユーティリティファースト
- `cn()` による条件付きクラス結合

### 4. アクセシビリティ

- WAI-ARIA 準拠
- キーボード操作対応
- スクリーンリーダー対応
- 適切なARIA属性の付与

### 5. テスト容易性

- `data-testid` 属性の統一的な命名規則
- テスタブルなProps設計
- Storybookによるビジュアルテスト

## コンポーネント一覧

### 1. フォーム関連

#### 1.1 Input

**概要**: テキスト入力フィールド

**Props型定義**:

```typescript
import { InputHTMLAttributes } from 'react'
import { VariantProps } from 'class-variance-authority'

export type InputProps = InputHTMLAttributes<HTMLInputElement> &
  VariantProps<typeof inputVariants> & {
    /**
     * エラー状態
     */
    error?: boolean
    /**
     * 左側アイコン
     */
    leftIcon?: React.ReactNode
    /**
     * 右側アイコン
     */
    rightIcon?: React.ReactNode
  }
```

**CVAバリアント定義**:

```typescript
import { cva } from 'class-variance-authority'

export const inputVariants = cva(
  'flex w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'border-input',
        error: 'border-destructive focus-visible:ring-destructive',
      },
      inputSize: {
        sm: 'h-8 px-2 text-xs',
        default: 'h-10 px-3 text-sm',
        lg: 'h-12 px-4 text-base',
      },
    },
    defaultVariants: {
      variant: 'default',
      inputSize: 'default',
    },
  }
)
```

**実装例**:

```typescript
import { forwardRef } from 'react'
import { cn } from '@/lib/utils'

/**
 * テキスト入力コンポーネント
 * @description アプリケーション全体で使用する汎用テキスト入力
 * @param {InputProps} props - インプットのプロパティ
 * @returns {JSX.Element} インプット要素
 * @example
 * <Input
 *   placeholder="メールアドレス"
 *   error={!!errors.email}
 *   leftIcon={<Mail className="h-4 w-4" />}
 * />
 */
export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant, inputSize, error, leftIcon, rightIcon, ...props }, ref) => {
    const hasIcon = leftIcon || rightIcon

    return (
      <div className="relative">
        {leftIcon && (
          <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            {leftIcon}
          </div>
        )}
        <input
          className={cn(
            inputVariants({ variant: error ? 'error' : variant, inputSize }),
            leftIcon && 'pl-10',
            rightIcon && 'pr-10',
            className
          )}
          ref={ref}
          data-testid="input"
          {...props}
        />
        {rightIcon && (
          <div className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground">
            {rightIcon}
          </div>
        )}
      </div>
    )
  }
)
Input.displayName = 'Input'
```

**アクセシビリティ要件**:

- `aria-invalid` をエラー時に設定
- `aria-describedby` でエラーメッセージと関連付け
- `aria-required` を必須項目に設定

**data-testid 命名規則**: `input`

---

#### 1.2 Textarea

**概要**: 複数行テキスト入力

**Props型定義**:

```typescript
import { TextareaHTMLAttributes } from 'react'
import { VariantProps } from 'class-variance-authority'

export type TextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement> &
  VariantProps<typeof textareaVariants> & {
    /**
     * エラー状態
     */
    error?: boolean
    /**
     * 最大文字数
     */
    maxLength?: number
    /**
     * 文字数カウンター表示
     */
    showCounter?: boolean
  }
```

**CVAバリアント定義**:

```typescript
export const textareaVariants = cva(
  'flex min-h-[80px] w-full rounded-md border bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'border-input',
        error: 'border-destructive focus-visible:ring-destructive',
      },
      resize: {
        none: 'resize-none',
        vertical: 'resize-y',
        horizontal: 'resize-x',
        both: 'resize',
      },
    },
    defaultVariants: {
      variant: 'default',
      resize: 'vertical',
    },
  }
)
```

**実装例**:

```typescript
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, variant, resize, error, maxLength, showCounter, ...props }, ref) => {
    const [count, setCount] = useState(props.value?.toString().length || 0)

    return (
      <div className="relative">
        <textarea
          className={cn(
            textareaVariants({ variant: error ? 'error' : variant, resize }),
            className
          )}
          ref={ref}
          maxLength={maxLength}
          onChange={(e) => {
            setCount(e.target.value.length)
            props.onChange?.(e)
          }}
          data-testid="textarea"
          {...props}
        />
        {showCounter && maxLength && (
          <div className="mt-1 text-xs text-muted-foreground text-right">
            {count} / {maxLength}
          </div>
        )}
      </div>
    )
  }
)
Textarea.displayName = 'Textarea'
```

**アクセシビリティ要件**:

- `aria-invalid` をエラー時に設定
- `aria-describedby` でエラーメッセージと関連付け

**data-testid 命名規則**: `textarea`

---

#### 1.3 Select

**概要**: セレクトボックス（Radix UI Select使用）

**Props型定義**:

```typescript
import * as SelectPrimitive from '@radix-ui/react-select'
import { VariantProps } from 'class-variance-authority'

export type SelectProps = SelectPrimitive.SelectProps & {
  /**
   * 選択肢
   */
  options: Array<{
    value: string
    label: string
    disabled?: boolean
  }>
  /**
   * プレースホルダー
   */
  placeholder?: string
  /**
   * エラー状態
   */
  error?: boolean
}
```

**実装例**:

```typescript
export const Select = ({ options, placeholder, error, ...props }: SelectProps) => {
  return (
    <SelectPrimitive.Root {...props}>
      <SelectPrimitive.Trigger
        className={cn(
          'flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50',
          error && 'border-destructive focus:ring-destructive'
        )}
        data-testid="select-trigger"
      >
        <SelectPrimitive.Value placeholder={placeholder} />
        <SelectPrimitive.Icon>
          <ChevronDown className="h-4 w-4 opacity-50" />
        </SelectPrimitive.Icon>
      </SelectPrimitive.Trigger>
      <SelectPrimitive.Portal>
        <SelectPrimitive.Content
          className="relative z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover text-popover-foreground shadow-md"
          data-testid="select-content"
        >
          <SelectPrimitive.Viewport className="p-1">
            {options.map((option) => (
              <SelectPrimitive.Item
                key={option.value}
                value={option.value}
                disabled={option.disabled}
                className="relative flex w-full cursor-pointer select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50"
                data-testid={`select-option-${option.value}`}
              >
                <span className="absolute left-2 flex h-3.5 w-3.5 items-center justify-center">
                  <SelectPrimitive.ItemIndicator>
                    <Check className="h-4 w-4" />
                  </SelectPrimitive.ItemIndicator>
                </span>
                <SelectPrimitive.ItemText>{option.label}</SelectPrimitive.ItemText>
              </SelectPrimitive.Item>
            ))}
          </SelectPrimitive.Viewport>
        </SelectPrimitive.Content>
      </SelectPrimitive.Portal>
    </SelectPrimitive.Root>
  )
}
```

**アクセシビリティ要件**:

- Radix UIにより自動的にARIA属性が付与される
- キーボード操作（矢印キー、Enter、Escape）に対応

**data-testid 命名規則**:

- トリガー: `select-trigger`
- コンテンツ: `select-content`
- オプション: `select-option-{value}`

---

#### 1.4 Checkbox

**概要**: チェックボックス（Radix UI Checkbox使用）

**Props型定義**:

```typescript
import * as CheckboxPrimitive from '@radix-ui/react-checkbox'

export type CheckboxProps = CheckboxPrimitive.CheckboxProps & {
  /**
   * ラベルテキスト
   */
  label?: string
}
```

**実装例**:

```typescript
export const Checkbox = forwardRef<
  React.ElementRef<typeof CheckboxPrimitive.Root>,
  CheckboxProps
>(({ className, label, ...props }, ref) => (
  <div className="flex items-center space-x-2">
    <CheckboxPrimitive.Root
      ref={ref}
      className={cn(
        'peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground',
        className
      )}
      data-testid="checkbox"
      {...props}
    >
      <CheckboxPrimitive.Indicator className="flex items-center justify-center text-current">
        <Check className="h-4 w-4" />
      </CheckboxPrimitive.Indicator>
    </CheckboxPrimitive.Root>
    {label && (
      <label
        htmlFor={props.id}
        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
      >
        {label}
      </label>
    )}
  </div>
))
Checkbox.displayName = 'Checkbox'
```

**アクセシビリティ要件**:

- `role="checkbox"` が自動付与（Radix UI）
- `aria-checked` 状態が自動管理
- ラベルとの関連付け（`htmlFor` / `id`）

**data-testid 命名規則**: `checkbox`

---

#### 1.5 RadioGroup

**概要**: ラジオボタングループ（Radix UI RadioGroup使用）

**Props型定義**:

```typescript
import * as RadioGroupPrimitive from '@radix-ui/react-radio-group'

export type RadioGroupOption = {
  value: string
  label: string
  disabled?: boolean
}

export type RadioGroupProps = RadioGroupPrimitive.RadioGroupProps & {
  /**
   * 選択肢
   */
  options: RadioGroupOption[]
  /**
   * レイアウト方向
   */
  orientation?: 'horizontal' | 'vertical'
}
```

**実装例**:

```typescript
export const RadioGroup = forwardRef<
  React.ElementRef<typeof RadioGroupPrimitive.Root>,
  RadioGroupProps
>(({ className, options, orientation = 'vertical', ...props }, ref) => {
  return (
    <RadioGroupPrimitive.Root
      className={cn(
        'grid gap-2',
        orientation === 'horizontal' ? 'grid-flow-col auto-cols-max' : 'grid-flow-row',
        className
      )}
      ref={ref}
      data-testid="radio-group"
      {...props}
    >
      {options.map((option) => (
        <div key={option.value} className="flex items-center space-x-2">
          <RadioGroupPrimitive.Item
            value={option.value}
            id={option.value}
            disabled={option.disabled}
            className="aspect-square h-4 w-4 rounded-full border border-primary text-primary ring-offset-background focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            data-testid={`radio-option-${option.value}`}
          >
            <RadioGroupPrimitive.Indicator className="flex items-center justify-center">
              <Circle className="h-2.5 w-2.5 fill-current text-current" />
            </RadioGroupPrimitive.Indicator>
          </RadioGroupPrimitive.Item>
          <label
            htmlFor={option.value}
            className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
          >
            {option.label}
          </label>
        </div>
      ))}
    </RadioGroupPrimitive.Root>
  )
})
RadioGroup.displayName = 'RadioGroup'
```

**アクセシビリティ要件**:

- `role="radiogroup"` が自動付与
- `aria-checked` 状態が自動管理
- キーボード操作（矢印キー）に対応

**data-testid 命名規則**:

- グループ: `radio-group`
- オプション: `radio-option-{value}`

---

#### 1.6 Switch

**概要**: トグルスイッチ（Radix UI Switch使用）

**Props型定義**:

```typescript
import * as SwitchPrimitive from '@radix-ui/react-switch'

export type SwitchProps = SwitchPrimitive.SwitchProps & {
  /**
   * ラベルテキスト
   */
  label?: string
}
```

**実装例**:

```typescript
export const Switch = forwardRef<
  React.ElementRef<typeof SwitchPrimitive.Root>,
  SwitchProps
>(({ className, label, ...props }, ref) => (
  <div className="flex items-center space-x-2">
    <SwitchPrimitive.Root
      className={cn(
        'peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=unchecked]:bg-input',
        className
      )}
      ref={ref}
      data-testid="switch"
      {...props}
    >
      <SwitchPrimitive.Thumb
        className={cn(
          'pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-5 data-[state=unchecked]:translate-x-0'
        )}
      />
    </SwitchPrimitive.Root>
    {label && (
      <label
        htmlFor={props.id}
        className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
      >
        {label}
      </label>
    )}
  </div>
))
Switch.displayName = 'Switch'
```

**アクセシビリティ要件**:

- `role="switch"` が自動付与
- `aria-checked` 状態が自動管理

**data-testid 命名規則**: `switch`

---

#### 1.7 DatePicker

**概要**: 日付選択（react-day-picker使用）

**Props型定義**:

```typescript
import { DayPickerSingleProps } from 'react-day-picker'
import { Matcher } from 'react-day-picker'

export type DatePickerProps = {
  /**
   * 選択された日付
   */
  value?: Date
  /**
   * 日付変更ハンドラー
   */
  onChange?: (date: Date | undefined) => void
  /**
   * 無効な日付
   */
  disabled?: Matcher | Matcher[]
  /**
   * プレースホルダー
   */
  placeholder?: string
  /**
   * エラー状態
   */
  error?: boolean
}
```

**実装例**:

```typescript
import { format } from 'date-fns'
import { ja } from 'date-fns/locale'
import { Calendar as CalendarIcon } from 'lucide-react'
import { DayPicker } from 'react-day-picker'

export const DatePicker = ({
  value,
  onChange,
  disabled,
  placeholder = '日付を選択',
  error,
}: DatePickerProps) => {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="outline"
          className={cn(
            'w-full justify-start text-left font-normal',
            !value && 'text-muted-foreground',
            error && 'border-destructive'
          )}
          data-testid="datepicker-trigger"
        >
          <CalendarIcon className="mr-2 h-4 w-4" />
          {value ? format(value, 'PPP', { locale: ja }) : placeholder}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" data-testid="datepicker-content">
        <DayPicker
          mode="single"
          selected={value}
          onSelect={(date) => {
            onChange?.(date)
            setIsOpen(false)
          }}
          disabled={disabled}
          locale={ja}
          initialFocus
        />
      </PopoverContent>
    </Popover>
  )
}
```

**アクセシビリティ要件**:

- キーボード操作（矢印キー、Enter、Escape）に対応
- `aria-label` で日付ピッカーを説明

**data-testid 命名規則**:

- トリガー: `datepicker-trigger`
- コンテンツ: `datepicker-content`

---

#### 1.8 Form

**概要**: React Hook Form統合フォームコンテナ

**Props型定義**:

```typescript
import { FieldValues, FormProvider, UseFormReturn } from 'react-hook-form'

export type FormProps<TFieldValues extends FieldValues> = {
  /**
   * React Hook Formのメソッド
   */
  form: UseFormReturn<TFieldValues>
  /**
   * 送信ハンドラー
   */
  onSubmit: (data: TFieldValues) => void | Promise<void>
  /**
   * 子要素
   */
  children: React.ReactNode
  /**
   * フォームクラス名
   */
  className?: string
}
```

**実装例**:

```typescript
/**
 * Formコンポーネント
 * @description React Hook Formと統合されたフォームコンテナ
 * @param {FormProps} props - フォームのプロパティ
 * @returns {JSX.Element} フォーム要素
 * @example
 * const form = useForm<LoginInput>({
 *   resolver: zodResolver(loginSchema),
 * })
 *
 * <Form form={form} onSubmit={handleSubmit}>
 *   <FormField name="email" label="メールアドレス" />
 *   <Button type="submit">ログイン</Button>
 * </Form>
 */
export const Form = <TFieldValues extends FieldValues>({
  form,
  onSubmit,
  children,
  className,
}: FormProps<TFieldValues>) => {
  return (
    <FormProvider {...form}>
      <form
        onSubmit={form.handleSubmit(onSubmit)}
        className={className}
        data-testid="form"
      >
        {children}
      </form>
    </FormProvider>
  )
}
```

**アクセシビリティ要件**:

- `noValidate` 属性で HTML5 バリデーションを無効化（カスタムバリデーション使用）

**data-testid 命名規則**: `form`

---

#### 1.9 FormField

**概要**: フォームフィールド（ラベル、エラー表示付き）

**Props型定義**:

```typescript
import { FieldPath, FieldValues } from 'react-hook-form'

export type FormFieldProps<
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
> = {
  /**
   * フィールド名
   */
  name: TName
  /**
   * ラベルテキスト
   */
  label?: string
  /**
   * 説明テキスト
   */
  description?: string
  /**
   * 必須フラグ
   */
  required?: boolean
  /**
   * 子要素（入力コンポーネント）
   */
  children: (field: ControllerRenderProps<TFieldValues, TName>) => React.ReactNode
}
```

**実装例**:

```typescript
import { useFormContext, Controller, ControllerRenderProps } from 'react-hook-form'

export const FormField = <
  TFieldValues extends FieldValues = FieldValues,
  TName extends FieldPath<TFieldValues> = FieldPath<TFieldValues>
>({
  name,
  label,
  description,
  required,
  children,
}: FormFieldProps<TFieldValues, TName>) => {
  const {
    control,
    formState: { errors },
  } = useFormContext<TFieldValues>()

  const error = errors[name]
  const errorMessage = error?.message?.toString()

  return (
    <div className="space-y-2" data-testid={`form-field-${name}`}>
      {label && (
        <label
          htmlFor={name}
          className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
        >
          {label}
          {required && <span className="ml-1 text-destructive">*</span>}
        </label>
      )}
      <Controller
        name={name}
        control={control}
        render={({ field }) => children(field)}
      />
      {description && !error && (
        <p className="text-sm text-muted-foreground">{description}</p>
      )}
      {errorMessage && (
        <p className="text-sm text-destructive" data-testid={`form-field-error-${name}`}>
          {errorMessage}
        </p>
      )}
    </div>
  )
}
```

**使用例**:

```typescript
<FormField
  name="email"
  label="メールアドレス"
  required
  description="ログインに使用するメールアドレスを入力してください"
>
  {(field) => (
    <Input
      {...field}
      type="email"
      placeholder="example@example.com"
      error={!!errors.email}
    />
  )}
</FormField>
```

**アクセシビリティ要件**:

- `aria-describedby` でエラーメッセージと関連付け
- `aria-invalid` をエラー時に設定
- `aria-required` を必須項目に設定

**data-testid 命名規則**:

- フィールド: `form-field-{name}`
- エラー: `form-field-error-{name}`

---

### 2. ボタン・アクション

#### 2.1 Button

**概要**: 汎用ボタン（完全なCVA実装例）

**Props型定義**:

```typescript
import { ButtonHTMLAttributes } from 'react'
import { VariantProps } from 'class-variance-authority'

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants> & {
    /**
     * ローディング状態
     */
    isLoading?: boolean
    /**
     * 左側アイコン
     */
    leftIcon?: React.ReactNode
    /**
     * 右側アイコン
     */
    rightIcon?: React.ReactNode
  }
```

**CVAバリアント定義**:

```typescript
export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive:
          'bg-destructive text-destructive-foreground hover:bg-destructive/90',
        outline:
          'border border-input bg-background hover:bg-accent hover:text-accent-foreground',
        secondary:
          'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-10 px-4 py-2',
        sm: 'h-9 rounded-md px-3',
        lg: 'h-11 rounded-md px-8',
        icon: 'h-10 w-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  }
)
```

**実装例**:

```typescript
/**
 * ボタンコンポーネント
 * @description アプリケーション全体で使用する汎用ボタン
 * @param {ButtonProps} props - ボタンのプロパティ
 * @returns {JSX.Element} ボタン要素
 * @example
 * // 基本的な使用
 * <Button onClick={handleClick}>クリック</Button>
 *
 * // バリアント指定
 * <Button variant="destructive" onClick={handleDelete}>
 *   削除
 * </Button>
 *
 * // ローディング状態
 * <Button isLoading disabled>
 *   送信中...
 * </Button>
 *
 * // アイコン付き
 * <Button leftIcon={<Plus className="h-4 w-4" />}>
 *   新規作成
 * </Button>
 */
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      isLoading,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <button
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || isLoading}
        data-testid="button"
        {...props}
      >
        {isLoading && <Spinner className="h-4 w-4" />}
        {!isLoading && leftIcon}
        {children}
        {!isLoading && rightIcon}
      </button>
    )
  }
)
Button.displayName = 'Button'
```

**アクセシビリティ要件**:

- `aria-busy` をローディング時に設定
- `aria-disabled` を無効時に設定
- 適切な `type` 属性（`button` / `submit` / `reset`）

**data-testid 命名規則**: `button`

---

#### 2.2 IconButton

**概要**: アイコンボタン

**Props型定義**:

```typescript
export type IconButtonProps = ButtonProps & {
  /**
   * アイコン
   */
  icon: React.ReactNode
  /**
   * アクセシビリティ用ラベル
   */
  'aria-label': string
}
```

**実装例**:

```typescript
export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ icon, className, size = 'icon', ...props }, ref) => {
    return (
      <Button
        ref={ref}
        size={size}
        className={className}
        data-testid="icon-button"
        {...props}
      >
        {icon}
      </Button>
    )
  }
)
IconButton.displayName = 'IconButton'
```

**アクセシビリティ要件**:

- `aria-label` は必須（アイコンのみなので説明が必要）

**data-testid 命名規則**: `icon-button`

---

#### 2.3 ButtonGroup

**概要**: ボタングループ

**Props型定義**:

```typescript
export type ButtonGroupProps = {
  /**
   * 子要素（Buttonコンポーネント）
   */
  children: React.ReactNode
  /**
   * 方向
   */
  orientation?: 'horizontal' | 'vertical'
  /**
   * クラス名
   */
  className?: string
}
```

**実装例**:

```typescript
export const ButtonGroup = ({
  children,
  orientation = 'horizontal',
  className,
}: ButtonGroupProps) => {
  return (
    <div
      className={cn(
        'inline-flex',
        orientation === 'horizontal'
          ? 'flex-row [&>button:not(:first-child)]:rounded-l-none [&>button:not(:last-child)]:rounded-r-none [&>button:not(:last-child)]:-mr-px'
          : 'flex-col [&>button:not(:first-child)]:rounded-t-none [&>button:not(:last-child)]:rounded-b-none [&>button:not(:last-child)]:-mb-px',
        className
      )}
      role="group"
      data-testid="button-group"
    >
      {children}
    </div>
  )
}
```

**アクセシビリティ要件**:

- `role="group"` で関連するボタンをグループ化

**data-testid 命名規則**: `button-group`

---

### 3. フィードバック

#### 3.1 Alert

**概要**: アラートメッセージ

**Props型定義**:

```typescript
export type AlertProps = {
  /**
   * バリアント
   */
  variant?: 'default' | 'destructive' | 'warning' | 'success'
  /**
   * タイトル
   */
  title?: string
  /**
   * 説明
   */
  description?: string | React.ReactNode
  /**
   * アイコン
   */
  icon?: React.ReactNode
  /**
   * クラス名
   */
  className?: string
}
```

**CVAバリアント定義**:

```typescript
export const alertVariants = cva(
  'relative w-full rounded-lg border p-4 [&>svg~*]:pl-7 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground',
  {
    variants: {
      variant: {
        default: 'bg-background text-foreground',
        destructive:
          'border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive',
        warning:
          'border-yellow-500/50 text-yellow-900 dark:text-yellow-400 [&>svg]:text-yellow-600',
        success:
          'border-green-500/50 text-green-900 dark:text-green-400 [&>svg]:text-green-600',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)
```

**実装例**:

```typescript
export const Alert = ({
  variant = 'default',
  title,
  description,
  icon,
  className,
}: AlertProps) => {
  const defaultIcons = {
    default: <Info className="h-4 w-4" />,
    destructive: <AlertCircle className="h-4 w-4" />,
    warning: <AlertTriangle className="h-4 w-4" />,
    success: <CheckCircle className="h-4 w-4" />,
  }

  return (
    <div
      className={cn(alertVariants({ variant }), className)}
      role="alert"
      data-testid="alert"
    >
      {icon || defaultIcons[variant]}
      <div>
        {title && (
          <h5 className="mb-1 font-medium leading-none tracking-tight">{title}</h5>
        )}
        {description && (
          <div className="text-sm [&_p]:leading-relaxed">{description}</div>
        )}
      </div>
    </div>
  )
}
```

**アクセシビリティ要件**:

- `role="alert"` で重要なメッセージを示す

**data-testid 命名規則**: `alert`

---

#### 3.2 Badge

**概要**: バッジ

**Props型定義**:

```typescript
export type BadgeProps = HTMLAttributes<HTMLDivElement> &
  VariantProps<typeof badgeVariants>
```

**CVAバリアント定義**:

```typescript
export const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
  {
    variants: {
      variant: {
        default:
          'border-transparent bg-primary text-primary-foreground hover:bg-primary/80',
        secondary:
          'border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80',
        destructive:
          'border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80',
        outline: 'text-foreground',
        success:
          'border-transparent bg-green-500 text-white hover:bg-green-600',
        warning:
          'border-transparent bg-yellow-500 text-white hover:bg-yellow-600',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)
```

**実装例**:

```typescript
export const Badge = ({ className, variant, ...props }: BadgeProps) => {
  return (
    <div
      className={cn(badgeVariants({ variant }), className)}
      data-testid="badge"
      {...props}
    />
  )
}
```

**アクセシビリティ要件**:

- 必要に応じて `role="status"` を設定

**data-testid 命名規則**: `badge`

---

#### 3.3 Spinner

**概要**: ローディングスピナー

**Props型定義**:

```typescript
export type SpinnerProps = {
  /**
   * サイズ
   */
  size?: 'sm' | 'default' | 'lg'
  /**
   * クラス名
   */
  className?: string
}
```

**実装例**:

```typescript
export const Spinner = ({ size = 'default', className }: SpinnerProps) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    default: 'h-8 w-8',
    lg: 'h-12 w-12',
  }

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-2 border-current border-t-transparent',
        sizeClasses[size],
        className
      )}
      role="status"
      aria-label="読み込み中"
      data-testid="spinner"
    >
      <span className="sr-only">読み込み中...</span>
    </div>
  )
}
```

**アクセシビリティ要件**:

- `role="status"` でステータス変更を示す
- `aria-label` で説明を提供
- `sr-only` クラスでスクリーンリーダー用テキスト

**data-testid 命名規則**: `spinner`

---

#### 3.4 Skeleton

**概要**: スケルトンローディング

**Props型定義**:

```typescript
export type SkeletonProps = HTMLAttributes<HTMLDivElement> & {
  /**
   * 幅
   */
  width?: string | number
  /**
   * 高さ
   */
  height?: string | number
  /**
   * 円形
   */
  circle?: boolean
}
```

**実装例**:

```typescript
export const Skeleton = ({
  className,
  width,
  height,
  circle,
  style,
  ...props
}: SkeletonProps) => {
  return (
    <div
      className={cn(
        'animate-pulse rounded-md bg-muted',
        circle && 'rounded-full',
        className
      )}
      style={{
        width: typeof width === 'number' ? `${width}px` : width,
        height: typeof height === 'number' ? `${height}px` : height,
        ...style,
      }}
      data-testid="skeleton"
      {...props}
    />
  )
}
```

**使用例**:

```typescript
// テキストスケルトン
<Skeleton height={20} width="80%" />

// アバタースケルトン
<Skeleton circle width={40} height={40} />

// カードスケルトン
<div className="space-y-3">
  <Skeleton height={200} />
  <Skeleton height={20} width="60%" />
  <Skeleton height={20} width="80%" />
</div>
```

**アクセシビリティ要件**:

- `aria-busy="true"` を親要素に設定

**data-testid 命名規則**: `skeleton`

---

#### 3.5 Toast

**概要**: トースト通知（Zustandストアとの統合）

**Zustand Store定義**:

```typescript
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

export type ToastType = 'default' | 'success' | 'error' | 'warning' | 'info'

export type Toast = {
  id: string
  type: ToastType
  title: string
  description?: string
  duration?: number
}

type ToastState = {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
  clearAll: () => void
}

export const useToastStore = create<ToastState>()(
  devtools(
    (set) => ({
      toasts: [],
      addToast: (toast) =>
        set((state) => ({
          toasts: [
            ...state.toasts,
            {
              ...toast,
              id: Math.random().toString(36).substring(2, 9),
            },
          ],
        })),
      removeToast: (id) =>
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        })),
      clearAll: () => set({ toasts: [] }),
    }),
    { name: 'ToastStore' }
  )
)
```

**カスタムフック**:

```typescript
export const useToast = () => {
  const { addToast, removeToast } = useToastStore()

  const toast = useCallback(
    (options: Omit<Toast, 'id'>) => {
      addToast({
        duration: 5000,
        ...options,
      })
    },
    [addToast]
  )

  return {
    toast,
    success: (title: string, description?: string) =>
      toast({ type: 'success', title, description }),
    error: (title: string, description?: string) =>
      toast({ type: 'error', title, description }),
    warning: (title: string, description?: string) =>
      toast({ type: 'warning', title, description }),
    info: (title: string, description?: string) =>
      toast({ type: 'info', title, description }),
  }
}
```

**Toast コンポーネント**:

```typescript
export const ToastItem = ({ toast }: { toast: Toast }) => {
  const { removeToast } = useToastStore()

  useEffect(() => {
    if (toast.duration) {
      const timer = setTimeout(() => {
        removeToast(toast.id)
      }, toast.duration)

      return () => clearTimeout(timer)
    }
  }, [toast.id, toast.duration, removeToast])

  const icons = {
    default: <Info className="h-5 w-5" />,
    success: <CheckCircle className="h-5 w-5" />,
    error: <AlertCircle className="h-5 w-5" />,
    warning: <AlertTriangle className="h-5 w-5" />,
    info: <Info className="h-5 w-5" />,
  }

  return (
    <div
      className={cn(
        'pointer-events-auto flex w-full max-w-md gap-3 rounded-lg border p-4 shadow-lg',
        {
          'bg-background': toast.type === 'default',
          'bg-green-50 border-green-200': toast.type === 'success',
          'bg-red-50 border-red-200': toast.type === 'error',
          'bg-yellow-50 border-yellow-200': toast.type === 'warning',
          'bg-blue-50 border-blue-200': toast.type === 'info',
        }
      )}
      role="alert"
      data-testid={`toast-${toast.type}`}
    >
      <div className="flex-shrink-0">{icons[toast.type]}</div>
      <div className="flex-1">
        <p className="font-semibold">{toast.title}</p>
        {toast.description && (
          <p className="mt-1 text-sm text-muted-foreground">{toast.description}</p>
        )}
      </div>
      <button
        onClick={() => removeToast(toast.id)}
        className="flex-shrink-0 rounded-md p-1 hover:bg-black/10"
        data-testid="toast-close"
      >
        <X className="h-4 w-4" />
      </button>
    </div>
  )
}

export const ToastContainer = () => {
  const toasts = useToastStore((state) => state.toasts)

  return (
    <div
      className="pointer-events-none fixed bottom-0 right-0 z-50 flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:bottom-0 sm:right-0 sm:top-auto sm:flex-col md:max-w-[420px]"
      data-testid="toast-container"
    >
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} />
      ))}
    </div>
  )
}
```

**使用例**:

```typescript
const { toast, success, error } = useToast()

// 成功通知
success('保存しました', 'データが正常に保存されました')

// エラー通知
error('エラーが発生しました', 'もう一度お試しください')

// カスタム通知
toast({
  type: 'warning',
  title: '確認が必要です',
  description: 'この操作は元に戻せません',
  duration: 10000,
})
```

**アクセシビリティ要件**:

- `role="alert"` で重要な通知を示す
- 自動的に消える時間を設定（ユーザーが読める時間）
- 閉じるボタンを提供

**data-testid 命名規則**:

- コンテナ: `toast-container`
- アイテム: `toast-{type}`
- 閉じるボタン: `toast-close`

---

#### 3.6 Progress

**概要**: プログレスバー

**Props型定義**:

```typescript
export type ProgressProps = {
  /**
   * 進捗率（0-100）
   */
  value: number
  /**
   * 最大値（デフォルト: 100）
   */
  max?: number
  /**
   * サイズ
   */
  size?: 'sm' | 'default' | 'lg'
  /**
   * ラベル表示
   */
  showLabel?: boolean
  /**
   * クラス名
   */
  className?: string
}
```

**実装例**:

```typescript
export const Progress = ({
  value,
  max = 100,
  size = 'default',
  showLabel,
  className,
}: ProgressProps) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100)

  const sizeClasses = {
    sm: 'h-1',
    default: 'h-2',
    lg: 'h-3',
  }

  return (
    <div className={cn('w-full', className)}>
      <div
        className={cn(
          'relative w-full overflow-hidden rounded-full bg-secondary',
          sizeClasses[size]
        )}
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={0}
        aria-valuemax={max}
        data-testid="progress"
      >
        <div
          className="h-full bg-primary transition-all duration-300 ease-in-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showLabel && (
        <div className="mt-1 text-sm text-muted-foreground text-right">
          {Math.round(percentage)}%
        </div>
      )}
    </div>
  )
}
```

**アクセシビリティ要件**:

- `role="progressbar"` で進捗状況を示す
- `aria-valuenow`, `aria-valuemin`, `aria-valuemax` で値を提供

**data-testid 命名規則**: `progress`

---

### 4. オーバーレイ

#### 4.1 Dialog

**概要**: ダイアログ/モーダル（Radix UI Dialog使用、完全なアクセシビリティ対応）

**Props型定義**:

```typescript
import * as DialogPrimitive from '@radix-ui/react-dialog'

export type DialogProps = {
  /**
   * 開閉状態
   */
  open?: boolean
  /**
   * 開閉状態変更ハンドラー
   */
  onOpenChange?: (open: boolean) => void
  /**
   * トリガー要素
   */
  trigger?: React.ReactNode
  /**
   * タイトル
   */
  title: string
  /**
   * 説明
   */
  description?: string
  /**
   * 子要素（コンテンツ）
   */
  children: React.ReactNode
  /**
   * フッター
   */
  footer?: React.ReactNode
  /**
   * サイズ
   */
  size?: 'sm' | 'default' | 'lg' | 'xl' | 'full'
}
```

**実装例**:

```typescript
/**
 * Dialogコンポーネント
 * @description アクセシビリティ対応のモーダルダイアログ
 * - フォーカストラップ: ダイアログ内でフォーカスを維持
 * - ESCキー: ダイアログを閉じる
 * - 背景クリック: ダイアログを閉じる（オプション）
 * - スクロールロック: 背景のスクロールを防止
 * @param {DialogProps} props - ダイアログのプロパティ
 * @returns {JSX.Element} ダイアログ要素
 * @example
 * <Dialog
 *   trigger={<Button>開く</Button>}
 *   title="確認"
 *   description="この操作を実行しますか？"
 *   footer={
 *     <>
 *       <Button variant="outline" onClick={onCancel}>キャンセル</Button>
 *       <Button onClick={onConfirm}>実行</Button>
 *     </>
 *   }
 * >
 *   <p>詳細な説明がここに入ります。</p>
 * </Dialog>
 */
export const Dialog = ({
  open,
  onOpenChange,
  trigger,
  title,
  description,
  children,
  footer,
  size = 'default',
}: DialogProps) => {
  const sizeClasses = {
    sm: 'max-w-sm',
    default: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
    full: 'max-w-full mx-4',
  }

  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      {trigger && (
        <DialogPrimitive.Trigger asChild data-testid="dialog-trigger">
          {trigger}
        </DialogPrimitive.Trigger>
      )}
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay
          className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
          data-testid="dialog-overlay"
        />
        <DialogPrimitive.Content
          className={cn(
            'fixed left-[50%] top-[50%] z-50 grid w-full translate-x-[-50%] translate-y-[-50%] gap-4 border bg-background p-6 shadow-lg duration-200 data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[state=closed]:slide-out-to-left-1/2 data-[state=closed]:slide-out-to-top-[48%] data-[state=open]:slide-in-from-left-1/2 data-[state=open]:slide-in-from-top-[48%] sm:rounded-lg',
            sizeClasses[size]
          )}
          data-testid="dialog-content"
        >
          <div className="flex flex-col space-y-1.5 text-center sm:text-left">
            <DialogPrimitive.Title
              className="text-lg font-semibold leading-none tracking-tight"
              data-testid="dialog-title"
            >
              {title}
            </DialogPrimitive.Title>
            {description && (
              <DialogPrimitive.Description
                className="text-sm text-muted-foreground"
                data-testid="dialog-description"
              >
                {description}
              </DialogPrimitive.Description>
            )}
          </div>
          <div data-testid="dialog-body">{children}</div>
          {footer && (
            <div className="flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2" data-testid="dialog-footer">
              {footer}
            </div>
          )}
          <DialogPrimitive.Close
            className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground"
            data-testid="dialog-close"
          >
            <X className="h-4 w-4" />
            <span className="sr-only">閉じる</span>
          </DialogPrimitive.Close>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
```

**アクセシビリティ要件**:

- **フォーカストラップ**: Radix UIにより自動実装
- **ESCキー**: ダイアログを閉じる（Radix UIにより自動実装）
- **スクロールロック**: 背景のスクロールを防止（Radix UIにより自動実装）
- `role="dialog"` が自動付与
- `aria-labelledby` でタイトルと関連付け
- `aria-describedby` で説明と関連付け

**data-testid 命名規則**:

- トリガー: `dialog-trigger`
- オーバーレイ: `dialog-overlay`
- コンテンツ: `dialog-content`
- タイトル: `dialog-title`
- 説明: `dialog-description`
- ボディ: `dialog-body`
- フッター: `dialog-footer`
- 閉じるボタン: `dialog-close`

---

#### 4.2 ConfirmDialog

**概要**: 確認ダイアログ（Dialog拡張）

**Props型定義**:

```typescript
export type ConfirmDialogProps = {
  /**
   * 開閉状態
   */
  open: boolean
  /**
   * 開閉状態変更ハンドラー
   */
  onOpenChange: (open: boolean) => void
  /**
   * タイトル
   */
  title: string
  /**
   * 説明
   */
  description: string
  /**
   * 確認ボタンテキスト
   */
  confirmText?: string
  /**
   * キャンセルボタンテキスト
   */
  cancelText?: string
  /**
   * 確認ボタンバリアント
   */
  confirmVariant?: 'default' | 'destructive'
  /**
   * 確認ハンドラー
   */
  onConfirm: () => void | Promise<void>
  /**
   * キャンセルハンドラー
   */
  onCancel?: () => void
  /**
   * ローディング状態
   */
  isLoading?: boolean
}
```

**実装例**:

```typescript
export const ConfirmDialog = ({
  open,
  onOpenChange,
  title,
  description,
  confirmText = '実行',
  cancelText = 'キャンセル',
  confirmVariant = 'default',
  onConfirm,
  onCancel,
  isLoading,
}: ConfirmDialogProps) => {
  const handleConfirm = async () => {
    await onConfirm()
    onOpenChange(false)
  }

  const handleCancel = () => {
    onCancel?.()
    onOpenChange(false)
  }

  return (
    <Dialog
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      description={description}
      footer={
        <>
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={isLoading}
            data-testid="confirm-dialog-cancel"
          >
            {cancelText}
          </Button>
          <Button
            variant={confirmVariant}
            onClick={handleConfirm}
            isLoading={isLoading}
            disabled={isLoading}
            data-testid="confirm-dialog-confirm"
          >
            {confirmText}
          </Button>
        </>
      }
    />
  )
}
```

**使用例**:

```typescript
const [isOpen, setIsOpen] = useState(false)

<ConfirmDialog
  open={isOpen}
  onOpenChange={setIsOpen}
  title="削除確認"
  description="このアイテムを削除してもよろしいですか？この操作は元に戻せません。"
  confirmText="削除"
  confirmVariant="destructive"
  onConfirm={async () => {
    await deleteItem()
  }}
/>
```

**data-testid 命名規則**:

- キャンセルボタン: `confirm-dialog-cancel`
- 確認ボタン: `confirm-dialog-confirm`

---

#### 4.3 Sheet

**概要**: サイドシート（Radix UI Dialog使用）

**Props型定義**:

```typescript
export type SheetProps = {
  /**
   * 開閉状態
   */
  open?: boolean
  /**
   * 開閉状態変更ハンドラー
   */
  onOpenChange?: (open: boolean) => void
  /**
   * トリガー要素
   */
  trigger?: React.ReactNode
  /**
   * タイトル
   */
  title?: string
  /**
   * 説明
   */
  description?: string
  /**
   * 子要素（コンテンツ）
   */
  children: React.ReactNode
  /**
   * 表示位置
   */
  side?: 'top' | 'right' | 'bottom' | 'left'
}
```

**実装例**:

```typescript
export const Sheet = ({
  open,
  onOpenChange,
  trigger,
  title,
  description,
  children,
  side = 'right',
}: SheetProps) => {
  const sideClasses = {
    top: 'inset-x-0 top-0 border-b data-[state=closed]:slide-out-to-top data-[state=open]:slide-in-from-top',
    bottom: 'inset-x-0 bottom-0 border-t data-[state=closed]:slide-out-to-bottom data-[state=open]:slide-in-from-bottom',
    left: 'inset-y-0 left-0 h-full w-3/4 border-r data-[state=closed]:slide-out-to-left data-[state=open]:slide-in-from-left sm:max-w-sm',
    right: 'inset-y-0 right-0 h-full w-3/4 border-l data-[state=closed]:slide-out-to-right data-[state=open]:slide-in-from-right sm:max-w-sm',
  }

  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      {trigger && (
        <DialogPrimitive.Trigger asChild data-testid="sheet-trigger">
          {trigger}
        </DialogPrimitive.Trigger>
      )}
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay
          className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0"
          data-testid="sheet-overlay"
        />
        <DialogPrimitive.Content
          className={cn(
            'fixed z-50 gap-4 bg-background p-6 shadow-lg transition ease-in-out data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:duration-300 data-[state=open]:duration-500',
            sideClasses[side]
          )}
          data-testid="sheet-content"
        >
          {title && (
            <div className="flex flex-col space-y-2">
              <DialogPrimitive.Title className="text-lg font-semibold" data-testid="sheet-title">
                {title}
              </DialogPrimitive.Title>
              {description && (
                <DialogPrimitive.Description className="text-sm text-muted-foreground" data-testid="sheet-description">
                  {description}
                </DialogPrimitive.Description>
              )}
            </div>
          )}
          <div data-testid="sheet-body">{children}</div>
          <DialogPrimitive.Close
            className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
            data-testid="sheet-close"
          >
            <X className="h-4 w-4" />
            <span className="sr-only">閉じる</span>
          </DialogPrimitive.Close>
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}
```

**アクセシビリティ要件**:

- Dialogと同様のアクセシビリティ対応

**data-testid 命名規則**:

- トリガー: `sheet-trigger`
- オーバーレイ: `sheet-overlay`
- コンテンツ: `sheet-content`
- タイトル: `sheet-title`
- 説明: `sheet-description`
- ボディ: `sheet-body`
- 閉じるボタン: `sheet-close`

---

#### 4.4 Popover

**概要**: ポップオーバー（Radix UI Popover使用）

**実装例**:

```typescript
import * as PopoverPrimitive from '@radix-ui/react-popover'

export const Popover = PopoverPrimitive.Root
export const PopoverTrigger = PopoverPrimitive.Trigger

export const PopoverContent = forwardRef<
  React.ElementRef<typeof PopoverPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof PopoverPrimitive.Content>
>(({ className, align = 'center', sideOffset = 4, ...props }, ref) => (
  <PopoverPrimitive.Portal>
    <PopoverPrimitive.Content
      ref={ref}
      align={align}
      sideOffset={sideOffset}
      className={cn(
        'z-50 w-72 rounded-md border bg-popover p-4 text-popover-foreground shadow-md outline-none data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
        className
      )}
      data-testid="popover-content"
      {...props}
    />
  </PopoverPrimitive.Portal>
))
PopoverContent.displayName = PopoverPrimitive.Content.displayName
```

**使用例**:

```typescript
<Popover>
  <PopoverTrigger asChild>
    <Button variant="outline">設定</Button>
  </PopoverTrigger>
  <PopoverContent>
    <div className="grid gap-4">
      <h4 className="font-medium">設定</h4>
      <div className="grid gap-2">
        <Switch label="通知を有効にする" />
        <Switch label="自動保存" />
      </div>
    </div>
  </PopoverContent>
</Popover>
```

**アクセシビリティ要件**:

- `role="dialog"` が自動付与
- ESCキーで閉じる

**data-testid 命名規則**: `popover-content`

---

#### 4.5 Tooltip

**概要**: ツールチップ（Radix UI Tooltip使用）

**実装例**:

```typescript
import * as TooltipPrimitive from '@radix-ui/react-tooltip'

export const TooltipProvider = TooltipPrimitive.Provider
export const Tooltip = TooltipPrimitive.Root
export const TooltipTrigger = TooltipPrimitive.Trigger

export const TooltipContent = forwardRef<
  React.ElementRef<typeof TooltipPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <TooltipPrimitive.Content
    ref={ref}
    sideOffset={sideOffset}
    className={cn(
      'z-50 overflow-hidden rounded-md border bg-popover px-3 py-1.5 text-sm text-popover-foreground shadow-md animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
      className
    )}
    data-testid="tooltip-content"
    {...props}
  />
))
TooltipContent.displayName = TooltipPrimitive.Content.displayName
```

**使用例**:

```typescript
<TooltipProvider>
  <Tooltip>
    <TooltipTrigger asChild>
      <Button variant="ghost" size="icon">
        <Info className="h-4 w-4" />
      </Button>
    </TooltipTrigger>
    <TooltipContent>
      <p>詳細情報がここに表示されます</p>
    </TooltipContent>
  </Tooltip>
</TooltipProvider>
```

**アクセシビリティ要件**:

- `role="tooltip"` が自動付与
- `aria-describedby` で関連付け

**data-testid 命名規則**: `tooltip-content`

---

#### 4.6 DropdownMenu

**概要**: ドロップダウンメニュー（Radix UI DropdownMenu使用）

**実装例**:

```typescript
import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu'

export const DropdownMenu = DropdownMenuPrimitive.Root
export const DropdownMenuTrigger = DropdownMenuPrimitive.Trigger
export const DropdownMenuGroup = DropdownMenuPrimitive.Group
export const DropdownMenuSub = DropdownMenuPrimitive.Sub
export const DropdownMenuRadioGroup = DropdownMenuPrimitive.RadioGroup

export const DropdownMenuContent = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content>
>(({ className, sideOffset = 4, ...props }, ref) => (
  <DropdownMenuPrimitive.Portal>
    <DropdownMenuPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className={cn(
        'z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2',
        className
      )}
      data-testid="dropdown-menu-content"
      {...props}
    />
  </DropdownMenuPrimitive.Portal>
))
DropdownMenuContent.displayName = DropdownMenuPrimitive.Content.displayName

export const DropdownMenuItem = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Item>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Item>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Item
    ref={ref}
    className={cn(
      'relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none transition-colors focus:bg-accent focus:text-accent-foreground data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
      className
    )}
    data-testid="dropdown-menu-item"
    {...props}
  />
))
DropdownMenuItem.displayName = DropdownMenuPrimitive.Item.displayName

export const DropdownMenuSeparator = forwardRef<
  React.ElementRef<typeof DropdownMenuPrimitive.Separator>,
  React.ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Separator>
>(({ className, ...props }, ref) => (
  <DropdownMenuPrimitive.Separator
    ref={ref}
    className={cn('-mx-1 my-1 h-px bg-muted', className)}
    {...props}
  />
))
DropdownMenuSeparator.displayName = DropdownMenuPrimitive.Separator.displayName
```

**使用例**:

```typescript
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="ghost" size="icon">
      <MoreVertical className="h-4 w-4" />
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end">
    <DropdownMenuItem onSelect={handleEdit}>
      <Edit className="mr-2 h-4 w-4" />
      編集
    </DropdownMenuItem>
    <DropdownMenuItem onSelect={handleDuplicate}>
      <Copy className="mr-2 h-4 w-4" />
      複製
    </DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem onSelect={handleDelete} className="text-destructive">
      <Trash className="mr-2 h-4 w-4" />
      削除
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

**アクセシビリティ要件**:

- `role="menu"` が自動付与
- キーボード操作（矢印キー、Enter、Escape）に対応

**data-testid 命名規則**:

- コンテンツ: `dropdown-menu-content`
- アイテム: `dropdown-menu-item`

---

### 5. データ表示

#### 5.1 Table

**概要**: テーブル（ソート、ページネーション、空状態対応）

**Props型定義**:

```typescript
export type Column<T> = {
  /**
   * カラムキー
   */
  key: keyof T
  /**
   * ヘッダーラベル
   */
  label: string
  /**
   * ソート可能
   */
  sortable?: boolean
  /**
   * カスタムレンダー関数
   */
  render?: (value: T[keyof T], row: T) => React.ReactNode
  /**
   * 幅
   */
  width?: string
}

export type TableProps<T> = {
  /**
   * データ
   */
  data: T[]
  /**
   * カラム定義
   */
  columns: Column<T>[]
  /**
   * ローディング状態
   */
  isLoading?: boolean
  /**
   * 空状態メッセージ
   */
  emptyMessage?: string
  /**
   * ソート状態
   */
  sortKey?: keyof T
  /**
   * ソート方向
   */
  sortDirection?: 'asc' | 'desc'
  /**
   * ソート変更ハンドラー
   */
  onSortChange?: (key: keyof T, direction: 'asc' | 'desc') => void
  /**
   * 行クリックハンドラー
   */
  onRowClick?: (row: T) => void
  /**
   * ページネーション
   */
  pagination?: {
    currentPage: number
    totalPages: number
    pageSize: number
    totalItems: number
    onPageChange: (page: number) => void
  }
}
```

**実装例**:

```typescript
/**
 * Tableコンポーネント
 * @description ソート、ページネーション、空状態に対応したテーブル
 * @param {TableProps} props - テーブルのプロパティ
 * @returns {JSX.Element} テーブル要素
 * @example
 * <Table
 *   data={users}
 *   columns={[
 *     { key: 'name', label: '名前', sortable: true },
 *     { key: 'email', label: 'メール', sortable: true },
 *     {
 *       key: 'role',
 *       label: '役割',
 *       render: (value) => <Badge>{value}</Badge>,
 *     },
 *   ]}
 *   sortKey="name"
 *   sortDirection="asc"
 *   onSortChange={handleSortChange}
 *   pagination={{
 *     currentPage: 1,
 *     totalPages: 10,
 *     pageSize: 20,
 *     totalItems: 200,
 *     onPageChange: handlePageChange,
 *   }}
 * />
 */
export const Table = <T extends Record<string, any>>({
  data,
  columns,
  isLoading,
  emptyMessage = 'データがありません',
  sortKey,
  sortDirection,
  onSortChange,
  onRowClick,
  pagination,
}: TableProps<T>) => {
  const handleSort = (key: keyof T) => {
    if (!onSortChange) return

    const newDirection =
      sortKey === key && sortDirection === 'asc' ? 'desc' : 'asc'
    onSortChange(key, newDirection)
  }

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <Skeleton key={i} height={40} />
        ))}
      </div>
    )
  }

  if (!data.length) {
    return <EmptyState message={emptyMessage} />
  }

  return (
    <div className="space-y-4" data-testid="table">
      <div className="relative w-full overflow-auto">
        <table className="w-full caption-bottom text-sm">
          <thead className="[&_tr]:border-b" data-testid="table-header">
            <tr className="border-b transition-colors hover:bg-muted/50">
              {columns.map((column) => (
                <th
                  key={String(column.key)}
                  className={cn(
                    'h-12 px-4 text-left align-middle font-medium text-muted-foreground',
                    column.sortable && 'cursor-pointer select-none hover:text-foreground'
                  )}
                  style={{ width: column.width }}
                  onClick={() => column.sortable && handleSort(column.key)}
                  data-testid={`table-header-${String(column.key)}`}
                >
                  <div className="flex items-center gap-2">
                    {column.label}
                    {column.sortable && sortKey === column.key && (
                      <span data-testid={`sort-indicator-${String(column.key)}`}>
                        {sortDirection === 'asc' ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="[&_tr:last-child]:border-0" data-testid="table-body">
            {data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={cn(
                  'border-b transition-colors',
                  onRowClick && 'cursor-pointer hover:bg-muted/50'
                )}
                onClick={() => onRowClick?.(row)}
                data-testid={`table-row-${rowIndex}`}
              >
                {columns.map((column) => (
                  <td
                    key={String(column.key)}
                    className="p-4 align-middle"
                    data-testid={`table-cell-${rowIndex}-${String(column.key)}`}
                  >
                    {column.render
                      ? column.render(row[column.key], row)
                      : row[column.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pagination && (
        <Pagination
          currentPage={pagination.currentPage}
          totalPages={pagination.totalPages}
          onPageChange={pagination.onPageChange}
        />
      )}
    </div>
  )
}
```

**アクセシビリティ要件**:

- `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<th>`, `<td>` の適切な使用
- ソート可能なヘッダーに `aria-sort` 属性

**data-testid 命名規則**:

- テーブル: `table`
- ヘッダー: `table-header`
- ヘッダーセル: `table-header-{key}`
- ボディ: `table-body`
- 行: `table-row-{index}`
- セル: `table-cell-{rowIndex}-{key}`
- ソートインジケーター: `sort-indicator-{key}`

---

#### 5.2 Card

**概要**: カード

**Props型定義**:

```typescript
export type CardProps = HTMLAttributes<HTMLDivElement> & {
  /**
   * ヘッダー
   */
  header?: React.ReactNode
  /**
   * フッター
   */
  footer?: React.ReactNode
  /**
   * パディングなし
   */
  noPadding?: boolean
}
```

**実装例**:

```typescript
export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, header, footer, noPadding, children, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'rounded-lg border bg-card text-card-foreground shadow-sm',
        className
      )}
      data-testid="card"
      {...props}
    >
      {header && (
        <div className="flex flex-col space-y-1.5 p-6" data-testid="card-header">
          {header}
        </div>
      )}
      <div className={cn(!noPadding && 'p-6', 'pt-0')} data-testid="card-content">
        {children}
      </div>
      {footer && (
        <div className="flex items-center p-6 pt-0" data-testid="card-footer">
          {footer}
        </div>
      )}
    </div>
  )
)
Card.displayName = 'Card'

export const CardHeader = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('flex flex-col space-y-1.5 p-6', className)} {...props} />
)

export const CardTitle = ({ className, ...props }: HTMLAttributes<HTMLHeadingElement>) => (
  <h3 className={cn('text-2xl font-semibold leading-none tracking-tight', className)} {...props} />
)

export const CardDescription = ({ className, ...props }: HTMLAttributes<HTMLParagraphElement>) => (
  <p className={cn('text-sm text-muted-foreground', className)} {...props} />
)

export const CardContent = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('p-6 pt-0', className)} {...props} />
)

export const CardFooter = ({ className, ...props }: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn('flex items-center p-6 pt-0', className)} {...props} />
)
```

**使用例**:

```typescript
<Card>
  <CardHeader>
    <CardTitle>カードタイトル</CardTitle>
    <CardDescription>カードの説明がここに入ります</CardDescription>
  </CardHeader>
  <CardContent>
    <p>カードのコンテンツ</p>
  </CardContent>
  <CardFooter>
    <Button>アクション</Button>
  </CardFooter>
</Card>
```

**アクセシビリティ要件**:

- 特になし（セマンティックHTML）

**data-testid 命名規則**:

- カード: `card`
- ヘッダー: `card-header`
- コンテンツ: `card-content`
- フッター: `card-footer`

---

#### 5.3 Avatar

**概要**: アバター

**Props型定義**:

```typescript
export type AvatarProps = {
  /**
   * 画像URL
   */
  src?: string
  /**
   * 代替テキスト
   */
  alt: string
  /**
   * フォールバックテキスト（イニシャルなど）
   */
  fallback?: string
  /**
   * サイズ
   */
  size?: 'sm' | 'default' | 'lg'
  /**
   * クラス名
   */
  className?: string
}
```

**実装例**:

```typescript
import * as AvatarPrimitive from '@radix-ui/react-avatar'

export const Avatar = ({
  src,
  alt,
  fallback,
  size = 'default',
  className,
}: AvatarProps) => {
  const sizeClasses = {
    sm: 'h-8 w-8 text-xs',
    default: 'h-10 w-10 text-sm',
    lg: 'h-12 w-12 text-base',
  }

  // イニシャルを生成
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  const initials = fallback ? getInitials(fallback) : alt.slice(0, 2).toUpperCase()

  return (
    <AvatarPrimitive.Root
      className={cn(
        'relative flex shrink-0 overflow-hidden rounded-full',
        sizeClasses[size],
        className
      )}
      data-testid="avatar"
    >
      <AvatarPrimitive.Image
        src={src}
        alt={alt}
        className="aspect-square h-full w-full object-cover"
      />
      <AvatarPrimitive.Fallback
        className="flex h-full w-full items-center justify-center rounded-full bg-muted font-medium"
        data-testid="avatar-fallback"
      >
        {initials}
      </AvatarPrimitive.Fallback>
    </AvatarPrimitive.Root>
  )
}
```

**アクセシビリティ要件**:

- `alt` 属性で画像を説明

**data-testid 命名規則**:

- アバター: `avatar`
- フォールバック: `avatar-fallback`

---

#### 5.4 EmptyState

**概要**: 空状態表示

**Props型定義**:

```typescript
export type EmptyStateProps = {
  /**
   * アイコン
   */
  icon?: React.ReactNode
  /**
   * メッセージ
   */
  message: string
  /**
   * 説明
   */
  description?: string
  /**
   * アクション
   */
  action?: React.ReactNode
  /**
   * クラス名
   */
  className?: string
}
```

**実装例**:

```typescript
export const EmptyState = ({
  icon,
  message,
  description,
  action,
  className,
}: EmptyStateProps) => {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border border-dashed p-8 text-center',
        className
      )}
      data-testid="empty-state"
    >
      {icon && <div className="mb-4 text-muted-foreground">{icon}</div>}
      <h3 className="mb-2 text-lg font-semibold">{message}</h3>
      {description && (
        <p className="mb-4 text-sm text-muted-foreground max-w-sm">{description}</p>
      )}
      {action && <div>{action}</div>}
    </div>
  )
}
```

**使用例**:

```typescript
<EmptyState
  icon={<Inbox className="h-12 w-12" />}
  message="データがありません"
  description="新しいアイテムを作成して始めましょう"
  action={
    <Button leftIcon={<Plus className="h-4 w-4" />}>
      新規作成
    </Button>
  }
/>
```

**アクセシビリティ要件**:

- 適切な見出しレベルの使用

**data-testid 命名規則**: `empty-state`

---

#### 5.5 ErrorMessage

**概要**: エラーメッセージ表示

**Props型定義**:

```typescript
export type ErrorMessageProps = {
  /**
   * エラー
   */
  error: Error | { message: string }
  /**
   * リトライハンドラー
   */
  onRetry?: () => void
  /**
   * クラス名
   */
  className?: string
}
```

**実装例**:

```typescript
export const ErrorMessage = ({ error, onRetry, className }: ErrorMessageProps) => {
  return (
    <Alert variant="destructive" className={className}>
      <AlertCircle className="h-4 w-4" />
      <div className="flex-1">
        <h5 className="mb-1 font-medium leading-none tracking-tight">
          エラーが発生しました
        </h5>
        <div className="text-sm">{error.message}</div>
      </div>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          className="ml-auto"
          data-testid="error-retry-button"
        >
          再試行
        </Button>
      )}
    </Alert>
  )
}
```

**アクセシビリティ要件**:

- `role="alert"` で重要なエラーを示す

**data-testid 命名規則**: `error-retry-button`

---

### 6. ナビゲーション

#### 6.1 Tabs

**概要**: タブ（Radix UI Tabs使用）

**実装例**:

```typescript
import * as TabsPrimitive from '@radix-ui/react-tabs'

export const Tabs = TabsPrimitive.Root

export const TabsList = forwardRef<
  React.ElementRef<typeof TabsPrimitive.List>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.List>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.List
    ref={ref}
    className={cn(
      'inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground',
      className
    )}
    data-testid="tabs-list"
    {...props}
  />
))
TabsList.displayName = TabsPrimitive.List.displayName

export const TabsTrigger = forwardRef<
  React.ElementRef<typeof TabsPrimitive.Trigger>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Trigger>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Trigger
    ref={ref}
    className={cn(
      'inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm',
      className
    )}
    data-testid="tabs-trigger"
    {...props}
  />
))
TabsTrigger.displayName = TabsPrimitive.Trigger.displayName

export const TabsContent = forwardRef<
  React.ElementRef<typeof TabsPrimitive.Content>,
  React.ComponentPropsWithoutRef<typeof TabsPrimitive.Content>
>(({ className, ...props }, ref) => (
  <TabsPrimitive.Content
    ref={ref}
    className={cn(
      'mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
      className
    )}
    data-testid="tabs-content"
    {...props}
  />
))
TabsContent.displayName = TabsPrimitive.Content.displayName
```

**使用例**:

```typescript
<Tabs defaultValue="account">
  <TabsList>
    <TabsTrigger value="account">アカウント</TabsTrigger>
    <TabsTrigger value="password">パスワード</TabsTrigger>
  </TabsList>
  <TabsContent value="account">
    <p>アカウント設定の内容</p>
  </TabsContent>
  <TabsContent value="password">
    <p>パスワード設定の内容</p>
  </TabsContent>
</Tabs>
```

**アクセシビリティ要件**:

- `role="tablist"`, `role="tab"`, `role="tabpanel"` が自動付与
- キーボード操作（矢印キー）に対応

**data-testid 命名規則**:

- リスト: `tabs-list`
- トリガー: `tabs-trigger`
- コンテンツ: `tabs-content`

---

#### 6.2 Breadcrumb

**概要**: パンくずリスト

**Props型定義**:

```typescript
export type BreadcrumbItem = {
  /**
   * ラベル
   */
  label: string
  /**
   * リンク先（最後のアイテムはnull）
   */
  href?: string
}

export type BreadcrumbProps = {
  /**
   * アイテム
   */
  items: BreadcrumbItem[]
  /**
   * セパレーター
   */
  separator?: React.ReactNode
  /**
   * クラス名
   */
  className?: string
}
```

**実装例**:

```typescript
import Link from 'next/link'

export const Breadcrumb = ({
  items,
  separator = <ChevronRight className="h-4 w-4" />,
  className,
}: BreadcrumbProps) => {
  return (
    <nav aria-label="パンくずリスト" className={className} data-testid="breadcrumb">
      <ol className="flex items-center space-x-2 text-sm">
        {items.map((item, index) => {
          const isLast = index === items.length - 1

          return (
            <li key={index} className="flex items-center space-x-2">
              {index > 0 && (
                <span className="text-muted-foreground" aria-hidden="true">
                  {separator}
                </span>
              )}
              {isLast || !item.href ? (
                <span
                  className="font-medium text-foreground"
                  aria-current={isLast ? 'page' : undefined}
                  data-testid={`breadcrumb-item-${index}`}
                >
                  {item.label}
                </span>
              ) : (
                <Link
                  href={item.href}
                  className="text-muted-foreground hover:text-foreground transition-colors"
                  data-testid={`breadcrumb-link-${index}`}
                >
                  {item.label}
                </Link>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
```

**使用例**:

```typescript
<Breadcrumb
  items={[
    { label: 'ホーム', href: '/' },
    { label: 'プロジェクト', href: '/projects' },
    { label: '詳細' },
  ]}
/>
```

**アクセシビリティ要件**:

- `aria-label` でナビゲーションを説明
- `aria-current="page"` で現在のページを示す

**data-testid 命名規則**:

- パンくずリスト: `breadcrumb`
- アイテム: `breadcrumb-item-{index}`
- リンク: `breadcrumb-link-{index}`

---

#### 6.3 Pagination

**概要**: ページネーション

**Props型定義**:

```typescript
export type PaginationProps = {
  /**
   * 現在のページ
   */
  currentPage: number
  /**
   * 総ページ数
   */
  totalPages: number
  /**
   * ページ変更ハンドラー
   */
  onPageChange: (page: number) => void
  /**
   * 表示するページボタンの数
   */
  siblingCount?: number
  /**
   * クラス名
   */
  className?: string
}
```

**実装例**:

```typescript
export const Pagination = ({
  currentPage,
  totalPages,
  onPageChange,
  siblingCount = 1,
  className,
}: PaginationProps) => {
  const range = (start: number, end: number) => {
    const length = end - start + 1
    return Array.from({ length }, (_, idx) => idx + start)
  }

  const paginationRange = useMemo(() => {
    const totalPageNumbers = siblingCount + 5

    if (totalPageNumbers >= totalPages) {
      return range(1, totalPages)
    }

    const leftSiblingIndex = Math.max(currentPage - siblingCount, 1)
    const rightSiblingIndex = Math.min(currentPage + siblingCount, totalPages)

    const shouldShowLeftDots = leftSiblingIndex > 2
    const shouldShowRightDots = rightSiblingIndex < totalPages - 2

    const firstPageIndex = 1
    const lastPageIndex = totalPages

    if (!shouldShowLeftDots && shouldShowRightDots) {
      const leftItemCount = 3 + 2 * siblingCount
      const leftRange = range(1, leftItemCount)
      return [...leftRange, '...', totalPages]
    }

    if (shouldShowLeftDots && !shouldShowRightDots) {
      const rightItemCount = 3 + 2 * siblingCount
      const rightRange = range(totalPages - rightItemCount + 1, totalPages)
      return [firstPageIndex, '...', ...rightRange]
    }

    if (shouldShowLeftDots && shouldShowRightDots) {
      const middleRange = range(leftSiblingIndex, rightSiblingIndex)
      return [firstPageIndex, '...', ...middleRange, '...', lastPageIndex]
    }
  }, [totalPages, siblingCount, currentPage])

  const handlePrevious = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1)
    }
  }

  const handleNext = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1)
    }
  }

  return (
    <nav
      role="navigation"
      aria-label="ページネーション"
      className={cn('flex items-center justify-center gap-1', className)}
      data-testid="pagination"
    >
      <Button
        variant="outline"
        size="sm"
        onClick={handlePrevious}
        disabled={currentPage === 1}
        data-testid="pagination-previous"
      >
        <ChevronLeft className="h-4 w-4" />
        <span className="sr-only">前のページ</span>
      </Button>

      {paginationRange?.map((pageNumber, index) => {
        if (pageNumber === '...') {
          return (
            <span key={index} className="px-2">
              &#8230;
            </span>
          )
        }

        return (
          <Button
            key={index}
            variant={currentPage === pageNumber ? 'default' : 'outline'}
            size="sm"
            onClick={() => onPageChange(pageNumber as number)}
            data-testid={`pagination-page-${pageNumber}`}
          >
            {pageNumber}
          </Button>
        )
      })}

      <Button
        variant="outline"
        size="sm"
        onClick={handleNext}
        disabled={currentPage === totalPages}
        data-testid="pagination-next"
      >
        <ChevronRight className="h-4 w-4" />
        <span className="sr-only">次のページ</span>
      </Button>
    </nav>
  )
}
```

**アクセシビリティ要件**:

- `role="navigation"` でナビゲーションを示す
- `aria-label` で説明を提供
- `sr-only` クラスでスクリーンリーダー用テキスト

**data-testid 命名規則**:

- ページネーション: `pagination`
- 前へボタン: `pagination-previous`
- 次へボタン: `pagination-next`
- ページボタン: `pagination-page-{pageNumber}`

---

### 7. レイアウト

#### 7.1 Container

**概要**: コンテナ

**Props型定義**:

```typescript
export type ContainerProps = HTMLAttributes<HTMLDivElement> & {
  /**
   * 最大幅
   */
  maxWidth?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full'
}
```

**実装例**:

```typescript
export const Container = forwardRef<HTMLDivElement, ContainerProps>(
  ({ className, maxWidth = 'lg', ...props }, ref) => {
    const maxWidthClasses = {
      sm: 'max-w-screen-sm',
      md: 'max-w-screen-md',
      lg: 'max-w-screen-lg',
      xl: 'max-w-screen-xl',
      '2xl': 'max-w-screen-2xl',
      full: 'max-w-full',
    }

    return (
      <div
        ref={ref}
        className={cn('mx-auto w-full px-4', maxWidthClasses[maxWidth], className)}
        data-testid="container"
        {...props}
      />
    )
  }
)
Container.displayName = 'Container'
```

**data-testid 命名規則**: `container`

---

#### 7.2 Stack

**概要**: スタックレイアウト

**Props型定義**:

```typescript
export type StackProps = HTMLAttributes<HTMLDivElement> & {
  /**
   * 方向
   */
  direction?: 'horizontal' | 'vertical'
  /**
   * 間隔
   */
  spacing?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  /**
   * 配置
   */
  align?: 'start' | 'center' | 'end' | 'stretch'
  /**
   * 均等配置
   */
  justify?: 'start' | 'center' | 'end' | 'between' | 'around'
}
```

**実装例**:

```typescript
export const Stack = forwardRef<HTMLDivElement, StackProps>(
  (
    {
      className,
      direction = 'vertical',
      spacing = 'md',
      align = 'stretch',
      justify = 'start',
      ...props
    },
    ref
  ) => {
    const spacingClasses = {
      none: 'gap-0',
      xs: 'gap-1',
      sm: 'gap-2',
      md: 'gap-4',
      lg: 'gap-6',
      xl: 'gap-8',
    }

    const alignClasses = {
      start: 'items-start',
      center: 'items-center',
      end: 'items-end',
      stretch: 'items-stretch',
    }

    const justifyClasses = {
      start: 'justify-start',
      center: 'justify-center',
      end: 'justify-end',
      between: 'justify-between',
      around: 'justify-around',
    }

    return (
      <div
        ref={ref}
        className={cn(
          'flex',
          direction === 'horizontal' ? 'flex-row' : 'flex-col',
          spacingClasses[spacing],
          alignClasses[align],
          justifyClasses[justify],
          className
        )}
        data-testid="stack"
        {...props}
      />
    )
  }
)
Stack.displayName = 'Stack'
```

**data-testid 命名規則**: `stack`

---

#### 7.3 Grid

**概要**: グリッドレイアウト

**Props型定義**:

```typescript
export type GridProps = HTMLAttributes<HTMLDivElement> & {
  /**
   * カラム数
   */
  columns?: 1 | 2 | 3 | 4 | 6 | 12
  /**
   * 間隔
   */
  gap?: 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl'
}
```

**実装例**:

```typescript
export const Grid = forwardRef<HTMLDivElement, GridProps>(
  ({ className, columns = 12, gap = 'md', ...props }, ref) => {
    const columnClasses = {
      1: 'grid-cols-1',
      2: 'grid-cols-2',
      3: 'grid-cols-3',
      4: 'grid-cols-4',
      6: 'grid-cols-6',
      12: 'grid-cols-12',
    }

    const gapClasses = {
      none: 'gap-0',
      xs: 'gap-1',
      sm: 'gap-2',
      md: 'gap-4',
      lg: 'gap-6',
      xl: 'gap-8',
    }

    return (
      <div
        ref={ref}
        className={cn('grid', columnClasses[columns], gapClasses[gap], className)}
        data-testid="grid"
        {...props}
      />
    )
  }
)
Grid.displayName = 'Grid'
```

**data-testid 命名規則**: `grid`

---

#### 7.4 Separator

**概要**: 区切り線

**Props型定義**:

```typescript
export type SeparatorProps = {
  /**
   * 方向
   */
  orientation?: 'horizontal' | 'vertical'
  /**
   * クラス名
   */
  className?: string
}
```

**実装例**:

```typescript
export const Separator = forwardRef<HTMLDivElement, SeparatorProps>(
  ({ className, orientation = 'horizontal', ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        'shrink-0 bg-border',
        orientation === 'horizontal' ? 'h-[1px] w-full' : 'h-full w-[1px]',
        className
      )}
      role="separator"
      aria-orientation={orientation}
      data-testid="separator"
      {...props}
    />
  )
)
Separator.displayName = 'Separator'
```

**アクセシビリティ要件**:

- `role="separator"` で区切りを示す
- `aria-orientation` で方向を指定

**data-testid 命名規則**: `separator`

---

## テスト戦略

### 1. ユニットテスト（Vitest + Testing Library）

**基本テストパターン**:

```typescript
import { render, screen, userEvent } from '@/test/test-utils'
import { Button } from './button'

describe('Button', () => {
  it('正しくレンダリングされる', () => {
    render(<Button>クリック</Button>)
    expect(screen.getByTestId('button')).toBeInTheDocument()
    expect(screen.getByText('クリック')).toBeInTheDocument()
  })

  it('クリックイベントが発火する', async () => {
    const handleClick = vi.fn()
    render(<Button onClick={handleClick}>クリック</Button>)

    await userEvent.click(screen.getByTestId('button'))
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('無効化状態でクリックできない', async () => {
    const handleClick = vi.fn()
    render(<Button disabled onClick={handleClick}>クリック</Button>)

    await userEvent.click(screen.getByTestId('button'))
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('ローディング状態でスピナーが表示される', () => {
    render(<Button isLoading>クリック</Button>)
    expect(screen.getByTestId('spinner')).toBeInTheDocument()
  })
})
```

### 2. アクセシビリティテスト

```typescript
import { axe, toHaveNoViolations } from 'jest-axe'

expect.extend(toHaveNoViolations)

describe('Button - アクセシビリティ', () => {
  it('アクセシビリティ違反がない', async () => {
    const { container } = render(<Button>クリック</Button>)
    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })
})
```

### 3. Storybookストーリー

```typescript
import type { Meta, StoryObj } from '@storybook/react'
import { Button } from './button'

const meta: Meta<typeof Button> = {
  title: 'UI/Button',
  component: Button,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'icon'],
    },
  },
}

export default meta
type Story = StoryObj<typeof Button>

export const Default: Story = {
  args: {
    children: 'Button',
  },
}

export const Destructive: Story = {
  args: {
    variant: 'destructive',
    children: '削除',
  },
}

export const Loading: Story = {
  args: {
    isLoading: true,
    children: '送信中...',
  },
}

export const WithIcon: Story = {
  args: {
    leftIcon: <Plus className="h-4 w-4" />,
    children: '新規作成',
  },
}
```

---

## まとめ

本仕様書では、bulletproof-react アーキテクチャに準拠した共通UIコンポーネントの設計を定義しました。

### 重要なポイント

1. **Features-based Architecture**: `components/ui/` に配置し、機能固有のロジックを含まない
2. **型安全性**: `type` のみ使用、`interface` 禁止、アロー関数必須
3. **CVAによるバリアント管理**: スタイリングの一貫性と拡張性
4. **アクセシビリティ**: WAI-ARIA 準拠、キーボード操作対応
5. **テスト容易性**: `data-testid` 属性、ユニットテスト、Storybook

### 次のステップ

1. 各コンポーネントの実装
2. Storybookストーリーの作成
3. ユニットテストの作成
4. アクセシビリティテストの実施
5. ドキュメントの充実

この設計に従うことで、保守性が高く、再利用可能で、アクセシブルなUIコンポーネントライブラリを構築できます。
