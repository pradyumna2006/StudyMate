from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from typing import Dict, List
import logging

# Import custom modules
from utils.pdf_processor import PDFProcessor
from utils.vector_store import VectorStore
from utils.ai_assistant import AIAssistant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global instances
pdf_processor = None
vector_store = None
ai_assistant = None
uploaded_documents = []
chat_history = []
study_session = {
    'start_time': datetime.now(),
    'questions_asked': 0,
    'documents_processed': 0,
    'total_tokens_used': 0
}

def initialize_components():
    """Initialize all application components"""
    global pdf_processor, vector_store, ai_assistant, uploaded_documents
    
    try:
        # Initialize PDF processor
        pdf_processor = PDFProcessor()
        logger.info("PDF processor initialized")
        
        # Initialize vector store
        vector_store = VectorStore()
        
        # Check if there are existing documents in the vector store
        if hasattr(vector_store, 'documents') and vector_store.documents:
            existing_count = len(vector_store.documents)
            logger.info(f"Found {existing_count} existing documents in vector store")
            
            # Sample a few documents to see what's in there
            for i, doc in enumerate(vector_store.documents[:3]):
                preview = doc[:100] if doc else "Empty"
                logger.info(f"Sample doc {i}: {preview}...")
            
            # Register existing documents
            uploaded_documents.extend([f"existing_doc_{i}" for i in range(existing_count)])
            logger.info(f"Registered {len(uploaded_documents)} existing documents")
        
        # Initialize AI assistant
        ai_assistant = AIAssistant()
        
        logger.info("All components initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        return False

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def serve_frontend():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'components': {
            'pdf_processor': pdf_processor is not None,
            'vector_store': vector_store is not None,
            'ai_assistant': ai_assistant is not None
        }
    })

@app.route('/upload-documents', methods=['POST'])
def upload_documents():
    """Upload and process PDF documents"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        processed_files = []
        errors = []
        
        for file in files:
            if file.filename == '':
                continue
                
            if not allowed_file(file.filename):
                errors.append(f"File {file.filename} is not a PDF")
                continue
            
            try:
                # Save uploaded file
                filename = secure_filename(file.filename)
                filepath = os.path.join(UPLOAD_FOLDER, filename)
                file.save(filepath)
                
                # Process PDF
                logger.info(f"Processing PDF: {filename}")
                chunks = pdf_processor.process_pdf(filepath)
                
                if chunks:
                    # Add to vector store
                    vector_store.add_documents(chunks, filename)
                    
                    # Track uploaded document
                    doc_info = {
                        'filename': filename,
                        'filepath': filepath,
                        'upload_time': datetime.now().isoformat(),
                        'chunks_count': len(chunks)
                    }
                    uploaded_documents.append(doc_info)
                    study_session['documents_processed'] += 1
                    
                    processed_files.append({
                        'filename': filename,
                        'chunks': len(chunks),
                        'status': 'success'
                    })
                    
                    logger.info(f"Successfully processed {filename} with {len(chunks)} chunks")
                else:
                    errors.append(f"No text could be extracted from {filename}")
                    os.remove(filepath)  # Clean up
                    
            except Exception as e:
                logger.error(f"Error processing {file.filename}: {str(e)}")
                errors.append(f"Error processing {file.filename}: {str(e)}")
                # Clean up file if it exists
                if os.path.exists(filepath):
                    os.remove(filepath)
        
        response_data = {
            'processed_files': processed_files,
            'total_documents': len(uploaded_documents),
            'total_chunks': sum(doc['chunks_count'] for doc in uploaded_documents)
        }
        
        if errors:
            response_data['errors'] = errors
            
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@app.route('/remove-document', methods=['POST'])
def remove_document():
    """Remove a document from the system"""
    try:
        data = request.get_json()
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'Filename required'}), 400
        
        # Remove from uploaded_documents list
        global uploaded_documents
        uploaded_documents = [doc for doc in uploaded_documents if doc['filename'] != filename]
        
        # Remove file from disk
        filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Note: Vector store doesn't have a remove method in the current implementation
        # You might want to add this functionality to the VectorStore class
        
        return jsonify({'message': f'Document {filename} removed successfully'})
        
    except Exception as e:
        logger.error(f"Remove document error: {str(e)}")
        return jsonify({'error': f'Failed to remove document: {str(e)}'}), 500

@app.route('/ask-question', methods=['POST'])
def ask_question():
    """Process a question and return AI-generated answer"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        if not uploaded_documents:
            return jsonify({'error': 'Please upload documents first'}), 400
        
        if not ai_assistant:
            return jsonify({'error': 'AI assistant not available'}), 500
        
        # Search for relevant context
        logger.info(f"Processing question: {question}")
        relevant_chunks = vector_store.search_similar(question, k=5, threshold=0.1)  # Lower threshold
        logger.info(f"Found {len(relevant_chunks)} relevant chunks")
        
        # Log first chunk for debugging
        if relevant_chunks:
            first_chunk = relevant_chunks[0]
            logger.info(f"First chunk source: {first_chunk.get('source', 'Unknown')}")
            logger.info(f"First chunk content preview: {first_chunk.get('content', '')[:100]}...")
        else:
            logger.info("No relevant chunks found")
        
        # Create context from relevant chunks
        context = "\n\n".join([
            f"Source: {chunk.get('source', 'Unknown')}\n{chunk.get('content', '')}"
            for chunk in relevant_chunks
        ])
        
        logger.info(f"Context length: {len(context)} characters")
        
        # Generate response using AI assistant
        response = ai_assistant.generate_response(question, context, chat_history)
        
        # Update session statistics
        study_session['questions_asked'] += 1
        study_session['total_tokens_used'] += response.get('tokens_used', 0)
        
        # Add to chat history
        chat_entry = {
            'question': question,
            'answer': response['answer'],
            'timestamp': datetime.now().isoformat(),
            'confidence': response.get('confidence', 0),
            'sources': response.get('sources_used', [])
        }
        chat_history.append(chat_entry)
        
        # Keep only last 20 conversations
        if len(chat_history) > 20:
            chat_history[:] = chat_history[-20:]
        
        logger.info(f"Generated response for question with {response.get('confidence', 0)}% confidence")
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Question processing error: {str(e)}")
        return jsonify({'error': f'Failed to process question: {str(e)}'}), 500

@app.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    """Generate quiz questions based on uploaded documents"""
    try:
        data = request.get_json()
        num_questions = data.get('num_questions', 5)
        
        if not uploaded_documents:
            return jsonify({'error': 'Please upload documents first'}), 400
        
        if not ai_assistant:
            return jsonify({'error': 'AI assistant not available'}), 500
        
        # Get random chunks for quiz generation
        all_chunks = vector_store.get_all_chunks()
        if not all_chunks:
            return jsonify({'error': 'No content available for quiz generation'}), 400
        
        # Create context from chunks (limit to reasonable size)
        context_chunks = all_chunks[:10]  # Use first 10 chunks
        context = "\n\n".join([
            f"Source: {chunk.get('source', 'Unknown')}\n{chunk.get('content', '')}"
            for chunk in context_chunks
        ])
        
        # Generate quiz questions
        logger.info(f"Generating {num_questions} quiz questions")
        quiz_questions = ai_assistant.generate_quiz_questions(context, num_questions)
        
        return jsonify({
            'quiz_questions': quiz_questions,
            'total_questions': len(quiz_questions),
            'generated_from': len(context_chunks)
        })
        
    except Exception as e:
        logger.error(f"Quiz generation error: {str(e)}")
        return jsonify({'error': f'Failed to generate quiz: {str(e)}'}), 500

@app.route('/summarize-documents', methods=['POST'])
def summarize_documents():
    """Generate summary of uploaded documents"""
    try:
        if not uploaded_documents:
            return jsonify({'error': 'Please upload documents first'}), 400
        
        if not ai_assistant:
            return jsonify({'error': 'AI assistant not available'}), 500
        
        # Get all chunks for summarization
        all_chunks = vector_store.get_all_chunks()
        if not all_chunks:
            return jsonify({'error': 'No content available for summarization'}), 400
        
        # Create context from all chunks (limit to reasonable size)
        context = "\n\n".join([
            chunk.get('content', '') for chunk in all_chunks[:15]  # Use first 15 chunks
        ])
        
        # Generate summary
        logger.info("Generating document summary")
        summary = ai_assistant.summarize_document(context)
        
        return jsonify({
            'summary': summary,
            'documents_count': len(uploaded_documents),
            'chunks_summarized': min(15, len(all_chunks))
        })
        
    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        return jsonify({'error': f'Failed to generate summary: {str(e)}'}), 500

@app.route('/chat-history', methods=['GET'])
def get_chat_history():
    """Get chat history"""
    return jsonify({
        'chat_history': chat_history,
        'total_conversations': len(chat_history)
    })

@app.route('/study-session', methods=['GET'])
def get_study_session():
    """Get current study session statistics"""
    session_duration = datetime.now() - study_session['start_time']
    
    return jsonify({
        'study_session': {
            **study_session,
            'start_time': study_session['start_time'].isoformat(),
            'duration_minutes': int(session_duration.total_seconds() //60),
            'uploaded_documents': len(uploaded_documents)
        }
    })

@app.route('/clear-session', methods=['POST'])
def clear_session():
    """Clear current session data"""
    try:
        global chat_history, uploaded_documents, study_session
        
        # Clear chat history
        chat_history.clear()
        
        # Clear uploaded documents and files
        for doc in uploaded_documents:
            filepath = doc.get('filepath')
            if filepath and os.path.exists(filepath):
                os.remove(filepath)
        
        uploaded_documents.clear()
        
        # Clear vector store
        if vector_store:
            vector_store.clear_index()
        
        # Reset study session
        study_session = {
            'start_time': datetime.now(),
            'questions_asked': 0,
            'documents_processed': 0,
            'total_tokens_used': 0
        }
        
        return jsonify({'message': 'Session cleared successfully'})
        
    except Exception as e:
        logger.error(f"Clear session error: {str(e)}")
        return jsonify({'error': f'Failed to clear session: {str(e)}'}), 500

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 50MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize components
    if not initialize_components():
        logger.error("Failed to initialize components. Exiting.")
        exit(1)
    
    logger.info("Starting StudyMate Flask API server...")
    app.run(host='0.0.0.0', port=8000, debug=True)
