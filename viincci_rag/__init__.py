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

# Core classes and utilities (wrap V4 classes for canonical viincci_rag imports)
try:
    # Import V4 classes as base classes
    from V4 import (
        ConfigManager as _V4ConfigManager,
        FloraDatabase as _V4FloraDatabase,
        RAGSystem as _V4RAGSystem,
        UniversalArticleGenerator as _V4UniversalArticleGenerator,
        UniversalResearchSpider as _V4UniversalResearchSpider,
        SerpAPIMonitor as _V4SerpAPIMonitor,
    )
    
    # Create lightweight subclasses to make viincci_rag the canonical path
    class ConfigManager(_V4ConfigManager):  # type: ignore
        """ConfigManager — viincci_rag canonical class (inherits from V4)."""
        pass
    
    class FloraDatabase(_V4FloraDatabase):  # type: ignore
        """FloraDatabase — viincci_rag canonical class (inherits from V4)."""
        pass
    
    class RAGSystem(_V4RAGSystem):  # type: ignore
        """RAGSystem — viincci_rag canonical class (inherits from V4)."""
        pass
    
    class UniversalArticleGenerator(_V4UniversalArticleGenerator):  # type: ignore
        """UniversalArticleGenerator — viincci_rag canonical class (inherits from V4)."""
        pass
    
    class UniversalResearchSpider(_V4UniversalResearchSpider):  # type: ignore
        """UniversalResearchSpider — viincci_rag canonical class (inherits from V4)."""
        pass
    
    class SerpAPIMonitor(_V4SerpAPIMonitor):  # type: ignore
        """SerpAPIMonitor — viincci_rag canonical class (inherits from V4)."""
        pass

except Exception as e:
    # Fallback stubs if V4 imports fail
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
]


__version__ = "4.0.0"
__author__ = "Viincci Team"
__license__ = "MIT"

# Import from V4 and re-export as viincci_rag (canonical import path).
# Try to import via viincci_rag.core wrappers (which subclass V4 classes),
# making viincci_rag the canonical package path. Fall back to direct V4
# import if core wrappers fail.
try:
    # Attempt to import from viincci_rag.core subclasses first
    from viincci_rag.core.config import ConfigManager  # type: ignore
    from viincci_rag.core.spider import UniversalResearchSpider  # type: ignore
    from viincci_rag.core.rag_system import RAGSystem  # type: ignore
    from viincci_rag.core.article_generator import UniversalArticleGenerator  # type: ignore
    from viincci_rag.core.api_monitor import SerpAPIMonitor  # type: ignore
    from viincci_rag.database import FloraDatabase  # type: ignore
except Exception:
    # If core wrappers fail, import directly from V4 (fallback)
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
