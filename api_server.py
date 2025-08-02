from flask import Flask, request, jsonify, send_from_directory, session
from flask_cors import CORS
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from typing import Dict, List
import logging
import uuid

# Import custom modules
from utils.pdf_processor import PDFProcessor
from utils.session_vector_store import SessionVectorStore
from utils.ai_assistant import AIAssistant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
CORS(app, supports_credentials=True)  # Enable CORS with session support

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Global instances
pdf_processor = None
session_vector_store = None
ai_assistant = None

def initialize_components():
    """Initialize all application components"""
    global pdf_processor, session_vector_store, ai_assistant
    
    try:
        # Initialize PDF processor
        pdf_processor = PDFProcessor()
        logger.info("PDF processor initialized")
        
        # Initialize session-based vector store
        session_vector_store = SessionVectorStore()
        logger.info("Session vector store initialized")
        
        # Initialize AI assistant
        ai_assistant = AIAssistant()
        logger.info("AI assistant initialized")
        
        logger.info("All components initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {str(e)}")
        return False

def get_or_create_session_id():
    """Get existing session ID or create a new one"""
    if 'session_id' not in session:
        session['session_id'] = session_vector_store.create_session()
        session['created_at'] = datetime.now().isoformat()
        logger.info(f"Created new session: {session['session_id'][:8]}...")
    
    return session['session_id']

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
            'vector_store': session_vector_store is not None,
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
                    # Get or create session
                    session_id = get_or_create_session_id()
                    
                    # Extract documents and metadata for session store
                    documents = [chunk['content'] for chunk in chunks]
                    metadata = [chunk['metadata'] for chunk in chunks]
                    
                    # Add to session vector store
                    session_vector_store.add_documents(session_id, documents, metadata)
                    
                    # Track uploaded document
                    doc_info = {
                        'filename': filename,
                        'filepath': filepath,
                        'upload_time': datetime.now().isoformat(),
                        'chunks_count': len(chunks),
                        'session_id': session_id
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
        
        # Get session ID
        session_id = get_or_create_session_id()
        
        # Check if session has documents
        session_stats = session_vector_store.get_session_stats(session_id)
        if session_stats.get('document_count', 0) == 0:
            return jsonify({'error': 'Please upload documents first'}), 400
        
        if not ai_assistant:
            return jsonify({'error': 'AI assistant not available'}), 500
        
        # Search for relevant context in session
        logger.info(f"Processing question: {question}")
        relevant_chunks = session_vector_store.search(session_id, question, k=5)
        logger.info(f"Found {len(relevant_chunks)} relevant chunks")
        
        # Log first chunk for debugging
        if relevant_chunks:
            first_chunk = relevant_chunks[0]
            logger.info(f"First chunk source: {first_chunk.get('metadata', {}).get('source', 'Unknown')}")
            logger.info(f"First chunk content preview: {first_chunk.get('content', '')[:100]}...")
        else:
            logger.info("No relevant chunks found")
        
        # Create context from relevant chunks
        context = "\n\n".join([
            f"Source: {chunk.get('metadata', {}).get('source', 'Unknown')}\n{chunk.get('content', '')}"
            for chunk in relevant_chunks
        ])
        
        logger.info(f"Context length: {len(context)} characters")
        
        # Generate response using AI assistant
        response = ai_assistant.generate_response(question, context)
        
        # Update session with question count
        if 'questions_asked' not in session:
            session['questions_asked'] = 0
        session['questions_asked'] += 1
        
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
        
        # Get session ID
        session_id = get_or_create_session_id()
        
        # Check if session has documents
        session_stats = session_vector_store.get_session_stats(session_id)
        if session_stats.get('document_count', 0) == 0:
            return jsonify({'error': 'Please upload documents first'}), 400
        
        if not ai_assistant:
            return jsonify({'error': 'AI assistant not available'}), 500
        
        # Get documents from session for quiz generation
        all_documents = session_vector_store.get_all_documents(session_id)
        if not all_documents:
            return jsonify({'error': 'No content available for quiz generation'}), 400
        
        # Create context from documents (limit to reasonable size)
        context_chunks = all_documents[:10]  # Use first 10 chunks
        context = "\n\n".join([
            f"Source: {chunk.get('metadata', {}).get('source', 'Unknown')}\n{chunk.get('content', '')}"
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
        # Get session ID
        session_id = get_or_create_session_id()
        
        # Check if session has documents
        session_stats = session_vector_store.get_session_stats(session_id)
        if session_stats.get('document_count', 0) == 0:
            return jsonify({'error': 'Please upload documents first'}), 400
        
        if not ai_assistant:
            return jsonify({'error': 'AI assistant not available'}), 500
        
        # Get all documents from session for summarization
        all_documents = session_vector_store.get_all_documents(session_id)
        if not all_documents:
            return jsonify({'error': 'No content available for summarization'}), 400
        
        # Create context from all documents (limit to reasonable size)
        context = "\n\n".join([
            doc.get('content', '') for doc in all_documents[:15]  # Use first 15 chunks
        ])
        
        # Generate summary
        logger.info("Generating document summary")
        summary = ai_assistant.summarize_document(context)
        
        return jsonify({
            'summary': summary,
            'session_stats': session_stats,
            'chunks_summarized': min(15, len(all_documents))
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
        # Clear session data
        if 'session_id' in session:
            session_id = session['session_id']
            session_vector_store.clear_session(session_id)
            logger.info(f"Cleared session: {session_id[:8]}...")
        
        # Clear Flask session
        session.clear()
        
        # Clean up uploaded files
        upload_dir = UPLOAD_FOLDER
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                if filename.lower().endswith('.pdf'):
                    filepath = os.path.join(upload_dir, filename)
                    try:
                        os.remove(filepath)
                        logger.info(f"Removed uploaded file: {filename}")
                    except Exception as e:
                        logger.warning(f"Could not remove file {filename}: {str(e)}")
        
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
