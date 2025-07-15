"""
Flask web application for secure file transfer with quantum-resistant cryptography.
Integrates AES-GCM encryption with simulated Kyber key exchange.
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

from encryption_utils import EncryptionUtils
from simulated_kyber import create_kyber_instance
from peer_server import start_peer_server, stop_peer_server, is_server_running
from peer_client import send_file_to_peer, test_peer_connection

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ENCRYPTED_FOLDER'] = 'encrypted'
app.config['DECRYPTED_FOLDER'] = 'decrypted'

# Allowed file extensions for security
ALLOWED_EXTENSIONS = {
    'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 
    'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar', '7z', 'tar', 
    'gz', 'mp3', 'mp4', 'avi', 'mov', 'csv', 'json', 'xml'
}

# Create necessary directories
for folder in [app.config['UPLOAD_FOLDER'], app.config['ENCRYPTED_FOLDER'], app.config['DECRYPTED_FOLDER']]:
    Path(folder).mkdir(exist_ok=True)

# Initialize encryption utilities
encryption_utils = EncryptionUtils()

# Start peer server on app startup
start_peer_server()

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_info(filepath):
    """Get file information including size and modification time."""
    if os.path.exists(filepath):
        stat = os.stat(filepath)
        return {
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'exists': True
        }
    return {'exists': False}

@app.route('/')
def index():
    """Main upload page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload, encryption, and decryption."""
    try:
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        file = request.files['file']
        
        # Check if file is empty
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        # Validate file type
        if not file or not allowed_file(file.filename):
            flash('File type not allowed. Please upload a valid file.', 'error')
            return redirect(url_for('index'))
        
        # Secure the filename
        filename = secure_filename(file.filename)
        if not filename:
            flash('Invalid filename', 'error')
            return redirect(url_for('index'))
        
        # Save uploaded file
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(upload_path)
        logger.info(f"File uploaded: {upload_path}")
        
        # Generate Kyber keypair and shared secret
        logger.info("Generating Kyber key exchange...")
        kyber = create_kyber_instance(security_level=3)
        public_key, private_key = kyber.generate_keypair()
        ciphertext, shared_secret = kyber.encapsulate(public_key)
        
        # Encrypt the file
        logger.info("Encrypting file...")
        encryption_result = encryption_utils.encrypt_file(upload_path, shared_secret)
        
        if encryption_result['status'] != 'success':
            flash(f'Encryption failed: {encryption_result["error"]}', 'error')
            return redirect(url_for('index'))
        
        # Save encrypted file
        encrypted_filename = f"encrypted_{filename}.enc"
        encrypted_path = os.path.join(app.config['ENCRYPTED_FOLDER'], encrypted_filename)
        
        if not encryption_utils.save_encrypted_file(encryption_result, encrypted_path):
            flash('Failed to save encrypted file', 'error')
            return redirect(url_for('index'))
        
        # Test decryption
        logger.info("Testing decryption...")
        loaded_encrypted = encryption_utils.load_encrypted_file(encrypted_path)
        
        if loaded_encrypted['status'] != 'success':
            flash(f'Failed to load encrypted file: {loaded_encrypted["error"]}', 'error')
            return redirect(url_for('index'))
        
        # Decrypt using the same shared secret
        decryption_result = encryption_utils.decrypt_file(
            loaded_encrypted['encrypted_data'],
            loaded_encrypted['salt'],
            loaded_encrypted['nonce'],
            shared_secret
        )
        
        if decryption_result['status'] != 'success':
            flash(f'Decryption failed: {decryption_result["error"]}', 'error')
            return redirect(url_for('index'))
        
        # Save decrypted file
        decrypted_filename = f"decrypted_{filename}"
        decrypted_path = os.path.join(app.config['DECRYPTED_FOLDER'], decrypted_filename)
        
        with open(decrypted_path, 'wb') as f:
            f.write(decryption_result['decrypted_data'])
        
        logger.info("File processing completed successfully")
        
        # Prepare result data
        result_data = {
            'success': True,
            'original_file': {
                'name': filename,
                'path': upload_path,
                'info': get_file_info(upload_path)
            },
            'encrypted_file': {
                'name': encrypted_filename,
                'path': encrypted_path,
                'info': get_file_info(encrypted_path)
            },
            'decrypted_file': {
                'name': decrypted_filename,
                'path': decrypted_path,
                'info': get_file_info(decrypted_path)
            },
            'encryption_info': {
                'algorithm': 'AES-256-GCM',
                'key_exchange': 'Simulated Kyber-1024',
                'original_size': encryption_result['original_size'],
                'encrypted_size': encryption_result['encrypted_size'],
                'file_hash': encryption_result['file_hash'],
                'quantum_resistant': True
            },
            'kyber_info': kyber.get_security_info()
        }
        
        flash('File uploaded and processed successfully!', 'success')
        return render_template('upload_result.html', result=result_data)
        
    except Exception as e:
        logger.error(f"Upload processing failed: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'encryption_ready': True,
        'kyber_ready': True
    })

@app.route('/demo-kyber')
def demo_kyber():
    """Demonstrate Kyber key exchange."""
    from simulated_kyber import demonstrate_kyber_exchange
    
    result = demonstrate_kyber_exchange()
    return jsonify(result)

@app.route('/peer-status')
def peer_status():
    """Get peer server status."""
    return jsonify({
        'server_running': is_server_running(),
        'port': 5001,
        'message': 'Peer server is ready to receive files' if is_server_running() else 'Peer server is not running'
    })

@app.route('/send-file', methods=['POST'])
def send_file():
    """Send a file to a remote peer."""
    try:
        target_host = request.form.get('target_host', '').strip()
        target_port = int(request.form.get('target_port', 5001))
        
        if not target_host:
            flash('Please enter a target host', 'error')
            return redirect(url_for('index'))
        
        # Check if file was uploaded
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('index'))
        
        if not allowed_file(file.filename):
            flash('File type not allowed', 'error')
            return redirect(url_for('index'))
        
        # Save file temporarily
        filename = secure_filename(file.filename or 'unnamed')
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{filename}")
        file.save(temp_path)
        
        logger.info(f"Sending file {filename} to {target_host}:{target_port}")
        
        # Test connection first
        if not test_peer_connection(target_host, target_port):
            flash(f'Cannot connect to {target_host}:{target_port}. Please check the address and ensure the peer is running.', 'error')
            os.remove(temp_path)
            return redirect(url_for('index'))
        
        # Send the file
        success, message = send_file_to_peer(temp_path, target_host, target_port)
        
        # Clean up temporary file
        os.remove(temp_path)
        
        if success:
            flash(f'File sent successfully to {target_host}:{target_port}!', 'success')
            logger.info(f"Successfully sent {filename} to {target_host}:{target_port}")
        else:
            flash(f'Failed to send file: {message}', 'error')
            logger.error(f"Failed to send {filename} to {target_host}:{target_port}: {message}")
        
        return redirect(url_for('index'))
        
    except ValueError:
        flash('Invalid port number', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        logger.error(f"Send file error: {str(e)}")
        flash(f'An error occurred: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/received-files')
def received_files():
    """List received files."""
    try:
        received_dir = 'received_files'
        if not os.path.exists(received_dir):
            os.makedirs(received_dir)
        
        files = []
        for filename in os.listdir(received_dir):
            file_path = os.path.join(received_dir, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    'name': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'path': file_path
                })
        
        # Sort by modification time (newest first)
        files.sort(key=lambda x: x['modified'], reverse=True)
        
        return render_template('received_files.html', files=files)
        
    except Exception as e:
        logger.error(f"Error listing received files: {str(e)}")
        flash(f'Error loading received files: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download-received/<filename>')
def download_received_file(filename):
    """Download a received file."""
    try:
        received_dir = 'received_files'
        file_path = os.path.join(received_dir, filename)
        
        # Security check: ensure file exists and is within received_files directory
        if not os.path.exists(file_path) or not os.path.abspath(file_path).startswith(os.path.abspath(received_dir)):
            flash('File not found', 'error')
            return redirect(url_for('received_files'))
        
        from flask import send_file
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Error downloading file {filename}: {str(e)}")
        flash(f'Error downloading file: {str(e)}', 'error')
        return redirect(url_for('received_files'))

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error."""
    flash('File is too large. Maximum size is 16MB.', 'error')
    return redirect(url_for('index'))

@app.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal server error: {str(e)}")
    flash('An internal error occurred. Please try again.', 'error')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
