"""LLM統合モジュール。

Azure OpenAIのLLMとEmbeddingsクライアントを提供します。
環境変数から設定を読み込みます。
遅延初期化により、テスト時の認証情報エラーを回避します。
"""

import os
from functools import lru_cache

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings


@lru_cache(maxsize=1)
def get_llm() -> AzureChatOpenAI:
    """LLMクライアントを取得（遅延初期化）。"""
    return AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        temperature=0,
        timeout=None,
        max_retries=2,
    )


@lru_cache(maxsize=1)
def get_embeddings() -> AzureOpenAIEmbeddings:
    """Embeddingsクライアントを取得（遅延初期化）。"""
    return AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-ada-002"),
        azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT"),
    )
