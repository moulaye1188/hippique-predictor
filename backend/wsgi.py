import sys
import os

# Ensure the backend directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, init_database
from model import initialize_model

# Initialize database on startup
print("Initializing database...")
try:
    init_database()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")

# Initialize model on startup
print("Initializing prediction model...")
try:
    model = initialize_model(input_dim=5)
    print("✅ Prediction model initialized successfully")
except Exception as e:
    print(f"⚠️ Model initialization warning: {e}")

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🐴 HIPPIQUE PREDICTOR - Starting Server")
    print("="*50)
    print("Frontend: http://localhost:5000")
    print("API Health: http://localhost:5000/api/health")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
