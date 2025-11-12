"""PPT Generatorサービスのテスト。

ビジネスロジックと検証のテストに焦点を当てます。
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.services.ppt_generator.ppt_generator import PPTGeneratorService


@pytest.fixture
def mock_storage_service():
    """モックストレージサービス。"""
    storage = AsyncMock()
    storage.download.return_value = b"mock pptx content"
    storage.exists.return_value = True
    storage.upload.return_value = True
    # list_blobs is used by find_file_in_directory
    storage.list_blobs.return_value = [
        "market-analysis/phase1/template_a/presentation.pptx",
        "market-analysis/phase1/template_a/questions.xlsx",
    ]
    return storage


@pytest.mark.asyncio
async def test_download_ppt_success(mock_storage_service, test_user, test_project):
    """PPTダウンロードの成功ケース。"""
    # Arrange
    service = PPTGeneratorService(mock_storage_service)

    # Act
    result = await service.download_ppt(
        package="market-analysis",
        phase="phase1",
        template="template_a",
    )

    # Assert
    assert result is not None
    assert isinstance(result, bytes)
    assert len(result) > 0

    # ストレージサービスが呼ばれたことを確認
    mock_storage_service.list_blobs.assert_called_once()
    mock_storage_service.download.assert_called_once()


@pytest.mark.asyncio
async def test_download_ppt_not_found(mock_storage_service, test_user, test_project):
    """存在しないPPTファイルのダウンロードエラー。"""
    # Arrange
    service = PPTGeneratorService(mock_storage_service)
    # ファイルが見つからない場合は空のリストを返す
    mock_storage_service.list_blobs.return_value = []

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.download_ppt(
            package="nonexistent",
            phase="phase1",
            template="template_a",
        )


@pytest.mark.asyncio
async def test_export_selected_slides_success(mock_storage_service, test_user, test_project):
    """選択されたスライドのエクスポート成功ケース。"""
    # Arrange
    service = PPTGeneratorService(mock_storage_service)

    # モックPPTXコンテンツ（実際のPowerPointファイル構造を簡易的にモック）
    with patch("app.services.ppt_generator.Presentation") as mock_prs:
        mock_presentation = MagicMock()
        mock_slides = MagicMock()
        mock_slides.__len__ = MagicMock(return_value=5)

        # _sldIdLst をモック
        mock_sldIdLst = []
        for i in range(5):
            mock_slide = MagicMock()
            mock_slide.rId = f"rId{i+1}"
            mock_sldIdLst.append(mock_slide)

        mock_slides._sldIdLst = mock_sldIdLst
        mock_presentation.slides = mock_slides
        mock_presentation.part = MagicMock()
        mock_presentation.save = MagicMock()
        mock_prs.return_value = mock_presentation

        # Act
        result = await service.export_selected_slides(
            package="market-analysis",
            phase="phase1",
            template="template_a",
            slide_numbers="1,3,5",
        )

        # Assert
        assert result is not None
        assert isinstance(result, bytes)



@pytest.mark.asyncio
async def test_get_slide_image_success(mock_storage_service, test_user, test_project):
    """スライド画像取得の成功ケース。"""
    # Arrange
    service = PPTGeneratorService(mock_storage_service)
    mock_image_data = b"PNG image data"
    mock_storage_service.download.return_value = mock_image_data

    # Act
    result = await service.get_slide_image(
        package="market-analysis",
        phase="phase1",
        template="template_a",
        slide_number=5,
    )

    # Assert
    assert result is not None
    assert isinstance(result, bytes)
    assert result == mock_image_data


@pytest.mark.asyncio
async def test_get_slide_image_not_found(mock_storage_service, test_user, test_project):
    """存在しないスライド画像の取得エラー。"""
    # Arrange
    service = PPTGeneratorService(mock_storage_service)
    mock_storage_service.download.side_effect = Exception("Image not found")

    # Act & Assert - get_slide_image catches Exception and raises ValidationError
    with pytest.raises(ValidationError):
        await service.get_slide_image(
            package="market-analysis",
            phase="phase1",
            template="template_a",
            slide_number=999,
        )


@pytest.mark.asyncio
async def test_download_question_success(mock_storage_service, test_user, test_project):
    """質問データダウンロードの成功ケース。"""
    # Arrange
    service = PPTGeneratorService(mock_storage_service)

    # モックExcelデータ
    mock_excel_data = b"mock excel content"
    mock_storage_service.download.return_value = mock_excel_data

    with patch("pandas.read_excel") as mock_read_excel:
        import pandas as pd

        mock_df = pd.DataFrame({
            "question": ["Q1", "Q2", "Q3"],
            "answer": ["A1", "A2", "A3"],
        })
        mock_read_excel.return_value = mock_df

        # Act - download_question returns tuple (content, filename)
        content, filename = await service.download_question(
            package="market-analysis",
            phase="phase1",
            template="template_a",
            question_type="customer_survey",
        )

        # Assert
        assert content is not None
        assert isinstance(content, bytes)
        assert isinstance(filename, str)
        assert "customer_survey" in filename


@pytest.mark.asyncio
async def test_download_question_not_found(mock_storage_service, test_user, test_project):
    """存在しない質問データのダウンロードエラー。"""
    # Arrange
    service = PPTGeneratorService(mock_storage_service)
    # ファイルが見つからない場合は空のリストを返す
    mock_storage_service.list_blobs.return_value = []

    # Act & Assert
    with pytest.raises(NotFoundError):
        await service.download_question(
            package="nonexistent",
            phase="phase1",
            template="template_a",
            question_type="customer_survey",
        )


@pytest.mark.asyncio
async def test_upload_ppt_success(mock_storage_service, test_user, test_project):
    """PPTアップロードの成功ケース。"""
    # Arrange
    service = PPTGeneratorService(mock_storage_service)
    ppt_content = b"mock pptx file content"

    # Act - upload_ppt returns tuple (path, size)
    file_path, file_size = await service.upload_ppt(
        package="market-analysis",
        phase="phase1",
        template="template_a",
        file_name="presentation.pptx",
        file_data=ppt_content,
    )

    # Assert
    assert isinstance(file_path, str)
    assert "presentation.pptx" in file_path
    assert file_size == len(ppt_content)

    # ストレージサービスが呼ばれたことを確認
    mock_storage_service.upload.assert_called_once()




@pytest.mark.asyncio
async def test_upload_ppt_storage_failure(mock_storage_service, test_user, test_project):
    """ストレージアップロード失敗のエラー。"""
    # Arrange
    service = PPTGeneratorService(mock_storage_service)
    mock_storage_service.upload.side_effect = Exception("Storage error")
    ppt_content = b"mock pptx content"

    # Act & Assert
    with pytest.raises(ValidationError):
        await service.upload_ppt(
            package="market-analysis",
            phase="phase1",
            template="template_a",
            file_name="presentation.pptx",
            file_data=ppt_content,
        )
