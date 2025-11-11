"""
Viincci-RAG: Universal Research & Article Generation System

A professional Python package for multi-domain research, retrieval-augmented
generation (RAG), and article generation.

Usage:
    from viincci_rag import ConfigManager, RAGSystem, UniversalResearchSpider
    
    config = ConfigManager(domain="botany")
    rag = RAGSystem(config)
    spider = UniversalResearchSpider(config)

Or import all:
    from viincci_rag import *
"""

__version__ = "4.0.0"
__author__ = "Viincci Team"
__license__ = "MIT"

# Prefer importing viincci_rag core modules (new layout). If those are not
# available, fall back to the legacy `V4` package. This makes `viincci_rag`
# the canonical import path while retaining backward compatibility.
try:
    # Import from the package-local core wrappers first
    from viincci_rag.core.config import ConfigManager  # type: ignore
    from viincci_rag.core.spider import UniversalResearchSpider  # type: ignore
    from viincci_rag.core.rag_system import RAGSystem  # type: ignore
    from viincci_rag.core.article_generator import UniversalArticleGenerator  # type: ignore
    from viincci_rag.core.api_monitor import SerpAPIMonitor  # type: ignore
    from viincci_rag.database import FloraDatabase  # type: ignore
except Exception:
    # Fallback to legacy V4 package if viincci_rag.core imports fail
    try:
        from V4 import (
            ConfigManager,
            FloraDatabase,
            RAGSystem,
            UniversalArticleGenerator,
            UniversalResearchSpider,
            SerpAPIMonitor,
        )
    except Exception:
        # Fallback stubs if nothing is importable
        ConfigManager = None
        FloraDatabase = None
        RAGSystem = None
        UniversalArticleGenerator = None
        UniversalResearchSpider = None
        SerpAPIMonitor = None

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    # Core classes
    "ConfigManager",
    "RAGSystem",
    "UniversalResearchSpider",
    "UniversalArticleGenerator",
    "SerpAPIMonitor",
    # Database and utilities
    "FloraDatabase",
    "EnhancedPlantArticleGenerator",
    "FloraWikipediaScraper",
]
