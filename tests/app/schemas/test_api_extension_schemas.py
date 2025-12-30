"""API拡張スキーマのユニットテスト。

このテストファイルは 07-api-extensions.md の実装に対するスキーマユニットテストです。

テスト対象:
    - ValidationInfo (analysis_session.py)
    - TreePolicyItem (driver_tree.py)
    - TreePoliciesResponse (driver_tree.py)
    - ColumnInfo (driver_tree_file.py)
    - SheetDetailResponse (driver_tree_file.py)
"""

import uuid

import pytest
from pydantic import ValidationError

from app.schemas.analysis.analysis_session import ValidationInfo
from app.schemas.driver_tree.driver_tree import TreePoliciesResponse, TreePolicyItem
from app.schemas.driver_tree.driver_tree_file import ColumnInfo, SheetDetailResponse


# ================================================================================
# ValidationInfo (analysis_session.py) のテスト
# ================================================================================
class TestValidationInfo:
    """ValidationInfo スキーマのテスト。"""

    def test_create_validation_info_success(self):
        """[test_api_extension_schemas-001] ValidationInfo作成の成功ケース。"""
        # Arrange & Act
        validation_id = uuid.uuid4()
        validation = ValidationInfo(id=validation_id, name="売上分析")

        # Assert
        assert validation.id == validation_id
        assert validation.name == "売上分析"

    def test_validation_info_field_types(self):
        """[test_api_extension_schemas-002] ValidationInfoのフィールド型検証。"""
        # Arrange & Act
        validation_id = uuid.uuid4()
        validation = ValidationInfo(id=validation_id, name="コスト分析")

        # Assert
        assert isinstance(validation.id, uuid.UUID)
        assert isinstance(validation.name, str)

    def test_validation_info_required_fields(self):
        """[test_api_extension_schemas-003] ValidationInfoの必須フィールド検証。"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ValidationInfo()  # idとnameが必須

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        assert "id" in error_fields
        assert "name" in error_fields

    def test_validation_info_invalid_id_type(self):
        """[test_api_extension_schemas-004] ValidationInfoの不正なID型検証。"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError):
            ValidationInfo(
                id="invalid-uuid-string",  # 文字列はUUID型に変換できない
                name="テスト",
            )


# ================================================================================
# TreePolicyItem (driver_tree.py) のテスト
# ================================================================================
class TestTreePolicyItem:
    """TreePolicyItem スキーマのテスト。"""

    def test_create_tree_policy_item_success(self):
        """[test_api_extension_schemas-005] TreePolicyItem作成の成功ケース。"""
        # Arrange & Act
        policy_id = uuid.uuid4()
        node_id = uuid.uuid4()
        policy = TreePolicyItem(
            policy_id=policy_id,
            node_id=node_id,
            node_label="売上",
            label="売上向上施策",
            description="新商品投入による売上向上",
            impact_type="multiply",
            impact_value=1.2,
            status="active",
        )

        # Assert
        assert policy.policy_id == policy_id
        assert policy.node_id == node_id
        assert policy.node_label == "売上"
        assert policy.label == "売上向上施策"
        assert policy.description == "新商品投入による売上向上"
        assert policy.impact_type == "multiply"
        assert policy.impact_value == 1.2
        assert policy.status == "active"

    def test_tree_policy_item_default_status(self):
        """[test_api_extension_schemas-006] TreePolicyItemのデフォルトstatus検証。"""
        # Arrange & Act
        policy = TreePolicyItem(
            policy_id=uuid.uuid4(), node_id=uuid.uuid4(), node_label="売上", label="テスト施策", impact_type="add", impact_value=100.0
        )

        # Assert
        assert policy.status == "active"  # デフォルト値

    def test_tree_policy_item_optional_description(self):
        """[test_api_extension_schemas-007] TreePolicyItemのオプションフィールド検証。"""
        # Arrange & Act
        policy = TreePolicyItem(
            policy_id=uuid.uuid4(),
            node_id=uuid.uuid4(),
            node_label="売上",
            label="テスト施策",
            impact_type="add",
            impact_value=100.0,
            # description は省略
        )

        # Assert
        assert policy.description is None

    def test_tree_policy_item_required_fields(self):
        """[test_api_extension_schemas-008] TreePolicyItemの必須フィールド検証。"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TreePolicyItem()

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        # 必須フィールド
        assert "policy_id" in error_fields
        assert "node_id" in error_fields
        assert "node_label" in error_fields
        assert "label" in error_fields
        assert "impact_type" in error_fields
        assert "impact_value" in error_fields


# ================================================================================
# TreePoliciesResponse (driver_tree.py) のテスト
# ================================================================================
class TestTreePoliciesResponse:
    """TreePoliciesResponse スキーマのテスト。"""

    def test_create_tree_policies_response_success(self):
        """[test_api_extension_schemas-009] TreePoliciesResponse作成の成功ケース。"""
        # Arrange
        tree_id = uuid.uuid4()
        policy1 = TreePolicyItem(
            policy_id=uuid.uuid4(), node_id=uuid.uuid4(), node_label="売上", label="施策1", impact_type="add", impact_value=100.0
        )
        policy2 = TreePolicyItem(
            policy_id=uuid.uuid4(), node_id=uuid.uuid4(), node_label="コスト", label="施策2", impact_type="multiply", impact_value=0.9
        )

        # Act
        response = TreePoliciesResponse(tree_id=tree_id, policies=[policy1, policy2], total_count=2)

        # Assert
        assert response.tree_id == tree_id
        assert len(response.policies) == 2
        assert response.total_count == 2
        assert response.policies[0].label == "施策1"
        assert response.policies[1].label == "施策2"

    def test_tree_policies_response_empty_policies(self):
        """[test_api_extension_schemas-010] TreePoliciesResponseの空の施策リスト検証。"""
        # Arrange & Act
        response = TreePoliciesResponse(tree_id=uuid.uuid4(), policies=[], total_count=0)

        # Assert
        assert len(response.policies) == 0
        assert response.total_count == 0

    def test_tree_policies_response_default_values(self):
        """[test_api_extension_schemas-011] TreePoliciesResponseのデフォルト値検証。"""
        # Arrange & Act
        response = TreePoliciesResponse(
            tree_id=uuid.uuid4()
            # policies と total_count は省略
        )

        # Assert
        assert response.policies == []
        assert response.total_count == 0

    def test_tree_policies_response_required_fields(self):
        """[test_api_extension_schemas-012] TreePoliciesResponseの必須フィールド検証。"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            TreePoliciesResponse()

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        assert "tree_id" in error_fields


# ================================================================================
# ColumnInfo (driver_tree_file.py) のテスト
# ================================================================================
class TestColumnInfo:
    """ColumnInfo スキーマのテスト。"""

    def test_create_column_info_success(self):
        """[test_api_extension_schemas-013] ColumnInfo作成の成功ケース。"""
        # Arrange & Act
        column = ColumnInfo(name="sales", display_name="売上", data_type="number", role="value")

        # Assert
        assert column.name == "sales"
        assert column.display_name == "売上"
        assert column.data_type == "number"
        assert column.role == "value"

    def test_column_info_optional_role(self):
        """[test_api_extension_schemas-014] ColumnInfoのオプションroleフィールド検証。"""
        # Arrange & Act
        column = ColumnInfo(
            name="id",
            display_name="ID",
            data_type="string",
            # role は省略
        )

        # Assert
        assert column.role is None

    def test_column_info_all_data_types(self):
        """[test_api_extension_schemas-015] ColumnInfoの各種データ型検証。"""
        # Arrange & Act
        columns = [
            ColumnInfo(name="col1", display_name="文字列", data_type="string"),
            ColumnInfo(name="col2", display_name="数値", data_type="number"),
            ColumnInfo(name="col3", display_name="日時", data_type="datetime"),
            ColumnInfo(name="col4", display_name="真偽値", data_type="boolean"),
        ]

        # Assert
        assert columns[0].data_type == "string"
        assert columns[1].data_type == "number"
        assert columns[2].data_type == "datetime"
        assert columns[3].data_type == "boolean"

    def test_column_info_required_fields(self):
        """[test_api_extension_schemas-016] ColumnInfoの必須フィールド検証。"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            ColumnInfo()

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        assert "name" in error_fields
        assert "display_name" in error_fields
        assert "data_type" in error_fields


# ================================================================================
# SheetDetailResponse (driver_tree_file.py) のテスト
# ================================================================================
class TestSheetDetailResponse:
    """SheetDetailResponse スキーマのテスト。"""

    def test_create_sheet_detail_response_success(self):
        """[test_api_extension_schemas-017] SheetDetailResponse作成の成功ケース。"""
        # Arrange
        sheet_id = uuid.uuid4()
        columns = [
            ColumnInfo(name="col1", display_name="売上", data_type="number", role="value"),
            ColumnInfo(name="col2", display_name="日付", data_type="datetime", role="timeline"),
        ]
        sample_data = [
            {"col1": 1000, "col2": "2024-01-01"},
            {"col1": 2000, "col2": "2024-01-02"},
        ]

        # Act
        response = SheetDetailResponse(sheet_id=sheet_id, sheet_name="売上データ", columns=columns, row_count=100, sample_data=sample_data)

        # Assert
        assert response.sheet_id == sheet_id
        assert response.sheet_name == "売上データ"
        assert len(response.columns) == 2
        assert response.row_count == 100
        assert len(response.sample_data) == 2
        assert response.columns[0].name == "col1"
        assert response.sample_data[0]["col1"] == 1000

    def test_sheet_detail_response_empty_data(self):
        """[test_api_extension_schemas-018] SheetDetailResponseの空データ検証。"""
        # Arrange & Act
        response = SheetDetailResponse(sheet_id=uuid.uuid4(), sheet_name="空シート", columns=[], row_count=0, sample_data=[])

        # Assert
        assert len(response.columns) == 0
        assert response.row_count == 0
        assert len(response.sample_data) == 0

    def test_sheet_detail_response_default_lists(self):
        """[test_api_extension_schemas-019] SheetDetailResponseのデフォルトリスト検証。"""
        # Arrange & Act
        response = SheetDetailResponse(
            sheet_id=uuid.uuid4(),
            sheet_name="テストシート",
            row_count=50,
            # columns と sample_data は省略
        )

        # Assert
        assert response.columns == []
        assert response.sample_data == []

    def test_sheet_detail_response_required_fields(self):
        """[test_api_extension_schemas-020] SheetDetailResponseの必須フィールド検証。"""
        # Arrange & Act & Assert
        with pytest.raises(ValidationError) as exc_info:
            SheetDetailResponse()

        errors = exc_info.value.errors()
        error_fields = {error["loc"][0] for error in errors}
        assert "sheet_id" in error_fields
        assert "sheet_name" in error_fields
        assert "row_count" in error_fields

    def test_sheet_detail_response_complex_sample_data(self):
        """[test_api_extension_schemas-021] SheetDetailResponseの複雑なサンプルデータ検証。"""
        # Arrange
        sample_data = [
            {"id": 1, "name": "商品A", "price": 1000, "available": True},
            {"id": 2, "name": "商品B", "price": 2000, "available": False},
        ]

        # Act
        response = SheetDetailResponse(sheet_id=uuid.uuid4(), sheet_name="商品マスタ", columns=[], row_count=2, sample_data=sample_data)

        # Assert
        assert len(response.sample_data) == 2
        assert response.sample_data[0]["name"] == "商品A"
        assert response.sample_data[1]["price"] == 2000
        assert response.sample_data[0]["available"] is True
