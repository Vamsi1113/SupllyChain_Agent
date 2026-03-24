"""
LLM and Embeddings factory functions returning models based on the selected provider.
Supports OpenAI, Azure, Groq, and local Ollama (Llama models).
"""

from __future__ import annotations

import logging
from typing import Any

from config import get_settings

logger = logging.getLogger(__name__)


def get_llm() -> Any:
    """Returns the configured Chat model (Ollama, Groq, Azure, or Standard OpenAI)."""
    settings = get_settings()
    provider = settings.llm_provider.lower()

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        logger.info(f"Using Ollama LLM: {settings.ollama_model}")
        return ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=settings.openai_temperature,
        )

    elif provider == "groq":
        from langchain_groq import ChatGroq
        logger.info(f"Using Groq LLM: {settings.openai_model}")
        return ChatGroq(
            model=settings.openai_model,
            temperature=settings.openai_temperature,
            api_key=settings.groq_api_key,
        )

    else:
        # Default to OpenAI / Azure
        from langchain_openai import ChatOpenAI, AzureChatOpenAI
        is_azure = provider == "azure" or (settings.openai_api_base and "openai.azure.com" in settings.openai_api_base.lower())

        if is_azure:
            logger.info(f"Using Azure OpenAI LLM: {settings.openai_model}")
            return AzureChatOpenAI(
                azure_endpoint=settings.openai_api_base,
                openai_api_version=settings.openai_api_version or "2024-02-15-preview",
                azure_deployment=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=settings.openai_temperature,
            )
        elif settings.openai_api_base:
            return ChatOpenAI(
                base_url=settings.openai_api_base,
                model=settings.openai_model,
                temperature=settings.openai_temperature,
                api_key=settings.openai_api_key,
            )
        else:
            return ChatOpenAI(
                model=settings.openai_model,
                temperature=settings.openai_temperature,
                api_key=settings.openai_api_key,
            )


def get_embeddings() -> Any:
    """Returns the configured Embeddings model."""
    settings = get_settings()
    provider = settings.llm_provider.lower()
    
    # For Ollama and Groq, default to fast local embeddings
    if provider in ["ollama", "groq"]:
        try:
            from langchain_ollama import OllamaEmbeddings
            return OllamaEmbeddings(model="nomic-embed-text", base_url=settings.ollama_base_url)
        except Exception as e:
            logger.info(f"Ollama embeddings not found, using generic SentenceTransformers: {e}")
            from langchain_community.embeddings import SentenceTransformerEmbeddings
            return SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")

    is_azure = provider == "azure" or (settings.openai_api_base and "openai.azure.com" in settings.openai_api_base.lower())

    try:
        if is_azure:
            from langchain_openai import AzureOpenAIEmbeddings
            return AzureOpenAIEmbeddings(
                azure_endpoint=settings.openai_api_base,
                openai_api_version=settings.openai_api_version or "2024-02-15-preview",
                azure_deployment="text-embedding-3-small",
                api_key=settings.openai_api_key,
            )
        else:
            from langchain_openai import OpenAIEmbeddings
            return OpenAIEmbeddings(
                base_url=settings.openai_api_base if settings.openai_api_base else None,
                model="text-embedding-3-small",
                api_key=settings.openai_api_key,
            )
    except Exception as e:
        logger.warning(f"Failed to load configured embeddings, trying SentenceTransformers: {e}")
        from langchain_community.embeddings import SentenceTransformerEmbeddings
        return SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
