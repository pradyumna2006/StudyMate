# 📚 StudyMate - AI-Powered Academic Assistant

> Transform your study materials into interactive learning experiences with advanced AI technology.

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.47+-red.svg)](https://streamlit.io)
# 📚 StudyMate - AI-Powered Academic Assistant

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![IBM Granite](https://img.shields.io/badge/IBM-Granite%20AI-blue.svg)](https://ibm.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

### 📖 Document Processing
- **PDF Upload & Processing**: Extract and process text from multiple PDF documents
- **Intelligent Text Chunking**: Optimized text segmentation for better context understanding
- **Multi-document Support**: Handle multiple study materials simultaneously
- **Real-time Processing**: Fast document analysis with progress indicators

### 🤖 AI-Powered Q&A
- **Contextual Answers**: Get precise answers based on your uploaded documents
- **Follow-up Suggestions**: AI-generated follow-up questions for deeper learning
- **Confidence Scoring**: Understand how confident the AI is in its responses
- **Conversation History**: Track your learning journey with persistent chat history

### 🎤 Speech-to-Text Integration
- **🎙️ Voice Questions**: Ask questions using your voice instead of typing
- **🔄 Real-time Processing**: Instant speech-to-text conversion with Google Speech Recognition
- **📁 Audio File Upload**: Support for WAV, MP3, FLAC, M4A, and OGG formats
- **⏱️ Flexible Recording**: Adjustable recording duration (3-15 seconds)
- **🎯 Smart Integration**: Voice input automatically fills the question field
- **🔊 Audio Playback**: Preview uploaded audio files before conversion
- **⚡ Multiple Input Methods**: Quick voice button or detailed speech interface

### 🧠 Advanced Learning Tools
- **Auto-Generated Quizzes**: Create multiple-choice questions from your documents
- **Document Summaries**: Get comprehensive overviews of your study materials
- **Concept Explanations**: Deep-dive explanations tailored to your level
- **Difficulty Levels**: Beginner, intermediate, and advanced explanations

### 🎨 World-Class UI/UX
- **Modern Glass-morphism Design**: Beautiful, modern interface with blur effects
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Dark/Light Themes**: Adaptive design for comfortable studying
- **Smooth Animations**: Engaging micro-interactions and transitions
- **Accessibility**: WCAG compliant design for all users

### 📊 Analytics & Progress Tracking
- **Study Session Analytics**: Track time spent, questions asked, and documents processed
- **Performance Metrics**: Monitor your learning progress over time
- **Document Statistics**: Visual insights into your study materials
- **Export Capabilities**: Save your study sessions and chat history

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- IBM Granite API credentials
- Hugging Face token (for enhanced embeddings)
- Modern web browser

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/StudyMate.git
cd StudyMate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up speech recognition (Optional for voice features)**
```bash
# For Ubuntu/Debian systems:
sudo apt-get update
sudo apt-get install portaudio19-dev python3-pyaudio

# For macOS:
brew install portaudio

# For Windows:
# PyAudio will be installed automatically with pip
```

4. **Set up environment variables**
```bash
cp .env.template .env
# Edit .env file and add your IBM Granite API credentials
```

5. **Run the application**
```bash
python app_complete.py
```

6. **Open your browser**
Navigate to `http://localhost:8001` to start using StudyMate!

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

```env
# IBM Granite Configuration (Primary AI Engine)
IBM_API_KEY=your_ibm_api_key_here
IBM_PROJECT_ID=your_ibm_project_id_here

# Google Cloud Configuration (Enhanced Speech Recognition)
GOOGLE_API_KEY=your_google_api_key_here

# Hugging Face Configuration (Enhanced Embeddings)
HF_TOKEN=your_hugging_face_token_here

# Application Settings
FLASK_ENV=development
FLASK_DEBUG=True
```

### API Key Setup

1. **IBM Granite API** (Required for AI responses):
   - Go to [IBM Cloud](https://cloud.ibm.com/catalog/services/watson-machine-learning)
   - Create a Watson Machine Learning service
   - Get your API key and Project ID

2. **Google Cloud API** (Optional for enhanced speech recognition):
   - Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
   - Create a new project or select existing one
   - Enable the Speech-to-Text API
   - Create credentials (API key)

3. **Hugging Face Token** (Optional for enhanced embeddings):
   - Go to [Hugging Face](https://huggingface.co/settings/tokens)
   - Create a new token with read permissions

## 📁 Project Structure

```
StudyMate/
├── app_complete.py       # Main Flask application
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables (create this)
├── .env.example         # Environment variables template
├── README.md            # This file
├── utils/               # Core utilities
│   ├── pdf_processor.py # PDF text extraction and processing
│   ├── vector_store.py  # Vector storage and similarity search
│   ├── ai_assistant.py  # AI-powered question answering
│   └── speech_handler.py # Speech-to-text functionality
└── .gitignore           # Git ignore rules
```

## 🎯 Usage Guide

### 1. Upload Documents
- Click on the document upload area
- Select one or more PDF files
- Wait for processing to complete

### 2. Ask Questions
- Type your question in the text area, or
- Use the voice input feature to speak your question
- Click "Ask Question" to get AI-powered answers

### 3. Generate Study Materials
- Click "Generate Quiz" to create practice questions
- Click "Summarize" to get document overviews
- Use follow-up questions for deeper exploration

### 4. Track Progress
- Monitor your study statistics in the dashboard
- Export your session data for future reference
- Review conversation history for key insights

## 🔊 Voice Features

StudyMate includes advanced speech recognition capabilities:

### Supported Audio Formats
- **WAV**: Uncompressed audio (best quality)
- **MP3**: Compressed audio (good balance)
- **FLAC**: Lossless compression
- **M4A**: Apple audio format
- **OGG**: Open-source format

### Recognition Engines
- **Google Speech Recognition**: Primary engine (requires internet)
- **Sphinx**: Offline fallback engine
- **Confidence Scoring**: Automatic selection of best result

## 🐛 Troubleshooting

### Common Issues

**1. IBM Granite API Configuration Error**
- Ensure your IBM API key is correctly set in the `.env` file
- Check that your IBM project ID and space ID are valid
- Verify you have access to IBM Granite 13B Instruct v2 model

**2. Audio Recognition Issues**
- Check microphone permissions in your browser
- Test with different audio formats
- Ensure stable internet connection for Google Speech API

**3. PDF Processing Errors**
- Verify PDF files are not password-protected
- Check file size limits (recommended < 100MB per file)
- Ensure PDFs contain extractable text (not just images)

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- **IBM Granite** - For the powerful AI language models
- **Hugging Face** - For the transformer models and embeddings
- **Google Cloud** - For enhanced speech recognition capabilities
- **Flask** - For the amazing web framework
- **FAISS** - For efficient vector similarity search

---

<div align="center">
  <strong>Transform your learning experience with StudyMate! 🚀</strong>
  <br>
  <em>Made with ❤️ for students worldwide</em>
</div>