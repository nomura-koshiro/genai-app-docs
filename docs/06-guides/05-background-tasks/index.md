# バックグラウンドタスク

このガイドでは、FastAPIのBackgroundTasksを使用した非同期バックグラウンド処理の実装方法を説明します。

## 目次

- [概要](#概要)
- [前提条件](#前提条件)
- [ステップバイステップ](#ステップバイステップ)
- [チェックリスト](#チェックリスト)
- [よくある落とし穴](#よくある落とし穴)
- [ベストプラクティス](#ベストプラクティス)
- [参考リンク](#参考リンク)

## 概要

バックグラウンドタスクは、リクエストのレスポンスを返した後に実行される処理です。以下のような用途に適しています：

- メール送信
- ファイル処理
- サムネイル生成
- ログ記録
- データベースクリーンアップ
- 通知送信

**FastAPI BackgroundTasksの特徴：**

- レスポンスを返した後に実行
- 同じプロセス内で実行（軽量タスク向け）
- リクエストコンテキストで実行
- エラーハンドリングが必要

**重要な制約：**

- 長時間実行タスクには不向き
- 複雑なタスクキューには CeleryやRQを検討
- タスクの失敗時に自動リトライなし

## 前提条件

- FastAPIの基礎知識
- 非同期プログラミング（async/await）の理解
- Pythonのデコレータパターンの理解

## ステップバイステップ

### 1. 基本的なバックグラウンドタスク

#### 1.1 シンプルなタスクの実装

```python
"""バックグラウンドタスクの例。"""

from fastapi import APIRouter, BackgroundTasks
from app.schemas.common import MessageResponse

router = APIRouter()


def write_log(message: str):
    """
    ログをファイルに書き込みます（同期関数）。

    Args:
        message: ログメッセージ
    """
    with open("log.txt", "a") as f:
        f.write(f"{message}\n")


@router.post("/send-notification")
async def send_notification(
    email: str,
    background_tasks: BackgroundTasks,
) -> MessageResponse:
    """
    通知を送信します（バックグラウンドでログ記録）。

    Args:
        email: メールアドレス
        background_tasks: バックグラウンドタスク

    Returns:
        成功メッセージ
    """
    # バックグラウンドタスクを追加
    background_tasks.add_task(write_log, f"Notification sent to {email}")

    # すぐにレスポンスを返す
    return MessageResponse(message="Notification will be sent")
```

#### 1.2 非同期タスクの実装

```python
"""非同期バックグラウンドタスク。"""

import asyncio
from datetime import datetime

from fastapi import BackgroundTasks


async def send_email_async(email: str, subject: str, body: str):
    """
    非同期でメールを送信します。

    Args:
        email: 送信先メールアドレス
        subject: 件名
        body: 本文
    """
    # メール送信をシミュレート
    print(f"Sending email to {email}")
    await asyncio.sleep(2)  # 送信処理
    print(f"Email sent to {email}")


@router.post("/register")
async def register_user(
    email: str,
    username: str,
    background_tasks: BackgroundTasks,
):
    """
    ユーザー登録とウェルカムメール送信。

    Args:
        email: メールアドレス
        username: ユーザー名
        background_tasks: バックグラウンドタスク

    Returns:
        登録成功メッセージ
    """
    # ユーザー登録処理
    # user = await create_user(email, username)

    # バックグラウンドでウェルカムメール送信
    background_tasks.add_task(
        send_email_async,
        email=email,
        subject="Welcome!",
        body=f"Hello {username}, welcome to our service!",
    )

    return {"message": "User registered successfully"}
```

### 2. 実践的なバックグラウンドタスク

#### 2.1 メール送信サービス

`src/app/services/email.py`を作成：

```python
"""メール送信サービス。"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """メール送信用サービス。"""

    def __init__(self):
        """メールサービスを初期化します。"""
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL

    async def send_email(
        self,
        to_email: str | List[str],
        subject: str,
        body: str,
        html: bool = False,
    ) -> None:
        """
        メールを送信します。

        Args:
            to_email: 送信先メールアドレス（複数可）
            subject: 件名
            body: 本文
            html: HTMLメールかどうか

        Raises:
            Exception: メール送信失敗時
        """
        try:
            # メッセージ作成
            message = MIMEMultipart()
            message["From"] = self.from_email
            message["Subject"] = subject

            # 複数の宛先に対応
            if isinstance(to_email, str):
                to_email = [to_email]
            message["To"] = ", ".join(to_email)

            # 本文設定
            if html:
                message.attach(MIMEText(body, "html"))
            else:
                message.attach(MIMEText(body, "plain"))

            # SMTP送信
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                use_tls=True,
            )

            logger.info(f"Email sent to {to_email}")

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            raise

    async def send_welcome_email(self, email: str, username: str) -> None:
        """
        ウェルカムメールを送信します。

        Args:
            email: メールアドレス
            username: ユーザー名
        """
        subject = "Welcome to Our Service!"
        body = f"""
        <html>
          <body>
            <h1>Hello {username}!</h1>
            <p>Thank you for registering with our service.</p>
            <p>We're excited to have you on board!</p>
          </body>
        </html>
        """
        await self.send_email(email, subject, body, html=True)

    async def send_password_reset_email(
        self, email: str, reset_token: str
    ) -> None:
        """
        パスワードリセットメールを送信します。

        Args:
            email: メールアドレス
            reset_token: リセットトークン
        """
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        subject = "Password Reset Request"
        body = f"""
        <html>
          <body>
            <h1>Password Reset</h1>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_url}">{reset_url}</a>
            <p>This link will expire in 1 hour.</p>
          </body>
        </html>
        """
        await self.send_email(email, subject, body, html=True)


# シングルトンインスタンス
email_service = EmailService()
```

#### 2.2 バックグラウンドタスクヘルパー

`src/app/core/background_tasks.py`を作成：

```python
"""バックグラウンドタスクユーティリティ。"""

import logging
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def background_task_with_logging(func: Callable) -> Callable:
    """
    バックグラウンドタスクにログ記録を追加するデコレータ。

    Args:
        func: ラップする関数

    Returns:
        ラップされた関数
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        """ラッパー関数。"""
        task_name = func.__name__
        logger.info(f"Background task started: {task_name}")

        try:
            result = await func(*args, **kwargs)
            logger.info(f"Background task completed: {task_name}")
            return result

        except Exception as e:
            logger.error(f"Background task failed: {task_name}, Error: {e}")
            raise

    return wrapper


def background_task_with_retry(
    max_retries: int = 3, delay: float = 1.0
) -> Callable:
    """
    リトライ機能付きバックグラウンドタスクデコレータ。

    Args:
        max_retries: 最大リトライ回数
        delay: リトライ間隔（秒）

    Returns:
        デコレータ関数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """ラッパー関数。"""
            import asyncio

            task_name = func.__name__
            last_exception = None

            for attempt in range(max_retries):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            f"Background task succeeded on retry {attempt}: {task_name}"
                        )
                    return result

                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Background task failed (attempt {attempt + 1}/{max_retries}): "
                        f"{task_name}, Error: {e}"
                    )

                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))  # 指数バックオフ

            logger.error(
                f"Background task failed after {max_retries} retries: {task_name}"
            )
            raise last_exception

        return wrapper

    return decorator
```

#### 2.3 実践的な使用例

`src/app/api/routes/sample_users.py`：

```python
"""ユーザーAPIルート（バックグラウンドタスク付き）。"""

from fastapi import APIRouter, BackgroundTasks

from app.core.background_tasks import (
    background_task_with_logging,
    background_task_with_retry,
)
from app.schemas.sample_user import SampleUserCreate, SampleUserResponse
from app.services.email import email_service

router = APIRouter()


@background_task_with_logging
@background_task_with_retry(max_retries=3)
async def send_welcome_email_task(email: str, username: str):
    """
    ウェルカムメール送信タスク（リトライ・ログ付き）。

    Args:
        email: メールアドレス
        username: ユーザー名
    """
    await email_service.send_welcome_email(email, username)


@background_task_with_logging
async def update_user_stats_task(user_id: int):
    """
    ユーザー統計更新タスク。

    Args:
        user_id: ユーザーID
    """
    # 統計更新処理
    # await stats_service.update_user_stats(user_id)
    pass


@router.post("/", response_model=SampleUserResponse)
async def create_user(
    user_data: SampleUserCreate,
    background_tasks: BackgroundTasks,
):
    """
    ユーザーを作成します。

    - ウェルカムメールをバックグラウンドで送信
    - ユーザー統計を非同期で更新

    Args:
        user_data: ユーザー作成データ
        background_tasks: バックグラウンドタスク

    Returns:
        作成されたユーザー情報
    """
    # ユーザー作成
    # user = await user_service.create_user(user_data)

    # バックグラウンドタスクを追加
    background_tasks.add_task(
        send_welcome_email_task,
        email=user_data.email,
        username=user_data.username,
    )

    background_tasks.add_task(
        update_user_stats_task,
        user_id=user.id,
    )

    return user
```

### 3. 画像処理のバックグラウンドタスク

#### 3.1 サムネイル生成

`src/app/services/image.py`を作成：

```python
"""画像処理サービス。"""

import io
from pathlib import Path

from PIL import Image

from app.storage import get_storage_backend


class ImageService:
    """画像処理用サービス。"""

    def __init__(self):
        """画像サービスを初期化します。"""
        self.storage = get_storage_backend()

    async def generate_thumbnail(
        self,
        source_path: str,
        thumbnail_path: str,
        size: tuple[int, int] = (150, 150),
    ) -> None:
        """
        サムネイルを生成します。

        Args:
            source_path: 元画像のパス
            thumbnail_path: サムネイル保存先パス
            size: サムネイルサイズ (width, height)
        """
        # 元画像を読み込み
        image_data = await self.storage.load(source_path)
        image = Image.open(io.BytesIO(image_data))

        # サムネイル生成
        image.thumbnail(size, Image.Resampling.LANCZOS)

        # バイトに変換
        thumbnail_io = io.BytesIO()
        image.save(thumbnail_io, format=image.format or "JPEG")
        thumbnail_data = thumbnail_io.getvalue()

        # 保存
        await self.storage.save(thumbnail_path, thumbnail_data)

    async def generate_multiple_sizes(
        self,
        source_path: str,
        base_name: str,
        sizes: dict[str, tuple[int, int]] = None,
    ) -> dict[str, str]:
        """
        複数サイズのサムネイルを生成します。

        Args:
            source_path: 元画像のパス
            base_name: ベースファイル名
            sizes: サイズ辞書 {"small": (150, 150), ...}

        Returns:
            サイズ名とパスの辞書
        """
        if sizes is None:
            sizes = {
                "thumbnail": (150, 150),
                "small": (300, 300),
                "medium": (600, 600),
                "large": (1200, 1200),
            }

        results = {}
        extension = Path(source_path).suffix

        for size_name, (width, height) in sizes.items():
            thumbnail_path = f"{base_name}_{size_name}{extension}"
            await self.generate_thumbnail(
                source_path, thumbnail_path, (width, height)
            )
            results[size_name] = thumbnail_path

        return results


# シングルトンインスタンス
image_service = ImageService()
```

#### 3.2 画像アップロードAPI

`src/app/api/routes/images.py`：

```python
"""画像アップロードAPIルート。"""

from fastapi import APIRouter, BackgroundTasks, File, UploadFile

from app.core.background_tasks import background_task_with_logging
from app.schemas.file import FileUploadResponse
from app.services.sample_file import SampleFileService
from app.services.image import image_service

router = APIRouter()


@background_task_with_logging
async def generate_thumbnails_task(file_id: str, storage_path: str):
    """
    サムネイル生成バックグラウンドタスク。

    Args:
        file_id: ファイルID
        storage_path: ストレージパス
    """
    await image_service.generate_multiple_sizes(
        source_path=storage_path,
        base_name=file_id,
    )


@router.post("/upload", response_model=FileUploadResponse)
async def upload_image(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    file_service: FileService = None,
):
    """
    画像をアップロードし、バックグラウンドでサムネイルを生成します。

    Args:
        file: アップロードする画像
        background_tasks: バックグラウンドタスク
        file_service: ファイルサービス

    Returns:
        アップロードされた画像情報
    """
    # 画像をアップロード
    db_file = await file_service.upload_file(file)

    # バックグラウンドでサムネイル生成
    background_tasks.add_task(
        generate_thumbnails_task,
        file_id=db_file.file_id,
        storage_path=db_file.storage_path,
    )

    return FileUploadResponse(
        file_id=db_file.file_id,
        filename=db_file.original_filename,
        size=db_file.size,
        content_type=db_file.content_type,
        message="Image uploaded, thumbnails are being generated",
    )
```

### 4. データクリーンアップタスク

#### 4.1 定期クリーンアップ

`src/app/tasks/cleanup.py`を作成：

```python
"""データクリーンアップタスク。"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.sample_file import SampleFile
from app.models.sample_session import SampleSession
from app.storage import get_storage_backend

logger = logging.getLogger(__name__)


async def cleanup_old_sessions(days: int = 30):
    """
    古いセッションを削除します。

    Args:
        days: 削除する日数の閾値
    """
    async for db in get_db():
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        # 古いセッションを取得
        query = select(SampleSession).where(Session.updated_at < cutoff_date)
        result = await db.execute(query)
        old_sessions = result.scalars().all()

        # 削除
        for session in old_sessions:
            await db.delete(session)

        await db.commit()
        logger.info(f"Deleted {len(old_sessions)} old sessions")


async def cleanup_orphaned_files():
    """
    孤立したファイル（DBレコードなし）を削除します。
    """
    storage = get_storage_backend()

    async for db in get_db():
        # ストレージの全ファイルを取得
        storage_files = await storage.list_files()

        # DBの全ファイルIDを取得
        query = select(File.file_id)
        result = await db.execute(query)
        db_file_ids = {row[0] for row in result.all()}

        # 孤立ファイルを削除
        deleted_count = 0
        for file_info in storage_files:
            file_id = file_info["file_id"]
            if file_id not in db_file_ids:
                try:
                    await storage.delete(file_id)
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete orphaned file {file_id}: {e}")

        logger.info(f"Deleted {deleted_count} orphaned files")
```

#### 4.2 スケジューラー統合（APScheduler）

`src/app/scheduler.py`を作成：

```python
"""バックグラウンドタスクスケジューラー。"""

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.tasks.cleanup import cleanup_old_sessions, cleanup_orphaned_files

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def setup_scheduler():
    """スケジューラーをセットアップします。"""
    # 毎日午前2時に古いセッションを削除
    scheduler.add_job(
        cleanup_old_sessions,
        "cron",
        hour=2,
        minute=0,
        id="cleanup_old_sessions",
    )

    # 毎週日曜日午前3時に孤立ファイルを削除
    scheduler.add_job(
        cleanup_orphaned_files,
        "cron",
        day_of_week="sun",
        hour=3,
        minute=0,
        id="cleanup_orphaned_files",
    )

    logger.info("Scheduler configured")


def start_scheduler():
    """スケジューラーを開始します。"""
    setup_scheduler()
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    """スケジューラーを停止します。"""
    scheduler.shutdown()
    logger.info("Scheduler stopped")
```

`src/app/main.py`にスケジューラーを追加：

```python
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフスパンマネージャー。"""
    # Startup
    await init_db()
    start_scheduler()  # スケジューラー開始

    yield

    # Shutdown
    stop_scheduler()  # スケジューラー停止
    await close_db()
```

## チェックリスト

バックグラウンドタスク実装のチェックリスト：

- [ ] BackgroundTasksの依存性注入
- [ ] 非同期タスク関数の実装
- [ ] エラーハンドリングの実装
- [ ] ログ記録の追加
- [ ] リトライロジックの実装（必要な場合）
- [ ] タスクのテスト
- [ ] パフォーマンステスト
- [ ] タイムアウト設定
- [ ] メモリ使用量のモニタリング
- [ ] 定期実行タスクのスケジューラー設定

## よくある落とし穴

### 1. 長時間実行タスク

```python
# 悪い例（レスポンスタイムアウト）
@router.post("/process")
async def process_data(background_tasks: BackgroundTasks):
    # 重い処理を同期的に実行
    result = heavy_processing()  # 30秒かかる
    return {"result": result}

# 良い例
@router.post("/process")
async def process_data(background_tasks: BackgroundTasks):
    # バックグラウンドで実行
    background_tasks.add_task(heavy_processing)
    return {"message": "Processing started"}
```

### 2. エラーハンドリング不足

```python
# 悪い例（エラーが隠蔽される）
async def send_email(email: str):
    # エラーハンドリングなし
    await email_service.send(email)

# 良い例
async def send_email(email: str):
    try:
        await email_service.send(email)
    except Exception as e:
        logger.error(f"Failed to send email to {email}: {e}")
        # 必要に応じてリトライや通知
```

### 3. データベースセッションの誤用

```python
# 悪い例（セッションがクローズされている）
@router.post("/create")
async def create_item(db: AsyncSession, background_tasks: BackgroundTasks):
    item = await create_item_in_db(db)
    # dbセッションは既にクローズされている
    background_tasks.add_task(update_item_stats, db, item.id)
    return item

# 良い例
@router.post("/create")
async def create_item(db: AsyncSession, background_tasks: BackgroundTasks):
    item = await create_item_in_db(db)
    # IDのみを渡す
    background_tasks.add_task(update_item_stats, item.id)
    return item

async def update_item_stats(item_id: int):
    # 新しいセッションを取得
    async for db in get_db():
        # 処理
        pass
```

### 4. メモリリーク

```python
# 悪い例（大きなオブジェクトを保持）
large_data = load_large_data()
background_tasks.add_task(process_data, large_data)

# 良い例（参照のみを渡す）
data_id = save_data_to_temp()
background_tasks.add_task(process_data, data_id)
```

## ベストプラクティス

### 1. タスクの分離

```python
# タスク関数を独立させる
# src/app/tasks/email_tasks.py
async def send_welcome_email_task(email: str, username: str):
    pass

# API層では呼び出すだけ
from app.tasks.email_tasks import send_welcome_email_task

background_tasks.add_task(send_welcome_email_task, email, username)
```

### 2. ログとモニタリング

```python
@background_task_with_logging
async def important_task():
    logger.info("Task started")
    # 処理
    logger.info("Task completed")
```

### 3. 冪等性の確保

```python
# 同じタスクを複数回実行しても安全に
async def send_notification(user_id: int, notification_id: str):
    # 既に送信済みかチェック
    if await is_notification_sent(notification_id):
        return

    # 通知送信
    await send_notification_to_user(user_id)

    # 送信済みフラグを設定
    await mark_notification_sent(notification_id)
```

### 4. 適切なタイムアウト

```python
import asyncio

async def task_with_timeout():
    try:
        async with asyncio.timeout(30):  # 30秒タイムアウト
            await long_running_task()
    except asyncio.TimeoutError:
        logger.error("Task timed out")
```

## 参考リンク

### 公式ドキュメント

- [FastAPI Background Tasks](https://fastapi.tiangolo.com/tutorial/background-tasks/)
- [APScheduler](https://apscheduler.readthedocs.io/)
- [Celery](https://docs.celeryq.dev/) - より高度なタスクキュー

### プロジェクト内リンク

- [ファイルアップロード](./04-file-upload.md)
- [エラーハンドリング](../03-core-concepts/04-error-handling.md)
- [ログ設定](../03-core-concepts/03-logging.md)

### 関連ガイド

- [新しいエンドポイント追加](./01-add-endpoint.md)
- [デプロイメント](./06-deployment.md)
