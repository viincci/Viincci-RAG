#!/usr/bin/env python3
"""
enhanced_research_cli.py - Enhanced CLI with Multiple Output Formats
Supports HTML, Plain Text, JSON outputs and creative writing capabilities
"""
#!/usr/bin/env python3
"""
research_cli.py - Command Line Interface for Universal Research System V4
Easily perform research in any domain with API monitoring
"""

import argparse
import sys
from pathlib import Path

try:
    from V4.ConfigManager import ConfigManager
    from V4.Spider import UniversalResearchSpider, research
    from V4.ApiMonitor import SerpAPIMonitor, check_api_credits
    from V4.RagSys import RAGSystem
except ImportError as e:
    print(f"❌ Error: Could not import required modules: {e}")
    print("Please ensure the V4 package is properly installed")
    sys.exit(1)


def list_domains(config: ConfigManager):
    """List available research domains."""
    print("\n" + "="*70)
    print("🌐 Available Research Domains")
    print("="*70 + "\n")
    
    for domain in config.get_available_domains():
        info = config.get_domain_info(domain)
        current = " ⭐ (CURRENT)" if domain == config.get_current_domain() else ""
        
        print(f"🔹 {domain}{current}")
        print(f"   {info.get('description', 'No description')}")
        keywords = info.get('keywords', [])
        if keywords:
            print(f"   Keywords: {', '.join(keywords[:5])}")
        print()


def check_credits(config: ConfigManager):
    """Check SerpAPI credits."""
    monitor = SerpAPIMonitor(config)
    status = monitor.check_credits(verbose=True)
    return status['can_proceed']


def perform_research(query: str, domain: str, config: ConfigManager, use_rag: bool = False):
    """Perform research with optional RAG analysis."""
    print(f"\n🔍 Starting research...")
    print(f"   Query: {query}")
    print(f"   Domain: {domain}\n")
    
    # Switch to requested domain
    config.switch_domain(domain)
    
    # Perform research
    spider = UniversalResearchSpider(config, check_credits=True)
    sources = spider.research(query, estimate_first=True)
    
    if not sources:
        print("\n❌ No sources found or insufficient API credits")
        return
    
    print(f"\n✅ Research complete! Found {len(sources)} sources")
    
    # RAG Analysis (optional)
    if use_rag and len(sources) > 0:
        print("\n🤖 Performing RAG analysis...")
        
        try:
            rag = RAGSystem(config)
            
            # Build index from sources
            texts = [s['text'] for s in sources]
            metadata = [s['metadata'] for s in sources]
            
            rag.build_index(texts, metadata)
            
            # Load LLM
            print("   Loading LLM model (this may take a moment)...")
            rag.load_llm()
            
            # Get domain questions
            questions = config.get_domain_questions()[:3]  # Top 3 questions
            
            print("\n📝 AI Insights:\n")
            
            for i, question in enumerate(questions, 1):
                full_question = f"{query} - {question}"
                print(f"{i}. {question}")
                print("   " + "-"*60)
                
                result = rag.query(full_question, k=5, max_new_tokens=300)
                answer = result['answer'][:500]  # Limit output
                
                print(f"   {answer}")
                print()
            
            print("✅ RAG analysis complete")
            
        except Exception as e:
            print(f"\n⚠️  RAG analysis failed: {str(e)}")
            print("   Research results still saved to file")


def show_domain_info(domain: str, config: ConfigManager):
    """Show detailed information about a specific domain."""
    if domain not in config.get_available_domains():
        print(f"\n❌ Domain '{domain}' not found")
        return
    
    info = config.get_domain_info(domain)
    
    print("\n" + "="*70)
    print(f"🔬 Domain: {domain.upper()}")
    print("="*70)
    print(f"\nName: {info.get('name', 'N/A')}")
    print(f"Description: {info.get('description', 'N/A')}")
    
    print("\n📚 Primary Sources:")
    for source in info.get('primary_sources', []):
        print(f"  • {source.replace('_', ' ').title()}")
    
    print("\n❓ Research Questions:")
    for i, question in enumerate(info.get('questions', []), 1):
        print(f"  {i}. {question}")
    
    print("\n🔑 Keywords:")
    keywords = info.get('keywords', [])
    if keywords:
        print(f"  {', '.join(keywords)}")
    else:
        print("  No keywords defined")
    
    print("\n" + "="*70 + "\n")


def test_system(config: ConfigManager):
    """Run system tests to verify everything is working."""
    print("\n" + "="*70)
    print("🧪 System Test - Universal Research System V4")
    print("="*70 + "\n")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Configuration
    print("1. Testing Configuration...")
    try:
        domains = config.get_available_domains()
        assert len(domains) > 0, "No domains available"
        print(f"   ✅ Found {len(domains)} domains")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    # Test 2: Domain Switching
    print("\n2. Testing Domain Switching...")
    try:
        original_domain = config.get_current_domain()
        test_domain = 'medical' if original_domain != 'medical' else 'botany'
        
        config.switch_domain(test_domain)
        assert config.get_current_domain() == test_domain
        config.switch_domain(original_domain)
        
        print(f"   ✅ Successfully switched domains")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    # Test 3: API Monitor
    print("\n3. Testing API Monitor...")
    try:
        monitor = SerpAPIMonitor(config)
        assert monitor.warning_threshold == 100
        assert monitor.critical_threshold == 20
        print(f"   ✅ API Monitor initialized correctly")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    # Test 4: RAG System
    print("\n4. Testing RAG System...")
    try:
        rag = RAGSystem(config)
        assert rag.embedding_model is not None
        
        # Test index building
        test_texts = ["Test document 1", "Test document 2"]
        test_metadata = [{"source": "test1"}, {"source": "test2"}]
        rag.build_index(test_texts, test_metadata)
        
        assert rag.index.ntotal == 2
        print(f"   ✅ RAG System working correctly")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    # Test 5: Article Generator
    print("\n5. Testing Article Generator...")
    try:
        from V4.UniversalArticleGenerator import UniversalArticleGenerator
        generator = UniversalArticleGenerator(config, fetch_images=False)
        assert generator is not None
        
        sections = generator.get_domain_sections("Test Topic")
        assert len(sections) > 0
        print(f"   ✅ Article Generator initialized")
        tests_passed += 1
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        tests_failed += 1
    
    # Summary
    print("\n" + "="*70)
    print(f"Test Results: {tests_passed} passed, {tests_failed} failed")
    print("="*70 + "\n")
    
    if tests_failed == 0:
        print("✅ All systems operational!\n")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.\n")
        return False


def oldmain():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Universal Research System V4 - Multi-Domain Research with API Monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available domains
  python research_cli.py --list-domains
  
  # Show information about a domain
  python research_cli.py --domain-info medical
  
  # Check API credits
  python research_cli.py --check-credits
  
  # Test the system
  python research_cli.py --test
  
  # Research in botany domain
  python research_cli.py -q "Rosa rubiginosa" -d botany
  
  # Research in medical domain with RAG analysis
  python research_cli.py -q "diabetes mellitus" -d medical --rag
  
  # Research in mathematics domain
  python research_cli.py -q "Pythagorean theorem" -d mathematics
  
  # Research in carpentry domain
  python research_cli.py -q "dovetail joints" -d carpentry
        """
    )
    
    parser.add_argument(
        '-q', '--query',
        type=str,
        help='Research query/topic'
    )
    
    parser.add_argument(
        '-d', '--domain',
        type=str,
        default='botany',
        help='Research domain (default: botany)'
    )
    
    parser.add_argument(
        '--list-domains',
        action='store_true',
        help='List all available research domains'
    )
    
    parser.add_argument(
        '--domain-info',
        type=str,
        metavar='DOMAIN',
        help='Show detailed information about a specific domain'
    )
    
    parser.add_argument(
        '--check-credits',
        action='store_true',
        help='Check SerpAPI credit status'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run system tests to verify everything is working'
    )
    
    parser.add_argument(
        '--rag',
        action='store_true',
        help='Perform RAG analysis with LiquidAI (requires GPU/powerful CPU)'
    )
    
    parser.add_argument(
        '--no-credit-check',
        action='store_true',
        help='Skip API credit checking (not recommended)'
    )
    
    parser.add_argument(
        '--config-dir',
        type=str,
        help='Custom configuration directory'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Initialize config
    try:
        config = ConfigManager(
            config_dir=args.config_dir,
            domain=args.domain,
            verbose=args.verbose
        )
    except Exception as e:
        print(f"❌ Error initializing configuration: {e}")
        sys.exit(1)
    
    # Handle commands
    if args.list_domains:
        list_domains(config)
        return
    
    if args.domain_info:
        show_domain_info(args.domain_info, config)
        return
    
    if args.check_credits:
        can_proceed = check_credits(config)
        sys.exit(0 if can_proceed else 1)
    
    if args.test:
        success = test_system(config)
        sys.exit(0 if success else 1)
    
    if not args.query:
        parser.print_help()
        print("\n💡 Tip: Use --test to verify your system is working correctly")
        print("💡 Tip: Use --list-domains to see available research domains")
        sys.exit(0)
    
    # Validate domain
    if args.domain not in config.get_available_domains():
        print(f"\n❌ Error: Unknown domain '{args.domain}'")
        print("\nAvailable domains:")
        for d in config.get_available_domains():
            print(f"  • {d}")
        sys.exit(1)
    
    # Check credits unless disabled
    if not args.no_credit_check:
        if not check_credits(config):
            print("\n⚠️  Insufficient API credits. Use --no-credit-check to override (not recommended)")
            sys.exit(1)
    
    # Perform research
    try:
        perform_research(args.query, args.domain, config, use_rag=args.rag)
    except KeyboardInterrupt:
        print("\n\n⚠️  Research interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

try:
    from V4.ConfigManager import ConfigManager
    from V4.Spider import UniversalResearchSpider
    from V4.ApiMonitor import SerpAPIMonitor
    from V4.RagSys import RAGSystem
    from V4.UniversalArticleGenerator import UniversalArticleGenerator
except ImportError as e:
    print(f"❌ Error: Could not import required modules: {e}")
    sys.exit(1)


class OutputFormatter:
    """Handle multiple output formats"""
    
    def __init__(self, format_type: str = 'html'):
        self.format_type = format_type.lower()
    
    def format_article(self, content: str, metadata: Dict) -> str:
        """Format article based on output type"""
        if self.format_type == 'text':
            return self._to_plain_text(content, metadata)
        elif self.format_type == 'json':
            return self._to_json(content, metadata)
        else:  # html
            return content
    
    def _to_plain_text(self, content: str, metadata: Dict) -> str:
        """Convert HTML to plain text"""
        import re
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', content)
        
        # Clean up extra whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Add metadata header
        header = f"""
{'='*70}
{metadata.get('title', 'Article')}
{'='*70}
Subtitle: {metadata.get('subtitle', '')}
Domain: {metadata.get('domain', 'N/A')}
Generated: {metadata.get('date', datetime.now().strftime('%Y-%m-%d'))}
{'='*70}

"""
        return header + text
    
    def _to_json(self, content: str, metadata: Dict) -> str:
        """Convert to JSON format"""
        import re
        
        # Extract sections
        sections = []
        current_section = None
        current_content = []
        
        for line in content.split('\n'):
            if '<h2' in line or '<h3' in line:
                # Save previous section
                if current_section:
                    sections.append({
                        'heading': current_section,
                        'content': '\n'.join(current_content).strip()
                    })
                # Start new section
                current_section = re.sub(r'<[^>]+>', '', line).strip()
                current_content = []
            else:
                current_content.append(line)
        
        # Add last section
        if current_section:
            sections.append({
                'heading': current_section,
                'content': '\n'.join(current_content).strip()
            })
        
        output = {
            'metadata': metadata,
            'sections': sections,
            'full_html': content
        }
        
        return json.dumps(output, indent=2, ensure_ascii=False)
    
    def get_file_extension(self) -> str:
        """Get appropriate file extension"""
        extensions = {
            'html': '.html',
            'text': '.txt',
            'json': '.json'
        }
        return extensions.get(self.format_type, '.html')


class CreativeWriter:
    """Generate creative content like poems and essays"""
    
    def __init__(self, config: ConfigManager, rag_system: Optional[RAGSystem] = None):
        self.config = config
        self.rag_system = rag_system
    
    def write_poem(self, topic: str, style: str = "free verse", research_data: List[Dict] = None) -> str:
        """Generate a poem about a topic"""
        
        if self.rag_system and research_data:
            # Build context from research
            texts = [s['text'] for s in research_data]
            metadata = [s['metadata'] for s in research_data]
            self.rag_system.build_index(texts, metadata)
            
            if not self.rag_system.is_llm_loaded():
                self.rag_system.load_llm()
            
            prompt = f"Write a {style} poem about {topic}. Make it vivid, evocative, and emotionally resonant."
            result = self.rag_system.query(prompt, k=5, max_new_tokens=500, temperature=0.9)
            return result['answer']
        else:
            # Basic template without RAG
            return f"""
A {style} poem about {topic}

[Generated poem would appear here with RAG/LLM]
To generate actual poems, use --rag flag and ensure research data is available.
"""
    
    def write_essay(self, topic: str, essay_type: str = "expository", 
                   research_data: List[Dict] = None, word_count: int = 1000) -> str:
        """Generate an essay"""
        
        if self.rag_system and research_data:
            texts = [s['text'] for s in research_data]
            metadata = [s['metadata'] for s in research_data]
            self.rag_system.build_index(texts, metadata)
            
            if not self.rag_system.is_llm_loaded():
                self.rag_system.load_llm()
            
            sections = []
            
            # Introduction
            intro_prompt = f"Write a compelling introduction for a {essay_type} essay about {topic}."
            intro = self.rag_system.query(intro_prompt, k=5, max_new_tokens=300)
            sections.append(f"<h2>Introduction</h2>\n<p>{intro['answer']}</p>")
            
            # Body paragraphs
            body_prompts = [
                f"Discuss the main aspects and characteristics of {topic}.",
                f"Analyze the significance and implications of {topic}.",
                f"Explore different perspectives or applications related to {topic}."
            ]
            
            for i, prompt in enumerate(body_prompts, 1):
                result = self.rag_system.query(prompt, k=5, max_new_tokens=300)
                sections.append(f"<h2>Body Paragraph {i}</h2>\n<p>{result['answer']}</p>")
            
            # Conclusion
            conclusion_prompt = f"Write a thoughtful conclusion summarizing the key points about {topic}."
            conclusion = self.rag_system.query(conclusion_prompt, k=5, max_new_tokens=250)
            sections.append(f"<h2>Conclusion</h2>\n<p>{conclusion['answer']}</p>")
            
            return "\n\n".join(sections)
        else:
            return f"""
Essay: {topic}
Type: {essay_type}
Target Length: {word_count} words

[Generated essay would appear here with RAG/LLM]
To generate actual essays, use --rag flag and ensure research data is available.
"""


def get_extended_domains():
    """Get extended domains including art and creative fields (backward compatible)"""
    extended_domains = {
        "art_history": {
            "name": "Art History Research",
            "description": "Art movements, artists, techniques, and historical periods",
            "primary_sources": ["museum", "university", "art_institute", "gallery"],
            "questions": [
                "what are the key characteristics of this art movement",
                "who were the major artists and their contributions",
                "what was the historical and cultural context",
                "what techniques and materials were used",
                "what is the lasting influence and legacy"
            ],
            "keywords": ["art", "artist", "painting", "sculpture", "movement", "style", "technique"]
        },
        "literature": {
            "name": "Literature Research",
            "description": "Literary works, authors, movements, and analysis",
            "primary_sources": ["university", "library", "literary_journal", "archive"],
            "questions": [
                "what are the themes and motifs",
                "what is the historical and biographical context",
                "what are the literary techniques used",
                "how was it received and interpreted",
                "what is its cultural significance"
            ],
            "keywords": ["literature", "author", "novel", "poetry", "literary", "writing", "text"]
        },
        "music": {
            "name": "Music Research",
            "description": "Musical genres, composers, theory, and history",
            "primary_sources": ["university", "conservatory", "music_journal", "archive"],
            "questions": [
                "what are the musical characteristics",
                "who were the key composers or performers",
                "what is the historical development",
                "what are the theoretical elements",
                "what is the cultural impact"
            ],
            "keywords": ["music", "composer", "musical", "symphony", "composition", "genre"]
        },
        "creative_writing": {
            "name": "Creative Writing",
            "description": "Fiction, poetry, narrative techniques, and storytelling",
            "primary_sources": ["university", "writing_workshop", "literary_magazine"],
            "questions": [
                "what are the narrative techniques",
                "what are the elements of craft",
                "what are the stylistic approaches",
                "what are contemporary trends",
                "what are best practices and examples"
            ],
            "keywords": ["writing", "narrative", "story", "fiction", "poetry", "creative"]
        }
    }
    
    return extended_domains


def check_and_add_extended_domains(config: ConfigManager):
    """Check if extended domains exist, add them if missing (backward compatible)"""
    domains_file = Path(config.config_dir) / 'domains.json'
    
    # Load existing domains
    with open(domains_file, 'r') as f:
        existing_domains = json.load(f)
    
    extended = get_extended_domains()
    added_domains = []
    
    # Only add domains that don't exist
    for domain_key, domain_config in extended.items():
        if domain_key not in existing_domains:
            existing_domains[domain_key] = domain_config
            added_domains.append(domain_key)
    
    # Save if any domains were added
    if added_domains:
        with open(domains_file, 'w') as f:
            json.dump(existing_domains, f, indent=2)
        return added_domains
    
    return []


def ensure_backward_compatibility(config: ConfigManager):
    """Ensure all old functionality works with new features"""
    # Auto-add extended domains if they don't exist
    added = check_and_add_extended_domains(config)
    
    if added:
        print(f"\n✨ Auto-added {len(added)} new domains: {', '.join(added)}")
        print("   (All existing domains preserved)")
    
    # Verify core domains still exist
    core_domains = ['botany', 'medical', 'mathematics', 'carpentry']
    available = config.get_available_domains()
    
    for core in core_domains:
        if core not in available:
            print(f"⚠️  Warning: Core domain '{core}' missing from configuration")
    
    return True


def perform_research(args, config: ConfigManager):
    """Perform research and generate output (backward compatible)"""
    
    # Ensure backward compatibility - add extended domains if needed
    ensure_backward_compatibility(config)
    
    print(f"\n🔍 Starting research...")
    print(f"   Query: {args.query}")
    print(f"   Domain: {args.domain}")
    print(f"   Output Format: {args.format}")
    
    if args.content_type in ['poem', 'essay']:
        print(f"   Content Type: {args.content_type}")
    
    # Switch domain (supports both old and new domains)
    if not config.switch_domain(args.domain):
        print(f"\n❌ Could not switch to domain: {args.domain}")
        return
    
    # Collect research data (same as before - backward compatible)
    spider = UniversalResearchSpider(config, check_credits=not args.no_credit_check)
    sources = spider.research(args.query, estimate_first=not args.no_credit_check)
    
    if not sources:
        print("\n❌ No sources found or insufficient API credits")
        return
    
    print(f"\n✅ Research complete! Found {len(sources)} sources")
    
    # Initialize RAG if requested (backward compatible)
    rag_system = None
    if args.rag:
        print("\n🤖 Initializing RAG system...")
        try:
            rag_system = RAGSystem(config)
            texts = [s['text'] for s in sources]
            metadata = [s['metadata'] for s in sources]
            rag_system.build_index(texts, metadata)
            rag_system.load_llm()
            print("✅ RAG system ready")
        except Exception as e:
            print(f"⚠️  RAG initialization failed: {e}")
            rag_system = None
    
    # Generate content based on type
    output_formatter = OutputFormatter(args.format)
    
    if args.content_type == 'poem':
        print("\n📝 Generating poem...")
        writer = CreativeWriter(config, rag_system)
        content = writer.write_poem(args.query, args.poem_style, sources)
        
        metadata = {
            'title': f'Poem: {args.query}',
            'subtitle': f'A {args.poem_style} composition',
            'domain': args.domain,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        
    elif args.content_type == 'essay':
        print("\n📝 Generating essay...")
        writer = CreativeWriter(config, rag_system)
        content = writer.write_essay(args.query, args.essay_type, sources, args.word_count)
        
        metadata = {
            'title': f'Essay: {args.query}',
            'subtitle': f'A {args.essay_type} analysis',
            'domain': args.domain,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        
    else:  # article (default - backward compatible)
        print("\n📝 Generating article...")
        generator = UniversalArticleGenerator(
            config=config,
            rag_system=rag_system,
            fetch_images=args.fetch_images
        )
        content = generator.generate_full_article(args.query, sources)
        
        metadata = {
            'title': f'Article: {args.query}',
            'subtitle': 'Comprehensive research article',
            'domain': args.domain,
            'date': datetime.now().strftime('%Y-%m-%d')
        }
    
    # Format output
    formatted_content = output_formatter.format_article(content, metadata)
    
    # Save to file
    safe_filename = args.query.lower().replace(' ', '-').replace('/', '-')
    date_str = datetime.now().strftime('%Y-%m-%d')
    extension = output_formatter.get_file_extension()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = output_dir / f"{date_str}-{safe_filename}{extension}"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(formatted_content)
    
    print(f"\n✅ Content generated successfully!")
    print(f"📁 Saved to: {filename}")
    print(f"📊 Size: {len(formatted_content):,} characters")
    
    # Also save metadata separately if JSON format
    if args.format == 'json':
        meta_file = output_dir / f"{date_str}-{safe_filename}-metadata.json"
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        print(f"📁 Metadata: {meta_file}")


def main():
    """Enhanced CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Enhanced Universal Research System V4 - Multi-Format Output & Creative Writing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Output Formats:
  --format html     Generate HTML article (default)
  --format text     Generate plain text article
  --format json     Generate JSON with structured data

Content Types:
  --content-type article    Research article (default)
  --content-type poem       Generate poem from research
  --content-type essay      Generate essay from research

Art & Creative Domains:
  - art_history: Art movements, artists, techniques
  - literature: Literary works, authors, analysis  
  - music: Musical genres, composers, theory
  - creative_writing: Fiction, poetry, narrative

Examples:
  # Standard HTML article
  python enhanced_research_cli.py -q "Rosa rubiginosa" -d botany
  
  # Plain text output
  python enhanced_research_cli.py -q "diabetes" -d medical --format text
  
  # JSON structured output
  python enhanced_research_cli.py -q "Pythagorean theorem" -d mathematics --format json
  
  # Research art movement and generate article
  python enhanced_research_cli.py -q "Impressionism" -d art_history
  
  # Generate poem with RAG
  python enhanced_research_cli.py -q "Van Gogh" -d art_history --content-type poem --rag
  
  # Generate essay about music
  python enhanced_research_cli.py -q "Baroque music" -d music --content-type essay --rag
  
  # Literature research with essay output
  python enhanced_research_cli.py -q "Shakespeare sonnets" -d literature --content-type essay
        """
    )
    
    # Basic arguments
    parser.add_argument('-q', '--query', type=str, help='Research query/topic')
    parser.add_argument('-d', '--domain', type=str, default='botany', 
                       help='Research domain')
    
    # Output format
    parser.add_argument('--format', type=str, choices=['html', 'text', 'json'],
                       default='html', help='Output format (default: html)')
    
    # Content type
    parser.add_argument('--content-type', type=str, 
                       choices=['article', 'poem', 'essay'],
                       default='article', help='Type of content to generate')
    
    # Creative writing options
    parser.add_argument('--poem-style', type=str, default='free verse',
                       help='Style of poem (e.g., "sonnet", "haiku", "free verse")')
    parser.add_argument('--essay-type', type=str, default='expository',
                       help='Type of essay (e.g., "expository", "argumentative", "analytical")')
    parser.add_argument('--word-count', type=int, default=1000,
                       help='Target word count for essays')
    
    # Research options
    parser.add_argument('--rag', action='store_true',
                       help='Use RAG for intelligent generation')
    parser.add_argument('--fetch-images', action='store_true', default=True,
                       help='Fetch images from Wikimedia Commons')
    parser.add_argument('--no-credit-check', action='store_true',
                       help='Skip API credit checking')
    
    # Output options
    parser.add_argument('--output-dir', type=str, default='_posts',
                       help='Output directory (default: _posts)')
    
    # Utility commands
    parser.add_argument('--list-domains', action='store_true',
                       help='List all available domains')
    parser.add_argument('--domain-info', type=str, metavar='DOMAIN',
                       help='Show detailed domain information')
    parser.add_argument('--check-credits', action='store_true',
                       help='Check SerpAPI credit status')
    parser.add_argument('--add-art-domains', action='store_true',
                       help='Add art/creative domains to configuration')
    
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Initialize config
    try:
        config = ConfigManager(domain=args.domain, verbose=args.verbose)
        
        # Ensure backward compatibility on startup
        ensure_backward_compatibility(config)
        
    except Exception as e:
        print(f"❌ Error initializing configuration: {e}")
        sys.exit(1)
    
    # Handle utility commands
    if args.list_domains:
        #from research_cli import list_domains
        list_domains(config)
        return
    
    if args.domain_info:
        #from research_cli import show_domain_info
        show_domain_info(args.domain_info, config)
        return
    
    if args.check_credits:
        #from research_cli import check_credits
        can_proceed = check_credits(config)
        sys.exit(0 if can_proceed else 1)
    
    if args.add_art_domains:
        print("\n📚 Manually adding art and creative domains...")
        added = check_and_add_extended_domains(config)
        
        if added:
            print(f"✅ Added {len(added)} new domains:")
            for domain in added:
                print(f"  • {domain}")
        else:
            print("ℹ️  All extended domains already exist in configuration")
        
        print("\n💡 These domains are now available for use!")
        return
    
    if not args.query:
        parser.print_help()
        print("\n💡 Tip: All original domains (botany, medical, mathematics, carpentry) are preserved")
        print("💡 Tip: New domains are automatically added on first use")
        print("💡 Tip: Use --list-domains to see all available research domains")
        sys.exit(0)
    
    # Validate domain (backward compatible - checks both old and new domains)
    available_domains = config.get_available_domains()
    extended_domains = get_extended_domains()
    
    if args.domain not in available_domains:
        # Check if it's an extended domain that needs to be added
        if args.domain in extended_domains:
            print(f"\n✨ Auto-adding domain '{args.domain}' to configuration...")
            added = check_and_add_extended_domains(config)
            if added:
                print(f"✅ Domain '{args.domain}' is now available!")
                # Reinitialize config to pick up new domain
                config = ConfigManager(domain=args.domain, verbose=args.verbose)
            else:
                print(f"✅ Domain '{args.domain}' already configured")
        else:
            print(f"\n❌ Error: Unknown domain '{args.domain}'")
            print("\nAvailable domains:")
            for d in available_domains:
                print(f"  • {d}")
            print("\nExtended domains (auto-added on use):")
            for d in extended_domains.keys():
                print(f"  • {d} (creative/art)")
        sys.exit(1)
    
    # Perform research and generate output
    try:
        perform_research(args, config)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
