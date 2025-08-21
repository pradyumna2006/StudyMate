from flask import Flask, render_template_string, request, jsonify
import os
try:
    from werkzeug.utils import secure_filename
except ImportError:
    def secure_filename(filename):
        return filename

# Import the actual processing modules
from utils.pdf_processor import PDFProcessor
from utils.ai_assistant import AIAssistant
from utils.vector_store import VectorStore

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize components
pdf_processor = PDFProcessor()
vector_store = VectorStore()
ai_assistant = AIAssistant()

# Store for tracking uploaded documents
uploaded_documents = []

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StudyMate - AI Academic Assistant</title>
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
            overflow-x: hidden;
        }

        #canvas-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
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
            animation: fadeInDown 1s ease-out;
        }

        .title {
            font-size: 3.5rem;
            font-weight: 700;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #f9ca24);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradientShift 3s ease-in-out infinite;
            text-shadow: 0 10px 30px rgba(0,0,0,0.3);
            margin-bottom: 10px;
        }

        .subtitle {
            font-size: 1.2rem;
            color: rgba(255, 255, 255, 0.9);
            font-weight: 300;
            text-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
            animation: fadeInUp 1s ease-out 0.3s both;
        }

        .card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 30px 60px rgba(0, 0, 0, 0.2);
            background: rgba(255, 255, 255, 0.15);
        }

        .upload-section {
            text-align: center;
        }

        .upload-zone {
            border: 2px dashed rgba(255, 255, 255, 0.4);
            border-radius: 15px;
            padding: 40px 20px;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }

        .upload-zone:hover {
            border-color: #4ecdc4;
            background: rgba(78, 205, 196, 0.1);
        }

        .upload-zone.dragover {
            border-color: #ff6b6b;
            background: rgba(255, 107, 107, 0.1);
            transform: scale(1.02);
        }

        .upload-icon {
            font-size: 3rem;
            color: rgba(255, 255, 255, 0.8);
            margin-bottom: 15px;
            animation: float 3s ease-in-out infinite;
        }

        .upload-text {
            color: rgba(255, 255, 255, 0.9);
            font-size: 1.1rem;
            margin-bottom: 15px;
        }

        .file-input {
            display: none;
        }

        .upload-btn {
            background: linear-gradient(45deg, #4ecdc4, #44a08d);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .upload-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(78, 205, 196, 0.4);
        }

        .question-section h3 {
            color: rgba(255, 255, 255, 0.9);
            margin-bottom: 20px;
            font-size: 1.4rem;
            font-weight: 600;
        }

        .question-input {
            width: 100%;
            padding: 15px 20px;
            border: none;
            border-radius: 15px;
            background: rgba(255, 255, 255, 0.9);
            font-size: 1rem;
            margin-bottom: 15px;
            transition: all 0.3s ease;
            resize: vertical;
            min-height: 120px;
        }

        .question-input:focus {
            outline: none;
            box-shadow: 0 0 20px rgba(78, 205, 196, 0.5);
            transform: translateY(-2px);
        }

        .ask-btn {
            background: linear-gradient(45deg, #ff6b6b, #ee5a52);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .ask-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(255, 107, 107, 0.4);
        }

        .answer-section {
            grid-column: 1 / -1;
            animation: fadeInUp 1s ease-out 0.6s both;
        }

        .answer-box {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 30px;
            min-height: 200px;
            color: #333;
            font-size: 1.1rem;
            line-height: 1.6;
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        .answer-placeholder {
            color: #999;
            font-style: italic;
            text-align: center;
            padding: 50px 20px;
        }

        .quiz-section {
            animation: fadeInUp 1s ease-out 0.9s both;
        }

        .quiz-button {
            background: linear-gradient(45deg, #f093fb, #f5576c);
            color: white;
            border: none;
            padding: 20px 40px;
            border-radius: 20px;
            font-size: 1.2rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            width: 100%;
            text-transform: uppercase;
            letter-spacing: 2px;
            position: relative;
            overflow: hidden;
        }

        .quiz-button:hover {
            transform: translateY(-3px) scale(1.02);
            box-shadow: 0 15px 35px rgba(240, 147, 251, 0.4);
        }

        .quiz-button::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.3), transparent);
            transform: rotate(45deg);
            transition: all 0.5s ease;
            opacity: 0;
        }

        .quiz-button:hover::before {
            animation: shine 0.5s ease-in-out;
        }

        @keyframes gradientShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }

        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }

        @keyframes shine {
            0% { opacity: 0; transform: translateX(-100%) translateY(-100%) rotate(45deg); }
            50% { opacity: 1; }
            100% { opacity: 0; transform: translateX(100%) translateY(100%) rotate(45deg); }
        }

        .file-list {
            margin-top: 15px;
            text-align: left;
        }

        .file-item {
            background: rgba(255, 255, 255, 0.2);
            padding: 10px 15px;
            border-radius: 10px;
            margin-bottom: 5px;
            color: rgba(255, 255, 255, 0.9);
            font-size: 0.9rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .remove-file {
            background: rgba(255, 107, 107, 0.8);
            border: none;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8rem;
        }

        .status-message {
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            font-weight: 600;
        }

        .success {
            background: rgba(76, 175, 80, 0.2);
            color: #4CAF50;
            border: 1px solid rgba(76, 175, 80, 0.5);
        }

        .error {
            background: rgba(244, 67, 54, 0.2);
            color: #F44336;
            border: 1px solid rgba(244, 67, 54, 0.5);
        }

        .loading {
            text-align: center;
            padding: 20px;
            color: rgba(255, 255, 255, 0.8);
        }

        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
            
            .title {
                font-size: 2.5rem;
            }
            
            .card {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div id="canvas-container"></div>
    
    <div class="container">
        <header class="header">
            <h1 class="title">StudyMate</h1>
            <p class="subtitle">Your AI-Powered Academic Assistant</p>
        </header>

        <div class="main-content">
            <div class="card upload-section">
                <h3 style="color: rgba(255, 255, 255, 0.9); margin-bottom: 20px; font-size: 1.4rem;">📚 Upload Study Materials</h3>
                <div class="upload-zone" id="uploadZone">
                    <div class="upload-icon">📄</div>
                    <div class="upload-text">Drag & drop your PDFs here</div>
                    <input type="file" id="fileInput" class="file-input" multiple accept=".pdf">
                    <button class="upload-btn" onclick="document.getElementById('fileInput').click()">
                        Choose Files
                    </button>
                </div>
                <div id="uploadStatus"></div>
                <div class="file-list" id="fileList">
                    {% for file in uploaded_files %}
                    <div class="file-item">
                        <span>📄 {{ file }}</span>
                        <button class="remove-file" onclick="removeFile('{{ file }}')">Remove</button>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="card question-section">
                <h3>💬 Ask Your Question</h3>
                <textarea 
                    class="question-input" 
                    id="questionInput"
                    placeholder="What would you like to know about your study materials? Ask anything - from specific concepts to detailed explanations..."
                ></textarea>
                <button class="ask-btn" id="askBtn">Ask StudyMate</button>
            </div>

            <div class="card answer-section">
                <h3 style="color: rgba(255, 255, 255, 0.9); margin-bottom: 20px; font-size: 1.4rem;">🤖 AI Response</h3>
                <div class="answer-box" id="answerBox">
                    {% if answer %}
                        {{ answer }}
                    {% else %}
                    <div class="answer-placeholder">
                        Upload your study materials and ask a question to get started! StudyMate will analyze your documents and provide detailed, contextual answers.
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>

        <div class="card quiz-section">
            <button class="quiz-button" id="quizBtn">
                🎯 Generate Interactive Quiz
            </button>
        </div>
    </div>

    <script>
        // Three.js Scene Setup
        let scene, camera, renderer, particles;

        function initThreeJS() {
            scene = new THREE.Scene();
            camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
            renderer = new THREE.WebGLRenderer({ alpha: true });
            renderer.setSize(window.innerWidth, window.innerHeight);
            document.getElementById('canvas-container').appendChild(renderer.domElement);

            // Create floating particles
            const geometry = new THREE.BufferGeometry();
            const particleCount = 100;
            const positions = new Float32Array(particleCount * 3);
            const colors = new Float32Array(particleCount * 3);

            for (let i = 0; i < particleCount * 3; i += 3) {
                positions[i] = (Math.random() - 0.5) * 20;
                positions[i + 1] = (Math.random() - 0.5) * 20;
                positions[i + 2] = (Math.random() - 0.5) * 20;

                colors[i] = Math.random();
                colors[i + 1] = Math.random();
                colors[i + 2] = Math.random();
            }

            geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

            const material = new THREE.PointsMaterial({
                size: 0.05,
                vertexColors: true,
                transparent: true,
                opacity: 0.6
            });

            particles = new THREE.Points(geometry, material);
            scene.add(particles);

            camera.position.z = 5;

            animate();
        }

        function animate() {
            requestAnimationFrame(animate);
            particles.rotation.x += 0.001;
            particles.rotation.y += 0.002;
            renderer.render(scene, camera);
        }

        // File Upload Functionality
        const uploadZone = document.getElementById('uploadZone');
        const fileInput = document.getElementById('fileInput');
        const fileList = document.getElementById('fileList');
        const questionInput = document.getElementById('questionInput');
        const askBtn = document.getElementById('askBtn');
        const answerBox = document.getElementById('answerBox');
        const quizBtn = document.getElementById('quizBtn');
        const uploadStatus = document.getElementById('uploadStatus');

        let uploadedFiles = [];

        // Drag and drop functionality
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            const files = Array.from(e.dataTransfer.files).filter(file => file.type === 'application/pdf');
            handleFiles(files);
        });

        fileInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            handleFiles(files);
        });

        function handleFiles(files) {
            files.forEach(file => {
                if (!uploadedFiles.some(f => f.name === file.name)) {
                    uploadedFiles.push(file);
                    uploadFile(file);
                }
            });
        }

        function uploadFile(file) {
            const formData = new FormData();
            formData.append('pdf_file', file);

            uploadStatus.innerHTML = '<div class="loading">📤 Uploading ' + file.name + '...</div>';

            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    uploadStatus.innerHTML = '<div class="status-message success">✅ ' + data.message + '</div>';
                    addFileToList(file.name);
                    setTimeout(() => {
                        uploadStatus.innerHTML = '';
                    }, 3000);
                } else {
                    uploadStatus.innerHTML = '<div class="status-message error">❌ ' + data.error + '</div>';
                    // Remove from uploaded files if failed
                    uploadedFiles = uploadedFiles.filter(f => f.name !== file.name);
                }
            })
            .catch(error => {
                console.error('Upload error:', error);
                uploadStatus.innerHTML = '<div class="status-message error">❌ Failed to upload ' + file.name + '</div>';
                uploadedFiles = uploadedFiles.filter(f => f.name !== file.name);
            });
        }

        function addFileToList(fileName) {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.innerHTML = `
                <span>📄 ${fileName}</span>
                <button class="remove-file" onclick="removeFile('${fileName}')">Remove</button>
            `;
            fileList.appendChild(fileItem);
        }

        function removeFile(fileName) {
            uploadedFiles = uploadedFiles.filter(f => f.name !== fileName);
            // Remove from DOM
            const fileItems = document.querySelectorAll('.file-item');
            fileItems.forEach(item => {
                if (item.textContent.includes(fileName)) {
                    item.remove();
                }
            });
        }

        // Question asking functionality
        askBtn.addEventListener('click', () => {
            const question = questionInput.value.trim();
            if (!question) {
                alert('Please enter a question!');
                return;
            }
            if (uploadedFiles.length === 0) {
                alert('Please upload at least one PDF document first!');
                return;
            }

            // Show loading state
            answerBox.innerHTML = '<div style="text-align: center; padding: 50px;"><div style="font-size: 2rem;">🤔</div><div>Analyzing your documents and generating response...</div></div>';
            
            fetch('/ask', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'question=' + encodeURIComponent(question)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    answerBox.innerHTML = '<div style="white-space: pre-line;">' + data.answer + '</div>';
                } else {
                    answerBox.innerHTML = '<div class="error">❌ ' + data.error + '</div>';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                answerBox.innerHTML = '<div class="error">❌ Failed to get answer. Please try again.</div>';
            });
        });

        // Quiz functionality
        quizBtn.addEventListener('click', () => {
            if (uploadedFiles.length === 0) {
                alert('Please upload study materials first to generate a quiz!');
                return;
            }
            
            alert('🎯 Quiz generation feature coming soon! This will create interactive quizzes based on your uploaded study materials.');
        });

        // Initialize Three.js when page loads
        window.addEventListener('load', initThreeJS);

        // Handle window resize
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });

        // Add some interactive hover effects
        document.querySelectorAll('.card').forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px) scale(1.01)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
            });
        });
    </script>
</body>
</html>
'''

@app.route('/', methods=['GET'])
def index():
    return render_template_string(HTML_TEMPLATE, uploaded_files=uploaded_documents)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "message": "StudyMate Flask API is running"})

@app.route('/upload', methods=['POST'])
def upload():
    try:
        file = request.files.get('pdf_file')
        if not file or not file.filename.endswith('.pdf'):
            return jsonify({"success": False, "error": "Please upload a valid PDF file."})
        
        # Save file temporarily
        filename = secure_filename(file.filename)
        temp_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(temp_path)
        
        # Process PDF
        try:
            # Extract text from PDF
            text = pdf_processor.extract_text_from_pdf(temp_path)
            
            if not text.strip():
                return jsonify({"success": False, "error": f"Could not extract text from {filename}. Please ensure it's a text-based PDF."})
            
            # Create documents for vector store
            documents = pdf_processor.create_documents(text, filename)
            
            # Add to vector store
            vector_store.add_documents(documents, filename)
            
            # Track uploaded file
            if filename not in uploaded_documents:
                uploaded_documents.append(filename)
            
            # Clean up temp file
            os.remove(temp_path)
            
            return jsonify({"success": True, "message": f"Successfully processed {filename}! You can now ask questions about it."})
        
        except Exception as process_error:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({"success": False, "error": f"Error processing {filename}: {str(process_error)}"})
    
    except Exception as e:
        return jsonify({"success": False, "error": f"Upload error: {str(e)}"})

@app.route('/ask', methods=['POST'])
def ask():
    try:
        question = request.form.get('question')
        if not question or not question.strip():
            return jsonify({"success": False, "error": "Please enter a question."})
        
        if not uploaded_documents:
            return jsonify({"success": False, "error": "Please upload a PDF document first before asking questions."})
        
        # Get relevant context from vector store
        context = vector_store.get_relevant_context(question, max_tokens=3000)
        
        if not context.strip():
            return jsonify({"success": False, "error": "Could not find relevant information in the uploaded documents."})
        
        # Generate answer using AI assistant
        response = ai_assistant.generate_response(question, context)
        
        return jsonify({
            "success": True, 
            "answer": response['answer'],
            "confidence": response.get('confidence', 0),
            "sources": response.get('sources_used', []),
            "follow_up_questions": response.get('follow_up_questions', [])
        })
    
    except Exception as e:
        return jsonify({"success": False, "error": f"Error processing question: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=True)
