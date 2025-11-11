# ツール設定

開発に使用するツールとその設定について説明します。

## 概要

本プロジェクトでは以下のツールを使用します：

- **Ruff** - 高速なPythonリンター/フォーマッター
- **pytest** - テストフレームワーク
- **VSCode** - 推奨エディタ

---

## 1. Ruff

### 概要

Ruffは、RustベースファイルのPythonリンター/フォーマッターです。従来のFlake8、Black、isortを統合し、高速に動作します。

### インストール

```powershell
# uvを使用している場合
uv add --dev ruff

# または直接インストール
pip install ruff
```

### 設定

プロジェクトの`pyproject.toml`に設定を記述しています：

```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
]
ignore = []

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 使用方法

#### リント実行

```powershell
# すべてのファイルをチェック
ruff check .

# 特定のディレクトリをチェック
ruff check src\

# 自動修正
ruff check --fix .
```

#### フォーマット実行

```powershell
# すべてのファイルをフォーマット
ruff format .

# 特定のディレクトリをフォーマット
ruff format src\

# チェックのみ（変更しない）
ruff format --check .
```

#### CIでの使用

```powershell
# リントとフォーマットの両方をチェック
ruff check . && ruff format --check .
```

### よく使うルール

| ルール | 説明 |
|-------|------|
| E | pycodestyleエラー（インデント、空白など） |
| W | pycodestyle警告 |
| F | pyflakes（未使用変数、importなど） |
| I | isort（import文の整理） |
| B | flake8-bugbear（よくあるバグパターン） |
| C4 | flake8-comprehensions（リスト内包表記の改善） |
| UP | pyupgrade（新しいPython構文への変換） |

---

## 2. pytest

### 概要

pytestは、Pythonの強力なテストフレームワークです。

### インストール

```powershell
# uvを使用している場合
uv add --dev pytest pytest-asyncio

# または直接インストール
pip install pytest pytest-asyncio
```

### 設定

`pyproject.toml`に設定を記述：

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### ディレクトリ構造

```text
tests/
├── __init__.py
├── conftest.py           # 共通フィクスチャ
├── test_models.py        # モデルのテスト
├── test_repositories.py  # リポジトリのテスト
├── test_services.py      # サービスのテスト
└── test_api.py           # APIエンドポイントのテスト
```

### 基本的な使用方法

```powershell
# すべてのテストを実行
pytest

# 特定のファイルを実行
pytest tests\test_services.py

# 特定のテストを実行
pytest tests\test_services.py::test_create_user

# カバレッジレポート付きで実行
pytest --cov=src --cov-report=html

# 詳細な出力
pytest -v

# 失敗したテストのみ再実行
pytest --lf
```

### テストの書き方

#### 非同期テスト

```python
# tests/test_services.py
import pytest
from app.services.sample_user import SampleUserService
from app.schemas.sample_user import SampleUserCreate


@pytest.mark.asyncio
async def test_create_user(db_session):
    """ユーザー作成のテスト。"""
    # Arrange
    service = SampleUserService(db_session)
    user_data = SampleUserCreate(
        email="test@example.com",
        username="testuser",
        password="password123"
    )

    # Act
    user = await service.create_user(user_data)

    # Assert
    assert user.email == "test@example.com"
    assert user.username == "testuser"
    assert user.hashed_password != "password123"  # ハッシュ化されている
    assert user.is_active is True
```

#### フィクスチャの使用

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from app.core.database import Base


@pytest.fixture
async def db_session():
    """テスト用データベースセッション。"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        yield session

    await engine.dispose()


@pytest.fixture
def user_data():
    """テスト用ユーザーデータ。"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "password123"
    }
```

---

## 3. VSCode設定

### 拡張機能

以下の拡張機能をインストール：

1. **Python** (ms-python.python)
2. **Pylance** (ms-python.vscode-pylance)
3. **Ruff** (charliermarsh.ruff)
4. **SQLTools** (mtxr.sqltools)

### settings.json

プロジェクトの`.vscode/settings.json`を作成：

```json
{
  // Python設定
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.languageServer": "Pylance",
  "python.analysis.typeCheckingMode": "basic",
  "python.analysis.autoImportCompletions": true,

  // Ruff設定
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": "explicit",
      "source.fixAll": "explicit"
    }
  },

  // エディタ設定
  "editor.rulers": [100],
  "editor.tabSize": 4,
  "editor.insertSpaces": true,
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,

  // ファイル除外
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/.pytest_cache": true,
    "**/.ruff_cache": true
  }
}
```

### launch.json

デバッグ設定（`.vscode/launch.json`）：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      }
    },
    {
      "name": "Python: pytest",
      "type": "debugpy",
      "request": "launch",
      "module": "pytest",
      "args": [
        "-v",
        "${file}"
      ],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### tasks.json

タスク設定（`.vscode/tasks.json`）：

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Ruff: Check",
      "type": "shell",
      "command": "ruff check .",
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Ruff: Format",
      "type": "shell",
      "command": "ruff format .",
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "pytest: Run All",
      "type": "shell",
      "command": "pytest -v",
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "Start Server",
      "type": "shell",
      "command": "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
      "options": {
        "env": {
          "PYTHONPATH": "${workspaceFolder}/src"
        }
      },
      "isBackground": true,
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
```

---

## 4. pre-commitフック（推奨）

### インストール

```bash
uv add --dev pre-commit
```

### 設定

`.pre-commit-config.yaml`を作成：

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

### 有効化

```bash
pre-commit install
```

これにより、コミット前に自動的にリントとフォーマットが実行されます。

---

## 5. 開発ワークフロー

### 日常的な開発フロー

```powershell
# 1. コード編集（VSCodeで保存時に自動フォーマット）

# 2. リントチェック
ruff check .

# 3. テスト実行
pytest

# 4. コミット（pre-commitフックが自動実行）
git add .
git commit -m "feat: add user authentication"
```

### CIでのチェック

```powershell
# リント
ruff check .

# フォーマットチェック
ruff format --check .

# テスト
pytest --cov=src --cov-report=xml

# 型チェック（mypy使用時）
mypy src\
```

---

## よくある問題と解決法

### 問題1: Ruffがimportを間違った順序に並べる

**解決法**: `pyproject.toml`でisort設定を調整

```toml
[tool.ruff.lint.isort]
known-first-party = ["app"]
```

### 問題2: VSCodeでPythonが見つからない

**解決法**: インタープリターパスを確認

1. Cmd/Ctrl + Shift + P
2. "Python: Select Interpreter"
3. `.venv/bin/python`を選択

### 問題3: pytestでimportエラー

**解決法**: PYTHONPATHを設定

```powershell
$env:PYTHONPATH="$env:PYTHONPATH;$PWD\src"
pytest
```

または`.env`ファイルに追加：

```ini
PYTHONPATH=.\src
```

---

## 参考リンク

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [pytest Documentation](https://docs.pytest.org/)
- [VSCode Python Documentation](https://code.visualstudio.com/docs/python/python-tutorial)
- [pre-commit](https://pre-commit.com/)

---

次のセクション: [02-layer-implementation/01-models.md](../02-layer-implementation/01-models.md)
