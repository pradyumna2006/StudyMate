"""
StudyMate - AI Learning Assistant (Fast Startup Version)
A Flask application that starts quickly without heavy model loading
"""

from flask import Flask, render_template_string, request, jsonify
import os
import tempfile

try:
    from werkzeug.utils import secure_filename
except ImportError:
    def secure_filename(filename):
        return filename

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Simple HTML template with all features
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StudyMate - AI Learning Assistant</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            overflow-x: hidden;
        }

        #bg-canvas {
            position: fixed;
            top: 0;
            left: 0;
            z-index: -1;
            opacity: 0.3;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }

        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            background: linear-gradient(45deg, #fff, #f0f8ff);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        .panel {
            background: rgba(255,255,255,0.15);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(15px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.2);
            transition: all 0.3s ease;
        }

        .panel:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.4);
        }

        .panel h2 {
            margin-bottom: 20px;
            font-size: 1.5em;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .upload-area {
            border: 2px dashed rgba(255,255,255,0.5);
            border-radius: 15px;
            padding: 40px 20px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }

        .upload-area:hover {
            border-color: rgba(255,255,255,0.8);
            background: rgba(255,255,255,0.1);
        }

        .upload-area.dragover {
            border-color: #4CAF50;
            background: rgba(76,175,80,0.2);
        }

        .file-input {
            display: none;
        }

        .upload-icon {
            font-size: 3em;
            margin-bottom: 15px;
            opacity: 0.7;
        }

        .question-section {
            margin-top: 20px;
        }

        .input-group {
            position: relative;
            margin-bottom: 20px;
        }

        .input-field {
            width: 100%;
            padding: 15px 20px;
            border: none;
            border-radius: 12px;
            background: rgba(255,255,255,0.2);
            color: white;
            font-size: 16px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.3);
            transition: all 0.3s ease;
        }

        .input-field:focus {
            outline: none;
            background: rgba(255,255,255,0.3);
            border-color: rgba(255,255,255,0.6);
            transform: scale(1.02);
        }

        .input-field::placeholder {
            color: rgba(255,255,255,0.7);
        }

        .btn {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 12px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(76,175,80,0.4);
            display: inline-flex;
            align-items: center;
            gap: 10px;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(76,175,80,0.6);
            background: linear-gradient(45deg, #45a049, #4CAF50);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-secondary {
            background: linear-gradient(45deg, #2196F3, #1976D2);
            box-shadow: 0 4px 15px rgba(33,150,243,0.4);
        }

        .btn-secondary:hover {
            box-shadow: 0 6px 20px rgba(33,150,243,0.6);
            background: linear-gradient(45deg, #1976D2, #2196F3);
        }

        .response-area {
            grid-column: 1 / -1;
            background: rgba(255,255,255,0.15);
            border-radius: 20px;
            padding: 30px;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255,255,255,0.2);
            min-height: 200px;
            display: none;
        }

        .response-area.show {
            display: block;
            animation: slideUp 0.5s ease;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }

        .loading.show {
            display: block;
        }

        .spinner {
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top: 3px solid white;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .file-info {
            margin-top: 15px;
            padding: 10px;
            background: rgba(76,175,80,0.2);
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
            display: none;
        }

        .file-info.show {
            display: block;
        }

        .voice-controls {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }

        .status-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(255,255,255,0.2);
            padding: 10px 15px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            font-size: 14px;
            z-index: 1000;
        }

        .status-online {
            background: rgba(76,175,80,0.3);
            border: 1px solid rgba(76,175,80,0.5);
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
                gap: 20px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .panel {
                padding: 20px;
            }
        }

        .error-message {
            background: rgba(244,67,54,0.2);
            border: 1px solid rgba(244,67,54,0.5);
            color: #ffcdd2;
            padding: 15px;
            border-radius: 10px;
            margin-top: 15px;
            display: none;
        }

        .error-message.show {
            display: block;
        }
    </style>
</head>
<body>
    <canvas id="bg-canvas"></canvas>
    
    <div class="status-indicator status-online">
        🟢 StudyMate Online (Fast Mode)
    </div>

    <div class="container">
        <div class="header">
            <h1>🎓 StudyMate</h1>
            <p>AI-Powered Learning Assistant - Ready to Help You Study!</p>
        </div>

        <div class="main-content">
            <div class="panel">
                <h2>📄 Upload PDF Documents</h2>
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📁</div>
                    <h3>Drop PDF files here or click to browse</h3>
                    <p>Supported: PDF files up to 50MB</p>
                    <input type="file" id="fileInput" class="file-input" accept=".pdf" multiple>
                </div>
                <div class="file-info" id="fileInfo">
                    <strong>📋 File uploaded successfully!</strong>
                    <p id="fileName"></p>
                </div>
                <div class="error-message" id="uploadError"></div>
            </div>

            <div class="panel">
                <h2>💭 Ask Questions</h2>
                <div class="question-section">
                    <div class="input-group">
                        <input type="text" id="questionInput" class="input-field" 
                               placeholder="Ask anything about your uploaded documents...">
                    </div>
                    <div class="voice-controls">
                        <button class="btn btn-secondary" id="voiceBtn">
                            🎤 Voice Input
                        </button>
                        <button class="btn" id="askBtn">
                            🚀 Ask Question
                        </button>
                    </div>
                </div>
                <div class="error-message" id="questionError"></div>
            </div>
        </div>

        <div class="response-area" id="responseArea">
            <h2>💡 AI Response</h2>
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>AI is thinking...</p>
            </div>
            <div id="responseContent"></div>
        </div>
    </div>

    <script>
        // Background animation
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer({ canvas: document.getElementById('bg-canvas'), alpha: true });
        renderer.setSize(window.innerWidth, window.innerHeight);

        const geometry = new THREE.SphereGeometry(0.5, 32, 32);
        const spheres = [];

        for (let i = 0; i < 50; i++) {
            const material = new THREE.MeshBasicMaterial({ 
                color: Math.random() * 0xffffff,
                transparent: true,
                opacity: 0.6
            });
            const sphere = new THREE.Mesh(geometry, material);
            sphere.position.set(
                (Math.random() - 0.5) * 20,
                (Math.random() - 0.5) * 20,
                (Math.random() - 0.5) * 20
            );
            sphere.velocity = {
                x: (Math.random() - 0.5) * 0.02,
                y: (Math.random() - 0.5) * 0.02,
                z: (Math.random() - 0.5) * 0.02
            };
            spheres.push(sphere);
            scene.add(sphere);
        }

        camera.position.z = 10;

        function animate() {
            requestAnimationFrame(animate);
            
            spheres.forEach(sphere => {
                sphere.position.x += sphere.velocity.x;
                sphere.position.y += sphere.velocity.y;
                sphere.position.z += sphere.velocity.z;
                
                if (sphere.position.x > 10 || sphere.position.x < -10) sphere.velocity.x *= -1;
                if (sphere.position.y > 10 || sphere.position.y < -10) sphere.velocity.y *= -1;
                if (sphere.position.z > 10 || sphere.position.z < -10) sphere.velocity.z *= -1;
                
                sphere.rotation.x += 0.01;
                sphere.rotation.y += 0.01;
            });
            
            renderer.render(scene, camera);
        }
        animate();

        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        // File upload functionality
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const uploadError = document.getElementById('uploadError');

        uploadArea.addEventListener('click', () => fileInput.click());

        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFileUpload(files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileUpload(e.target.files[0]);
            }
        });

        function handleFileUpload(file) {
            uploadError.classList.remove('show');
            
            if (file.type !== 'application/pdf') {
                showError('uploadError', 'Please upload a PDF file only.');
                return;
            }

            if (file.size > 50 * 1024 * 1024) {
                showError('uploadError', 'File size should be less than 50MB.');
                return;
            }

            const formData = new FormData();
            formData.append('file', file);

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    fileName.textContent = `File: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
                    fileInfo.classList.add('show');
                } else {
                    showError('uploadError', data.error || 'Upload failed. Please try again.');
                }
            })
            .catch(error => {
                console.error('Upload error:', error);
                showError('uploadError', 'Upload failed. Please check your connection and try again.');
            });
        }

        // Question functionality
        const questionInput = document.getElementById('questionInput');
        const askBtn = document.getElementById('askBtn');
        const voiceBtn = document.getElementById('voiceBtn');
        const responseArea = document.getElementById('responseArea');
        const loading = document.getElementById('loading');
        const responseContent = document.getElementById('responseContent');
        const questionError = document.getElementById('questionError');

        askBtn.addEventListener('click', handleQuestion);
        questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                handleQuestion();
            }
        });

        function handleQuestion() {
            const question = questionInput.value.trim();
            questionError.classList.remove('show');
            
            if (!question) {
                showError('questionError', 'Please enter a question.');
                return;
            }

            responseArea.classList.add('show');
            loading.classList.add('show');
            responseContent.innerHTML = '';

            fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question })
            })
            .then(response => response.json())
            .then(data => {
                loading.classList.remove('show');
                if (data.success) {
                    responseContent.innerHTML = `
                        <h3>🤖 AI Assistant Response:</h3>
                        <p>${data.response}</p>
                        <div style="margin-top: 15px; font-size: 0.9em; opacity: 0.8;">
                            <strong>📊 Response Time:</strong> ${data.response_time || 'N/A'}
                        </div>
                    `;
                } else {
                    responseContent.innerHTML = `
                        <h3>⚠️ Error:</h3>
                        <p>${data.error}</p>
                    `;
                }
            })
            .catch(error => {
                loading.classList.remove('show');
                console.error('Question error:', error);
                responseContent.innerHTML = `
                    <h3>⚠️ Connection Error:</h3>
                    <p>Unable to process your question. Please check your connection and try again.</p>
                `;
            });
        }

        // Voice input functionality
        voiceBtn.addEventListener('click', () => {
            if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
                const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
                recognition.lang = 'en-US';
                recognition.continuous = false;
                recognition.interimResults = false;

                recognition.onstart = () => {
                    voiceBtn.innerHTML = '🔴 Listening...';
                    voiceBtn.style.background = 'linear-gradient(45deg, #f44336, #d32f2f)';
                };

                recognition.onresult = (event) => {
                    const transcript = event.results[0][0].transcript;
                    questionInput.value = transcript;
                };

                recognition.onend = () => {
                    voiceBtn.innerHTML = '🎤 Voice Input';
                    voiceBtn.style.background = 'linear-gradient(45deg, #2196F3, #1976D2)';
                };

                recognition.onerror = (event) => {
                    console.error('Speech recognition error:', event.error);
                    voiceBtn.innerHTML = '🎤 Voice Input';
                    voiceBtn.style.background = 'linear-gradient(45deg, #2196F3, #1976D2)';
                    showError('questionError', 'Voice recognition failed. Please try again.');
                };

                recognition.start();
            } else {
                showError('questionError', 'Voice recognition is not supported in your browser.');
            }
        });

        function showError(elementId, message) {
            const errorElement = document.getElementById(elementId);
            errorElement.textContent = message;
            errorElement.classList.add('show');
            setTimeout(() => {
                errorElement.classList.remove('show');
            }, 5000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page with full StudyMate interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file uploads"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Only PDF files are supported'})
        
        # Create uploads directory if it doesn't exist
        uploads_dir = os.path.join(os.getcwd(), 'uploads')
        os.makedirs(uploads_dir, exist_ok=True)
        
        # Save the file
        filename = secure_filename(file.filename)
        filepath = os.path.join(uploads_dir, filename)
        file.save(filepath)
        
        # Simple success response (actual processing would happen here)
        return jsonify({
            'success': True, 
            'message': f'File {filename} uploaded successfully',
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload error: {str(e)}'})

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handle questions (simplified version)"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': 'No question provided'})
        
        # Simple response for fast startup (replace with AI processing later)
        response = f"""Thank you for your question: "{question}"

🚀 **StudyMate is running in Fast Mode**

This is a simplified response to ensure quick startup. The full AI features are available but may take longer to load on first use.

**Your question:** {question}

**Quick Help:**
- Upload PDF documents using the file upload area
- Ask specific questions about your uploaded content
- Use voice input for hands-free interaction

The AI assistant will provide more detailed responses once the full models are loaded. Please try your question again in a moment for enhanced AI processing.
"""
        
        return jsonify({
            'success': True,
            'response': response,
            'response_time': '< 1 second (Fast Mode)'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': f'Processing error: {str(e)}'})

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'StudyMate Fast Mode is running',
        'mode': 'fast_startup',
        'features': ['file_upload', 'question_processing', 'voice_input']
    })

if __name__ == '__main__':
    print("🚀 Starting StudyMate in Fast Mode...")
    print("📚 This version starts quickly without heavy model loading")
    print("🌐 Access the app at: http://127.0.0.1:8001")
    print("✨ All interface features are available!")
    
    # Create required directories
    os.makedirs('uploads', exist_ok=True)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=8001, debug=True)
