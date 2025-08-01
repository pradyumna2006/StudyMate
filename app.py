import streamlit as st
import os
import tempfile
import json
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import pandas as pd
import time
from typing import Dict, List

# Import custom modules
from utils.pdf_processor import PDFProcessor
from utils.vector_store import VectorStore
from utils.ai_assistant import AIAssistant
from utils.speech_handler import SpeechHandler

# Page configuration
st.set_page_config(
    page_title="StudyMate - AI Academic Assistant",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for clean, modern UI like the image
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Hide Streamlit branding and default elements */
    .stDeployButton {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stSidebar {display: none;}
    
    /* Main app styling */
    .stApp {
        background: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Container styling */
    .main .block-container {
        padding: 1rem;
        max-width: 600px;
        margin: 0 auto;
    }
    
    /* Header section */
    .app-header {
        text-align: center;
        padding: 2rem 0 3rem 0;
        background: white;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 2px 20px rgba(0,0,0,0.08);
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1a202c;
        margin-bottom: 0.5rem;
    }
    
    .app-subtitle {
        font-size: 1.1rem;
        color: #64748b;
        font-weight: 400;
    }
    
    /* Upload section */
    .upload-section {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 20px rgba(0,0,0,0.08);
        text-align: center;
    }
    
    .upload-button {
        background: #4f46e5;
        color: white;
        border: none;
        border-radius: 50px;
        padding: 1rem 3rem;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
        margin: 1rem 0;
    }
    
    .upload-button:hover {
        background: #4338ca;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
    }
    
    /* Question input section */
    .question-section {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 20px rgba(0,0,0,0.08);
    }
    
    .question-input {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 50px;
        padding: 1rem 2rem;
        width: 100%;
        font-size: 1rem;
        outline: none;
        transition: all 0.3s ease;
    }
    
    .question-input:focus {
        border-color: #4f46e5;
        background: white;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    }
    
    .voice-button {
        position: absolute;
        right: 1rem;
        top: 50%;
        transform: translateY(-50%);
        background: #4f46e5;
        color: white;
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .voice-button:hover {
        background: #4338ca;
        transform: translateY(-50%) scale(1.1);
    }
    
    /* Answer section */
    .answer-section {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 20px rgba(0,0,0,0.08);
        min-height: 200px;
    }
    
    .answer-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    .answer-content {
        font-size: 1rem;
        color: #4a5568;
        line-height: 1.6;
        text-align: center;
        padding: 2rem 0;
    }
    
    /* File display */
    .file-display {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 15px;
        padding: 1rem;
        margin: 1rem 0;
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .file-icon {
        width: 40px;
        height: 40px;
        background: #4f46e5;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 1.2rem;
    }
    
    .file-info {
        flex: 1;
    }
    
    .file-name {
        font-weight: 600;
        color: #1a202c;
        margin-bottom: 0.25rem;
    }
    
    .file-status {
        font-size: 0.9rem;
        color: #10b981;
    }
    
    /* Chat messages */
    .user-message {
        background: #4f46e5;
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 5px 20px;
        margin: 1rem 0 1rem 2rem;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 10px rgba(79, 70, 229, 0.3);
    }
    
    .assistant-message {
        background: #f8fafc;
        color: #1a202c;
        padding: 1rem 1.5rem;
        border-radius: 20px 20px 20px 5px;
        margin: 1rem 2rem 1rem 0;
        max-width: 80%;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* Buttons */
    .stButton > button {
        background: #4f46e5;
        color: white;
        border: none;
        border-radius: 50px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3);
        width: 100%;
    }
    
    .stButton > button:hover {
        background: #4338ca;
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
    }
    
    /* Text input styling */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        border-radius: 15px;
        padding: 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #4f46e5;
        background: white;
        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    }
    
    /* File uploader */
    .stFileUploader > div {
        border: 2px dashed #cbd5e0;
        border-radius: 15px;
        background: #f8fafc;
        padding: 2rem;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stFileUploader > div:hover {
        border-color: #4f46e5;
        background: rgba(79, 70, 229, 0.05);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: white;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Remove default margins */
    .stMarkdown {
        margin-bottom: 0;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: #10b981;
        color: white;
        border-radius: 15px;
        padding: 1rem;
        border: none;
    }
    
    .stError {
        background: #ef4444;
        color: white;
        border-radius: 15px;
        padding: 1rem;
        border: none;
    }
    
    .stWarning {
        background: #f59e0b;
        color: white;
        border-radius: 15px;
        padding: 1rem;
        border: none;
    }
    
    .stInfo {
        background: #3b82f6;
        color: white;
        border-radius: 15px;
        padding: 1rem;
        border: none;
    }
</style>""", unsafe_allow_html=True)

# JavaScript for enhanced interactivity
st.markdown("""
<script>
// Auto-scroll chat to bottom
function scrollChatToBottom() {
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
}

// Enhanced drag and drop functionality
function setupDragAndDrop() {
    const uploadArea = document.querySelector('.upload-area');
    if (uploadArea) {
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#764ba2';
            uploadArea.style.backgroundColor = 'rgba(118, 75, 162, 0.1)';
            uploadArea.style.transform = 'scale(1.02)';
        });
        
        uploadArea.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadArea.style.borderColor = '#667eea';
            uploadArea.style.backgroundColor = 'rgba(102, 126, 234, 0.05)';
            uploadArea.style.transform = 'scale(1)';
        });
    }
}

// Initialize enhancements
document.addEventListener('DOMContentLoaded', function() {
    setupDragAndDrop();
    setInterval(scrollChatToBottom, 1000);
});
</script>
""", unsafe_allow_html=True)

# Initialize session state
def initialize_session_state():
    """Initialize all session state variables"""
    if 'pdf_processor' not in st.session_state:
        st.session_state.pdf_processor = PDFProcessor()
    
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = VectorStore()
    
    if 'ai_assistant' not in st.session_state:
        try:
            st.session_state.ai_assistant = AIAssistant()
        except Exception as e:
            st.session_state.ai_assistant = None
            st.session_state.ai_error = str(e)
    
    if 'speech_handler' not in st.session_state:
        st.session_state.speech_handler = SpeechHandler()
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    if 'uploaded_documents' not in st.session_state:
        st.session_state.uploaded_documents = []
    
    if 'current_query' not in st.session_state:
        st.session_state.current_query = ""
    
    if 'voice_query' not in st.session_state:
        st.session_state.voice_query = ""
    
    if 'study_session' not in st.session_state:
        st.session_state.study_session = {
            'start_time': datetime.now(),
            'questions_asked': 0,
            'documents_processed': 0,
            'total_tokens_used': 0
        }
    
    if 'last_processed_question' not in st.session_state:
        st.session_state.last_processed_question = ""

def create_hero_section():
    """Create the clean header section like the image"""
    st.markdown("""
    <div class="app-header">
        <div class="app-title">📚 StudyMate</div>
        <div class="app-subtitle">Your AI Study Assistant</div>
    </div>
    """, unsafe_allow_html=True)

def create_stats_dashboard():
    """Create the statistics dashboard"""
    stats = st.session_state.vector_store.get_stats()
    session = st.session_state.study_session
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <span class="stats-number">{stats['total_documents']}</span>
            <span class="stats-label">Documents Loaded</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <span class="stats-number">{session['questions_asked']}</span>
            <span class="stats-label">Questions Asked</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <span class="stats-number">{len(st.session_state.chat_history)}</span>
            <span class="stats-label">Conversations</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        study_time = datetime.now() - session['start_time']
        minutes = int(study_time.total_seconds() / 60)
        st.markdown(f"""
        <div class="stats-card">
            <span class="stats-number">{minutes}</span>
            <span class="stats-label">Study Minutes</span>
        </div>
        """, unsafe_allow_html=True)

def create_document_manager():
    """Create clean document upload section like the image"""
    st.markdown('<div class="upload-section">', unsafe_allow_html=True)
    
    # Check if we have documents
    has_documents = len(st.session_state.uploaded_documents) > 0
    
    if not has_documents:
        # First-time user experience
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div class="upload-icon">�</div>
            <div class="upload-text">Upload Your Study Materials</div>
            <div class="upload-hint">Start by uploading PDF documents to build your knowledge base</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.subheader("📂 Your Study Library")
    
    # File upload with improved UI
    st.markdown('<div class="upload-area">', unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "📄 Choose PDF files" if not has_documents else "Add more PDFs",
        type=['pdf'],
        accept_multiple_files=True,
        help="Drag and drop PDF files here or click to browse",
        label_visibility="collapsed" if not has_documents else "visible"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    if uploaded_files:
        progress_bar = st.progress(0)
        total_files = len(uploaded_files)
        
        for i, uploaded_file in enumerate(uploaded_files):
            if uploaded_file not in st.session_state.uploaded_documents:
                progress_bar.progress((i + 1) / total_files)
                
                with st.spinner(f"📖 Processing {uploaded_file.name}..."):
                    try:
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                            tmp_file.write(uploaded_file.read())
                            tmp_file_path = tmp_file.name
                        
                        # Extract text
                        text = st.session_state.pdf_processor.extract_text_from_pdf(tmp_file_path)
                        
                        if not text.strip():
                            st.warning(f"⚠️ No text found in {uploaded_file.name}. Please check if it's a text-based PDF.")
                            continue
                        
                        # Create documents for vector store
                        documents = st.session_state.pdf_processor.create_documents(
                            text, uploaded_file.name
                        )
                        
                        # Add to vector store
                        st.session_state.vector_store.add_documents(documents, uploaded_file.name)
                        
                        # Clean up
                        os.unlink(tmp_file_path)
                        
                        # Track upload
                        st.session_state.uploaded_documents.append(uploaded_file)
                        st.session_state.study_session['documents_processed'] += 1
                        
                        st.success(f"✅ {uploaded_file.name} added to your library!")
                        
                    except Exception as e:
                        st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
        
        progress_bar.empty()
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def create_question_input():
    """Create clean question input like the image"""
    st.markdown('<div class="question-section">', unsafe_allow_html=True)
    
    # Container for input with integrated voice button
    st.markdown("""
    <div style="position: relative; margin-bottom: 1rem;">
    </div>
    """, unsafe_allow_html=True)
    
    # Question input
    question = st.text_input(
        "Ask your question",
        placeholder="Ask your question...",
        label_visibility="collapsed",
        key="main_question_input"
    )
    
    # Voice input section (below the input)
    if st.button("🎤 Voice Input", help="Use voice input", key="voice_button"):
        with st.expander("🎤 Voice Input", expanded=True):
            voice_result = st.session_state.speech_handler.create_voice_interface()
            if voice_result:
                st.session_state["main_question_input"] = voice_result
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    return question

def create_answer_section():
    """Create clean answer display like the image"""
    st.markdown('<div class="answer-section">', unsafe_allow_html=True)
    st.markdown('<div class="answer-title">Answer</div>', unsafe_allow_html=True)
    
    if st.session_state.chat_history:
        # Show the most recent answer
        latest_response = None
        for msg in reversed(st.session_state.chat_history):
            if msg['role'] == 'assistant':
                latest_response = msg
                break
        
        if latest_response:
            st.markdown(f'<div class="answer-content">{latest_response["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="answer-content">Hello! How can I assist you with your studies today?</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="answer-content">Hello! How can I assist you with your studies today?</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def process_query(query: str):
    """Process user query and generate response"""
    if not st.session_state.ai_assistant:
        st.error("AI Assistant not available. Please check your OpenAI API key.")
        return
    
    with st.spinner("🤔 Thinking..."):
        try:
            # Get relevant context
            context = st.session_state.vector_store.get_relevant_context(query)
            
            if not context.strip():
                st.warning("No relevant information found in uploaded documents. Please upload relevant PDFs first.")
                return
            
            # Generate AI response
            response = st.session_state.ai_assistant.generate_response(
                query, context, st.session_state.chat_history
            )
            
            # Add to chat history
            st.session_state.chat_history.append({
                'role': 'user',
                'content': query,
                'timestamp': datetime.now()
            })
            
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response['answer'],
                'timestamp': datetime.now(),
                'metadata': {
                    'sources': response['sources_used'],
                    'confidence': response['confidence'],
                    'follow_up': response['follow_up_questions'],
                    'tokens': response['tokens_used']
                }
            })
            
            # Update session statistics
            st.session_state.study_session['questions_asked'] += 1
            st.session_state.study_session['total_tokens_used'] += response['tokens_used']
            
            # Clear current query
            st.session_state.current_query = ""
            st.session_state.voice_query = ""
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Error processing query: {str(e)}")

def generate_quiz():
    """Generate quiz questions from uploaded documents"""
    if not st.session_state.ai_assistant:
        st.error("AI Assistant not available.")
        return
    
    with st.spinner("📝 Generating quiz questions..."):
        try:
            # Get all document context
            context = st.session_state.vector_store.get_relevant_context("", max_tokens=3000)
            
            if not context.strip():
                st.warning("No content available for quiz generation.")
                return
            
            # Generate quiz
            questions = st.session_state.ai_assistant.generate_quiz_questions(context, 5)
            
            # Store in session state
            st.session_state.quiz_questions = questions
            st.session_state.show_quiz = True
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Error generating quiz: {str(e)}")

def generate_summary():
    """Generate document summary"""
    if not st.session_state.ai_assistant:
        st.error("AI Assistant not available.")
        return
    
    with st.spinner("📄 Generating summary..."):
        try:
            # Get all document context
            context = st.session_state.vector_store.get_relevant_context("", max_tokens=4000)
            
            if not context.strip():
                st.warning("No content available for summary generation.")
                return
            
            # Generate summary
            summary = st.session_state.ai_assistant.summarize_document(
                context, "Uploaded Documents"
            )
            
            # Store in session state
            st.session_state.document_summary = summary
            st.session_state.show_summary = True
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Error generating summary: {str(e)}")

def create_chat_display():
    """Create the chat display area"""
    if not st.session_state.chat_history:
        st.markdown("""
        <div class="chat-container">
            <div style="text-align: center; padding: 3rem;">
                <div style="font-size: 4rem; margin-bottom: 1rem; opacity: 0.3;">💬</div>
                <div style="font-size: 1.5rem; font-weight: 600; color: #667eea; margin-bottom: 1rem;">
                    Your Conversation Will Appear Here
                </div>
                <div style="color: #666; font-size: 1.1rem;">
                    Start by uploading documents and asking your first question!
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        return
    
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)
    
    for i, message in enumerate(st.session_state.chat_history):
        if message['role'] == 'user':
            st.markdown(f"""
            <div class="user-message">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <div style="font-size: 1.2rem; margin-right: 0.5rem;">👤</div>
                    <strong>You asked:</strong>
                </div>
                <div style="margin-left: 1.7rem; line-height: 1.5;">
                    {message['content']}
                </div>
                <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 1rem; text-align: right;">
                    {message['timestamp'].strftime('%I:%M %p')}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            metadata = message.get('metadata', {})
            confidence = metadata.get('confidence', 0)
            tokens = metadata.get('tokens', 0)
            sources = metadata.get('sources', [])
            
            st.markdown(f"""
            <div class="assistant-message">
                <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                    <div style="font-size: 1.2rem; margin-right: 0.5rem;">🤖</div>
                    <strong>StudyMate answered:</strong>
                </div>
                <div style="margin-left: 1.7rem; line-height: 1.6;">
                    {message['content']}
                </div>
                <div style="font-size: 0.8rem; opacity: 0.7; margin-top: 1rem; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        📊 Confidence: {confidence}% | 🔤 Tokens: {tokens}
                        {f' | 📚 Sources: {len(sources)}' if sources else ''}
                    </div>
                    <div>
                        {message['timestamp'].strftime('%I:%M %p')}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Show follow-up questions in a more attractive way
            follow_up = metadata.get('follow_up', [])
            if follow_up:
                st.markdown("""
                <div style="margin: 1rem 0; padding: 1rem; background: rgba(102, 126, 234, 0.1); 
                           border-radius: 15px; border-left: 4px solid #667eea;">
                    <div style="font-weight: 600; margin-bottom: 0.5rem; color: #667eea;">
                        💡 Follow-up Questions:
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                cols = st.columns(min(len(follow_up), 2))
                for j, question in enumerate(follow_up):
                    with cols[j % 2]:
                        if st.button(
                            f"❓ {question}", 
                            key=f"followup_{i}_{j}",
                            help="Click to ask this follow-up question"
                        ):
                            st.session_state.current_query = question
                            process_query(question)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add a "clear chat" button at the bottom
    if st.session_state.chat_history:
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🗑️ Clear Conversation", help="Clear all chat history"):
                st.session_state.chat_history.clear()
                st.success("💬 Conversation cleared!")
                st.rerun()

def create_sidebar():
    """Create the sidebar with additional features"""
    with st.sidebar:
        st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
        st.title("🎛️ Control Panel")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # AI Settings
        st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
        st.subheader("🤖 AI Settings")
        
        if 'ai_error' in st.session_state:
            st.error(f"AI Assistant Error: {st.session_state.ai_error}")
            st.info("Please set your OpenAI API key in the environment variables.")
        
        # Difficulty level
        difficulty = st.selectbox(
            "Explanation Level",
            ["beginner", "intermediate", "advanced"],
            index=1
        )
        st.session_state.difficulty_level = difficulty
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Document Stats
        if st.session_state.uploaded_documents:
            st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
            st.subheader("📊 Document Stats")
            
            stats = st.session_state.vector_store.get_stats()
            
            fig = px.pie(
                values=list(stats['sources'].values()),
                names=list(stats['sources'].keys()),
                title="Documents by Source"
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Session Management
        st.markdown('<div class="sidebar-card">', unsafe_allow_html=True)
        st.subheader("💾 Session")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📁 Save"):
                # Export chat history
                export_data = {
                    'chat_history': st.session_state.chat_history,
                    'study_session': st.session_state.study_session,
                    'timestamp': datetime.now().isoformat()
                }
                st.download_button(
                    label="💾 Download",
                    data=json.dumps(export_data, indent=2, default=str),
                    file_name=f"studymate_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("🔄 Reset"):
                st.session_state.chat_history.clear()
                st.session_state.study_session = {
                    'start_time': datetime.now(),
                    'questions_asked': 0,
                    'documents_processed': 0,
                    'total_tokens_used': 0
                }
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def show_quiz():
    """Display quiz interface"""
    if 'quiz_questions' not in st.session_state or not st.session_state.quiz_questions:
        return
    
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.subheader("📝 Generated Quiz")
    
    if 'quiz_answers' not in st.session_state:
        st.session_state.quiz_answers = {}
    
    for i, question in enumerate(st.session_state.quiz_questions):
        st.write(f"**Question {i+1}:** {question['question']}")
        
        # Radio buttons for options
        answer = st.radio(
            "Select your answer:",
            question['options'],
            key=f"quiz_q{i}",
            index=None
        )
        
        if answer:
            st.session_state.quiz_answers[i] = answer[0]  # Get letter (A, B, C, D)
        
        st.write("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Submit Quiz"):
            show_quiz_results()
    
    with col2:
        if st.button("❌ Close Quiz"):
            st.session_state.show_quiz = False
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_quiz_results():
    """Show quiz results"""
    if not st.session_state.quiz_answers:
        st.warning("Please answer at least one question!")
        return
    
    correct_count = 0
    total_questions = len(st.session_state.quiz_questions)
    
    st.subheader("📊 Quiz Results")
    
    for i, question in enumerate(st.session_state.quiz_questions):
        user_answer = st.session_state.quiz_answers.get(i, "")
        correct_answer = question['correct']
        
        is_correct = user_answer == correct_answer
        if is_correct:
            correct_count += 1
        
        # Display result
        status = "✅" if is_correct else "❌"
        st.write(f"{status} **Question {i+1}:** {question['question']}")
        st.write(f"Your answer: {user_answer} | Correct: {correct_answer}")
        if 'explanation' in question:
            st.write(f"**Explanation:** {question['explanation']}")
        st.write("---")
    
    # Overall score
    score = (correct_count / total_questions) * 100
    st.success(f"🎯 **Final Score: {score:.1f}% ({correct_count}/{total_questions})**")
    
    # Performance feedback
    if score >= 80:
        st.success("🌟 Excellent work! You have a strong understanding of the material.")
    elif score >= 60:
        st.info("👍 Good job! Consider reviewing the topics you missed.")
    else:
        st.warning("📚 Keep studying! Focus on the areas where you had incorrect answers.")

def show_summary():
    """Display document summary"""
    if 'document_summary' not in st.session_state:
        return
    
    summary = st.session_state.document_summary
    
    st.markdown('<div class="feature-card">', unsafe_allow_html=True)
    st.subheader("📄 Document Summary")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(summary['summary'])
    
    with col2:
        st.metric("Word Count", summary['word_count'])
        st.metric("Reading Time", f"{summary['estimated_reading_time']} min")
        st.metric("Tokens Used", summary['tokens_used'])
    
    if st.button("❌ Close Summary"):
        st.session_state.show_summary = False
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application function with clean UI like the image"""
    # Initialize session state
    initialize_session_state()
    
    # Create clean header
    create_hero_section()
    
    # Document upload section
    create_document_manager()
    
    # Question input
    question = create_question_input()
    
    # Auto-process question when entered (similar to the image)
    if question and question.strip() and question != st.session_state.get('last_processed_question', ''):
        if st.session_state.uploaded_documents:
            process_query(question)
            st.session_state['last_processed_question'] = question
            st.rerun()
        else:
            st.warning("Please upload a document first!")
    
    # Answer section
    create_answer_section()
    
def create_simple_sidebar():
    """Create a simple sidebar with essential controls"""
    with st.sidebar:
        st.markdown("### 📚 StudyMate")
        
        # Show document count
        doc_count = len(st.session_state.uploaded_documents)
        st.metric("Documents", doc_count)
        
        # Show questions asked
        questions_count = st.session_state.study_session['questions_asked']
        st.metric("Questions Asked", questions_count)
        
        st.markdown("---")
        
        # Clear chat history
        if st.button("🗑️ Clear History"):
            st.session_state.chat_history.clear()
            st.rerun()
        
        # Clear all documents
        if st.button("📂 Clear Documents"):
            st.session_state.vector_store.clear_index()
            st.session_state.uploaded_documents.clear()
            st.success("Documents cleared!")
            st.rerun()

if __name__ == "__main__":
    main()
