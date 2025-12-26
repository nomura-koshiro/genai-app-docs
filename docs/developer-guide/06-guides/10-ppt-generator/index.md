# PPT Generator機能

このガイドでは、camp-backend-code-analysisから移植されたPowerPointファイル生成・操作機能の使用方法と実装の詳細を説明します。

## 目次

- [概要](#概要)
- [機能説明](#機能説明)
- [アーキテクチャ](#アーキテクチャ)
- [データフロー](#データフロー)
- [使用方法](#使用方法)
- [API仕様](#api仕様)
- [実装詳細](#実装詳細)
- [参考リンク](#参考リンク)

## 概要

PPT Generator機能は、PowerPointファイルのダウンロード、スライド選択エクスポート、画像抽出、質問データ変換、アップロードなど、プレゼンテーションファイルに関する包括的な操作を提供します。

### 主要コンポーネント

```text
PPT Generator機能
├── スキーマ（schemas/）
│   └── ppt_generator.py - リクエスト/レスポンス定義
├── サービス（services/）
│   ├── ppt_generator.py - ビジネスロジック
│   └── storage.py - ストレージ統合
└── API（api/routes/v1/）
    └── ppt_generator.py - RESTful エンドポイント
```

### 依存ライブラリ

- **python-pptx**: PowerPointファイルの生成・編集
- **Pillow (PIL)**: スライド画像の生成
- **pandas**: Excel→CSV変換
- **openpyxl**: Excelファイル読み込み

## 機能説明

### 1. PPTファイルダウンロード

- パッケージ/フェーズ/テンプレート指定でPPTXファイルを取得
- Azure Blob Storage / ローカルストレージから読み込み
- ブラウザで直接ダウンロード可能な形式で返却

### 2. 選択スライドエクスポート

- カンマ区切りのスライド番号指定（例: "1,3,5,7"）
- 指定されたスライドのみを含む新しいPPTXファイルを生成
- 元のフォーマット・レイアウトを維持

### 3. スライド画像取得

- 指定されたスライド番号のPNG画像を生成
- プレビュー表示やサムネイル生成に使用
- 高解像度画像のサポート

### 4. 質問データダウンロード

- Excelファイルの特定シートをCSV形式に変換
- 質問タイプ（シート名）を指定して取得
- UTF-8エンコーディングで出力

### 5. PPTファイルアップロード

- PPTXファイルのアップロードと保存
- ファイルサイズ・拡張子の検証
- ストレージパスとメタデータの返却

## アーキテクチャ

### サービス構造

::: mermaid
graph TB
    Client[クライアント<br/>ブラウザ]
    API[API層<br/>FastAPI Router]
    Service[サービス層<br/>PPTGeneratorService]
    Storage[ストレージ層<br/>Azure Blob / Local]
    PPTX[python-pptx<br/>ライブラリ]
    PIL[Pillow<br/>画像処理]
    Pandas[pandas<br/>データ処理]

    Client -->|HTTP Request| API
    API -->|ビジネスロジック| Service
    Service -->|ファイル読込| Storage
    Service -->|PPT操作| PPTX
    Service -->|画像生成| PIL
    Service -->|CSV変換| Pandas

    style Client fill:#81d4fa
    style API fill:#ffb74d
    style Service fill:#ce93d8
    style Storage fill:#fff176
    style PPTX fill:#81c784
    style PIL fill:#f06292
    style Pandas fill:#ce93d8
:::

### ストレージパス構造

```text
storage_root/
├── {package}/
│   ├── {phase}/
│   │   ├── {template}/
│   │   │   ├── presentation.pptx
│   │   │   ├── questions.xlsx
│   │   │   └── slides/
│   │   │       ├── slide_001.png
│   │   │       ├── slide_002.png
│   │   │       └── ...
```

## データフロー

### PPTダウンロードフロー

::: mermaid
sequenceDiagram
    participant C as クライアント
    participant API as FastAPI Router
    participant S as PPTGeneratorService
    participant ST as Storage
    participant Blob as Azure Blob Storage

    C->>+API: GET /ppt/download?<br/>package&phase&template
    API->>+S: download_ppt()

    S->>S: ストレージパス構築<br/>{package}/{phase}/{template}.pptx

    S->>+ST: download(path)
    ST->>+Blob: get_blob_client().download_blob()
    Blob-->>-ST: blob_bytes
    ST-->>-S: pptx_bytes

    S-->>-API: pptx_bytes
    API-->>-C: Response<br/>Content-Type: application/vnd...<br/>Content-Disposition: attachment

    style C fill:#81d4fa
    style API fill:#ffb74d
    style S fill:#ce93d8
    style ST fill:#fff176
    style Blob fill:#64b5f6
:::

### スライドエクスポートフロー

::: mermaid
sequenceDiagram
    participant C as クライアント
    participant API as FastAPI Router
    participant S as PPTGeneratorService
    participant PPTX as python-pptx
    participant ST as Storage

    C->>+API: GET /ppt/export-slides?<br/>slide_numbers=1,3,5
    API->>+S: export_selected_slides()

    S->>+ST: download(pptx_path)
    ST-->>-S: pptx_bytes

    S->>+PPTX: Presentation(BytesIO(pptx_bytes))
    PPTX-->>-S: presentation

    S->>S: スライド番号パース<br/>[1, 3, 5] → [0, 2, 4]

    loop 削除対象スライド（逆順）
        S->>PPTX: 不要スライド削除<br/>drop_rel() + del slides[i]
    end

    S->>S: BytesIOに保存<br/>presentation.save(output)

    S-->>-API: new_pptx_bytes
    API-->>-C: Response<br/>Content-Disposition: attachment

    style C fill:#81d4fa
    style API fill:#ffb74d
    style S fill:#ce93d8
    style PPTX fill:#81c784
    style ST fill:#fff176
:::

### スライド画像生成フロー

::: mermaid
sequenceDiagram
    participant C as クライアント
    participant API as FastAPI Router
    participant S as PPTGeneratorService
    participant ST as Storage

    C->>+API: GET /ppt/slide-image?<br/>slide_number=5
    API->>+S: get_slide_image()

    S->>S: 画像パス構築<br/>{pkg}/{phase}/{tpl}/slides/slide_{num:03d}.png

    S->>+ST: download(image_path)
    ST-->>-S: image_bytes

    S-->>-API: image_bytes
    API-->>-C: Response<br/>Content-Type: image/png

    Note over C,ST: 画像が存在しない場合は<br/>PPTXから動的生成することも可能
:::

### 質問データ変換フロー

::: mermaid
sequenceDiagram
    participant C as クライアント
    participant API as FastAPI Router
    participant S as PPTGeneratorService
    participant ST as Storage
    participant PD as pandas

    C->>+API: GET /ppt/questions?<br/>question_type=customer_survey
    API->>+S: download_question()

    S->>S: Excelパス構築<br/>{pkg}/{phase}/{tpl}/questions.xlsx

    S->>+ST: download(excel_path)
    ST-->>-S: excel_bytes

    S->>+PD: read_excel(BytesIO(excel_bytes),<br/>sheet_name=question_type)
    PD-->>-S: DataFrame

    S->>PD: to_csv(index=False)
    PD-->>S: csv_string

    S-->>-API: csv_bytes
    API-->>-C: Response<br/>Content-Type: text/csv<br/>Content-Disposition: attachment
:::

## 使用方法

### 1. PPTファイルのダウンロード

```python
import httpx

async with httpx.AsyncClient() as client:
    response = await client.get(
        "http://localhost:8000/api/v1/ppt/download",
        params={
            "package": "market-analysis",
            "phase": "phase1",
            "template": "template_a"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    # ファイルとして保存
    with open("presentation.pptx", "wb") as f:
        f.write(response.content)
```

### 2. 選択スライドのエクスポート

```python
response = await client.get(
    "http://localhost:8000/api/v1/ppt/export-slides",
    params={
        "package": "market-analysis",
        "phase": "phase1",
        "template": "template_a",
        "slide_numbers": "1,3,5,7"  # 1, 3, 5, 7番目のスライドのみ
    },
    headers={"Authorization": f"Bearer {token}"}
)

with open("selected_slides.pptx", "wb") as f:
    f.write(response.content)
```

### 3. スライド画像の取得

```python
response = await client.get(
    "http://localhost:8000/api/v1/ppt/slide-image",
    params={
        "package": "market-analysis",
        "phase": "phase1",
        "template": "template_a",
        "slide_number": 5  # 5番目のスライド
    },
    headers={"Authorization": f"Bearer {token}"}
)

# PNG画像として保存
with open("slide_5.png", "wb") as f:
    f.write(response.content)
```

### 4. 質問データのダウンロード

```python
response = await client.get(
    "http://localhost:8000/api/v1/ppt/questions",
    params={
        "package": "market-analysis",
        "phase": "phase1",
        "template": "template_a",
        "question_type": "customer_survey"  # Excelシート名
    },
    headers={"Authorization": f"Bearer {token}"}
)

# CSVとして保存
with open("customer_survey.csv", "wb") as f:
    f.write(response.content)
```

### 5. PPTファイルのアップロード

```python
with open("new_presentation.pptx", "rb") as f:
    response = await client.post(
        "http://localhost:8000/api/v1/ppt/upload",
        files={
            "file": ("presentation.pptx", f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")
        },
        data={
            "package": "market-analysis",
            "phase": "phase1",
            "template": "template_a"
        },
        headers={"Authorization": f"Bearer {token}"}
    )

    result = response.json()
    print(f"Upload success: {result['success']}")
    print(f"File path: {result['file_path']}")
    print(f"File size: {result['file_size']} bytes")
```

## API仕様

### エンドポイント一覧

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/api/v1/ppt/download` | PPTファイルダウンロード |
| GET | `/api/v1/ppt/export-slides` | 選択スライドエクスポート |
| GET | `/api/v1/ppt/slide-image` | スライド画像取得 |
| GET | `/api/v1/ppt/questions` | 質問データダウンロード |
| POST | `/api/v1/ppt/upload` | PPTファイルアップロード |

### リクエストスキーマ

#### PPTDownloadRequest (Query Parameters)

```python
{
    "package": str,     # パッケージ名 (min_length=1, max_length=100)
    "phase": str,       # フェーズ名 (min_length=1, max_length=100)
    "template": str     # テンプレート名 (min_length=1, max_length=100)
}
```

#### PPTSlideExportRequest (Query Parameters)

```python
{
    "package": str,          # パッケージ名
    "phase": str,            # フェーズ名
    "template": str,         # テンプレート名
    "slide_numbers": str     # スライド番号 (pattern: r"^\d+(,\d+)*$")
}
```

#### PPTSlideImageRequest (Query Parameters)

```python
{
    "package": str,        # パッケージ名
    "phase": str,          # フェーズ名
    "template": str,       # テンプレート名
    "slide_number": int    # スライド番号 (ge=1, le=1000)
}
```

#### QuestionDownloadRequest (Query Parameters)

```python
{
    "package": str,         # パッケージ名
    "phase": str,           # フェーズ名
    "template": str,        # テンプレート名
    "question_type": str    # 質問タイプ (Excelシート名)
}
```

#### PPTUploadRequest (Form Data + File)

```python
{
    "package": str,      # パッケージ名 (Form data)
    "phase": str,        # フェーズ名 (Form data)
    "template": str,     # テンプレート名 (Form data)
    "file": UploadFile   # PPTXファイル (multipart/form-data)
}
```

### レスポンススキーマ

#### PPTUploadResponse

```python
{
    "success": bool,        # アップロード成功フラグ
    "file_path": str,       # ストレージパス
    "file_size": int        # ファイルサイズ（バイト）
}
```

## 実装詳細

### スライド削除の実装

選択スライドエクスポートでは、python-pptxの内部構造を直接操作してスライドを削除します：

```python
from pptx import Presentation
from io import BytesIO

# PPTXファイル読み込み
prs = Presentation(BytesIO(pptx_bytes))

# 選択されたスライドインデックス
selected_indices = {0, 2, 4}  # 1,3,5番目

# 逆順で削除（インデックスずれを防ぐ）
total_slides = len(prs.slides)
for i in reversed(range(total_slides)):
    if i not in selected_indices:
        # リレーションとスライドIDリストから削除
        rId = prs.slides._sldIdLst[i].rId
        prs.part.drop_rel(rId)
        del prs.slides._sldIdLst[i]

# 新しいファイルに保存
output = BytesIO()
prs.save(output)
return output.getvalue()
```

### デコレーター適用

すべてのサービスメソッドは以下のデコレーターを適用：

```python
@measure_performance    # パフォーマンス計測
@async_timeout(timeout=300)  # 5分タイムアウト
async def download_ppt(
    self, package: str, phase: str, template: str
) -> bytes:
    """PPTファイルダウンロード。"""
    logger.info("ppt_download_started", package=package, phase=phase)
    # ...処理...
```

### エラーハンドリング

カスタム例外を使用した明示的なエラー処理：

```python
try:
    pptx_bytes = await self.storage.download(container, pptx_path)
except Exception as e:
    logger.error("ppt_download_failed", error=str(e))
    raise NotFoundError(
        f"PPTファイルが見つかりません: {package}/{phase}/{template}"
    )
```

### ロギング

structlogによる構造化ログ：

```python
import structlog

logger = structlog.get_logger(__name__)

logger.info(
    "slide_export_completed",
    package=package,
    selected_count=len(selected_indices),
    total_slides=total_slides
)
```

## 参考リンク

### プロジェクト内リンク

- [レイヤードアーキテクチャ](../../02-architecture/02-layered-architecture.md)
- [API設計](../../04-development/05-api-design/01-api-overview.md)
- [エラーハンドリング](../../04-development/05-api-design/06-error-responses.md)
- [ファイルアップロード実装](../04-file-upload/index.md)

### 関連ガイド

- [新しいエンドポイント追加](../01-add-endpoint/index.md)
- [データ分析機能](../09-analysis-feature/index.md)

### 外部リソース

- [python-pptx Documentation](https://python-pptx.readthedocs.io/)
- [Pillow Documentation](https://pillow.readthedocs.io/)
- [pandas Documentation](https://pandas.pydata.org/docs/)
- [FastAPI File Responses](https://fastapi.tiangolo.com/advanced/custom-response/#fileresponse)
