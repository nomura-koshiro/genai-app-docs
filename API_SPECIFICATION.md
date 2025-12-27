# API仕様書

モックアップから策定したAPI一覧とリクエスト/レスポンス仕様

---

## 1. 認証 (Authentication)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/auth/login` | Azure AD認証リダイレクト |
| GET | `/api/v1/auth/callback` | Azure ADコールバック |
| POST | `/api/v1/auth/logout` | ログアウト |
| GET | `/api/v1/auth/me` | 現在のユーザー情報取得 |

### `GET /api/v1/auth/me`

**Response:**

```json
{
  "id": "uuid",
  "azure_id": "string",
  "email": "string",
  "display_name": "string",
  "system_role": "ADMIN | SYSTEM_USER",
  "is_active": true,
  "created_at": "2025-12-01T00:00:00Z",
  "last_login_at": "2025-12-25T10:30:00Z"
}
```

---

## 2. ダッシュボード (Dashboard)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/dashboard/stats` | ダッシュボード統計情報 |
| GET | `/api/v1/dashboard/activities` | 最近のアクティビティ |
| GET | `/api/v1/dashboard/charts` | チャートデータ |

### `GET /api/v1/dashboard/stats`

**Query Parameters:**

- `period`: `7 | 30 | 90` (日数)

**Response:**

```json
{
  "project_count": 12,
  "project_change": 2,
  "active_session_count": 5,
  "driver_tree_count": 8,
  "tree_change": 1,
  "file_count": 47
}
```

### `GET /api/v1/dashboard/activities`

**Query Parameters:**

- `limit`: number (default: 10)

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "type": "SESSION_CREATED | TREE_UPDATED | FILE_UPLOADED | PROJECT_JOINED | SESSION_COMPLETED",
      "user": {
        "id": "uuid",
        "display_name": "山田 太郎"
      },
      "target_name": "Q4売上分析",
      "project": {
        "id": "uuid",
        "name": "売上分析プロジェクト"
      },
      "created_at": "2025-12-25T10:30:00Z"
    }
  ]
}
```

---

## 3. プロジェクト (Projects)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/projects` | プロジェクト一覧取得 |
| POST | `/api/v1/projects` | プロジェクト作成 |
| GET | `/api/v1/projects/{id}` | プロジェクト詳細取得 |
| PUT | `/api/v1/projects/{id}` | プロジェクト更新 |
| DELETE | `/api/v1/projects/{id}` | プロジェクト削除 |
| PATCH | `/api/v1/projects/{id}/archive` | アーカイブ/復元 |

### `GET /api/v1/projects`

**Query Parameters:**

- `search`: string (プロジェクト名検索)
- `status`: `active | archived`
- `page`: number
- `per_page`: number

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "売上分析プロジェクト",
      "description": "2025年度の売上データ分析",
      "member_count": 5,
      "status": "active",
      "created_at": "2025-12-01T00:00:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "per_page": 20
}
```

### `POST /api/v1/projects`

**Request:**

```json
{
  "name": "新規プロジェクト",
  "description": "プロジェクトの説明",
  "start_date": "2025-12-01",
  "end_date": "2026-03-31",
  "member_ids": ["uuid1", "uuid2"]
}
```

**Response:**

```json
{
  "id": "uuid",
  "name": "新規プロジェクト",
  "description": "プロジェクトの説明",
  "status": "active",
  "start_date": "2025-12-01",
  "end_date": "2026-03-31",
  "created_by": {
    "id": "uuid",
    "display_name": "山田 太郎"
  },
  "created_at": "2025-12-25T00:00:00Z"
}
```

### `GET /api/v1/projects/{id}`

**Response:**

```json
{
  "id": "uuid",
  "name": "売上分析プロジェクト",
  "description": "2025年度の売上データを分析し...",
  "status": "active",
  "start_date": "2025-12-01",
  "end_date": "2026-03-31",
  "created_by": {
    "id": "uuid",
    "display_name": "山田 太郎"
  },
  "created_at": "2025-12-01T00:00:00Z",
  "stats": {
    "session_count": 2,
    "snapshot_count": 8,
    "tree_count": 1,
    "file_count": 3
  }
}
```

---

## 4. プロジェクトメンバー (Project Members)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/projects/{project_id}/members` | メンバー一覧 |
| POST | `/api/v1/projects/{project_id}/members` | メンバー追加 |
| PUT | `/api/v1/projects/{project_id}/members/{user_id}` | ロール変更 |
| DELETE | `/api/v1/projects/{project_id}/members/{user_id}` | メンバー削除 |

### `GET /api/v1/projects/{project_id}/members`

**Response:**

```json
{
  "items": [
    {
      "user": {
        "id": "uuid",
        "display_name": "山田 太郎",
        "email": "yamada@example.com"
      },
      "role": "PROJECT_MANAGER | MODERATOR | MEMBER | VIEWER",
      "joined_at": "2025-12-01T00:00:00Z"
    }
  ]
}
```

### `POST /api/v1/projects/{project_id}/members`

**Request:**

```json
{
  "user_id": "uuid",
  "role": "MEMBER"
}
```

---

## 5. ファイル管理 (Files)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/projects/{project_id}/files` | ファイル一覧 |
| POST | `/api/v1/projects/{project_id}/files` | ファイルアップロード |
| GET | `/api/v1/projects/{project_id}/files/{id}` | ファイル情報取得 |
| GET | `/api/v1/projects/{project_id}/files/{id}/download` | ファイルダウンロード |
| DELETE | `/api/v1/projects/{project_id}/files/{id}` | ファイル削除 |
| GET | `/api/v1/projects/{project_id}/files/{id}/sheets` | Excelシート一覧 |
| GET | `/api/v1/projects/{project_id}/files/{id}/sheets/{sheet}/columns` | シートの列情報 |

### `GET /api/v1/projects/{project_id}/files`

**Query Parameters:**

- `search`: string
- `type`: `xlsx | csv | json`

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "sales_2025q4.xlsx",
      "type": "xlsx",
      "size": 2516582,
      "uploaded_by": {
        "id": "uuid",
        "display_name": "山田 太郎"
      },
      "uploaded_at": "2025-12-20T00:00:00Z",
      "usage": {
        "session_count": 2,
        "tree_count": 1
      }
    }
  ]
}
```

### `POST /api/v1/projects/{project_id}/files`

**Request:** `multipart/form-data`

- `file`: File

**Response:**

```json
{
  "id": "uuid",
  "name": "new_data.xlsx",
  "type": "xlsx",
  "size": 1234567,
  "uploaded_at": "2025-12-25T00:00:00Z"
}
```

### `GET /api/v1/projects/{project_id}/files/{id}/sheets`

**Response:**

```json
{
  "sheets": [
    {
      "index": 0,
      "name": "Sheet1",
      "display_name": "売上データ",
      "row_count": 15230
    }
  ]
}
```

### `GET /api/v1/projects/{project_id}/files/{id}/sheets/{sheet}/columns`

**Response:**

```json
{
  "columns": [
    {
      "index": 0,
      "name": "date",
      "display_name": "日付",
      "data_type": "datetime"
    },
    {
      "index": 1,
      "name": "sales_amount",
      "display_name": "売上金額",
      "data_type": "number"
    }
  ]
}
```

---

## 6. 分析セッション (Analysis Sessions)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/projects/{project_id}/sessions` | セッション一覧 |
| POST | `/api/v1/projects/{project_id}/sessions` | セッション作成 |
| GET | `/api/v1/sessions/{id}` | セッション詳細 |
| PUT | `/api/v1/sessions/{id}` | セッション更新 |
| DELETE | `/api/v1/sessions/{id}` | セッション削除 |
| POST | `/api/v1/sessions/{id}/duplicate` | セッション複製 |

### `GET /api/v1/projects/{project_id}/sessions`

**Query Parameters:**

- `search`: string
- `template_id`: uuid (課題フィルター)

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "Q4売上分析",
      "template": {
        "id": "uuid",
        "name": "売上予測"
      },
      "file": {
        "id": "uuid",
        "name": "sales_2025q4.xlsx"
      },
      "snapshot_count": 5,
      "created_by": {
        "id": "uuid",
        "display_name": "山田 太郎"
      },
      "updated_at": "2025-12-25T10:30:00Z"
    }
  ]
}
```

### `POST /api/v1/projects/{project_id}/sessions`

**Request:**

```json
{
  "name": "Q4売上予測分析",
  "category_id": "uuid",
  "template_id": "uuid",
  "file_id": "uuid",
  "sheet_index": 0,
  "axis_settings": {
    "time_column": "date",
    "value_column": "sales_amount",
    "group_column": "category"
  }
}
```

### `GET /api/v1/sessions/{id}`

**Response:**

```json
{
  "id": "uuid",
  "name": "Q4売上分析",
  "status": "in_progress | completed",
  "template": {
    "id": "uuid",
    "name": "売上予測",
    "category": {
      "id": "uuid",
      "name": "時系列分析"
    }
  },
  "file": {
    "id": "uuid",
    "name": "sales_2025q4.xlsx",
    "size": 2516582,
    "row_count": 15230,
    "column_count": 12
  },
  "axis_settings": {
    "time_column": "date",
    "value_column": "sales_amount",
    "group_column": null
  },
  "current_snapshot_id": "uuid",
  "snapshot_count": 5,
  "created_by": {
    "id": "uuid",
    "display_name": "山田 太郎"
  },
  "created_at": "2025-12-25T10:30:00Z",
  "completed_at": null
}
```

---

## 7. 分析チャット (Analysis Chat)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/sessions/{session_id}/messages` | メッセージ履歴取得 |
| POST | `/api/v1/sessions/{session_id}/messages` | メッセージ送信 |
| GET | `/api/v1/sessions/{session_id}/steps` | ステップ一覧 |

### `GET /api/v1/sessions/{session_id}/messages`

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "role": "assistant | user",
      "content": "こんにちは！売上予測分析を開始します。",
      "created_at": "2025-12-25T10:30:00Z"
    }
  ]
}
```

### `POST /api/v1/sessions/{session_id}/messages`

**Request:**

```json
{
  "content": "月別の売上推移を見せてください。"
}
```

**Response:** (Server-Sent Events)

```json
{
  "id": "uuid",
  "role": "assistant",
  "content": "承知しました。月別売上推移のグラフを作成しました...",
  "step": {
    "id": "uuid",
    "number": 4,
    "title": "カテゴリ別分析",
    "status": "running"
  },
  "created_at": "2025-12-25T10:45:00Z"
}
```

### `GET /api/v1/sessions/{session_id}/steps`

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "number": 1,
      "title": "データ読み込み",
      "status": "completed | running | pending",
      "completed_at": "2025-12-25T10:30:00Z"
    }
  ]
}
```

---

## 8. スナップショット (Snapshots)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/sessions/{session_id}/snapshots` | スナップショット一覧 |
| POST | `/api/v1/sessions/{session_id}/snapshots` | スナップショット保存 |
| GET | `/api/v1/snapshots/{id}` | スナップショット詳細 |
| POST | `/api/v1/snapshots/{id}/restore` | スナップショット復元 |

### `GET /api/v1/sessions/{session_id}/snapshots`

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "number": 5,
      "description": "カテゴリ別分析を実行中",
      "is_current": true,
      "created_at": "2025-12-25T10:45:00Z"
    }
  ]
}
```

### `POST /api/v1/snapshots/{id}/restore`

**Response:**

```json
{
  "session_id": "uuid",
  "new_snapshot_id": "uuid",
  "message": "スナップショット#3から復元しました"
}
```

---

## 9. ドライバーツリー (Driver Trees)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/projects/{project_id}/trees` | ツリー一覧 |
| POST | `/api/v1/projects/{project_id}/trees` | ツリー作成 |
| GET | `/api/v1/trees/{id}` | ツリー詳細 |
| PUT | `/api/v1/trees/{id}` | ツリー更新 |
| DELETE | `/api/v1/trees/{id}` | ツリー削除 |
| POST | `/api/v1/trees/{id}/duplicate` | ツリー複製 |
| POST | `/api/v1/trees/{id}/calculate` | 計算実行 |

### `GET /api/v1/projects/{project_id}/trees`

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "売上ドライバーツリー",
      "category": {
        "id": "uuid",
        "name": "売上分解モデル v2"
      },
      "node_count": 12,
      "policy_count": 3,
      "updated_at": "2025-12-25T09:00:00Z"
    }
  ]
}
```

### `POST /api/v1/projects/{project_id}/trees`

**Request:**

```json
{
  "name": "売上ドライバーツリー",
  "description": "売上分析用のドライバーツリー",
  "category_id": "uuid"
}
```

### `GET /api/v1/trees/{id}`

**Response:**

```json
{
  "id": "uuid",
  "name": "売上ドライバーツリー",
  "description": "...",
  "category": {
    "id": "uuid",
    "name": "売上分解モデル v2"
  },
  "nodes": [
    {
      "id": "uuid",
      "label": "売上高",
      "type": "driver | kpi | metric",
      "parent_id": null,
      "position": { "x": 400, "y": 20 },
      "data_binding": {
        "column": "sales_amount",
        "aggregation": "sum"
      },
      "current_value": 41500000
    }
  ],
  "edges": [
    {
      "id": "uuid",
      "source_id": "uuid",
      "target_id": "uuid"
    }
  ],
  "updated_at": "2025-12-25T09:00:00Z"
}
```

---

## 10. ツリーノード (Tree Nodes)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| POST | `/api/v1/trees/{tree_id}/nodes` | ノード追加 |
| PUT | `/api/v1/trees/{tree_id}/nodes/{id}` | ノード更新 |
| DELETE | `/api/v1/trees/{tree_id}/nodes/{id}` | ノード削除 |

### `POST /api/v1/trees/{tree_id}/nodes`

**Request:**

```json
{
  "label": "新規ノード",
  "type": "driver",
  "parent_id": "uuid",
  "position": { "x": 200, "y": 300 }
}
```

---

## 11. 施策 (Policies)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/trees/{tree_id}/policies` | 施策一覧 |
| POST | `/api/v1/trees/{tree_id}/policies` | 施策作成 |
| PUT | `/api/v1/policies/{id}` | 施策更新 |
| DELETE | `/api/v1/policies/{id}` | 施策削除 |

### `GET /api/v1/trees/{tree_id}/policies`

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "新規顧客獲得キャンペーン",
      "description": "デジタルマーケティングを強化し...",
      "target_node": {
        "id": "uuid",
        "label": "新規顧客"
      },
      "impact_percentage": 15,
      "cost": 5000000,
      "duration_months": 3,
      "status": "active | planned | draft"
    }
  ]
}
```

### `POST /api/v1/trees/{tree_id}/policies`

**Request:**

```json
{
  "name": "新規顧客獲得キャンペーン",
  "description": "...",
  "target_node_id": "uuid",
  "impact_percentage": 15,
  "cost": 5000000,
  "duration_months": 3
}
```

---

## 12. データ紐付け (Data Binding)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/trees/{tree_id}/bindings` | 紐付け情報取得 |
| PUT | `/api/v1/trees/{tree_id}/bindings` | 紐付け更新 |
| POST | `/api/v1/trees/{tree_id}/bindings/refresh` | データ更新 |

### `GET /api/v1/trees/{tree_id}/bindings`

**Response:**

```json
{
  "data_source": {
    "file_id": "uuid",
    "file_name": "sales_2025q4.xlsx",
    "sheet_index": 0,
    "sheet_name": "Sheet1",
    "period": "latest"
  },
  "bindings": [
    {
      "node_id": "uuid",
      "node_label": "新規顧客",
      "column": "new_customers",
      "aggregation": "sum",
      "current_value": 1200,
      "status": "bound | unbound | calculated"
    }
  ]
}
```

### `PUT /api/v1/trees/{tree_id}/bindings`

**Request:**

```json
{
  "data_source": {
    "file_id": "uuid",
    "sheet_index": 0,
    "period": "2025q4"
  },
  "bindings": [
    {
      "node_id": "uuid",
      "column": "new_customers",
      "aggregation": "sum"
    }
  ]
}
```

---

## 13. 計算結果 (Calculation Results)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/trees/{tree_id}/results` | 計算結果取得 |
| POST | `/api/v1/trees/{tree_id}/results/export` | エクスポート |

### `GET /api/v1/trees/{tree_id}/results`

**Response:**

```json
{
  "summary": {
    "current_value": 41500000,
    "projected_value": 48130000,
    "change_rate": 16.0,
    "change_amount": 6630000,
    "total_policy_cost": 15000000
  },
  "nodes": [
    {
      "node_id": "uuid",
      "label": "売上高",
      "current_value": 41500000,
      "projected_value": 48130000,
      "change_rate": 16.0,
      "applied_policies": []
    }
  ],
  "policy_effects": [
    {
      "policy_id": "uuid",
      "name": "新規顧客獲得キャンペーン",
      "impact_amount": 3225000,
      "cost": 5000000,
      "roi": 64.5
    }
  ]
}
```

---

## 14. カテゴリマスタ (Categories - Admin)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/admin/categories` | カテゴリ一覧 |
| POST | `/api/v1/admin/categories` | カテゴリ作成 |
| GET | `/api/v1/admin/categories/{id}` | カテゴリ詳細 |
| PUT | `/api/v1/admin/categories/{id}` | カテゴリ更新 |
| DELETE | `/api/v1/admin/categories/{id}` | カテゴリ削除 |

### `GET /api/v1/admin/categories`

**Query Parameters:**

- `search`: string
- `industry`: string

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "売上分解モデル v2",
      "industry": "全業種共通",
      "driver_type": "Revenue | Cost | Profit",
      "formula_count": 5,
      "updated_at": "2025-12-20T00:00:00Z"
    }
  ]
}
```

### `GET /api/v1/admin/categories/{id}`

**Response:**

```json
{
  "id": "uuid",
  "name": "売上分解モデル v2",
  "description": "...",
  "industry": "全業種共通",
  "driver_type": "Revenue",
  "formulas": [
    {
      "order": 1,
      "kpi": "売上高",
      "formula": "顧客数 × 顧客単価"
    }
  ],
  "tree_structure": {
    "nodes": [],
    "edges": []
  },
  "usage_count": 12,
  "created_by": {},
  "created_at": "2025-09-15T00:00:00Z",
  "updated_at": "2025-12-20T00:00:00Z"
}
```

---

## 15. 検証マスタ (Verifications - Admin)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/admin/verifications` | 検証マスタ一覧 |
| POST | `/api/v1/admin/verifications` | 検証マスタ作成 |
| GET | `/api/v1/admin/verifications/{id}` | 検証マスタ詳細 |
| PUT | `/api/v1/admin/verifications/{id}` | 検証マスタ更新 |
| DELETE | `/api/v1/admin/verifications/{id}` | 検証マスタ削除 |

### `GET /api/v1/admin/verifications`

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "時系列分析",
      "description": "時系列データの予測と分析",
      "template_count": 2,
      "status": "active | inactive",
      "updated_at": "2025-12-20T00:00:00Z"
    }
  ]
}
```

---

## 16. 課題マスタ (Templates - Admin)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/admin/templates` | 課題マスタ一覧 |
| POST | `/api/v1/admin/templates` | 課題マスタ作成 |
| GET | `/api/v1/admin/templates/{id}` | 課題マスタ詳細 |
| PUT | `/api/v1/admin/templates/{id}` | 課題マスタ更新 |
| DELETE | `/api/v1/admin/templates/{id}` | 課題マスタ削除 |

### `GET /api/v1/admin/templates`

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "売上予測",
      "verification": {
        "id": "uuid",
        "name": "時系列分析"
      },
      "has_prompt": true,
      "has_initial_message": true,
      "status": "active | draft | inactive",
      "updated_at": "2025-12-25T00:00:00Z"
    }
  ]
}
```

### `GET /api/v1/admin/templates/{id}`

**Response:**

```json
{
  "id": "uuid",
  "name": "売上予測",
  "description": "過去の売上データを基に...",
  "verification": {
    "id": "uuid",
    "name": "時系列分析"
  },
  "system_prompt": "あなたは売上データ分析の専門家です...",
  "initial_message": "こんにちは！売上予測分析を始めましょう...",
  "available_variables": [
    "{{data}}",
    "{{period}}",
    "{{forecast_period}}",
    "{{user_name}}",
    "{{project_name}}",
    "{{tree_context}}"
  ],
  "dummy_files": [
    {
      "id": "uuid",
      "name": "sample_sales_2024.csv",
      "size": 2516582,
      "uploaded_at": "2025-12-20T00:00:00Z"
    }
  ],
  "status": "active",
  "usage_count": 47,
  "created_at": "2025-11-01T00:00:00Z",
  "updated_at": "2025-12-25T00:00:00Z"
}
```

---

## 17. ユーザー管理 (Users - Admin)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/admin/users` | ユーザー一覧 |
| GET | `/api/v1/admin/users/{id}` | ユーザー詳細 |
| PUT | `/api/v1/admin/users/{id}` | ユーザー更新 |
| PATCH | `/api/v1/admin/users/{id}/activate` | 有効化/無効化 |

### `GET /api/v1/admin/users`

**Query Parameters:**

- `search`: string
- `role`: `ADMIN | SYSTEM_USER`
- `status`: `active | inactive`
- `page`: number
- `per_page`: number

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "display_name": "山田 太郎",
      "email": "yamada@example.com",
      "system_role": "SYSTEM_USER",
      "is_active": true,
      "last_login_at": "2025-12-25T10:30:00Z"
    }
  ],
  "total": 50,
  "page": 1,
  "per_page": 20
}
```

### `GET /api/v1/admin/users/{id}`

**Response:**

```json
{
  "id": "uuid",
  "azure_id": "abc123-def456",
  "display_name": "山田 太郎",
  "email": "yamada.taro@example.com",
  "system_role": "SYSTEM_USER",
  "is_active": true,
  "stats": {
    "project_count": 5,
    "session_count": 23,
    "tree_count": 12
  },
  "projects": [
    {
      "project": {
        "id": "uuid",
        "name": "売上分析プロジェクト"
      },
      "role": "MEMBER",
      "status": "active",
      "joined_at": "2025-10-15T00:00:00Z"
    }
  ],
  "activities": [
    {
      "type": "SESSION_CREATED",
      "target_name": "Q4売上分析",
      "project_name": "売上分析プロジェクト",
      "created_at": "2025-12-25T10:30:00Z"
    }
  ],
  "created_at": "2025-06-15T00:00:00Z",
  "last_login_at": "2025-12-25T10:30:00Z",
  "login_count": 156
}
```

---

## 18. システムロール一覧 (Roles - Admin)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/admin/roles/system` | システムロール一覧 |
| GET | `/api/v1/admin/roles/project` | プロジェクトロール一覧 |

### `GET /api/v1/admin/roles/system`

**Response:**

```json
{
  "roles": [
    {
      "name": "ADMIN",
      "description": "システム管理者",
      "permissions": "全ての操作が可能。マスタ管理、ユーザー管理を含む"
    },
    {
      "name": "SYSTEM_USER",
      "description": "一般ユーザー",
      "permissions": "プロジェクト作成、分析セッション、ドライバーツリーの操作が可能"
    }
  ]
}
```

---

## 19. ツリーテンプレート一覧 (Tree Templates)

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/tree-templates` | テンプレート一覧 |

### `GET /api/v1/tree-templates`

**Query Parameters:**

- `industry`: string (業種フィルター)
- `analysis_type`: string (分析タイプフィルター)

**Response:**

```json
{
  "items": [
    {
      "id": "uuid",
      "name": "売上分解モデル（基本）",
      "description": "顧客数 × 顧客単価で売上を分解する基本モデル",
      "icon": "📈",
      "tags": ["小売・EC", "売上分析"],
      "node_count": 8,
      "usage_count": 150,
      "is_popular": true,
      "preview": {
        "nodes": [],
        "edges": []
      }
    }
  ]
}
```

---

## サマリー

| カテゴリ | エンドポイント数 |
|---------|-----------------|
| 認証 | 4 |
| ダッシュボード | 3 |
| プロジェクト | 6 |
| プロジェクトメンバー | 4 |
| ファイル管理 | 7 |
| 分析セッション | 6 |
| 分析チャット | 3 |
| スナップショット | 4 |
| ドライバーツリー | 7 |
| ツリーノード | 3 |
| 施策 | 4 |
| データ紐付け | 3 |
| 計算結果 | 2 |
| カテゴリマスタ (Admin) | 5 |
| 検証マスタ (Admin) | 5 |
| 課題マスタ (Admin) | 5 |
| ユーザー管理 (Admin) | 4 |
| ロール一覧 (Admin) | 2 |
| ツリーテンプレート | 1 |
| **合計** | **約78** |
