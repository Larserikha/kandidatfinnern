"""
ChromaDB Indexer for CV-RAG System
Handles indexing, chunking, and searching of CVs in the local vector database
"""
import chromadb
from chromadb.config import Settings
from pathlib import Path
from typing import List, Dict, Optional
import logging
import re
import json
from datetime import datetime

import config
from cv_embeddings import LocalEmbeddingFunction

logger = logging.getLogger(__name__)

# Lazy import of cross-encoder (only if re-ranking is enabled)
_reranker = None

def _get_reranker():
    """Lazy-load cross-encoder reranker (only if enabled)"""
    global _reranker
    if config.ENABLE_RERANKING:
        if _reranker is None:
            try:
                from cross_encoder_reranker import CrossEncoderReranker
                _reranker = CrossEncoderReranker()
                logger.info("Cross-encoder reranker initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize cross-encoder reranker: {e}")
                logger.warning("Continuing without re-ranking")
                _reranker = False  # Mark as failed to avoid retrying
    return _reranker


class CVIndexer:
    """
    Main indexer class for managing CV embeddings in ChromaDB
    
    Responsibilities:
    - Load and chunk CV documents
    - Index chunks with embeddings in ChromaDB
    - Perform semantic search
    - Manage metadata
    """
    
    def __init__(self, reset: bool = False):
        """
        Initialize the CVIndexer with ChromaDB
        
        Args:
            reset: If True, delete existing collection and start fresh
        """
        logger.info("Initializing CVIndexer...")
        
        # Initialize embedding function
        self.embedding_function = LocalEmbeddingFunction()
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(config.CHROMADB_DIR),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        if reset:
            try:
                self.client.delete_collection(name=config.CHROMADB_COLLECTION_NAME)
                logger.info(f"Deleted existing collection: {config.CHROMADB_COLLECTION_NAME}")
            except:
                pass
        
        self.collection = self.client.get_or_create_collection(
            name=config.CHROMADB_COLLECTION_NAME,
            embedding_function=self.embedding_function,
            metadata={
                "description": "CV database for semantic search",
                "created": datetime.now().isoformat()
            }
        )
        
        logger.info(f"Collection '{config.CHROMADB_COLLECTION_NAME}' ready")
        logger.info(f"Current document count: {self.collection.count()}")
    
    def _split_into_chunks(self, text: str, chunk_size: int = None, overlap: int = None) -> List[str]:
        """
        Split text into overlapping chunks based on word count
        
        Args:
            text: Text to split
            chunk_size: Size of chunks in words (defaults to config.CHUNK_SIZE)
            overlap: Overlap between chunks in words (defaults to config.CHUNK_OVERLAP)
            
        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or config.CHUNK_SIZE
        overlap = overlap or config.CHUNK_OVERLAP
        
        # Split into words (preserving whitespace structure roughly)
        words = text.split()
        
        if len(words) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(words):
            end = start + chunk_size
            chunk_words = words[start:end]
            
            # Skip very small chunks at the end
            if len(chunk_words) >= config.MIN_CHUNK_SIZE:
                chunk = " ".join(chunk_words)
                chunks.append(chunk)
            
            # Move forward by (chunk_size - overlap)
            start += (chunk_size - overlap)
            
            # Break if we've passed the end
            if start >= len(words):
                break
        
        return chunks
    
    def _parse_cv_file(self, file_path: Path) -> tuple[str, Dict]:
        """
        Parse CV file (JSON or Markdown) and extract text + metadata
        
        Args:
            file_path: Path to CV file
            
        Returns:
            Tuple of (text_content, metadata_dict)
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            return "", {}
        
        # Check if file is JSON
        if file_path.suffix == '.json':
            try:
                cv_data = json.loads(content)
                text = self._extract_text_from_json(cv_data)
                
                # Get user metadata (office, etc) if available
                user_meta = cv_data.get('_user_metadata', {})
                
                metadata = {
                    "source": file_path.name,
                    "file_path": str(file_path),
                    "cv_name": cv_data.get('name', file_path.stem.replace("-", " ").replace("_", " ").title()),
                    "office": user_meta.get('office_name', ''),
                }
                
                # Add years of experience if available
                if 'years_of_experience' in cv_data:
                    metadata['years_of_experience'] = cv_data['years_of_experience']
                return text, metadata
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from {file_path}: {e}")
                return "", {}
        else:
            # Markdown or plain text
            metadata = {
                "source": file_path.name,
                "file_path": str(file_path),
                "cv_name": file_path.stem.replace("-", " ").replace("_", " ").title(),
            }
            return content, metadata
    
    def _extract_text_from_json(self, cv_data: Dict) -> str:
        """
        Extract searchable text from Flowcase JSON CV data
        
        Args:
            cv_data: Parsed JSON CV data
            
        Returns:
            Text content for embedding
        """
        lines = []
        
        # Name and contact
        if cv_data.get('name'):
            lines.append(f"# {cv_data['name']}")
        
        # Office/Department - make it prominent
        user_meta = cv_data.get('_user_metadata', {})
        office = user_meta.get('office_name', '')
        if office:
            lines.append(f"**Avdeling:** {office}")
        
        # Profile/summary
        for field in ['summary', 'profile', 'description']:
            value = cv_data.get(field)
            if value and isinstance(value, (str, dict)):
                if isinstance(value, dict):
                    # Handle multilingual fields
                    value = value.get('no', value.get('en', value.get('int', '')))
                if isinstance(value, str) and value.strip():
                    lines.append(f"\n{value}")
        
        # Technologies/skills
        if cv_data.get('technologies'):
            techs = []
            for t in cv_data['technologies']:
                if isinstance(t, dict):
                    # Skip disabled technology categories
                    if t.get('disabled'):
                        continue
                    
                    # Extract individual technology skills from technology_skills array
                    if t.get('technology_skills'):
                        for skill in t['technology_skills']:
                            if isinstance(skill, dict):
                                tags = skill.get('tags', {})
                                if isinstance(tags, dict):
                                    skill_name = tags.get('no', tags.get('en', tags.get('int', '')))
                                    if skill_name and isinstance(skill_name, str):
                                        techs.append(skill_name)
                    
                    # Fallback: try to get name or category if no skills found
                    if not t.get('technology_skills'):
                        name = t.get('name', '')
                        if isinstance(name, str) and name:
                            techs.append(name)
                        elif t.get('category') and isinstance(t.get('category'), dict):
                            cat = t.get('category', {})
                            cat_name = cat.get('no', cat.get('en', cat.get('int', '')))
                            if isinstance(cat_name, str) and cat_name:
                                techs.append(cat_name)
            if techs:
                lines.append(f"\n## Technologies\n{', '.join(techs)}")
        
        # Work experiences
        if cv_data.get('work_experiences'):
            lines.append("\n## Work Experience")
            for exp in cv_data['work_experiences']:
                if isinstance(exp, dict):
                    # Handle multilingual fields
                    employer = exp.get('employer', '')
                    if isinstance(employer, dict):
                        employer = employer.get('no', employer.get('en', employer.get('int', '')))
                    employer = str(employer) if employer else ''
                    
                    role = exp.get('role', exp.get('title', ''))
                    if isinstance(role, dict):
                        role = role.get('no', role.get('en', role.get('int', '')))
                    role = str(role) if role else ''
                    
                    desc = exp.get('description', exp.get('long_description', ''))
                    if isinstance(desc, dict):
                        desc = desc.get('no', desc.get('en', desc.get('int', '')))
                    if not isinstance(desc, str):
                        desc = ''
                    
                    if employer or role:
                        lines.append(f"\n### {role} at {employer}")
                    if desc and desc.strip():
                        lines.append(desc)
        
        # Education
        if cv_data.get('educations'):
            lines.append("\n## Education")
            for edu in cv_data['educations']:
                if isinstance(edu, dict):
                    school = edu.get('school', '')
                    if isinstance(school, dict):
                        school = school.get('no', school.get('en', school.get('int', '')))
                    school = str(school) if school else ''
                    
                    degree = edu.get('degree', edu.get('title', ''))
                    if isinstance(degree, dict):
                        degree = degree.get('no', degree.get('en', degree.get('int', '')))
                    degree = str(degree) if degree else ''
                    
                    if school or degree:
                        lines.append(f"\n{degree} - {school}")
        
        # Key qualifications (project descriptions, roles, etc.)
        if cv_data.get('key_qualifications'):
            quals = cv_data.get('key_qualifications')
            if isinstance(quals, list):
                lines.append("\n## Key Qualifications")
                for qual in quals:
                    if isinstance(qual, dict):
                        # Skip disabled entries
                        if qual.get('disabled'):
                            continue
                        
                        # Extract label (project/role name)
                        label = qual.get('label', '')
                        if isinstance(label, dict):
                            label = label.get('no', label.get('en', label.get('int', '')))
                        label = str(label) if label else ''
                        
                        # Extract long_description (main content)
                        desc = qual.get('long_description', qual.get('description', ''))
                        if isinstance(desc, dict):
                            desc = desc.get('no', desc.get('en', desc.get('int', '')))
                        if not isinstance(desc, str):
                            desc = ''
                        
                        # Extract text field as fallback
                        if not desc:
                            text = qual.get('text', '')
                            if isinstance(text, dict):
                                text = text.get('no', text.get('en', text.get('int', '')))
                            desc = str(text) if text else ''
                        
                        # Add the qualification with label if available
                        if label and desc.strip():
                            lines.append(f"\n### {label}")
                            lines.append(desc)
                        elif desc.strip():
                            lines.append(f"\n{desc}")
                    elif isinstance(qual, str):
                        lines.append(f"- {qual}")
        
        # Project experiences (detailed project descriptions)
        if cv_data.get('project_experiences'):
            projects = cv_data.get('project_experiences')
            if isinstance(projects, list):
                lines.append("\n## Project Experiences")
                for proj in projects:
                    if isinstance(proj, dict):
                        # Skip disabled entries
                        if proj.get('disabled'):
                            continue
                        
                        # Extract customer/client
                        customer = proj.get('customer', '')
                        if isinstance(customer, dict):
                            customer = customer.get('no', customer.get('en', customer.get('int', '')))
                        customer = str(customer) if customer else ''
                        
                        # Extract role
                        role = proj.get('role', '')
                        if isinstance(role, dict):
                            role = role.get('no', role.get('en', role.get('int', '')))
                        role = str(role) if role else ''
                        
                        # Extract description (prefer long_description over short description)
                        long_desc = proj.get('long_description', '')
                        if isinstance(long_desc, dict):
                            long_desc = long_desc.get('no', long_desc.get('en', long_desc.get('int', '')))
                        if not isinstance(long_desc, str):
                            long_desc = ''
                        
                        # Use short description as title if no long description
                        short_desc = proj.get('description', '')
                        if isinstance(short_desc, dict):
                            short_desc = short_desc.get('no', short_desc.get('en', short_desc.get('int', '')))
                        if not isinstance(short_desc, str):
                            short_desc = ''
                        
                        # Prefer long_description, fallback to short
                        desc = long_desc if long_desc.strip() else short_desc
                        
                        # Build project header
                        header_parts = []
                        
                        # Use short_desc as project title if available
                        if short_desc:
                            header_parts.append(short_desc)
                        elif role:
                            header_parts.append(role)
                        
                        if customer:
                            header_parts.append(f"@ {customer}")
                        
                        if header_parts:
                            lines.append(f"\n### {' '.join(header_parts)}")
                        
                        # Add long description if available
                        if long_desc.strip():
                            lines.append(long_desc)
        
        return "\n".join(filter(None, lines))
    
    def _extract_cv_metadata(self, file_path: Path, text: str) -> Dict[str, str]:
        """
        DEPRECATED: Use _parse_cv_file instead
        Extract metadata from CV file
        """
        metadata = {
            "source": file_path.name,
            "file_path": str(file_path),
        }
        
        name = file_path.stem.replace("-", " ").replace("_", " ").title()
        metadata["cv_name"] = name
        
        return metadata
    
    def index_cv(self, file_path: Path) -> int:
        """
        Index a single CV file (JSON or Markdown)
        
        Args:
            file_path: Path to CV file
            
        Returns:
            Number of chunks created
        """
        logger.info(f"Indexing CV: {file_path.name}")
        
        # Parse file (handles both JSON and Markdown)
        try:
            content, base_metadata = self._parse_cv_file(file_path)
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            return 0
        
        if not content.strip():
            logger.warning(f"Skipping empty file: {file_path.name}")
            return 0
        
        # Split into chunks
        chunks = self._split_into_chunks(content)
        logger.info(f"  Split into {len(chunks)} chunks")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            # Create unique ID for this chunk
            chunk_id = f"{file_path.stem}_{i}"
            
            # Metadata for this chunk
            chunk_metadata = base_metadata.copy()
            chunk_metadata.update({
                "chunk_id": i,
                "total_chunks": len(chunks)
            })
            
            ids.append(chunk_id)
            documents.append(chunk)
            metadatas.append(chunk_metadata)
        
        # Add to ChromaDB
        try:
            self.collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            logger.info(f"  ✅ Indexed {len(chunks)} chunks from {file_path.name}")
            return len(chunks)
        
        except Exception as e:
            logger.error(f"  ❌ Failed to index {file_path.name}: {e}")
            return 0
    
    def index_all_cvs(self, cvs_dir: Path = None) -> Dict[str, int]:
        """
        Index all CVs in the CVs directory
        
        Args:
            cvs_dir: Directory containing CV files (defaults to config.CVS_DIR)
            
        Returns:
            Dictionary with indexing statistics
        """
        cvs_dir = cvs_dir or config.CVS_DIR
        
        logger.info(f"Indexing all CVs from: {cvs_dir}")
        
        # Find all CV files
        cv_files = []
        for ext in config.SUPPORTED_CV_FORMATS:
            cv_files.extend(cvs_dir.glob(f"*{ext}"))
        
        if not cv_files:
            logger.warning(f"No CV files found in {cvs_dir}")
            logger.warning(f"Supported formats: {config.SUPPORTED_CV_FORMATS}")
            return {"total_files": 0, "total_chunks": 0, "failed": 0}
        
        logger.info(f"Found {len(cv_files)} CV files")
        
        # Index each file
        total_chunks = 0
        failed = 0
        
        for cv_file in cv_files:
            chunks = self.index_cv(cv_file)
            if chunks > 0:
                total_chunks += chunks
            else:
                failed += 1
        
        stats = {
            "total_files": len(cv_files),
            "total_chunks": total_chunks,
            "failed": failed,
            "success": len(cv_files) - failed
        }
        
        logger.info(f"Indexing complete: {stats}")
        return stats
    
    def search(
        self,
        query: str,
        n_results: int = None,
        filter_metadata: Optional[Dict] = None,
        use_reranking: bool = None
    ) -> Dict:
        """
        Search for relevant CV chunks using semantic search
        
        Args:
            query: Search query
            n_results: Number of results to return (defaults to config.DEFAULT_SEARCH_RESULTS)
            filter_metadata: Optional metadata filters (e.g., {"source": "ola-nordmann.md"})
            use_reranking: Whether to use cross-encoder re-ranking (defaults to config.ENABLE_RERANKING)
            
        Returns:
            Dictionary with search results containing:
            - ids: List of chunk IDs
            - documents: List of matching text chunks
            - metadatas: List of metadata dictionaries
            - distances: List of distance scores (lower is better)
            - rerank_scores: List of cross-encoder scores (if re-ranking was used)
        """
        n_results = n_results or config.DEFAULT_SEARCH_RESULTS
        n_results = min(n_results, config.MAX_SEARCH_RESULTS)
        
        # Determine if re-ranking should be used
        if use_reranking is None:
            use_reranking = config.ENABLE_RERANKING
        
        # If re-ranking is enabled, fetch more candidates than requested
        # Then re-rank and return top n_results
        fetch_count = config.RERANK_TOP_K if use_reranking else n_results
        fetch_count = max(fetch_count, n_results)  # At least fetch what we need
        
        logger.info(f"Searching for: '{query}' (returning {n_results} results, re-ranking: {use_reranking})")
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=fetch_count,
                where=filter_metadata
            )
            
            # ChromaDB returns nested lists, flatten for single query
            if results['ids']:
                search_results = {
                    "ids": results['ids'][0],
                    "documents": results['documents'][0],
                    "metadatas": results['metadatas'][0],
                    "distances": results['distances'][0] if 'distances' in results else []
                }
            else:
                return {
                    "ids": [],
                    "documents": [],
                    "metadatas": [],
                    "distances": []
                }
            
            # Apply cross-encoder re-ranking if enabled
            if use_reranking and len(search_results['documents']) > 0:
                reranker = _get_reranker()
                if reranker and reranker is not False:  # Check if reranker is available
                    logger.info(f"Re-ranking {len(search_results['documents'])} candidates...")
                    search_results = reranker.rerank_search_results(
                        query,
                        search_results,
                        top_k=n_results
                    )
                    logger.info("Re-ranking complete")
                else:
                    logger.warning("Re-ranking requested but reranker not available, using original results")
            
            # Ensure we only return the requested number of results
            if len(search_results['ids']) > n_results:
                search_results = {
                    "ids": search_results['ids'][:n_results],
                    "documents": search_results['documents'][:n_results],
                    "metadatas": search_results['metadatas'][:n_results],
                    "distances": search_results['distances'][:n_results] if search_results.get('distances') else [],
                    "rerank_scores": search_results.get('rerank_scores', [])[:n_results]
                }
            
            return search_results
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def get_stats(self) -> Dict:
        """
        Get statistics about the indexed CVs
        
        Returns:
            Dictionary with statistics
        """
        count = self.collection.count()
        
        # Get unique sources
        if count > 0:
            # Get ALL metadata to count unique sources accurately
            results = self.collection.get()
            
            unique_sources = set()
            if results['metadatas']:
                for metadata in results['metadatas']:
                    unique_sources.add(metadata.get('source', 'unknown'))
            
            unique_cvs = len(unique_sources)
        else:
            unique_cvs = 0
        
        return {
            "total_chunks": count,
            "unique_cvs": unique_cvs,
            "embedding_model": self.embedding_function.model_name,
            "collection_name": config.CHROMADB_COLLECTION_NAME
        }
    
    def delete_cv(self, source: str):
        """
        Delete all chunks from a specific CV file
        
        Args:
            source: Filename of CV to delete (e.g., "ola-nordmann.md")
        """
        logger.info(f"Deleting CV: {source}")
        
        try:
            # Find all chunks from this source
            results = self.collection.get(
                where={"source": source}
            )
            
            if results['ids']:
                self.collection.delete(ids=results['ids'])
                logger.info(f"  ✅ Deleted {len(results['ids'])} chunks from {source}")
            else:
                logger.warning(f"  No chunks found for {source}")
        
        except Exception as e:
            logger.error(f"  ❌ Failed to delete {source}: {e}")


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format=config.LOG_FORMAT
    )
    
    # Test the indexer
    print("CV Indexer Test")
    print("=" * 50)
    
    indexer = CVIndexer()
    print(f"\nCurrent stats: {indexer.get_stats()}")



