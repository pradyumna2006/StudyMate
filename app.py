import streamlit as st
import os
import tempfile
import json
import requests
from datetime import datetime
import plotly.express as px
from typing import Dict, List

# Flask API Configuration
FLASK_API_URL = "http://127.0.0.1:8001"

# Import only for speech handler (if needed)
from utils.speech_handler import SpeechHandler

# Page configuration
st.set_page_config(
    page_title="StudyMate - AI Academic Assistant",
    page_icon="📚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for study room interface matching the provided image
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Poppins:wght@300;400;500;600;700;800;900&display=swap');
    
    /* Hide Streamlit branding and default elements */
    .stDeployButton {display: none;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stSidebar {display: none;}
    
    /* Animated StudyMate Title */
    .studymate-title {
        text-align: center;
        margin: 2rem 0 3rem 0;
        position: relative;
        z-index: 10;
    }
    
    .studymate-main-title {
        font-family: 'Poppins', sans-serif;
        font-size: 4rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: gradientShift 4s ease-in-out infinite;
        text-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        letter-spacing: -2px;
        margin: 0;
        position: relative;
    }
    
    .studymate-subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 1.2rem;
        font-weight: 500;
        color: #64748b;
        margin: 0.5rem 0 0 0;
        opacity: 0;
        animation: fadeInUp 1s ease-out 0.5s both;
    }
    
    .studymate-icon {
        display: inline-block;
        font-size: 4rem;
        margin-right: 1rem;
        animation: bounce 2s infinite;
        filter: drop-shadow(0 4px 12px rgba(102, 126, 234, 0.3));
    }
    
    /* Animated background gradients */
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        60% { transform: translateY(-5px); }
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    @keyframes slideInFromLeft {
        0% {
            opacity: 0;
            transform: translateX(-50px);
        }
        100% {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes floatUpDown {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-8px); }
    }
    
    /* Main app styling with enhanced animations */
    .stApp {
        background: linear-gradient(
            135deg, 
            rgba(139, 115, 85, 0.3) 0%,
            rgba(160, 140, 115, 0.4) 25%,
            rgba(180, 165, 140, 0.3) 50%,
            rgba(200, 185, 165, 0.4) 75%,
            rgba(220, 205, 185, 0.3) 100%
        ),
        url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 800"><defs><radialGradient id="window" cx="0.2" cy="0.3"><stop offset="0%" stop-color="%23fff5e6"/><stop offset="100%" stop-color="%23f4e4d1"/></radialGradient></defs><rect width="1200" height="800" fill="%23d4c4a8"/><rect x="0" y="100" width="300" height="500" fill="url(%23window)" opacity="0.8"/><rect x="50" y="150" width="200" height="50" fill="%23e8dcc0" opacity="0.6"/><rect x="800" y="400" width="300" height="100" fill="%238b6f47" opacity="0.3"/><circle cx="100" cy="600" r="30" fill="%237d5a2b" opacity="0.4"/><rect x="900" y="300" width="200" height="300" fill="%23a0895a" opacity="0.2"/></svg>');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        min-height: 100vh;
        animation: backgroundGlow 8s ease-in-out infinite;
    }
    
    @keyframes backgroundGlow {
        0%, 100% { filter: brightness(1) contrast(1); }
        50% { filter: brightness(1.05) contrast(1.1); }
    }
    
    /* Enhanced main interface container */
    .main-interface {
        max-width: 500px;
        margin: 2rem auto;
        padding: 2.5rem;
        background: rgba(255, 255, 255, 0.95);
        border-radius: 24px;
        box-shadow: 
            0 20px 60px rgba(139, 115, 85, 0.2),
            0 8px 25px rgba(0, 0, 0, 0.1),
            inset 0 1px 0 rgba(255, 255, 255, 0.6);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        position: relative;
        animation: slideInFromLeft 0.8s ease-out, floatUpDown 6s ease-in-out infinite;
        transition: all 0.3s ease;
    }
    
    .main-interface:hover {
        transform: translateY(-5px);
        box-shadow: 
            0 25px 80px rgba(139, 115, 85, 0.25),
            0 12px 35px rgba(0, 0, 0, 0.15),
            inset 0 1px 0 rgba(255, 255, 255, 0.7);
    }
    
    /* Animated decorative elements */
    .main-interface::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(
            145deg, 
            rgba(248, 235, 220, 0.1) 0%,
            rgba(245, 230, 210, 0.05) 100%
        );
        border-radius: 24px;
        pointer-events: none;
        animation: pulse 4s ease-in-out infinite;
    }
    
    /* Container styling */
    .main .block-container {
        padding: 0;
        max-width: 100%;
        margin: 0;
    }
    
    /* Enhanced upload section with animations */
    .upload-section {
        text-align: center;
        margin-bottom: 2rem;
        position: relative;
        z-index: 1;
        animation: fadeInUp 1s ease-out 0.3s both;
    }
    
    /* Enhanced question section */
    .question-section {
        margin-bottom: 2rem;
        position: relative;
        z-index: 1;
        animation: fadeInUp 1s ease-out 0.6s both;
    }
    
    /* Enhanced answer section with animations */
    .answer-section {
        background: rgba(255, 255, 255, 0.95);
        border-radius: 16px;
        padding: 2rem;
        margin-bottom: 2rem;
        text-align: left;
        min-height: 120px;
        border: 1px solid rgba(200, 200, 200, 0.2);
        box-shadow: 
            0 4px 20px rgba(0, 0, 0, 0.08),
            0 2px 8px rgba(0, 0, 0, 0.04);
        position: relative;
        z-index: 1;
        backdrop-filter: blur(10px);
        animation: fadeInUp 1s ease-out 0.9s both;
        transition: all 0.3s ease;
    }
    
    .answer-section:hover {
        transform: translateY(-2px);
        box-shadow: 
            0 8px 30px rgba(0, 0, 0, 0.12),
            0 4px 12px rgba(0, 0, 0, 0.06);
    }
    
    .answer-section h3 {
        color: #2c3e50;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 0.8rem;
        font-family: 'Inter', sans-serif;
    }
    
    .answer-section p {
        color: #34495e;
        font-size: 1rem;
        line-height: 1.6;
        margin: 0;
    }
    
    /* Additional styling for content within answer section */
    .answer-section .stMarkdown,
    .answer-section div,
    .answer-section pre,
    .answer-section code {
        background: transparent !important;
        color: #2c3e50 !important;
    }
    
    .answer-section ul,
    .answer-section ol {
        color: #34495e;
        padding-left: 1.5rem;
    }
    
    .answer-section li {
        margin-bottom: 0.5rem;
        line-height: 1.6;
    }
    
    /* Enhanced file uploader with animations */
    .stFileUploader > div {
        border: 2px dashed rgba(66, 133, 244, 0.3);
        border-radius: 16px;
        background: rgba(255, 255, 255, 0.7);
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        backdrop-filter: blur(10px);
        animation: pulse 3s ease-in-out infinite;
    }
    
    .stFileUploader > div:hover {
        border-color: #4285f4;
        background: rgba(255, 255, 255, 0.9);
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 8px 25px rgba(66, 133, 244, 0.2);
        animation: none;
    }
    
    .stFileUploader label {
        background: linear-gradient(135deg, #4285f4 0%, #667eea 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(66, 133, 244, 0.3) !important;
        font-family: 'Inter', sans-serif !important;
        animation: floatUpDown 4s ease-in-out infinite !important;
    }
    
    .stFileUploader label:hover {
        background: linear-gradient(135deg, #3367d6 0%, #5a67d8 100%) !important;
        transform: translateY(-2px) scale(1.05) !important;
        box-shadow: 0 6px 20px rgba(66, 133, 244, 0.4) !important;
        animation: none !important;
    }
    
    /* Enhanced text input styling */
    .stTextInput > div > div > input {
        background: rgba(255, 255, 255, 0.9);
        border: 2px solid rgba(200, 185, 165, 0.4);
        border-radius: 12px;
        padding: 1rem 1.5rem;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
        color: #5d4037;
        font-family: 'Inter', sans-serif;
        backdrop-filter: blur(10px);
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #4285f4;
        background: rgba(255, 255, 255, 0.95);
        box-shadow: 0 0 0 3px rgba(66, 133, 244, 0.1);
        outline: none;
        transform: scale(1.02);
    }
    
    .stTextInput > div > div > input::placeholder {
        color: rgba(93, 64, 55, 0.6);
        font-style: italic;
    }
    
    /* Enhanced button styling with animations */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        font-family: 'Inter', sans-serif;
        animation: floatUpDown 5s ease-in-out infinite;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #667eea 100%);
        transform: translateY(-2px) scale(1.05);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        animation: none;
    }
    
    /* Voice button special styling */
    .stButton > button[title*="voice"], .stButton > button[title*="Voice"] {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
        width: 60px;
        height: 60px;
        border-radius: 50%;
        padding: 0;
        font-size: 1.5rem;
        animation: pulse 2s ease-in-out infinite;
    }
    
    .stButton > button[title*="voice"]:hover, .stButton > button[title*="Voice"]:hover {
        background: linear-gradient(135deg, #ee5a52 0%, #e84142 100%);
        transform: scale(1.1);
        animation: none;
    }
    
    /* Enhanced messages with animations */
    .stSuccess {
        background: linear-gradient(135deg, #48bb78, #38a169);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        border: none;
        text-align: center;
        box-shadow: 0 4px 15px rgba(72, 187, 120, 0.3);
        animation: fadeInUp 0.5s ease-out;
    }
    
    .stError {
        background: linear-gradient(135deg, #f56565, #e53e3e);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        border: none;
        text-align: center;
        box-shadow: 0 4px 15px rgba(245, 101, 101, 0.3);
        animation: fadeInUp 0.5s ease-out;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #ffb74d, #ffa726);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        border: none;
        text-align: center;
        box-shadow: 0 4px 15px rgba(255, 183, 77, 0.3);
        animation: fadeInUp 0.5s ease-out;
    }
    
    /* Progress bar with gradient animations */
    .stProgress > div > div {
        background: linear-gradient(90deg, #4285f4, #667eea, #764ba2);
        background-size: 200% 100%;
        border-radius: 10px;
        animation: gradientMove 2s ease-in-out infinite;
    }
    
    @keyframes gradientMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Additional animation for fadeInUp */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.8);
        border-radius: 12px;
        padding: 0.5rem 1rem;
        border: 1px solid rgba(200, 200, 200, 0.2);
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(255, 255, 255, 0.95);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    /* Remove default margins */
    .stMarkdown {
        margin-bottom: 0;
    }
    
    /* Column gap adjustment */
    .row-widget.stHorizontal > div {
        padding-right: 0.5rem;
    }
    
    .row-widget.stHorizontal > div:last-child {
        padding-right: 0;
    }
    
    /* Loading and success animations */
    .stSpinner {
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* Floating particles effect */
    .floating-particles {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        pointer-events: none;
        z-index: 1;
        overflow: hidden;
    }
    
    .particle {
        position: absolute;
        background: rgba(102, 126, 234, 0.1);
        border-radius: 50%;
        animation: float 15s infinite linear;
    }
    
    .particle:nth-child(1) { left: 10%; animation-delay: 0s; width: 10px; height: 10px; }
    .particle:nth-child(2) { left: 20%; animation-delay: 2s; width: 15px; height: 15px; }
    .particle:nth-child(3) { left: 30%; animation-delay: 4s; width: 8px; height: 8px; }
    .particle:nth-child(4) { left: 40%; animation-delay: 6s; width: 12px; height: 12px; }
    .particle:nth-child(5) { left: 50%; animation-delay: 8s; width: 6px; height: 6px; }
    .particle:nth-child(6) { left: 60%; animation-delay: 10s; width: 14px; height: 14px; }
    .particle:nth-child(7) { left: 70%; animation-delay: 12s; width: 9px; height: 9px; }
    .particle:nth-child(8) { left: 80%; animation-delay: 14s; width: 11px; height: 11px; }
    .particle:nth-child(9) { left: 90%; animation-delay: 16s; width: 7px; height: 7px; }
    
    @keyframes float {
        0% {
            transform: translateY(100vh) rotate(0deg);
            opacity: 0;
        }
        10% {
            opacity: 1;
        }
        90% {
            opacity: 1;
        }
        100% {
            transform: translateY(-100px) rotate(360deg);
            opacity: 0;
        }
    }
</style>""", unsafe_allow_html=True)
    
# Initialize session state
def initialize_session_state():
    """Initialize all session state variables for Flask API integration"""
    # Flask API connection status
    if 'flask_api_connected' not in st.session_state:
        st.session_state.flask_api_connected = check_flask_api_connection()
    
    if 'speech_handler' not in st.session_state:
        try:
            st.session_state.speech_handler = SpeechHandler()
        except Exception as e:
            st.session_state.speech_handler = None
    
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

def check_flask_api_connection():
    """Check if Flask API is running and accessible"""
    try:
        response = requests.get(f"{FLASK_API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def create_animated_title():
    """Create an attractive animated title section"""
    st.markdown("""
    <div class="floating-particles">
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
        <div class="particle"></div>
    </div>
    
    <div class="studymate-title">
        <h1 class="studymate-main-title">
            <span class="studymate-icon">📚</span>StudyMate
        </h1>
        <p class="studymate-subtitle">Your AI-Powered Study Companion</p>
    </div>
    """, unsafe_allow_html=True)

def create_upload_section():
    """Create the upload file button section that communicates with Flask API"""
    st.markdown("""
    <div class="upload-section">
        <div style="margin-bottom: 1rem;">
    """, unsafe_allow_html=True)
    
    # Check Flask API connection
    if not st.session_state.flask_api_connected:
        st.error("❌ Flask API is not running. Please start the Flask server first.")
        st.markdown('</div></div>', unsafe_allow_html=True)
        return
    
    # File upload with custom styling
    uploaded_files = st.file_uploader(
        "📎 Upload File",
        type=['pdf'],
        accept_multiple_files=True,
        help="Upload PDF documents to ask questions about",
        label_visibility="collapsed"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Process uploaded files via Flask API
    if uploaded_files:
        progress_bar = st.progress(0)
        total_files = len(uploaded_files)
        
        for i, uploaded_file in enumerate(uploaded_files):
            if uploaded_file.name not in st.session_state.uploaded_documents:
                progress_bar.progress((i + 1) / total_files)
                
                with st.spinner(f"📖 Processing {uploaded_file.name}..."):
                    try:
                        # Prepare file for Flask API
                        files = {'files': (uploaded_file.name, uploaded_file.read(), 'application/pdf')}
                        
                        # Send to Flask API
                        response = requests.post(f"{FLASK_API_URL}/upload-documents", files=files, timeout=120)
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.session_state.uploaded_documents.append(uploaded_file.name)
                            st.session_state.study_session['documents_processed'] += 1
                            st.success(f"✅ {uploaded_file.name} processed successfully!")
                        else:
                            error_msg = response.json().get('error', 'Unknown error')
                            st.error(f"❌ Error processing {uploaded_file.name}: {error_msg}")
                        
                    except requests.exceptions.Timeout:
                        st.error(f"❌ Timeout processing {uploaded_file.name}. File might be too large.")
                    except Exception as e:
                        st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
        
        progress_bar.empty()
    
    st.markdown('</div>', unsafe_allow_html=True)

def create_question_input_with_voice():
    """Create question input with integrated voice button like the image"""
    st.markdown('<div class="question-section">', unsafe_allow_html=True)
    
    # Initialize speech handler
    if 'speech_handler' not in st.session_state:
        try:
            st.session_state.speech_handler = SpeechHandler()
        except Exception as e:
            st.error(f"Could not initialize speech recognition: {str(e)}")
            st.session_state.speech_handler = None
    
    # Create columns for input and voice button
    col1, col2 = st.columns([5, 1])
    
    with col1:
        # Check if we have voice input to populate the text box
        voice_text = st.session_state.get('voice_input_text', '')
        if voice_text:
            question = st.text_input(
                "Question",
                value=voice_text,
                placeholder="Ask your question...",
                label_visibility="collapsed",
                key="main_question_input"
            )
            # Clear the voice input after using it
            st.session_state.voice_input_text = ''
        else:
            question = st.text_input(
                "Question",
                placeholder="Ask your question...",
                label_visibility="collapsed",
                key="main_question_input"
            )
    
    with col2:
        if st.session_state.speech_handler:
            if st.button("🎤", help="Click to record voice input", key="voice_input_btn"):
                with st.spinner("🎤 Recording for 5 seconds... Speak now!"):
                    try:
                        audio_data = st.session_state.speech_handler.record_audio(5)
                        if audio_data:
                            with st.spinner("🔄 Converting speech to text..."):
                                text = st.session_state.speech_handler.convert_speech_to_text(audio_data)
                                if text:
                                    st.session_state.voice_input_text = text
                                    st.success(f"✅ Voice recognized: {text}")
                                    st.rerun()
                    except Exception as e:
                        st.error(f"Voice input error: {str(e)}")
        else:
            st.button("🎤", help="Voice input unavailable", key="voice_input_btn_disabled", disabled=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    return question

def create_welcome_answer_section():
    """Create the answer/welcome section exactly like the image"""
    st.markdown('<div class="answer-section">', unsafe_allow_html=True)
    
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
            # Empty section when no assistant responses yet
            st.markdown('<div class="empty-section" style="min-height: 80px;"></div>', unsafe_allow_html=True)
    else:
        # Empty section when no chat history
        st.markdown('<div class="empty-section" style="min-height: 80px;"></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

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
    """Process user query via Flask API"""
    if not st.session_state.flask_api_connected:
        st.error("❌ Flask API is not running. Please start the Flask server first.")
        return
    
    with st.spinner("🤔 Thinking..."):
        try:
            # Send question to Flask API
            response = requests.post(
                f"{FLASK_API_URL}/ask-question",
                json={"question": query},
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Add to chat history
                st.session_state.chat_history.append({
                    'role': 'user',
                    'content': query,
                    'timestamp': datetime.now()
                })
                
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': result['answer'],
                    'timestamp': datetime.now(),
                    'metadata': {
                        'sources': result.get('sources_used', []),
                        'confidence': result.get('confidence', 0),
                        'follow_up': result.get('follow_up_questions', []),
                        'tokens': result.get('tokens_used', 0)
                    }
                })
                
                # Update session statistics
                st.session_state.study_session['questions_asked'] += 1
                st.session_state.study_session['total_tokens_used'] += result.get('tokens_used', 0)
                
                # Clear current query
                st.session_state.current_query = ""
                st.session_state.voice_query = ""
                
                st.rerun()
                
            else:
                error_msg = response.json().get('error', 'Unknown error')
                st.error(f"❌ Error getting answer: {error_msg}")
            
        except requests.exceptions.Timeout:
            st.error("❌ Request timeout. The question might be too complex.")
        except Exception as e:
            st.error(f"❌ Error processing query: {str(e)}")

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
            st.info("Please set your IBM Granite API key and project ID in the environment variables.")
        
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
    """Main application function with Flask API integration"""
    # Initialize session state
    initialize_session_state()
    
    # Show API connection status
    if st.session_state.flask_api_connected:
        st.success("✅ Connected to Flask API")
    else:
        st.error("❌ Flask API not accessible. Please start the Flask server.")
        if st.button("🔄 Retry Connection"):
            st.session_state.flask_api_connected = check_flask_api_connection()
            st.rerun()
    
    # Create animated title section
    create_animated_title()
    
    # Create the main interface container
    st.markdown('<div class="main-interface">', unsafe_allow_html=True)
    
    # Upload File Button (prominent at top)
    create_upload_section()
    
    # Question input with integrated voice button
    question = create_question_input_with_voice()
    
    # Advanced Speech Features (expandable section)
    with st.expander("🎤 Advanced Speech Features", expanded=False):
        if 'speech_handler' in st.session_state and st.session_state.speech_handler:
            st.markdown("### 🎙️ Extended Voice Input Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**⏱️ Custom Recording Duration:**")
                duration = st.slider("Recording time (seconds)", 3, 15, 5, key="voice_duration")
                
                if st.button("🎤 Record with Custom Duration", key="custom_record"):
                    with st.spinner(f"🎤 Recording for {duration} seconds... Speak now!"):
                        try:
                            audio_data = st.session_state.speech_handler.record_audio(duration)
                            if audio_data:
                                with st.spinner("🔄 Converting to text..."):
                                    text = st.session_state.speech_handler.convert_speech_to_text(audio_data)
                                    if text:
                                        st.session_state.voice_input_text = text
                                        st.success(f"✅ Recognized: {text}")
                                        st.rerun()
                        except Exception as e:
                            st.error(f"Recording error: {str(e)}")
            
            with col2:
                st.markdown("**📁 Upload Audio File:**")
                uploaded_audio = st.file_uploader(
                    "Choose an audio file",
                    type=['wav', 'mp3', 'flac', 'm4a', 'ogg'],
                    key="audio_file_upload"
                )
                
                if uploaded_audio is not None:
                    st.audio(uploaded_audio, format='audio/wav')
                    
                    if st.button("🔄 Convert Audio to Text", key="convert_audio"):
                        with st.spinner("🔄 Processing audio file..."):
                            try:
                                text = st.session_state.speech_handler.process_uploaded_audio(uploaded_audio)
                                if text:
                                    st.session_state.voice_input_text = text
                                    st.success(f"✅ Recognized: {text}")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Audio processing error: {str(e)}")
        else:
            st.warning("⚠️ Speech recognition is not available. Please check your system audio settings.")
    
    # Welcome/Answer section  
    create_welcome_answer_section()
    
    # Answer button functionality
    if st.button("Answer", key="answer_button", use_container_width=True):
        if question and question.strip():
            if st.session_state.uploaded_documents:
                process_query(question)
                st.rerun()
            else:
                st.warning("Please upload a document first to get answers!")
        else:
            st.warning("Please enter a question first!")
    
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
