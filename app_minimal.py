"""
StudyMate - AI-Powered Learning Assistant (Minimal Version)
A minimal Flask app to test connectivity
"""

from flask import Flask, render_template_string

app = Flask(__name__)

# Basic HTML template for testing
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>StudyMate - AI Learning Assistant</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
        }
        .container {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status {
            text-align: center;
            font-size: 18px;
            color: #90EE90;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎓 StudyMate - AI Learning Assistant</h1>
        <div class="status">
            ✅ Flask application is running successfully!<br>
            📡 Connection test completed<br>
            🚀 Ready to load full application
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    """Health check endpoint"""
    return {"status": "healthy", "message": "StudyMate minimal app is running"}

if __name__ == '__main__':
    print("🚀 Starting StudyMate minimal application...")
    print("📍 This is a connectivity test version")
    print("🌐 Access the app at: http://127.0.0.1:8001")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=8001, debug=True)
