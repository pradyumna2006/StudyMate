import PyPDF2
import io
from typing import List, Dict, Tuple
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
import nltk
from collections import Counter

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

class PDFProcessor:
    """Enhanced PDF document processing with intelligent chunking and context preservation"""
    
    def __init__(self, chunk_size: int = 1200, chunk_overlap: int = 300):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Enhanced text splitter with better separators for academic content
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=[
                "\n\n\n",  # Major section breaks
                "\n\n",    # Paragraph breaks
                "\n",      # Line breaks
                ". ",      # Sentence breaks
                "? ",      # Question breaks
                "! ",      # Exclamation breaks
                "; ",      # Semicolon breaks
                ", ",      # Comma breaks
                " ",       # Word breaks
                ""         # Character breaks
            ]
        )
        
        # Academic keywords for better context identification
        self.academic_keywords = {
            'definition': ['definition', 'define', 'is defined as', 'refers to', 'means'],
            'example': ['example', 'for instance', 'such as', 'e.g.', 'for example'],
            'concept': ['concept', 'principle', 'theory', 'approach', 'method'],
            'process': ['process', 'procedure', 'steps', 'algorithm', 'workflow'],
            'comparison': ['compare', 'contrast', 'difference', 'similarity', 'versus'],
            'classification': ['types', 'categories', 'classification', 'kinds', 'varieties']
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Enhanced text extraction with better structure preservation"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            # Enhanced text cleaning and structure preservation
                            page_text = self.enhanced_clean_text(page_text)
                            text += f"\n\n--- Page {page_num + 1} ---\n{page_text}"
                    except Exception as e:
                        # Skip pages with extraction errors
                        continue
                
                return text
        except Exception as e:
            raise Exception(f"Error reading PDF file: {str(e)}")
    
    def enhanced_clean_text(self, text: str) -> str:
        """Enhanced text cleaning with better academic content preservation"""
        # Preserve section headers and important formatting
        text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)  # Normalize multiple newlines
        
        # Fix common PDF extraction issues
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)  # Fix hyphenated words split across lines
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        
        # Preserve important academic formatting
        text = re.sub(r'([.!?])\s*([A-Z])', r'\1\n\n\2', text)  # Add breaks after sentences starting new topics
        
        # Preserve numbered lists and bullet points
        text = re.sub(r'\n\s*(\d+\.|\•|\*|\-)\s*', r'\n\1 ', text)
        
        # Remove problematic characters but preserve academic symbols
        text = re.sub(r'[^\w\s\.,;:!?()\-+=/\'"°%$#@&\[\]{}]', '', text)
        
        return text.strip()
    
    def create_enhanced_chunks(self, text: str, filename: str) -> List[Dict]:
        """Create intelligent chunks with enhanced context and metadata"""
        # Split text into base chunks
        base_chunks = self.text_splitter.split_text(text)
        
        enhanced_chunks = []
        for i, chunk in enumerate(base_chunks):
            # Analyze chunk content for better metadata
            chunk_metadata = self.analyze_chunk_content(chunk, filename, i)
            
            # Add contextual information
            enhanced_chunk = self.add_contextual_info(chunk, base_chunks, i)
            
            chunk_data = {
                'content': enhanced_chunk,
                'metadata': chunk_metadata,
                'chunk_id': f"{filename}_chunk_{i}",
                'source': filename,
                'chunk_index': i,
                'total_chunks': len(base_chunks)
            }
            
            enhanced_chunks.append(chunk_data)
        
        return enhanced_chunks
    
    def analyze_chunk_content(self, chunk: str, filename: str, chunk_index: int) -> Dict:
        """Analyze chunk content to extract meaningful metadata"""
        metadata = {
            'source': filename,
            'chunk_id': chunk_index,
            'page': self.extract_page_number(chunk),
            'content_type': self.identify_content_type(chunk),
            'key_concepts': self.extract_key_concepts(chunk),
            'academic_elements': self.identify_academic_elements(chunk),
            'word_count': len(chunk.split()),
            'sentence_count': len([s for s in chunk.split('.') if s.strip()])
        }
        
        return metadata
    
    def identify_content_type(self, chunk: str) -> str:
        """Identify the type of academic content in the chunk"""
        chunk_lower = chunk.lower()
        
        # Check for different types of academic content
        if any(keyword in chunk_lower for keyword in self.academic_keywords['definition']):
            return 'definition'
        elif any(keyword in chunk_lower for keyword in self.academic_keywords['example']):
            return 'example'
        elif any(keyword in chunk_lower for keyword in self.academic_keywords['process']):
            return 'process'
        elif any(keyword in chunk_lower for keyword in self.academic_keywords['comparison']):
            return 'comparison'
        elif re.search(r'\d+\.\s|\•\s|\*\s', chunk):
            return 'list'
        elif '?' in chunk:
            return 'question'
        else:
            return 'general'
    
    def extract_key_concepts(self, chunk: str) -> List[str]:
        """Extract key concepts and technical terms from the chunk"""
        # Simple keyword extraction (can be enhanced with NLP)
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', chunk)  # Capitalized terms
        technical_terms = re.findall(r'\b[a-z]+(?:_[a-z]+)*\b', chunk)  # Technical terms with underscores
        
        # Filter and clean
        key_concepts = []
        for word in words + technical_terms:
            if len(word) > 3 and word.lower() not in ['page', 'chapter', 'section']:
                key_concepts.append(word)
        
        return list(set(key_concepts))[:10]  # Return top 10 unique concepts
    
    def identify_academic_elements(self, chunk: str) -> List[str]:
        """Identify academic elements like definitions, examples, etc."""
        elements = []
        chunk_lower = chunk.lower()
        
        for element_type, keywords in self.academic_keywords.items():
            if any(keyword in chunk_lower for keyword in keywords):
                elements.append(element_type)
        
        # Check for additional elements
        if re.search(r'\d+\.\s|\•\s|\*\s', chunk):
            elements.append('list')
        if re.search(r'figure\s+\d+|table\s+\d+|diagram', chunk_lower):
            elements.append('reference')
        if '?' in chunk:
            elements.append('question')
        
        return elements
    
    def add_contextual_info(self, current_chunk: str, all_chunks: List[str], index: int) -> str:
        """Add contextual information from surrounding chunks"""
        context_parts = [current_chunk]
        
        # Add context from previous chunk if available
        if index > 0:
            prev_chunk = all_chunks[index - 1]
            # Extract last sentence for context
            prev_sentences = prev_chunk.split('.')
            if len(prev_sentences) > 1:
                context_parts.insert(0, f"[Previous context: ...{prev_sentences[-2].strip()}.]")
        
        # Add context from next chunk if available
        if index < len(all_chunks) - 1:
            next_chunk = all_chunks[index + 1]
            # Extract first sentence for context
            next_sentences = next_chunk.split('.')
            if len(next_sentences) > 0:
                context_parts.append(f"[Next context: {next_sentences[0].strip()}...]")
        
        return '\n\n'.join(context_parts)
    
    def extract_page_number(self, chunk: str) -> str:
        """Extract page number from chunk content"""
        page_match = re.search(r'--- Page (\d+) ---', chunk)
        if page_match:
            return page_match.group(1)
        return 'Unknown'
        text = text.replace('\\n', '\n')
        text = text.replace('\\t', '\t')
        
        # Remove very short lines (likely artifacts)
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 3]
        
        return '\n'.join(cleaned_lines)
    
    def process_pdf(self, pdf_path: str) -> List[Dict]:
        """Process a PDF and return text chunks with metadata"""
        # Extract text
        full_text = self.extract_text_from_pdf(pdf_path)
        
        if not full_text.strip():
            raise Exception("No text could be extracted from the PDF")
        
        # Split into chunks
        chunks = self.text_splitter.split_text(full_text)
        
        # Create document objects with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                'content': chunk,
                'metadata': {
                    'source': pdf_path.split('/')[-1],  # Just the filename
                    'chunk_id': i,
                    'total_chunks': len(chunks),
                    'chunk_size': len(chunk)
                }
            }
            documents.append(doc)
        
        return documents
    
    def extract_metadata(self, pdf_path: str) -> Dict:
        """Extract metadata from PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                metadata = pdf_reader.metadata
                
                return {
                    'title': metadata.get('/Title', 'Unknown'),
                    'author': metadata.get('/Author', 'Unknown'),
                    'subject': metadata.get('/Subject', 'Unknown'),
                    'creator': metadata.get('/Creator', 'Unknown'),
                    'producer': metadata.get('/Producer', 'Unknown'),
                    'creation_date': metadata.get('/CreationDate', 'Unknown'),
                    'modification_date': metadata.get('/ModDate', 'Unknown'),
                    'pages': len(pdf_reader.pages)
                }
        except Exception as e:
            return {
                'title': 'Unknown',
                'author': 'Unknown',
                'pages': 0,
                'error': str(e)
            }
    
    def get_page_content(self, pdf_path: str, page_num: int) -> str:
        """Get content from a specific page"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if 0 <= page_num < len(pdf_reader.pages):
                    page = pdf_reader.pages[page_num]
                    return self.clean_text(page.extract_text())
                else:
                    raise Exception(f"Page {page_num + 1} does not exist")
        except Exception as e:
            raise Exception(f"Error reading page {page_num + 1}: {str(e)}")
    
    def search_in_pdf(self, pdf_path: str, query: str) -> List[Dict]:
        """Search for specific text in PDF and return matching chunks"""
        documents = self.process_pdf(pdf_path)
        matching_chunks = []
        
        query_lower = query.lower()
        
        for doc in documents:
            content_lower = doc['content'].lower()
            if query_lower in content_lower:
                # Find the position of the match
                match_start = content_lower.find(query_lower)
                
                # Extract context around the match
                context_start = max(0, match_start - 100)
                context_end = min(len(doc['content']), match_start + len(query) + 100)
                context = doc['content'][context_start:context_end]
                
                matching_chunks.append({
                    'content': doc['content'],
                    'context': context,
                    'metadata': doc['metadata'],
                    'match_position': match_start
                })
        
        return matching_chunks

    def create_documents(self, text: str, filename: str) -> List[Dict]:
        """Create document chunks from extracted text"""
        # Split into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Create document objects with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc = {
                'content': chunk,
                'metadata': {
                    'source': filename,
                    'chunk_id': i,
                    'total_chunks': len(chunks),
                    'chunk_size': len(chunk)
                }
            }
            documents.append(doc)
        
        return documents
