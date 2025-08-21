import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import json
import re
import uuid
import os
from datetime import datetime, timedelta

class SessionVectorStore:
    """Session-based vector storage that clears when browser/session closes"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        
        # Set Hugging Face token if available
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            os.environ["HUGGINGFACE_HUB_TOKEN"] = hf_token
        
        self.embedding_model = SentenceTransformer(model_name)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Session-based storage (in memory only)
        self.sessions = {}  # session_id -> session_data
        self.cleanup_interval = timedelta(hours=2)  # Auto cleanup after 2 hours
        
    def create_session(self) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = {
            'index': faiss.IndexFlatIP(self.dimension),
            'documents': [],
            'metadata': [],
            'created_at': datetime.now(),
            'last_accessed': datetime.now()
        }
        
        # Cleanup old sessions
        self._cleanup_old_sessions()
        
        print(f"🆕 Created new session: {session_id[:8]}...")
        return session_id
    
    def _cleanup_old_sessions(self):
        """Remove sessions older than cleanup_interval"""
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            if current_time - session_data['last_accessed'] > self.cleanup_interval:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            print(f"🧹 Cleaned up expired session: {session_id[:8]}...")
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data and update last accessed time"""
        if session_id not in self.sessions:
            return None
        
        self.sessions[session_id]['last_accessed'] = datetime.now()
        return self.sessions[session_id]
    
    def clear_session(self, session_id: str):
        """Clear a specific session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            print(f"🗑️  Cleared session: {session_id[:8]}...")
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        embedding = self.embedding_model.encode([text])
        faiss.normalize_L2(embedding)
        return embedding[0]
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        embeddings = self.embedding_model.encode(texts)
        faiss.normalize_L2(embeddings)
        return embeddings
    
    def add_documents(self, session_id: str, documents: List[str], metadata: List[Dict] = None):
        """Add documents to a specific session"""
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        if not documents:
            return
        
        # Process documents and remove any OS unit-1.pdf references
        processed_documents = []
        processed_metadata = []
        
        for i, doc in enumerate(documents):
            # Skip any document that mentions OS unit-1.pdf
            doc_meta = metadata[i] if metadata and i < len(metadata) else {}
            source = doc_meta.get('source', '').lower()
            
            if 'os unit-1' in source or 'os unit-1' in doc.lower():
                print(f"🚫 Skipping OS unit-1.pdf content: {source}")
                continue
            
            # Enhanced preprocessing for better embeddings
            processed_doc = self._preprocess_document(doc)
            processed_documents.append(processed_doc)
            
            # Enhanced metadata
            enhanced_metadata = {
                'original_content': doc,
                'processed_content': processed_doc,
                'content_type': self._identify_content_type(doc),
                'word_count': len(doc.split()),
                'session_id': session_id,
                'added_at': datetime.now().isoformat(),
                **doc_meta
            }
            processed_metadata.append(enhanced_metadata)
        
        if not processed_documents:
            print("📝 No valid documents to add (OS unit-1.pdf filtered out)")
            return
        
        # Generate embeddings
        embeddings = self.embed_texts(processed_documents)
        
        # Add to session's index
        session['index'].add(embeddings)
        session['documents'].extend(processed_documents)
        session['metadata'].extend(processed_metadata)
        
        print(f"✅ Added {len(processed_documents)} documents to session {session_id[:8]}...")
        print(f"📊 Session now contains {len(session['documents'])} total documents")
    
    def _preprocess_document(self, document: str) -> str:
        """Preprocess document for better embedding quality"""
        # Remove OS unit-1.pdf references
        doc = re.sub(r'OS\s+unit-1\.pdf', '', document, flags=re.IGNORECASE)
        doc = re.sub(r'OS\s+unit\s*-?\s*1', '', doc, flags=re.IGNORECASE)
        
        # Clean and normalize text
        doc = re.sub(r'\s+', ' ', doc)  # Normalize whitespace
        doc = re.sub(r'[^\w\s\.,;:!?()\-\'"°%$#@&\[\]{}]', '', doc)  # Remove problematic chars
        
        # Add semantic markers for better context
        if 'definition' in doc.lower() or 'define' in doc.lower():
            doc = f"[DEFINITION] {doc}"
        elif 'example' in doc.lower() or 'for instance' in doc.lower():
            doc = f"[EXAMPLE] {doc}"
        elif any(keyword in doc.lower() for keyword in ['step', 'process', 'procedure']):
            doc = f"[PROCESS] {doc}"
        
        return doc.strip()
    
    def _identify_content_type(self, text: str) -> str:
        """Identify the type of content for better categorization"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['definition', 'define', 'is defined as']):
            return 'definition'
        elif any(word in text_lower for word in ['example', 'for instance', 'such as']):
            return 'example'
        elif any(word in text_lower for word in ['process', 'procedure', 'steps']):
            return 'process'
        elif '?' in text:
            return 'question'
        elif re.search(r'\d+\.|•|\*', text):
            return 'list'
        else:
            return 'general'
    
    def search(self, session_id: str, query: str, k: int = 5) -> List[Dict]:
        """Search for similar documents in a specific session"""
        session = self.get_session(session_id)
        if not session or len(session['documents']) == 0:
            return []
        
        # Remove OS unit-1.pdf references from query
        clean_query = re.sub(r'OS\s+unit-1\.pdf', '', query, flags=re.IGNORECASE)
        clean_query = re.sub(r'OS\s+unit\s*-?\s*1', '', clean_query, flags=re.IGNORECASE)
        
        # Generate query embedding
        query_embedding = self.embed_text(clean_query).reshape(1, -1)
        
        # Search in session's index
        k = min(k, len(session['documents']))
        scores, indices = session['index'].search(query_embedding, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(session['documents']):
                result = {
                    'content': session['documents'][idx],
                    'metadata': session['metadata'][idx],
                    'similarity_score': float(score),
                    'relevance': self._calculate_relevance(clean_query, session['documents'][idx])
                }
                results.append(result)
        
        # Sort by relevance score (combination of similarity and relevance)
        results.sort(key=lambda x: x['similarity_score'] + x['relevance'], reverse=True)
        
        print(f"🔍 Found {len(results)} results for query in session {session_id[:8]}...")
        return results
    
    def _calculate_relevance(self, query: str, document: str) -> float:
        """Calculate relevance based on query-document word overlap"""
        query_words = set(query.lower().split())
        doc_words = set(document.lower().split())
        
        if not query_words:
            return 0.0
        
        overlap = len(query_words.intersection(doc_words))
        relevance = overlap / len(query_words)
        
        return relevance
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Get statistics for a specific session"""
        session = self.get_session(session_id)
        if not session:
            return {'error': 'Session not found'}
        
        return {
            'session_id': session_id,
            'document_count': len(session['documents']),
            'created_at': session['created_at'].isoformat(),
            'last_accessed': session['last_accessed'].isoformat(),
            'sources': list(set(meta.get('source', 'Unknown') for meta in session['metadata'])),
            'content_types': list(set(meta.get('content_type', 'unknown') for meta in session['metadata']))
        }
    
    def list_active_sessions(self) -> List[Dict]:
        """List all active sessions"""
        sessions = []
        for session_id, session_data in self.sessions.items():
            sessions.append({
                'session_id': session_id,
                'document_count': len(session_data['documents']),
                'created_at': session_data['created_at'].isoformat(),
                'last_accessed': session_data['last_accessed'].isoformat()
            })
        
        return sessions
    
    def get_all_documents(self, session_id: str) -> List[Dict]:
        """Get all documents from a session for summary/quiz generation"""
        session = self.get_session(session_id)
        if not session:
            return []
        
        documents = []
        for i, (doc, meta) in enumerate(zip(session['documents'], session['metadata'])):
            documents.append({
                'content': doc,
                'metadata': meta,
                'index': i
            })
        
        return documents
