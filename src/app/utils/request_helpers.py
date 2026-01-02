"""HTTPリクエスト関連のユーティリティ。

このモジュールは、HTTPリクエストからの情報抽出を支援するユーティリティを提供します。
"""

import ipaddress

from fastapi import Request

from app.core.logging import get_logger

logger = get_logger(__name__)


class RequestHelper:
    """HTTPリクエスト情報抽出ヘルパー。

    メソッド:
        - get_client_ip: クライアントIPアドレスを取得
        - is_valid_ip: IPアドレス形式を検証
        - is_trusted_proxy: IPアドレスが信頼できるプロキシか判定
    """

    @staticmethod
    def is_trusted_proxy(ip: str) -> bool:
        """IPアドレスが信頼できるプロキシか判定します。

        設定されたTRUSTED_PROXIESのCIDR範囲に含まれるかをチェックします。

        Args:
            ip: 検証するIPアドレス文字列

        Returns:
            bool: 信頼できるプロキシの場合True
        """
        try:
            from app.core.config import settings

            ip_obj = ipaddress.ip_address(ip)
            for trusted_network in settings.TRUSTED_PROXIES:
                if ip_obj in ipaddress.ip_network(trusted_network):
                    return True
            return False
        except ValueError:
            return False

    @staticmethod
    def get_client_ip(request: Request) -> str | None:
        """クライアントIPアドレスを取得します。

        セキュリティ考慮事項:
            - X-Forwarded-Forヘッダーは信頼できるプロキシからのみ使用
            - 直接接続元が信頼できるプロキシでない場合はX-Forwarded-Forを無視
            - IPアドレス形式の検証を実施

        Args:
            request: リクエストオブジェクト

        Returns:
            クライアントIPアドレス、または取得できない場合はNone
        """
        # 直接接続元IPを取得
        direct_ip = request.client.host if request.client else None

        # 直接接続元が信頼できるプロキシでない場合はX-Forwarded-Forを無視
        if direct_ip and not RequestHelper.is_trusted_proxy(direct_ip):
            logger.debug(
                "直接接続元が信頼できるプロキシではないため、X-Forwarded-Forを無視します",
                direct_ip=direct_ip,
            )
            return direct_ip

        # 信頼できるプロキシからのX-Forwarded-Forを使用
        forwarded_for = request.headers.get("x-forwarded-for")

        if forwarded_for:
            # 最初のIPがオリジナルクライアント
            client_ip = forwarded_for.split(",")[0].strip()

            # IPアドレス形式の検証
            if RequestHelper.is_valid_ip(client_ip):
                return client_ip
            else:
                # 無効なIPアドレス形式の場合は直接接続元を使用
                logger.warning(
                    "無効なX-Forwarded-For形式",
                    forwarded_for=forwarded_for,
                    direct_ip=direct_ip,
                )
                return direct_ip

        return direct_ip

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        """IPアドレスの形式を検証します。

        Args:
            ip: 検証するIPアドレス文字列

        Returns:
            有効なIPアドレス形式の場合True
        """
        try:
            ipaddress.ip_address(ip)
            return True
        except ValueError:
            return False
