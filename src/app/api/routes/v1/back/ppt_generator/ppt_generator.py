"""Azure AD認証用PPT Generator APIエンドポイント。

このモジュールは、Azure AD認証に対応したPPT Generator機能のRESTful APIエンドポイントを定義します。
PPTファイルのダウンロード、スライドエクスポート、画像取得、質問データダウンロード、
ファイルアップロードなどの操作を提供します。

主な機能:
    - PPTファイルダウンロード（GET /api/v1/ppt/packages/{package}/phases/{phase}/templates/{template}/download）
    - 選択スライドエクスポート（GET /api/v1/ppt/packages/{package}/phases/{phase}/templates/{template}/export）
    - スライド画像取得（GET /api/v1/ppt/packages/{package}/phases/{phase}/templates/{template}/slides/{slide_number}/image）
    - 質問データダウンロード（GET /api/v1/ppt/packages/{package}/phases/{phase}/templates/{template}/questions）
    - PPTファイルアップロード（POST /api/v1/ppt/packages/{package}/phases/{phase}/templates/{template}）

セキュリティ:
    - Azure AD Bearer認証（本番環境）
    - モック認証（開発環境）

使用例:
    >>> # PPTダウンロード
    >>> GET /api/v1/ppt/packages/market-analysis/phases/phase1/templates/template_a/download
    >>> Authorization: Bearer <Azure_AD_Token>
"""

import urllib.parse

from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import Response

from app.api.core import CurrentUserAccountDep
from app.api.decorators import async_timeout, handle_service_errors
from app.core.exceptions import ValidationError
from app.core.logging import get_logger
from app.schemas import PPTUploadResponse
from app.services import PPTGeneratorService

logger = get_logger(__name__)

ppt_generator_router = APIRouter()


# ================================================================================
# 依存性注入ヘルパー
# ================================================================================


def get_ppt_generator_service() -> PPTGeneratorService:
    """PPT Generatorサービスインスタンスを生成します。

    Returns:
        PPTGeneratorService: 初期化されたPPT Generatorサービス
    """
    return PPTGeneratorService()


# ================================================================================
# GET Endpoints
# ================================================================================


@ppt_generator_router.get(
    "/packages/{package}/phases/{phase}/templates/{template}/download",
    summary="PPTファイルダウンロード",
    description="""
    PPTファイルをダウンロードします。

    **認証が必要です。**

    - 指定されたpackage/phase/template配下のPPTXファイルをダウンロード
    - タイムアウト: 5分

    パスパラメータ:
        - package: パッケージ名（必須）
        - phase: フェーズ名（必須）
        - template: テンプレート名（必須）
    """,
)
@handle_service_errors
@async_timeout(30.0)  # 30秒タイムアウト（ファイルダウンロード）
async def download_ppt(
    current_user: CurrentUserAccountDep,
    package: str,
    phase: str,
    template: str,
    ppt_service: PPTGeneratorService = Depends(get_ppt_generator_service),
) -> Response:
    """PPTファイルをダウンロードします。

    Args:
        package: パッケージ名
        phase: フェーズ名
        template: テンプレート名
        current_user: 認証済みユーザー（自動注入）
        ppt_service: PPT Generatorサービス（自動注入）

    Returns:
        Response: PPTファイル（application/vnd.openxmlformats-officedocument.presentationml.presentation）

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 404: ファイルが存在しない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/ppt/packages/market-analysis/phases/phase1/templates/template_a/download
        >>> Authorization: Bearer <Azure_AD_Token>
        >>>
        >>> # レスポンス (200 OK)
        >>> Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation
        >>> Content-Disposition: attachment; filename*=UTF-8''presentation.pptx

    Note:
        - タイムアウトは5分です
        - ファイル名はContent-Dispositionヘッダーに含まれます
    """
    logger.info(
        "PPTダウンロードリクエスト",
        package=package,
        phase=phase,
        template=template,
        user_id=str(current_user.id),
        action="download_ppt",
    )

    # PPTファイルをダウンロード
    content = await ppt_service.download_ppt(package, phase, template)

    # ファイル名を生成
    filename = f"{package}_{phase}_{template}.pptx"
    encoded_filename = urllib.parse.quote(filename)

    logger.info(
        "PPTをダウンロードしました",
        package=package,
        phase=phase,
        template=template,
        size=len(content),
    )

    return Response(
        content,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@ppt_generator_router.get(
    "/packages/{package}/phases/{phase}/templates/{template}/export",
    summary="選択スライドエクスポート",
    description="""
    選択されたスライドのみを含む新しいPPTファイルを生成してダウンロードします。

    **認証が必要です。**

    - 指定されたスライド番号のみを含むPPTXファイルを生成
    - スライド番号はカンマ区切りで指定（例: "1,3,5,7"）
    - タイムアウト: 5分

    パスパラメータ:
        - package: パッケージ名（必須）
        - phase: フェーズ名（必須）
        - template: テンプレート名（必須）

    クエリパラメータ:
        - slide_numbers: スライド番号のカンマ区切り（必須）
    """,
)
@handle_service_errors
@async_timeout(60.0)  # 60秒タイムアウト（PPT生成）
async def export_selected_slides(
    current_user: CurrentUserAccountDep,
    package: str,
    phase: str,
    template: str,
    slide_numbers: str = Query(..., pattern=r"^\d+(,\d+)*$", description="スライド番号のカンマ区切り（例: '1,3,5,7'）"),
    ppt_service: PPTGeneratorService = Depends(get_ppt_generator_service),
) -> Response:
    """選択されたスライドのみをエクスポートします。

    Args:
        package: パッケージ名
        phase: フェーズ名
        template: テンプレート名
        slide_numbers: スライド番号のカンマ区切り
        current_user: 認証済みユーザー（自動注入）
        ppt_service: PPT Generatorサービス（自動注入）

    Returns:
        Response: PPTファイル（選択されたスライドのみ）

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 404: ファイルが存在しない
            - 400: スライド番号の形式が不正
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/ppt/packages/market-analysis/phases/phase1/templates/template_a/export?slide_numbers=1,3,5,7
        >>> Authorization: Bearer <Azure_AD_Token>

    Note:
        - スライド番号は1から開始します
        - 存在しないスライド番号は無視されます
        - タイムアウトは5分です
    """
    logger.info(
        "スライドエクスポートリクエスト",
        package=package,
        phase=phase,
        template=template,
        slide_numbers=slide_numbers,
        user_id=str(current_user.id),
        action="export_selected_slides",
    )

    # 選択されたスライドをエクスポート
    content = await ppt_service.export_selected_slides(package, phase, template, slide_numbers)

    # ファイル名を生成
    filename = f"{package}_{phase}_{template}_selected.pptx"
    encoded_filename = urllib.parse.quote(filename)

    logger.info(
        "スライドをエクスポートしました",
        package=package,
        phase=phase,
        template=template,
        slide_numbers=slide_numbers,
        size=len(content),
    )

    return Response(
        content,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@ppt_generator_router.get(
    "/packages/{package}/phases/{phase}/templates/{template}/slides/{slide_number}/image",
    summary="スライド画像取得",
    description="""
    指定されたスライドを画像（PNG）として取得します。

    **認証が必要です。**

    - 事前に生成された画像を取得します
    - 画像パス: {package}/{phase}/{template}/img/XXX.png
    - タイムアウト: 3分

    パスパラメータ:
        - package: パッケージ名（必須）
        - phase: フェーズ名（必須）
        - template: テンプレート名（必須）
        - slide_number: スライド番号（必須、1から開始）
    """,
)
@handle_service_errors
@async_timeout(30.0)  # 30秒タイムアウト（画像取得）
async def get_slide_image(
    current_user: CurrentUserAccountDep,
    package: str,
    phase: str,
    template: str,
    slide_number: int,
    ppt_service: PPTGeneratorService = Depends(get_ppt_generator_service),
) -> Response:
    """スライドを画像として取得します。

    Args:
        package: パッケージ名
        phase: フェーズ名
        template: テンプレート名
        slide_number: スライド番号
        current_user: 認証済みユーザー（自動注入）
        ppt_service: PPT Generatorサービス（自動注入）

    Returns:
        Response: PNG画像

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 404: 画像が存在しない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/ppt/packages/market-analysis/phases/phase1/templates/template_a/slides/5/image
        >>> Authorization: Bearer <Azure_AD_Token>

    Note:
        - 画像は事前に生成されている必要があります
        - タイムアウトは3分です
    """
    logger.info(
        "スライド画像取得リクエスト",
        package=package,
        phase=phase,
        template=template,
        slide_number=slide_number,
        user_id=str(current_user.id),
        action="get_slide_image",
    )

    # スライド画像を取得
    content = await ppt_service.get_slide_image(package, phase, template, slide_number)

    # ファイル名を生成
    filename = f"{package}_{phase}_{template}_slide_{slide_number}.png"
    encoded_filename = urllib.parse.quote(filename)

    logger.info(
        "スライド画像を取得しました",
        package=package,
        phase=phase,
        template=template,
        slide_number=slide_number,
        size=len(content),
    )

    return Response(
        content,
        media_type="image/png",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


@ppt_generator_router.get(
    "/packages/{package}/phases/{phase}/templates/{template}/questions",
    summary="質問データダウンロード",
    description="""
    質問データをExcelからCSV形式でダウンロードします。

    **認証が必要です。**

    - ExcelファイルからCSVに変換してダウンロード
    - UTF-8 BOMエンコーディングで出力
    - タイムアウト: 5分

    パスパラメータ:
        - package: パッケージ名（必須）
        - phase: フェーズ名（必須）
        - template: テンプレート名（必須）

    クエリパラメータ:
        - question_type: 質問タイプ/シート名（必須）
    """,
)
@handle_service_errors
@async_timeout(30.0)  # 30秒タイムアウト（Excel→CSV変換）
async def download_questions(
    current_user: CurrentUserAccountDep,
    package: str,
    phase: str,
    template: str,
    question_type: str = Query(..., description="質問タイプ（Excelシート名）"),
    ppt_service: PPTGeneratorService = Depends(get_ppt_generator_service),
) -> Response:
    """質問データをダウンロードします。

    Args:
        package: パッケージ名
        phase: フェーズ名
        template: テンプレート名
        question_type: 質問タイプ（Excelシート名）
        current_user: 認証済みユーザー（自動注入）
        ppt_service: PPT Generatorサービス（自動注入）

    Returns:
        Response: CSVファイル

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 404: ファイルまたはシートが存在しない
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> GET /api/v1/ppt/packages/market-analysis/phases/phase1/templates/template_a/questions?question_type=customer_survey
        >>> Authorization: Bearer <Azure_AD_Token>

    Note:
        - ExcelファイルからCSVに変換されます
        - UTF-8 BOMエンコーディングで出力されます
        - タイムアウトは5分です
    """
    logger.info(
        "質問データダウンロードリクエスト",
        package=package,
        phase=phase,
        template=template,
        question_type=question_type,
        user_id=str(current_user.id),
        action="download_questions",
    )

    # 質問データをダウンロード
    content, filename = await ppt_service.download_question(package, phase, template, question_type)

    encoded_filename = urllib.parse.quote(filename)

    logger.info(
        "質問データをダウンロードしました",
        package=package,
        phase=phase,
        template=template,
        question_type=question_type,
        filename=filename,
        size=len(content),
    )

    return Response(
        content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
    )


# ================================================================================
# POST Endpoints
# ================================================================================


@ppt_generator_router.post(
    "/packages/{package}/phases/{phase}/templates/{template}",
    response_model=PPTUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="PPTファイルアップロード",
    description="""
    PPTファイルをアップロードします。

    **認証が必要です。**

    - multipart/form-dataでPPTXファイルをアップロード
    - タイムアウト: 5分

    パスパラメータ:
        - package: パッケージ名（必須）
        - phase: フェーズ名（必須）
        - template: テンプレート名（必須）

    フォームデータ:
        - file: PPTXファイル（必須）
    """,
)
@handle_service_errors
@async_timeout(60.0)  # 60秒タイムアウト（PPTアップロード）
async def upload_ppt(
    current_user: CurrentUserAccountDep,
    package: str,
    phase: str,
    template: str,
    file: UploadFile = File(..., description="PPTXファイル"),
    ppt_service: PPTGeneratorService = Depends(get_ppt_generator_service),
) -> PPTUploadResponse:
    """PPTファイルをアップロードします。

    Args:
        package: パッケージ名
        phase: フェーズ名
        template: テンプレート名
        file: アップロードファイル
        current_user: 認証済みユーザー（自動注入）
        ppt_service: PPT Generatorサービス（自動注入）

    Returns:
        PPTUploadResponse: アップロード結果

    Raises:
        HTTPException:
            - 401: 認証されていない
            - 400: ファイル形式が不正
            - 500: 内部エラー

    Example:
        >>> # リクエスト
        >>> POST /api/v1/ppt/packages/market-analysis/phases/phase1/templates/template_a
        >>> Authorization: Bearer <Azure_AD_Token>
        >>> Content-Type: multipart/form-data
        >>> file: presentation.pptx
        >>>
        >>> # レスポンス (201 Created)
        >>> {
        ...     "success": true,
        ...     "file_path": "market-analysis/phase1/template_a/presentation.pptx",
        ...     "file_size": 1024000
        ... }

    Note:
        - タイムアウトは5分です
        - 既存のファイルは上書きされます
    """
    logger.info(
        "PPTアップロードリクエスト",
        package=package,
        phase=phase,
        template=template,
        filename=file.filename,
        user_id=str(current_user.id),
        action="upload_ppt",
    )

    # ファイルデータを読み込み
    file_data = await file.read()

    # ファイル形式チェック
    if not file.filename or not file.filename.endswith(".pptx"):
        logger.warning(
            "不正なファイル形式",
            filename=file.filename,
        )
        raise ValidationError(
            "PPTXファイルのみアップロード可能です",
            details={"filename": file.filename},
        )

    # ファイルをアップロード
    file_path, file_size = await ppt_service.upload_ppt(package, phase, template, file.filename, file_data)

    logger.info(
        "PPTをアップロードしました",
        package=package,
        phase=phase,
        template=template,
        file_path=file_path,
        file_size=file_size,
    )

    return PPTUploadResponse(
        success=True,
        file_path=file_path,
        file_size=file_size,
    )
