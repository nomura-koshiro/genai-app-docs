FROM python:3.13-slim

# 非ルートユーザの作成
# 参考：https://github.com/astral-sh/uv-docker-example/blob/main/Dockerfile
RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

WORKDIR /app

# uvのインストール
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 依存関係のインストール
# 依存関係に変更がない場合に再利用するため、ソースコードより先にコピーしておく
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-editable

# ソースコードをコピー
COPY --chown=nonroot:nonroot . .

EXPOSE 8000

USER nonroot

ENV PYTHONPATH=/app/src:$PYTHONPATH

CMD [".venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
