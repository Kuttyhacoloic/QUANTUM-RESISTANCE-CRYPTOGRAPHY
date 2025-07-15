"""
Peer-to-peer server component for secure file transfer.
Handles incoming file transfers from other instances.
Uses the existing encryption utilities for consistency.
"""

import socket
import struct
import os
import threading
import logging
from datetime import datetime
from encryption_utils import EncryptionUtils
from simulated_kyber import create_kyber_instance

logger = logging.getLogger(__name__)

class PeerServer:
    def __init__(self, host='0.0.0.0', port=5001, save_dir='received_files'):
        self.host = host
        self.port = port
        self.save_dir = save_dir
        self.running = False
        self.server_socket = None
        self.encryption_utils = EncryptionUtils()
        
        # Create save directory
        os.makedirs(save_dir, exist_ok=True)
        
    def recv_data(self, sock):
        """Receive data with length prefix."""
        try:
            # Receive length (4 bytes)
            raw_len = sock.recv(4)
            if not raw_len:
                return None
            
            length = struct.unpack('!I', raw_len)[0]
            
            # Receive data
            data = b''
            while len(data) < length:
                chunk = sock.recv(min(4096, length - len(data)))
                if not chunk:
                    raise ConnectionError("Connection lost during recv_data.")
                data += chunk
            
            return data
        except Exception as e:
            logger.error(f"Error receiving data: {e}")
            return None
    
    def handle_client(self, conn, addr):
        """Handle incoming client connection."""
        logger.info(f"Connection established from {addr}")
        
        try:
            # Receive shared secret
            shared_secret_data = self.recv_data(conn)
            if not shared_secret_data:
                logger.error("Failed to receive shared secret")
                return
            
            # Receive file name
            file_name_data = self.recv_data(conn)
            if not file_name_data:
                logger.error("Failed to receive file name")
                return
            
            file_name = file_name_data.decode('utf-8')
            
            # Receive encrypted file data
            encrypted_data = self.recv_data(conn)
            if not encrypted_data:
                logger.error("Failed to receive file data")
                return
            
            logger.info(f"Received file '{file_name}' from {addr}")
            
            # Decrypt the file using your encryption utilities
            try:
                # Create a temporary file to save encrypted data
                temp_encrypted_path = os.path.join(self.save_dir, f"temp_encrypted_{file_name}")
                with open(temp_encrypted_path, 'wb') as f:
                    f.write(encrypted_data)
                
                # Load and decrypt using your encryption utilities
                loaded_encrypted = self.encryption_utils.load_encrypted_file(temp_encrypted_path)
                if loaded_encrypted['status'] != 'success':
                    logger.error(f"Failed to load encrypted file: {loaded_encrypted['error']}")
                    return
                
                # Decrypt using your utilities
                decryption_result = self.encryption_utils.decrypt_file(
                    loaded_encrypted['encrypted_data'],
                    loaded_encrypted['salt'], 
                    loaded_encrypted['nonce'],
                    shared_secret_data
                )
                
                if decryption_result['status'] != 'success':
                    logger.error(f"Failed to decrypt file: {decryption_result['error']}")
                    return
                
                decrypted_data = decryption_result['decrypted_data']
                
                # Clean up temp file
                os.remove(temp_encrypted_path)
                
            except Exception as e:
                logger.error(f"Failed to decrypt file: {e}")
                return
            
            # Save decrypted file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_filename = f"received_{timestamp}_{file_name}"
            file_path = os.path.join(self.save_dir, safe_filename)
            
            with open(file_path, 'wb') as f:
                f.write(decrypted_data)
            
            logger.info(f"File saved to: {file_path}")
            
            # Send success response
            response = b"SUCCESS"
            conn.sendall(struct.pack('!I', len(response)) + response)
            
        except Exception as e:
            logger.error(f"Error handling client {addr}: {e}")
            try:
                response = f"ERROR: {str(e)}".encode()
                conn.sendall(struct.pack('!I', len(response)) + response)
            except:
                pass
        
        finally:
            conn.close()
    
    def start(self):
        """Start the peer server."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.running = True
            logger.info(f"Peer server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                    
                    # Handle each client in a separate thread
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(conn, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.error as e:
                    if self.running:
                        logger.error(f"Socket error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Failed to start peer server: {e}")
            
        finally:
            self.stop()
    
    def stop(self):
        """Stop the peer server."""
        self.running = False
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        logger.info("Peer server stopped")

# Global server instance
peer_server = None

def start_peer_server():
    """Start the peer server in a background thread."""
    global peer_server
    
    if peer_server and peer_server.running:
        return True
    
    try:
        peer_server = PeerServer()
        server_thread = threading.Thread(target=peer_server.start)
        server_thread.daemon = True
        server_thread.start()
        
        # Give the server a moment to start
        import time
        time.sleep(0.5)
        
        return True
    except Exception as e:
        logger.error(f"Failed to start peer server: {e}")
        return False

def stop_peer_server():
    """Stop the peer server."""
    global peer_server
    
    if peer_server:
        peer_server.stop()
        peer_server = None

def is_server_running():
    """Check if the peer server is running."""
    global peer_server
    return peer_server and peer_server.running