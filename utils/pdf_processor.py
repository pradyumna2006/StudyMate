import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
from pdfminer.high_level import extract_text as pdfminer_extract_text
from pdfminer.layout import LAParams
import pytesseract
from PIL import Image
import io
from typing import List, Dict, Tuple, Optional
import re
import os
import tempfile
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
        """Enhanced text extraction with multiple libraries for maximum PDF compatibility"""
        extraction_methods = [
            ("pdfplumber", self._extract_with_pdfplumber),
            ("pymupdf", self._extract_with_pymupdf),
            ("pypdf2", self._extract_with_pypdf2),
            ("pdfminer", self._extract_with_pdfminer),
            ("ocr", self._extract_with_ocr)
        ]
        
        best_text = ""
        best_method = "none"
        
        for method_name, method_func in extraction_methods:
            try:
                print(f"Attempting extraction with {method_name}...")
                text = method_func(pdf_path)
                
                if text and len(text.strip()) > 100:  # Minimum viable text length
                    text_quality = self._assess_text_quality(text)
                    
                    # If we get good quality text, use it
                    if text_quality > 0.7:
                        print(f"✅ Successfully extracted text using {method_name} (quality: {text_quality:.2f})")
                        return self.enhanced_clean_text(text)
                    
                    # Keep track of the best extraction so far
                    if len(text) > len(best_text):
                        best_text = text
                        best_method = method_name
                        
            except Exception as e:
                print(f"⚠️  {method_name} extraction failed: {str(e)}")
                continue
        
        if best_text:
            print(f"✅ Using best available extraction from {best_method}")
            return self.enhanced_clean_text(best_text)
        
        raise Exception("❌ Failed to extract text using any method. This PDF may be corrupted, password-protected, or contain only images without OCR-readable text.")

    def _extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber (best for tables and complex layouts)"""
        text = ""
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n\n--- Page {page_num + 1} ---\n{page_text}"
                    
                    # Also extract tables if present
                    tables = page.extract_tables()
                    for table in tables:
                        if table:
                            table_text = "\n".join([" | ".join([str(cell) if cell else "" for cell in row]) for row in table])
                            text += f"\n\n[TABLE]\n{table_text}\n[/TABLE]\n"
                            
                except Exception:
                    continue
        return text

    def _extract_with_pymupdf(self, pdf_path: str) -> str:
        """Extract text using PyMuPDF (best for general PDFs and metadata)"""
        text = ""
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            try:
                page = doc.load_page(page_num)
                page_text = page.get_text()
                if page_text:
                    text += f"\n\n--- Page {page_num + 1} ---\n{page_text}"
            except Exception:
                continue
                
        doc.close()
        return text

    def _extract_with_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2 (original method, kept as fallback)"""
        text = ""
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += f"\n\n--- Page {page_num + 1} ---\n{page_text}"
                except Exception:
                    continue
        return text

    def _extract_with_pdfminer(self, pdf_path: str) -> str:
        """Extract text using pdfminer (best for academic papers and complex formatting)"""
        laparams = LAParams(
            detect_vertical=True,
            word_margin=0.1,
            char_margin=2.0,
            line_margin=0.5,
            boxes_flow=0.5
        )
        
        text = pdfminer_extract_text(pdf_path, laparams=laparams)
        
        # Add page markers (approximate, since pdfminer doesn't give page info easily)
        if text:
            # Split by form feed characters or large gaps to approximate pages
            pages = re.split(r'\f|\n\s*\n\s*\n\s*\n', text)
            formatted_text = ""
            for i, page_content in enumerate(pages):
                if page_content.strip():
                    formatted_text += f"\n\n--- Page {i + 1} ---\n{page_content.strip()}"
            return formatted_text
        
        return text

    def _extract_with_ocr(self, pdf_path: str) -> str:
        """Extract text using OCR for scanned PDFs or image-based content"""
        try:
            # Check if tesseract is available
            pytesseract.get_tesseract_version()
        except Exception:
            raise Exception("Tesseract OCR not installed. Cannot process image-based PDFs.")
        
        text = ""
        doc = fitz.open(pdf_path)
        
        for page_num in range(len(doc)):
            try:
                page = doc.load_page(page_num)
                
                # First try regular text extraction
                page_text = page.get_text()
                
                # If no text or very little text, use OCR
                if not page_text or len(page_text.strip()) < 50:
                    print(f"Using OCR for page {page_num + 1}...")
                    
                    # Convert page to image
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # Higher resolution
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Extract text using OCR
                    ocr_text = pytesseract.image_to_string(img, config='--psm 6')
                    if ocr_text.strip():
                        text += f"\n\n--- Page {page_num + 1} (OCR) ---\n{ocr_text}"
                else:
                    text += f"\n\n--- Page {page_num + 1} ---\n{page_text}"
                    
            except Exception as e:
                print(f"OCR failed for page {page_num + 1}: {str(e)}")
                continue
                
        doc.close()
        return text

    def _assess_text_quality(self, text: str) -> float:
        """Assess the quality of extracted text to choose the best method"""
        if not text or len(text.strip()) < 10:
            return 0.0
        
        # Count readable characters vs total characters
        readable_chars = len(re.findall(r'[a-zA-Z0-9\s\.,;:!?()\-]', text))
        total_chars = len(text)
        
        if total_chars == 0:
            return 0.0
        
        readability_score = readable_chars / total_chars
        
        # Bonus for having complete words and sentences
        words = text.split()
        complete_words = [w for w in words if len(w) > 2 and w.isascii()]
        word_score = len(complete_words) / len(words) if words else 0
        
        # Check for common academic/document patterns
        pattern_score = 0
        patterns = [r'\b\w+\b', r'[.!?]', r'\d+', r'[A-Z][a-z]+']
        for pattern in patterns:
            if re.search(pattern, text):
                pattern_score += 0.1
        
        # Combined quality score
        quality = (readability_score * 0.5 + word_score * 0.3 + min(pattern_score, 0.2))
        return min(quality, 1.0)
    
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
        """Enhanced PDF processing with detailed feedback and multi-library support"""
        filename = pdf_path.split('/')[-1]
        print(f"\n🔄 Processing PDF: {filename}")
        
        # Extract text using enhanced multi-library approach
        try:
            full_text = self.extract_text_from_pdf(pdf_path)
            
            if not full_text.strip():
                raise Exception("❌ No text could be extracted from the PDF. This might be a scanned document requiring OCR or a corrupted file.")
            
            print(f"✅ Successfully extracted {len(full_text)} characters from {filename}")
            
            # Split into chunks
            chunks = self.text_splitter.split_text(full_text)
            print(f"📄 Created {len(chunks)} text chunks for processing")
            
            # Create document objects with enhanced metadata
            documents = []
            for i, chunk in enumerate(chunks):
                # Enhanced metadata with text quality assessment
                doc = {
                    'content': chunk,
                    'metadata': {
                        'source': filename,
                        'chunk_id': i,
                        'total_chunks': len(chunks),
                        'chunk_size': len(chunk),
                        'text_quality': self._assess_text_quality(chunk),
                        'content_type': self.identify_content_type(chunk),
                        'word_count': len(chunk.split()),
                        'has_tables': '[TABLE]' in chunk,
                        'is_ocr': '(OCR)' in chunk
                    }
                }
                documents.append(doc)
            
            # Quality assessment
            avg_quality = sum(doc['metadata']['text_quality'] for doc in documents) / len(documents)
            ocr_chunks = sum(1 for doc in documents if doc['metadata']['is_ocr'])
            table_chunks = sum(1 for doc in documents if doc['metadata']['has_tables'])
            
            print(f"📊 Processing Summary:")
            print(f"   • Average text quality: {avg_quality:.2f}/1.0")
            print(f"   • OCR-processed chunks: {ocr_chunks}")
            print(f"   • Chunks with tables: {table_chunks}")
            print(f"   • Ready for vector storage and Q&A")
            
            return documents
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ PDF Processing Error: {error_msg}")
            
            # Provide helpful guidance based on error type
            if "password" in error_msg.lower():
                print("💡 This PDF appears to be password-protected. Please provide an unlocked version.")
            elif "corrupted" in error_msg.lower() or "invalid" in error_msg.lower():
                print("💡 This PDF may be corrupted. Try re-downloading or using a different PDF.")
            elif "tesseract" in error_msg.lower():
                print("💡 For scanned PDFs, OCR support requires Tesseract. Consider installing it or use text-based PDFs.")
            else:
                print("💡 Try using a different PDF format or check if the file is accessible.")
            
            raise Exception(f"Failed to process PDF '{filename}': {error_msg}")

    def get_pdf_info(self, pdf_path: str) -> Dict:
        """Get comprehensive information about a PDF before processing"""
        filename = pdf_path.split('/')[-1]
        info = {
            'filename': filename,
            'file_size': os.path.getsize(pdf_path) if os.path.exists(pdf_path) else 0,
            'is_accessible': os.path.exists(pdf_path) and os.access(pdf_path, os.R_OK),
            'extraction_methods': [],
            'estimated_difficulty': 'unknown'
        }
        
        # Test each extraction method quickly
        methods_to_test = [
            ("PyPDF2", self._quick_test_pypdf2),
            ("pdfplumber", self._quick_test_pdfplumber),
            ("PyMuPDF", self._quick_test_pymupdf),
            ("pdfminer", self._quick_test_pdfminer)
        ]
        
        for method_name, test_func in methods_to_test:
            try:
                if test_func(pdf_path):
                    info['extraction_methods'].append(method_name)
            except:
                continue
        
        # Estimate processing difficulty
        if len(info['extraction_methods']) >= 3:
            info['estimated_difficulty'] = 'easy'
        elif len(info['extraction_methods']) >= 1:
            info['estimated_difficulty'] = 'moderate'
        else:
            info['estimated_difficulty'] = 'hard'
        
        return info

    def _quick_test_pypdf2(self, pdf_path: str) -> bool:
        """Quick test if PyPDF2 can read the PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                if len(pdf_reader.pages) > 0:
                    test_text = pdf_reader.pages[0].extract_text()
                    return bool(test_text and len(test_text.strip()) > 10)
        except:
            pass
        return False

    def _quick_test_pdfplumber(self, pdf_path: str) -> bool:
        """Quick test if pdfplumber can read the PDF"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if len(pdf.pages) > 0:
                    test_text = pdf.pages[0].extract_text()
                    return bool(test_text and len(test_text.strip()) > 10)
        except:
            pass
        return False

    def _quick_test_pymupdf(self, pdf_path: str) -> bool:
        """Quick test if PyMuPDF can read the PDF"""
        try:
            doc = fitz.open(pdf_path)
            if len(doc) > 0:
                test_text = doc[0].get_text()
                doc.close()
                return bool(test_text and len(test_text.strip()) > 10)
        except:
            pass
        return False

    def _quick_test_pdfminer(self, pdf_path: str) -> bool:
        """Quick test if pdfminer can read the PDF"""
        try:
            # Test just first few characters
            test_text = pdfminer_extract_text(pdf_path, maxpages=1)
            return bool(test_text and len(test_text.strip()) > 10)
        except:
            pass
        return False
    
    def extract_metadata(self, pdf_path: str) -> Dict:
        """Extract comprehensive metadata from PDF using multiple libraries"""
        metadata = {
            'title': 'Unknown',
            'author': 'Unknown',
            'subject': 'Unknown',
            'creator': 'Unknown',
            'producer': 'Unknown',
            'creation_date': 'Unknown',
            'modification_date': 'Unknown',
            'pages': 0,
            'file_size': 0,
            'extraction_method': 'none'
        }
        
        # Get file size
        if os.path.exists(pdf_path):
            metadata['file_size'] = os.path.getsize(pdf_path)
        
        # Try PyMuPDF first (usually has the best metadata support)
        try:
            doc = fitz.open(pdf_path)
            doc_metadata = doc.metadata
            metadata.update({
                'title': doc_metadata.get('title', 'Unknown'),
                'author': doc_metadata.get('author', 'Unknown'),
                'subject': doc_metadata.get('subject', 'Unknown'),
                'creator': doc_metadata.get('creator', 'Unknown'),
                'producer': doc_metadata.get('producer', 'Unknown'),
                'creation_date': doc_metadata.get('creationDate', 'Unknown'),
                'modification_date': doc_metadata.get('modDate', 'Unknown'),
                'pages': len(doc),
                'extraction_method': 'PyMuPDF'
            })
            doc.close()
            return metadata
        except Exception:
            pass
        
        # Fallback to PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                pdf_metadata = pdf_reader.metadata or {}
                
                metadata.update({
                    'title': pdf_metadata.get('/Title', 'Unknown'),
                    'author': pdf_metadata.get('/Author', 'Unknown'),
                    'subject': pdf_metadata.get('/Subject', 'Unknown'),
                    'creator': pdf_metadata.get('/Creator', 'Unknown'),
                    'producer': pdf_metadata.get('/Producer', 'Unknown'),
                    'creation_date': pdf_metadata.get('/CreationDate', 'Unknown'),
                    'modification_date': pdf_metadata.get('/ModDate', 'Unknown'),
                    'pages': len(pdf_reader.pages),
                    'extraction_method': 'PyPDF2'
                })
                return metadata
        except Exception as e:
            metadata['error'] = str(e)
            metadata['extraction_method'] = 'failed'
            return metadata
    
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
