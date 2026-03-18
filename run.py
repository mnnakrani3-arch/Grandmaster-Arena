import os
import sys
from pathlib import Path

def check_python_version():
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required.")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def check_dependencies():
    try:
        import flask
        import flask_sqlalchemy
        import flask_bcrypt
        import flask_mail
        import flask_socketio
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("💡 Install dependencies with: pip install -r requirements.txt")
        return False

def setup_environment():
    if 'FLASK_ENV' not in os.environ:
        os.environ['FLASK_ENV'] = 'development'
    

def main():
    print("♔ Chess Game Pro - Starting Application")
    print("=" * 50)
    
    check_python_version()
    
    if not check_dependencies():
        sys.exit(1)
    
    setup_environment()
    
    try:
        print("🚀 Starting Chess Game Pro...")
        print("📍 Server will be available at: http://localhost:5000")
        print("🔄 Press Ctrl+C to stop the server")
        print("=" * 50)
        
        from app import app, socketio, init_db

        init_db()
        
        socketio.run(
            app,
            debug=True,
            host='0.0.0.0',
            port=5000,
            allow_unsafe_werkzeug=True
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 