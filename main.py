#!/usr/bin/env python3
"""
viincci_main.py - Comprehensive Main Controller for Viincci-RAG
Highly customizable research system with database flexibility
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging

# Import core components
from V4.ConfigManager import ConfigManager
from V4.Spider import UniversalResearchSpider
from V4.RagSys import RAGSystem
from V4.UniversalArticleGenerator import UniversalArticleGenerator
from V4.ApiMonitor import SerpAPIMonitor
from V4.FloraDatabase import FloraDatabase


# ============================================================================
# DATABASE ADAPTERS
# ============================================================================

class DatabaseAdapter:
    """Base class for database adapters"""
    
    def __init__(self, connection_config: Dict):
        self.config = connection_config
        self.connection = None
    
    def connect(self):
        raise NotImplementedError
    
    def disconnect(self):
        raise NotImplementedError
    
    def save_research(self, data: Dict) -> bool:
        raise NotImplementedError
    
    def load_research(self, query: str) -> Optional[Dict]:
        raise NotImplementedError
    
    def list_research(self, filters: Dict = None) -> List[Dict]:
        raise NotImplementedError


class SQLiteAdapter(DatabaseAdapter):
    """SQLite database adapter"""
    
    def __init__(self, connection_config: Dict):
        super().__init__(connection_config)
        self.db_path = connection_config.get('path', 'viincci_research.db')
    
    def connect(self):
        import sqlite3
        self.connection = sqlite3.connect(self.db_path)
        self._create_schema()
        logging.info(f"Connected to SQLite: {self.db_path}")
    
    def _create_schema(self):
        cursor = self.connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                domain TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                sources_count INTEGER,
                metadata TEXT,
                content TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                url TEXT,
                title TEXT,
                reliability TEXT,
                content TEXT,
                metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES research_sessions(id)
            )
        ''')
        self.connection.commit()
    
    def save_research(self, data: Dict) -> bool:
        try:
            cursor = self.connection.cursor()
            
            # Save session
            cursor.execute('''
                INSERT INTO research_sessions (query, domain, sources_count, metadata, content)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data['query'],
                data['domain'],
                len(data.get('sources', [])),
                json.dumps(data.get('metadata', {})),
                data.get('content', '')
            ))
            
            session_id = cursor.lastrowid
            
            # Save sources
            for source in data.get('sources', []):
                cursor.execute('''
                    INSERT INTO research_sources (session_id, url, title, reliability, content, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    session_id,
                    source.get('metadata', {}).get('url', ''),
                    source.get('metadata', {}).get('title', ''),
                    source.get('metadata', {}).get('reliability', ''),
                    source.get('text', ''),
                    json.dumps(source.get('metadata', {}))
                ))
            
            self.connection.commit()
            logging.info(f"Saved research session {session_id}")
            return True
        except Exception as e:
            logging.error(f"Error saving to SQLite: {e}")
            return False
    
    def load_research(self, query: str) -> Optional[Dict]:
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT id, query, domain, timestamp, sources_count, metadata, content
            FROM research_sessions
            WHERE query = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (query,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        session_id = row[0]
        
        # Load sources
        cursor.execute('''
            SELECT url, title, reliability, content, metadata
            FROM research_sources
            WHERE session_id = ?
        ''', (session_id,))
        
        sources = []
        for source_row in cursor.fetchall():
            sources.append({
                'metadata': {
                    'url': source_row[0],
                    'title': source_row[1],
                    'reliability': source_row[2],
                    **json.loads(source_row[4])
                },
                'text': source_row[3]
            })
        
        return {
            'query': row[1],
            'domain': row[2],
            'timestamp': row[3],
            'sources_count': row[4],
            'metadata': json.loads(row[5]),
            'content': row[6],
            'sources': sources
        }
    
    def list_research(self, filters: Dict = None) -> List[Dict]:
        cursor = self.connection.cursor()
        query = 'SELECT id, query, domain, timestamp, sources_count FROM research_sessions'
        
        if filters:
            conditions = []
            params = []
            if 'domain' in filters:
                conditions.append('domain = ?')
                params.append(filters['domain'])
            if 'date_from' in filters:
                conditions.append('timestamp >= ?')
                params.append(filters['date_from'])
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
            
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'query': row[1],
                'domain': row[2],
                'timestamp': row[3],
                'sources_count': row[4]
            })
        
        return results
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            logging.info("Disconnected from SQLite")


class MongoDBAdapter(DatabaseAdapter):
    """MongoDB database adapter"""
    
    def __init__(self, connection_config: Dict):
        super().__init__(connection_config)
        self.host = connection_config.get('host', 'localhost')
        self.port = connection_config.get('port', 27017)
        self.database_name = connection_config.get('database', 'viincci_research')
        self.username = connection_config.get('username')
        self.password = connection_config.get('password')
    
    def connect(self):
        try:
            from pymongo import MongoClient
            
            if self.username and self.password:
                connection_string = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/"
            else:
                connection_string = f"mongodb://{self.host}:{self.port}/"
            
            self.connection = MongoClient(connection_string)
            self.db = self.connection[self.database_name]
            self.sessions = self.db['research_sessions']
            
            # Create indexes
            self.sessions.create_index('query')
            self.sessions.create_index('domain')
            self.sessions.create_index('timestamp')
            
            logging.info(f"Connected to MongoDB: {self.host}:{self.port}/{self.database_name}")
        except ImportError:
            logging.error("pymongo not installed. Install with: pip install pymongo")
            raise
    
    def save_research(self, data: Dict) -> bool:
        try:
            document = {
                'query': data['query'],
                'domain': data['domain'],
                'timestamp': datetime.now(),
                'sources_count': len(data.get('sources', [])),
                'metadata': data.get('metadata', {}),
                'content': data.get('content', ''),
                'sources': data.get('sources', [])
            }
            
            result = self.sessions.insert_one(document)
            logging.info(f"Saved research session {result.inserted_id}")
            return True
        except Exception as e:
            logging.error(f"Error saving to MongoDB: {e}")
            return False
    
    def load_research(self, query: str) -> Optional[Dict]:
        result = self.sessions.find_one(
            {'query': query},
            sort=[('timestamp', -1)]
        )
        
        if result:
            result['_id'] = str(result['_id'])  # Convert ObjectId to string
            return result
        return None
    
    def list_research(self, filters: Dict = None) -> List[Dict]:
        query = {}
        if filters:
            if 'domain' in filters:
                query['domain'] = filters['domain']
            if 'date_from' in filters:
                query['timestamp'] = {'$gte': filters['date_from']}
        
        results = []
        for doc in self.sessions.find(query).sort('timestamp', -1):
            doc['_id'] = str(doc['_id'])
            results.append({
                'id': doc['_id'],
                'query': doc['query'],
                'domain': doc['domain'],
                'timestamp': doc['timestamp'],
                'sources_count': doc.get('sources_count', 0)
            })
        
        return results
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            logging.info("Disconnected from MongoDB")


class PostgreSQLAdapter(DatabaseAdapter):
    """PostgreSQL database adapter"""
    
    def __init__(self, connection_config: Dict):
        super().__init__(connection_config)
        self.host = connection_config.get('host', 'localhost')
        self.port = connection_config.get('port', 5432)
        self.database = connection_config.get('database', 'viincci_research')
        self.user = connection_config.get('user', 'postgres')
        self.password = connection_config.get('password', '')
    
    def connect(self):
        try:
            import psycopg2
            
            self.connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            self._create_schema()
            logging.info(f"Connected to PostgreSQL: {self.host}:{self.port}/{self.database}")
        except ImportError:
            logging.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
            raise
    
    def _create_schema(self):
        cursor = self.connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_sessions (
                id SERIAL PRIMARY KEY,
                query TEXT NOT NULL,
                domain TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sources_count INTEGER,
                metadata JSONB,
                content TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_sources (
                id SERIAL PRIMARY KEY,
                session_id INTEGER REFERENCES research_sessions(id),
                url TEXT,
                title TEXT,
                reliability TEXT,
                content TEXT,
                metadata JSONB
            )
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_query ON research_sessions(query);
            CREATE INDEX IF NOT EXISTS idx_sessions_domain ON research_sessions(domain);
            CREATE INDEX IF NOT EXISTS idx_sources_session ON research_sources(session_id);
        ''')
        self.connection.commit()
    
    def save_research(self, data: Dict) -> bool:
        try:
            cursor = self.connection.cursor()
            
            cursor.execute('''
                INSERT INTO research_sessions (query, domain, sources_count, metadata, content)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                data['query'],
                data['domain'],
                len(data.get('sources', [])),
                json.dumps(data.get('metadata', {})),
                data.get('content', '')
            ))
            
            session_id = cursor.fetchone()[0]
            
            for source in data.get('sources', []):
                cursor.execute('''
                    INSERT INTO research_sources (session_id, url, title, reliability, content, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', (
                    session_id,
                    source.get('metadata', {}).get('url', ''),
                    source.get('metadata', {}).get('title', ''),
                    source.get('metadata', {}).get('reliability', ''),
                    source.get('text', ''),
                    json.dumps(source.get('metadata', {}))
                ))
            
            self.connection.commit()
            logging.info(f"Saved research session {session_id}")
            return True
        except Exception as e:
            logging.error(f"Error saving to PostgreSQL: {e}")
            self.connection.rollback()
            return False
    
    def load_research(self, query: str) -> Optional[Dict]:
        cursor = self.connection.cursor()
        cursor.execute('''
            SELECT id, query, domain, timestamp, sources_count, metadata, content
            FROM research_sessions
            WHERE query = %s
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (query,))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        session_id = row[0]
        
        cursor.execute('''
            SELECT url, title, reliability, content, metadata
            FROM research_sources
            WHERE session_id = %s
        ''', (session_id,))
        
        sources = []
        for source_row in cursor.fetchall():
            sources.append({
                'metadata': {
                    'url': source_row[0],
                    'title': source_row[1],
                    'reliability': source_row[2],
                    **json.loads(source_row[4])
                },
                'text': source_row[3]
            })
        
        return {
            'query': row[1],
            'domain': row[2],
            'timestamp': row[3],
            'sources_count': row[4],
            'metadata': json.loads(row[5]),
            'content': row[6],
            'sources': sources
        }
    
    def list_research(self, filters: Dict = None) -> List[Dict]:
        cursor = self.connection.cursor()
        query = 'SELECT id, query, domain, timestamp, sources_count FROM research_sessions'
        params = []
        
        if filters:
            conditions = []
            if 'domain' in filters:
                conditions.append('domain = %s')
                params.append(filters['domain'])
            if 'date_from' in filters:
                conditions.append('timestamp >= %s')
                params.append(filters['date_from'])
            
            if conditions:
                query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY timestamp DESC'
        cursor.execute(query, params)
        
        results = []
        for row in cursor.fetchall():
            results.append({
                'id': row[0],
                'query': row[1],
                'domain': row[2],
                'timestamp': row[3],
                'sources_count': row[4]
            })
        
        return results
    
    def disconnect(self):
        if self.connection:
            self.connection.close()
            logging.info("Disconnected from PostgreSQL")


# ============================================================================
# DATABASE FACTORY
# ============================================================================

class DatabaseFactory:
    """Factory for creating database adapters"""
    
    @staticmethod
    def create(db_type: str, config: Dict) -> DatabaseAdapter:
        adapters = {
            'sqlite': SQLiteAdapter,
            'mongodb': MongoDBAdapter,
            'postgres': PostgreSQLAdapter,
            'postgresql': PostgreSQLAdapter
        }
        
        adapter_class = adapters.get(db_type.lower())
        if not adapter_class:
            raise ValueError(f"Unknown database type: {db_type}")
        
        return adapter_class(config)


# ============================================================================
# VIINCCI CONTROLLER
# ============================================================================

class ViincciController:
    """
    Main controller for Viincci-RAG system with extensive customization
    """
    
    def __init__(self, config_file: str = None):
        """
        Initialize controller with configuration
        
        Args:
            config_file: Path to JSON configuration file
        """
        self.config_file = config_file or "viincci_config.json"
        self.settings = self._load_settings()
        self._setup_logging()
        
        # Initialize components
        self.config_manager = None
        self.spider = None
        self.rag_system = None
        self.generator = None
        self.api_monitor = None
        self.db_adapter = None
        
        logging.info("Viincci Controller initialized")
    
    def _load_settings(self) -> Dict:
        """Load settings from configuration file"""
        default_settings = {
            "system": {
                "log_level": "INFO",
                "log_file": "viincci.log",
                "default_domain": "botany",
                "verbose": False
            },
            "database": {
                "type": "sqlite",
                "connection": {
                    "path": "viincci_research.db"
                },
                "auto_save": True,
                "cache_results": True
            },
            "rag": {
                "embedding_model": "all-MiniLM-L6-v2",
                "llm_model": "LiquidAI/LFM-40B-MoE",
                "device": "cpu",
                "load_in_8bit": False,
                "retrieval": {
                    "k": 5,
                    "similarity_threshold": 0.7,
                    "max_context_length": 2000
                },
                "generation": {
                    "max_new_tokens": 500,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 50,
                    "do_sample": True
                },
                "indexing": {
                    "chunk_size": 500,
                    "chunk_overlap": 50,
                    "use_faiss": True,
                    "index_type": "IndexFlatL2"
                }
            },
            "search": {
                "max_sources": 20,
                "delay_between_requests": 1.5,
                "timeout": 30,
                "retry_attempts": 3,
                "pdf_extraction": True,
                "max_pdf_pages": 50
            },
            "api_monitor": {
                "enabled": True,
                "warning_threshold": 100,
                "critical_threshold": 20,
                "auto_stop_on_critical": True,
                "estimate_before_research": True
            },
            "article_generation": {
                "fetch_images": True,
                "image_count": 5,
                "include_front_matter": True,
                "output_formats": ["html"],
                "image_settings": {
                    "width": 800,
                    "height": 600,
                    "default_fallback": "/img/posts/default.jpg"
                }
            },
            "output": {
                "directory": "_posts",
                "filename_pattern": "{date}-{query}.{ext}",
                "save_metadata": True,
                "save_sources": True
            }
        }
        
        if Path(self.config_file).exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_settings = json.load(f)
                    # Deep merge user settings with defaults
                    self._deep_merge(default_settings, user_settings)
                    logging.info(f"Loaded settings from {self.config_file}")
            except Exception as e:
                logging.warning(f"Error loading config file: {e}. Using defaults.")
        else:
            # Save default settings
            self._save_settings(default_settings)
            logging.info(f"Created default config: {self.config_file}")
        
        return default_settings
    
    def _deep_merge(self, base: Dict, update: Dict):
        """Deep merge update dict into base dict"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _save_settings(self, settings: Dict):
        """Save settings to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
    
    def _setup_logging(self):
        """Setup logging system"""
        log_level = getattr(logging, self.settings['system']['log_level'])
        log_file = self.settings['system']['log_file']
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    def initialize(self):
        """Initialize all components"""
        logging.info("Initializing Viincci-RAG components...")
        
        # Config Manager
        self.config_manager = ConfigManager(
            domain=self.settings['system']['default_domain'],
            verbose=self.settings['system']['verbose']
        )
        
        # Update ConfigManager with custom settings
        self.config_manager._configs['ai_settings']['embedding_model'] = \
            self.settings['rag']['embedding_model']
        self.config_manager._configs['ai_settings']['llm_model'] = \
            self.settings['rag']['llm_model']
        self.config_manager._configs['ai_settings']['device'] = \
            self.settings['rag']['device']
        self.config_manager._configs['ai_settings']['load_in_8bit'] = \
            self.settings['rag']['load_in_8bit']
        
        # API Monitor
        if self.settings['api_monitor']['enabled']:
            self.api_monitor = SerpAPIMonitor(self.config_manager)
        
        # Database Adapter
        db_config = self.settings['database']
        self.db_adapter = DatabaseFactory.create(
            db_config['type'],
            db_config['connection']
        )
        self.db_adapter.connect()
        
        logging.info("All components initialized successfully")
    
    def set_rag_config(self, **kwargs):
        """
        Update RAG configuration dynamically
        
        Example:
            controller.set_rag_config(
                embedding_model="all-mpnet-base-v2",
                k=10,
                temperature=0.8
            )
        """
        if 'embedding_model' in kwargs:
            self.settings['rag']['embedding_model'] = kwargs['embedding_model']
        
        if 'llm_model' in kwargs:
            self.settings['rag']['llm_model'] = kwargs['llm_model']
        
        if 'device' in kwargs:
            self.settings['rag']['device'] = kwargs['device']
        
        if 'k' in kwargs:
            self.settings['rag']['retrieval']['k'] = kwargs['k']
        
        if 'temperature' in kwargs:
            self.settings['rag']['generation']['temperature'] = kwargs['temperature']
        
        if 'max_new_tokens' in kwargs:
            self.settings['rag']['generation']['max_new_tokens'] = kwargs['max_new_tokens']
        
        logging.info(f"Updated RAG configuration: {kwargs}")
    
    def research(self, query: str, domain: str = None, 
                cache: bool = True, **kwargs) -> Dict:
        """
        Perform research with full customization
        
        Args:
            query: Research query
            domain: Research domain
            cache: Use cached results if available
            **kwargs: Override any setting temporarily
        
        Returns:
            Research results dictionary
        """
        # Check cache first
        if cache and self.settings['database']['cache_results']:
            cached = self.db_adapter.load_research(query)
            if cached:
                logging.info(f"Using cached results for: {query}")
                return cached
        
        # Apply domain
        if domain:
            self.config_manager.switch_domain(domain)
        
        # Initialize spider with custom settings
        spider_settings = {**self.settings['search'], **kwargs}
        self.spider = UniversalResearchSpider(
            self.config_manager,
            check_credits=self.settings['api_monitor']['enabled']
        )
        
        # Override spider settings
        if 'max_sources' in spider_settings:
            self.spider.max_sources = spider_settings['max_sources']
        if 'delay' in spider_settings:
            self.spider.delay = spider_settings['delay']
        
        # Perform research
        logging.info(f"Starting research: {query}")
        sources = self.spider.research(query, estimate_first=True)
        
        result = {
            'query': query,
            'domain': self.config_manager.get_current_domain(),
            'timestamp': datetime.now().isoformat(),
            'sources': sources,
            'sources_count': len(sources),
            'metadata': {
                'settings': spider_settings
            }
        }
        
        # Auto-save if enabled
        if self.settings['database']['auto_save']:
            self.db_adapter.save_research(result)
        
        return result
    
    def generate_with_rag(self, query: str, sources: List[Dict], 
                         **kwargs) -> str:
        """
        Generate content using RAG
        
        Args:
            query: Question or prompt
            sources: Research sources
            **kwargs: Override RAG settings
        """
        # Initialize RAG if needed
        if not self.rag_system:
            self.rag_system = RAGSystem(self.config_manager)
            
            # Apply custom settings
            rag_config = self.settings['rag']
            self.rag_system.embedding_model_name = rag_config['embedding_model']
            self.rag_system.llm_model_name = rag_config['llm_model']
            self.rag_system.device = rag_config['device']
        
        # Build index
        texts = [s['text'] for s in sources]
        metadata = [s['metadata'] for s in sources]
        self.rag_system.build_index(texts, metadata)
        
        # Load LLM if not loaded
        if not self.rag_system.is_llm_loaded():
            self.rag_system.load_llm()
        
        # Get retrieval settings
        retrieval_config = {
            **self.settings['rag']['retrieval'],
            **self.settings['rag']['generation'],
            **kwargs
        }
        
        # Generate response
        result = self.rag_system.query(
            query,
            k=retrieval_config['k'],
            max_new_tokens=retrieval_config['max_new_tokens'],
            temperature=retrieval_config['temperature']
        )
        
        return result['answer']
    
    def generate_article(self, query: str, sources: List[Dict], 
                        use_rag: bool = True, **kwargs) -> str:
        """
        Generate complete article
        
        Args:
            query: Article topic
            sources: Research sources
            use_rag: Use RAG for content generation
            **kwargs: Override generation settings
        """
        # Initialize RAG if needed
        rag_system = None
        if use_rag:
            if not self.rag_system:
                self.rag_system = RAGSystem(self.config_manager)
                texts = [s['text'] for s in sources]
                metadata = [s['metadata'] for s in sources]
                self.rag_system.build_index(texts, metadata)
                self.rag_system.load_llm()
            rag_system = self.rag_system
        
        # Initialize generator
        gen_config = {**self.settings['article_generation'], **kwargs}
        self.generator = UniversalArticleGenerator(
            config=self.config_manager,
            rag_system=rag_system,
            fetch_images=gen_config['fetch_images']
        )
        
        # Generate article
        article = self.generator.generate_full_article(query, sources)
        
        return article
    
    def save_output(self, content: str, query: str, format: str = 'html'):
        """Save generated content to file"""
        output_dir = Path(self.settings['output']['directory'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        date_str = datetime.now().strftime('%Y-%m-%d')
        safe_query = query.lower().replace(' ', '-').replace('/', '-')
        
        pattern = self.settings['output']['filename_pattern']
        filename = pattern.format(
            date=date_str,
            query=safe_query,
            ext=format
        )
        
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logging.info(f"Saved output to: {filepath}")
        return str(filepath)
    
    def list_cached_research(self, domain: str = None) -> List[Dict]:
        """List all cached research sessions"""
        filters = {'domain': domain} if domain else None
        return self.db_adapter.list_research(filters)
    
    def shutdown(self):
        """Clean shutdown of all components"""
        logging.info("Shutting down Viincci Controller...")
        
        if self.db_adapter:
            self.db_adapter.disconnect()
        
        # Save current settings
        self._save_settings(self.settings)
        
        logging.info("Shutdown complete")


# ============================================================================
# CLI INTERFACE
# ============================================================================

def create_cli_parser():
    """Create CLI argument parser"""
    parser = argparse.ArgumentParser(
        description="Viincci-RAG Main Controller - Highly Customizable Research System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic research
  python viincci_main.py research "Rosa rubiginosa" -d botany
  
  # Custom RAG settings
  python viincci_main.py research "diabetes" -d medical --rag-k 10 --temperature 0.8
  
  # Use different database
  python viincci_main.py research "topic" --db-type mongodb --db-host localhost
  
  # Custom embedding model
  python viincci_main.py research "topic" --embedding-model all-mpnet-base-v2
  
  # List cached research
  python viincci_main.py list --domain medical
  
  # Full workflow with custom settings
  python viincci_main.py workflow "Pythagorean theorem" -d mathematics --rag --output json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Research command
    research_parser = subparsers.add_parser('research', help='Perform research')
    research_parser.add_argument('query', type=str, help='Research query')
    research_parser.add_argument('-d', '--domain', type=str, default='botany',
                                help='Research domain')
    research_parser.add_argument('--no-cache', action='store_true',
                                help='Disable cache lookup')
    research_parser.add_argument('--max-sources', type=int,
                                help='Maximum number of sources')
    research_parser.add_argument('--delay', type=float,
                                help='Delay between requests (seconds)')
    
    # RAG settings
    research_parser.add_argument('--embedding-model', type=str,
                                help='Sentence embedding model')
    research_parser.add_argument('--llm-model', type=str,
                                help='LLM model for generation')
    research_parser.add_argument('--rag-k', type=int,
                                help='Number of vectors to retrieve')
    research_parser.add_argument('--temperature', type=float,
                                help='Generation temperature')
    research_parser.add_argument('--max-tokens', type=int,
                                help='Maximum tokens to generate')
    
    # Database settings
    research_parser.add_argument('--db-type', type=str,
                                choices=['sqlite', 'mongodb', 'postgresql'],
                                help='Database type')
    research_parser.add_argument('--db-host', type=str,
                                help='Database host')
    research_parser.add_argument('--db-port', type=int,
                                help='Database port')
    research_parser.add_argument('--db-name', type=str,
                                help='Database name')
    
    # Workflow command (research + generate)
    workflow_parser = subparsers.add_parser('workflow', 
                                           help='Full research and generation workflow')
    workflow_parser.add_argument('query', type=str, help='Research query')
    workflow_parser.add_argument('-d', '--domain', type=str, default='botany',
                                help='Research domain')
    workflow_parser.add_argument('--rag', action='store_true',
                                help='Use RAG for generation')
    workflow_parser.add_argument('--no-images', action='store_true',
                                help='Skip image fetching')
    workflow_parser.add_argument('--output', type=str, default='html',
                                choices=['html', 'json', 'text'],
                                help='Output format')
    workflow_parser.add_argument('--embedding-model', type=str,
                                help='Sentence embedding model')
    workflow_parser.add_argument('--llm-model', type=str,
                                help='LLM model for generation')
    workflow_parser.add_argument('--rag-k', type=int,
                                help='Number of vectors to retrieve')
    workflow_parser.add_argument('--temperature', type=float,
                                help='Generation temperature')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List cached research')
    list_parser.add_argument('--domain', type=str, help='Filter by domain')
    list_parser.add_argument('--limit', type=int, default=10,
                            help='Maximum results to show')
    
    # Generate command (from cached research)
    generate_parser = subparsers.add_parser('generate',
                                           help='Generate article from cached research')
    generate_parser.add_argument('query', type=str, 
                                help='Query to load from cache')
    generate_parser.add_argument('--rag', action='store_true',
                                help='Use RAG for generation')
    generate_parser.add_argument('--output', type=str, default='html',
                                choices=['html', 'json', 'text'],
                                help='Output format')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('action', choices=['show', 'edit', 'reset'],
                              help='Configuration action')
    config_parser.add_argument('--key', type=str, help='Configuration key path')
    config_parser.add_argument('--value', type=str, help='New value')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show system statistics')
    stats_parser.add_argument('--domain', type=str, help='Domain filter')
    
    # Global options
    parser.add_argument('-c', '--config', type=str, default='viincci_config.json',
                       help='Configuration file path')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    return parser


def handle_research_command(controller: ViincciController, args):
    """Handle research command"""
    print(f"\n{'='*80}")
    print(f"🔬 VIINCCI-RAG RESEARCH")
    print(f"{'='*80}")
    print(f"Query: {args.query}")
    print(f"Domain: {args.domain}")
    print(f"{'='*80}\n")
    
    # Prepare kwargs
    kwargs = {}
    if args.max_sources:
        kwargs['max_sources'] = args.max_sources
    if args.delay:
        kwargs['delay'] = args.delay
    if args.embedding_model:
        controller.set_rag_config(embedding_model=args.embedding_model)
    if args.llm_model:
        controller.set_rag_config(llm_model=args.llm_model)
    if args.rag_k:
        controller.set_rag_config(k=args.rag_k)
    if args.temperature:
        controller.set_rag_config(temperature=args.temperature)
    if args.max_tokens:
        controller.set_rag_config(max_new_tokens=args.max_tokens)
    
    # Perform research
    result = controller.research(
        args.query,
        domain=args.domain,
        cache=not args.no_cache,
        **kwargs
    )
    
    print(f"\n✅ Research Complete!")
    print(f"   Sources collected: {result['sources_count']}")
    print(f"   Domain: {result['domain']}")
    print(f"   Timestamp: {result['timestamp']}")
    
    return result


def handle_workflow_command(controller: ViincciController, args):
    """Handle full workflow command"""
    print(f"\n{'='*80}")
    print(f"🚀 VIINCCI-RAG FULL WORKFLOW")
    print(f"{'='*80}")
    print(f"Query: {args.query}")
    print(f"Domain: {args.domain}")
    print(f"RAG Enabled: {args.rag}")
    print(f"Output Format: {args.output}")
    print(f"{'='*80}\n")
    
    # Apply custom settings
    if args.embedding_model:
        controller.set_rag_config(embedding_model=args.embedding_model)
    if args.llm_model:
        controller.set_rag_config(llm_model=args.llm_model)
    if args.rag_k:
        controller.set_rag_config(k=args.rag_k)
    if args.temperature:
        controller.set_rag_config(temperature=args.temperature)
    
    # Step 1: Research
    print("📚 Step 1: Performing research...")
    result = controller.research(args.query, domain=args.domain)
    print(f"   ✓ Collected {result['sources_count']} sources")
    
    # Step 2: Generate article
    print("\n📝 Step 2: Generating article...")
    article = controller.generate_article(
        args.query,
        result['sources'],
        use_rag=args.rag,
        fetch_images=not args.no_images
    )
    print(f"   ✓ Generated {len(article)} characters")
    
    # Step 3: Save output
    print("\n💾 Step 3: Saving output...")
    filepath = controller.save_output(article, args.query, format=args.output)
    print(f"   ✓ Saved to: {filepath}")
    
    print(f"\n{'='*80}")
    print("✅ Workflow Complete!")
    print(f"{'='*80}\n")


def handle_list_command(controller: ViincciController, args):
    """Handle list command"""
    print(f"\n{'='*80}")
    print(f"📋 CACHED RESEARCH SESSIONS")
    print(f"{'='*80}\n")
    
    sessions = controller.list_cached_research(domain=args.domain)
    
    if not sessions:
        print("No cached research found.")
        return
    
    # Limit results
    sessions = sessions[:args.limit]
    
    for i, session in enumerate(sessions, 1):
        print(f"{i}. {session['query']}")
        print(f"   Domain: {session['domain']}")
        print(f"   Timestamp: {session['timestamp']}")
        print(f"   Sources: {session['sources_count']}")
        print()


def handle_generate_command(controller: ViincciController, args):
    """Handle generate from cache command"""
    print(f"\n{'='*80}")
    print(f"📝 GENERATE FROM CACHED RESEARCH")
    print(f"{'='*80}\n")
    
    # Load cached research
    cached = controller.db_adapter.load_research(args.query)
    
    if not cached:
        print(f"❌ No cached research found for: {args.query}")
        return
    
    print(f"✓ Found cached research from {cached['timestamp']}")
    print(f"  Domain: {cached['domain']}")
    print(f"  Sources: {cached['sources_count']}")
    
    # Generate article
    print("\n📝 Generating article...")
    article = controller.generate_article(
        args.query,
        cached['sources'],
        use_rag=args.rag
    )
    
    # Save output
    filepath = controller.save_output(article, args.query, format=args.output)
    print(f"\n✅ Generated and saved to: {filepath}")


def handle_config_command(controller: ViincciController, args):
    """Handle config management"""
    if args.action == 'show':
        print(f"\n{'='*80}")
        print(f"⚙️  CURRENT CONFIGURATION")
        print(f"{'='*80}\n")
        print(json.dumps(controller.settings, indent=2))
    
    elif args.action == 'edit':
        if not args.key or not args.value:
            print("❌ --key and --value required for edit action")
            return
        
        # Parse nested key (e.g., "rag.retrieval.k")
        keys = args.key.split('.')
        target = controller.settings
        for key in keys[:-1]:
            target = target[key]
        
        # Try to parse value as JSON
        try:
            value = json.loads(args.value)
        except:
            value = args.value
        
        target[keys[-1]] = value
        controller._save_settings(controller.settings)
        print(f"✅ Updated {args.key} = {value}")
    
    elif args.action == 'reset':
        print("⚠️  This will reset all configuration to defaults.")
        response = input("Continue? (yes/no): ")
        if response.lower() == 'yes':
            os.remove(controller.config_file)
            print("✅ Configuration reset. Restart to apply.")


def handle_stats_command(controller: ViincciController, args):
    """Handle statistics command"""
    print(f"\n{'='*80}")
    print(f"📊 SYSTEM STATISTICS")
    print(f"{'='*80}\n")
    
    sessions = controller.list_cached_research(domain=args.domain)
    
    if not sessions:
        print("No data available.")
        return
    
    # Calculate statistics
    total_sessions = len(sessions)
    total_sources = sum(s['sources_count'] for s in sessions)
    avg_sources = total_sources / total_sessions if total_sessions > 0 else 0
    
    # Domain breakdown
    domains = {}
    for session in sessions:
        domain = session['domain']
        domains[domain] = domains.get(domain, 0) + 1
    
    print(f"Total Research Sessions: {total_sessions}")
    print(f"Total Sources Collected: {total_sources}")
    print(f"Average Sources per Session: {avg_sources:.1f}")
    print(f"\nDomain Breakdown:")
    for domain, count in sorted(domains.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {domain}: {count} sessions")
    
    print(f"\n{'='*80}\n")


def main():
    """Main CLI entry point"""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize controller
    try:
        controller = ViincciController(config_file=args.config)
        
        # Override database settings if provided
        if hasattr(args, 'db_type') and args.db_type:
            controller.settings['database']['type'] = args.db_type
        if hasattr(args, 'db_host') and args.db_host:
            controller.settings['database']['connection']['host'] = args.db_host
        if hasattr(args, 'db_port') and args.db_port:
            controller.settings['database']['connection']['port'] = args.db_port
        if hasattr(args, 'db_name') and args.db_name:
            controller.settings['database']['connection']['database'] = args.db_name
        
        # Set verbose mode
        if args.verbose:
            controller.settings['system']['verbose'] = True
            logging.getLogger().setLevel(logging.DEBUG)
        
        controller.initialize()
        
        # Route to appropriate handler
        if args.command == 'research':
            handle_research_command(controller, args)
        
        elif args.command == 'workflow':
            handle_workflow_command(controller, args)
        
        elif args.command == 'list':
            handle_list_command(controller, args)
        
        elif args.command == 'generate':
            handle_generate_command(controller, args)
        
        elif args.command == 'config':
            handle_config_command(controller, args)
        
        elif args.command == 'stats':
            handle_stats_command(controller, args)
        
        # Cleanup
        controller.shutdown()
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(0)
    
    except Exception as e:
        logging.error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
