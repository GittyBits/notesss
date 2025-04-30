from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/notes_app')
    UPLOAD_FOLDER = '/tmp/uploads'  # Safe temporary storage on Render
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
