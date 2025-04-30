from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
import hashlib
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
import io
import uuid
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
# Using simple hashing instead of bcrypt

# Create necessary folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('data', exist_ok=True)  # For storing JSON data files

# Define paths for our data files
USERS_FILE = 'data/users.json'
NOTES_FILE = 'data/notes.json'

# File-based storage functions
def load_json_file(file_path, default=None):
    """Load data from a JSON file or return default if file doesn't exist"""
    if default is None:
        default = []
    
    if not os.path.exists(file_path):
        return default
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return default

def save_json_file(file_path, data):
    """Save data to a JSON file"""
    with open(file_path, 'w') as f:
        json.dump(data, f, default=str)  # default=str handles datetime objects

# User management functions
def get_users():
    """Get all users from the JSON file"""
    return load_json_file(USERS_FILE, default=[])

def save_users(users):
    """Save users to the JSON file"""
    save_json_file(USERS_FILE, users)

def find_user(username):
    """Find a user by username"""
    users = get_users()
    for user in users:
        if user['username'] == username:
            return user
    return None

def insert_user(user):
    """Insert a new user"""
    users = get_users()
    users.append(user)
    save_users(users)

# Note management functions
def get_notes():
    """Get all notes from the JSON file"""
    return load_json_file(NOTES_FILE, default=[])

def save_notes(notes):
    """Save notes to the JSON file"""
    save_json_file(NOTES_FILE, notes)

def find_note(note_id):
    """Find a note by ID"""
    notes = get_notes()
    for note in notes:
        if note['_id'] == note_id:
            return note
    return None

def insert_note(note):
    """Insert a new note"""
    notes = get_notes()
    # Generate a unique ID if not provided
    if '_id' not in note:
        note['_id'] = str(uuid.uuid4())
    notes.append(note)
    save_notes(notes)
    return note['_id']

def delete_note_by_id(note_id):
    """Delete a note by ID"""
    notes = get_notes()
    notes = [note for note in notes if note['_id'] != note_id]
    save_notes(notes)

# Initialize admin account if not exists
def create_admin_if_not_exists():
    admin = find_user('admin')
    if not admin:
        # Create default admin (username: admin, password: admin123)
        # Using simple SHA-256 hashing instead of bcrypt
        hashed_password = hashlib.sha256('admin123'.encode()).hexdigest()
        insert_user({
            'username': 'admin',
            'password': hashed_password,
            'is_admin': True
        })
        print("Default admin account created!")

# Call this function when the app starts
create_admin_if_not_exists()

# Helper function to check if user is logged in
def is_logged_in():
    return session.get('logged_in', False)

# Helper function to check if user is admin
def is_admin():
    return session.get('is_admin', False)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = find_user(username)
        
        # Using simple SHA-256 hashing for password check
        hashed_input_password = hashlib.sha256(password.encode()).hexdigest()
        if user and user['password'] == hashed_input_password:
            session['logged_in'] = True
            session['username'] = username
            session['is_admin'] = user.get('is_admin', False)
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))

@app.route('/admin')
def admin_dashboard():
    if not is_logged_in() or not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    notes = get_notes()
    return render_template('admin_dashboard.html', notes=notes)

@app.route('/notes')
def notes():
    notes = get_notes()
    return render_template('notes.html', notes=notes)

@app.route('/upload_note', methods=['POST'])
def upload_note():
    if not is_logged_in() or not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        title = request.form.get('title', 'Untitled Note')
        description = request.form.get('description', '')
        
        note = {
            'title': title,
            'description': description,
            'filename': filename,
            'file_path': file_path,
            'uploaded_at': datetime.now(),
            'uploaded_by': session.get('username')
        }
        
        # Insert note and get the generated ID
        note_id = insert_note(note)
        flash('Note uploaded successfully!', 'success')
        
    return redirect(url_for('admin_dashboard'))

@app.route('/download/<note_id>')
def download_note(note_id):
    note = find_note(note_id)
    
    if not note:
        flash('Note not found', 'danger')
        return redirect(url_for('notes'))
    
    try:
        return send_file(note['file_path'], 
                         download_name=note['filename'], 
                         as_attachment=True)
    except Exception as e:
        flash(f'Error downloading file: {str(e)}', 'danger')
        return redirect(url_for('notes'))

@app.route('/delete_note/<note_id>')
def delete_note(note_id):
    if not is_logged_in() or not is_admin():
        flash('Unauthorized access', 'danger')
        return redirect(url_for('login'))
    
    note = find_note(note_id)
    
    if not note:
        flash('Note not found', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # Delete the file from the filesystem
    try:
        os.remove(note['file_path'])
    except OSError:
        pass  # File might not exist
    
    # Delete the note from the database
    delete_note_by_id(note_id)
    
    flash('Note deleted successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
