"""LLM統合モジュール。

Azure OpenAIのLLMとEmbeddingsクライアントを提供します。
環境変数から設定を読み込みます。
"""

import os

from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings

# 環境変数から設定を取得
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4.1")
AZURE_OPENAI_EMBEDDING_ENDPOINT = os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
AZURE_OPENAI_EMBEDDING_MODEL = os.getenv("AZURE_OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")

# LLMクライアントの初期化
llm = AzureChatOpenAI(
    azure_deployment=AZURE_OPENAI_DEPLOYMENT_NAME,
    api_version=AZURE_OPENAI_API_VERSION,
    temperature=0,
    timeout=None,
    max_retries=2,
)

# Embeddingsクライアントの初期化
emb = AzureOpenAIEmbeddings(
    model=AZURE_OPENAI_EMBEDDING_MODEL,
    azure_endpoint=AZURE_OPENAI_EMBEDDING_ENDPOINT,
    openai_api_type="azure",
)
