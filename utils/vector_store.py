import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import pickle
import os
import json
import re

class VectorStore:
    """Manages vector storage and similarity search for documents"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: str = "vector_index"):
        self.model_name = model_name
        self.index_path = index_path
        self.embedding_model = SentenceTransformer(model_name)
        self.dimension = self.embedding_model.get_sentence_embedding_dimension()
        
        # Initialize FAISS index
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        self.documents = []  # Store original documents
        self.document_metadata = []  # Store metadata
        
        # Load existing index if available
        self.load_index()
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for a single text"""
        embedding = self.embedding_model.encode([text])
        # Normalize for cosine similarity
        faiss.normalize_L2(embedding)
        return embedding[0]
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts"""
        embeddings = self.embedding_model.encode(texts)
        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        return embeddings
    
    def add_documents(self, documents: List[str], metadata: List[Dict] = None):
        """Add documents to the vector store with enhanced processing"""
        if not documents:
            return
        
        # Enhanced preprocessing for better embeddings
        processed_documents = []
        processed_metadata = []
        
        for i, doc in enumerate(documents):
            # Enhance document content for better similarity search
            enhanced_doc = self._enhance_document_content(doc)
            processed_documents.append(enhanced_doc)
            
            # Enhanced metadata with content analysis
            doc_metadata = metadata[i] if metadata and i < len(metadata) else {}
            enhanced_metadata = self._enhance_metadata(doc, doc_metadata)
            processed_metadata.append(enhanced_metadata)
        
        # Generate embeddings for processed documents
        embeddings = self.embed_texts(processed_documents)
        
        # Add to FAISS index
        if self.index.ntotal == 0:
            self.index.add(embeddings.astype('float32'))
        else:
            self.index.add(embeddings.astype('float32'))
        
        # Store documents and metadata
        self.documents.extend(processed_documents)
        self.document_metadata.extend(processed_metadata)
        
        # Save the updated index
        self.save_index()
    
    def _enhance_document_content(self, document: str) -> str:
        """Enhance document content for better embeddings and search"""
        # Extract key phrases and concepts
        key_phrases = self._extract_key_phrases(document)
        
        # Add semantic markers for better understanding
        enhanced_content = document
        
        # Add content type indicators
        if any(keyword in document.lower() for keyword in ['define', 'definition', 'is defined as']):
            enhanced_content = f"[DEFINITION] {enhanced_content}"
        elif any(keyword in document.lower() for keyword in ['example', 'for instance', 'such as']):
            enhanced_content = f"[EXAMPLE] {enhanced_content}"
        elif any(keyword in document.lower() for keyword in ['process', 'steps', 'procedure']):
            enhanced_content = f"[PROCESS] {enhanced_content}"
        
        # Add key phrases as searchable terms
        if key_phrases:
            enhanced_content += f"\n[KEY_TERMS] {', '.join(key_phrases[:10])}"
        
        return enhanced_content
    
    def _enhance_metadata(self, document: str, existing_metadata: Dict) -> Dict:
        """Enhance metadata with content analysis"""
        enhanced_metadata = existing_metadata.copy()
        
        # Add content analysis
        enhanced_metadata.update({
            'word_count': len(document.split()),
            'sentence_count': len([s for s in document.split('.') if s.strip()]),
            'has_definition': any(keyword in document.lower() for keyword in ['define', 'definition']),
            'has_example': any(keyword in document.lower() for keyword in ['example', 'for instance']),
            'has_process': any(keyword in document.lower() for keyword in ['process', 'steps']),
            'has_list': bool(re.search(r'\d+\.\s|\•\s|\*\s', document)),
            'content_density': len(document.split()) / max(len(document), 1),  # Words per character
            'key_phrases': self._extract_key_phrases(document)
        })
        
        return enhanced_metadata
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text for better searchability"""
        # Simple key phrase extraction
        # Look for capitalized terms, technical terms, and important phrases
        phrases = []
        
        # Capitalized multi-word terms
        cap_phrases = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b', text)
        phrases.extend(cap_phrases)
        
        # Technical terms (words with underscores or camelCase)
        tech_terms = re.findall(r'\b[a-z]+(?:_[a-z]+)+\b|\b[a-z]+[A-Z][a-z]+\b', text)
        phrases.extend(tech_terms)
        
        # Important single words (longer than 5 characters, not common words)
        important_words = re.findall(r'\b[a-zA-Z]{6,}\b', text)
        common_words = {'system', 'process', 'example', 'definition', 'important', 'different', 'various', 'general'}
        important_words = [word for word in important_words if word.lower() not in common_words]
        phrases.extend(important_words[:5])  # Limit to 5 important words
        
        # Clean and deduplicate
        unique_phrases = list(set([phrase.strip() for phrase in phrases if len(phrase.strip()) > 3]))
        
        return unique_phrases[:15]  # Return top 15 phrases
    
    def similarity_search(self, query: str, k: int = 5, threshold: float = 0.3) -> List[Dict]:
        """Search for similar documents"""
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embed_text(query)
        
        # Search in FAISS index
        scores, indices = self.index.search(
            query_embedding.reshape(1, -1).astype('float32'), 
            min(k, self.index.ntotal)
        )
        
        # Filter by threshold and prepare results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= threshold and idx < len(self.documents):
                result = Document(
                    content=self.documents[idx],
                    metadata=self.document_metadata[idx].copy(),
                    similarity_score=float(score)
                )
                result.metadata['similarity_score'] = float(score)
                results.append(result)
        
        return results
    
    def get_relevant_context(self, query: str, max_tokens: int = 3000) -> str:
        """Get relevant context for a query, respecting token limits"""
        relevant_docs = self.similarity_search(query, k=10)
        
        context_parts = []
        current_tokens = 0
        
        for doc in relevant_docs:
            # Rough token estimation (4 characters per token)
            doc_tokens = len(doc.content) // 4
            
            if current_tokens + doc_tokens > max_tokens:
                # Try to fit partial content
                remaining_tokens = max_tokens - current_tokens
                remaining_chars = remaining_tokens * 4
                
                if remaining_chars > 100:  # Only add if substantial content fits
                    partial_content = doc.content[:remaining_chars] + "..."
                    context_parts.append(f"Source: {doc.metadata.get('source', 'Unknown')}\n{partial_content}")
                
                break
            
            context_parts.append(f"Source: {doc.metadata.get('source', 'Unknown')}\n{doc.content}")
            current_tokens += doc_tokens
        
        return "\n\n---\n\n".join(context_parts)
    
    def delete_documents_by_source(self, source_name: str):
        """Delete all documents from a specific source"""
        # Find indices to remove
        indices_to_remove = []
        for i, metadata in enumerate(self.document_metadata):
            if metadata.get('source') == source_name:
                indices_to_remove.append(i)
        
        if not indices_to_remove:
            return
        
        # Remove from documents and metadata (in reverse order to maintain indices)
        for idx in reversed(indices_to_remove):
            del self.documents[idx]
            del self.document_metadata[idx]
        
        # Rebuild the FAISS index
        self._rebuild_index()
    
    def _rebuild_index(self):
        """Rebuild the FAISS index from current documents"""
        if not self.documents:
            self.index = faiss.IndexFlatIP(self.dimension)
            return
        
        # Generate embeddings for all documents
        embeddings = self.embed_texts(self.documents)
        
        # Create new index
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings.astype('float32'))
        
        # Update document IDs in metadata
        for i, metadata in enumerate(self.document_metadata):
            metadata['doc_id'] = i
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store"""
        sources = {}
        for metadata in self.document_metadata:
            source = metadata.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1
        
        return {
            'total_documents': len(self.documents),
            'total_sources': len(sources),
            'sources': sources,
            'index_size': self.index.ntotal,
            'embedding_dimension': self.dimension
        }
    
    def save_index(self):
        """Save the vector index and metadata to disk"""
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.index_path, exist_ok=True)
            
            # Save FAISS index
            faiss.write_index(self.index, os.path.join(self.index_path, "faiss_index.bin"))
            
            # Save documents and metadata
            with open(os.path.join(self.index_path, "documents.pkl"), "wb") as f:
                pickle.dump(self.documents, f)
            
            with open(os.path.join(self.index_path, "metadata.json"), "w") as f:
                json.dump(self.document_metadata, f, indent=2, default=str)
            
        except Exception as e:
            # Silently handle save errors - index will be rebuilt if needed
            pass
    
    def load_index(self):
        """Load the vector index and metadata from disk"""
        try:
            faiss_path = os.path.join(self.index_path, "faiss_index.bin")
            docs_path = os.path.join(self.index_path, "documents.pkl")
            metadata_path = os.path.join(self.index_path, "metadata.json")
            
            if os.path.exists(faiss_path) and os.path.exists(docs_path) and os.path.exists(metadata_path):
                # Load FAISS index
                self.index = faiss.read_index(faiss_path)
                
                # Load documents
                with open(docs_path, "rb") as f:
                    self.documents = pickle.load(f)
                
                # Load metadata
                with open(metadata_path, "r") as f:
                    self.document_metadata = json.load(f)
                
                # Index loaded successfully - documents available
            
        except Exception as e:
            # Initialize empty index on error - silently handle
            self.index = faiss.IndexFlatIP(self.dimension)
            self.documents = []
            self.document_metadata = []
    
    def search_similar(self, query: str, k: int = 5, threshold: float = 0.3) -> List[Dict]:
        """Search for similar documents and return as dictionaries"""
        if self.index.ntotal == 0:
            return []
        
        # Generate query embedding
        query_embedding = self.embed_text(query)
        
        # Search in FAISS index
        scores, indices = self.index.search(
            query_embedding.reshape(1, -1).astype('float32'), 
            min(k, self.index.ntotal)
        )
        
        # Filter by threshold and prepare results
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if score >= threshold and idx < len(self.documents):
                metadata = self.document_metadata[idx].copy()
                metadata['similarity_score'] = float(score)
                
                result = {
                    'content': self.documents[idx],
                    'metadata': metadata,
                    'similarity_score': float(score),
                    'source': metadata.get('source', 'Unknown'),
                    'page': metadata.get('page', 'Unknown'),
                    'chunk_id': metadata.get('chunk_id', idx)
                }
                results.append(result)
        
        return results
    
    def get_all_chunks(self) -> List[Dict]:
        """Get all document chunks"""
        all_chunks = []
        for i, doc in enumerate(self.documents):
            metadata = self.document_metadata[i] if i < len(self.document_metadata) else {}
            all_chunks.append({
                'content': doc,
                'source': metadata.get('source', 'Unknown'),
                'chunk_id': metadata.get('chunk_id', i),
                'page': metadata.get('page', 'Unknown')
            })
        return all_chunks

    def clear_index(self):
        """Clear all documents from the index"""
        self.index = faiss.IndexFlatIP(self.dimension)
        self.documents = []
        self.document_metadata = []
        
        # Remove saved files
        try:
            import shutil
            if os.path.exists(self.index_path):
                shutil.rmtree(self.index_path)
        except Exception as e:
            # Silently handle clear errors
            pass


class Document:
    """Simple document class to hold content and metadata"""
    
    def __init__(self, content: str, metadata: Dict[str, Any] = None, similarity_score: float = 0.0):
        self.content = content
        self.metadata = metadata or {}
        self.similarity_score = similarity_score
    
    def __repr__(self):
        return f"Document(content='{self.content[:50]}...', metadata={self.metadata})"
