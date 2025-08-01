import PyPDF2
import io
from typing import List, Dict
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter

class PDFProcessor:
    """Handles PDF document processing and text extraction"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from a PDF file"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            # Clean the text
                            page_text = self.clean_text(page_text)
                            text += f"\n\n--- Page {page_num + 1} ---\n{page_text}"
                    except Exception as e:
                        print(f"Error extracting text from page {page_num + 1}: {str(e)}")
                        continue
                
                return text
        except Exception as e:
            raise Exception(f"Error reading PDF file: {str(e)}")
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might interfere
        text = re.sub(r'[^\w\s\.,;:!?()-]', '', text)
        
        # Fix common OCR errors
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
