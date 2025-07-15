"""
Peer client for sending files to remote instances.
Uses your existing encryption utilities for consistency.
"""

import socket
import struct
import os
import logging
from typing import Tuple
from encryption_utils import EncryptionUtils
from simulated_kyber import create_kyber_instance

logger = logging.getLogger(__name__)

def send_data(sock, data):
    """Send data with length prefix."""
    sock.sendall(struct.pack('!I', len(data)) + data)

def send_file_to_peer(file_path: str, target_host: str, target_port: int = 5001) -> Tuple[bool, str]:
    """
    Send a file to a remote peer using your encryption utilities.
    
    Args:
        file_path: Path to the file to send
        target_host: Target host IP or hostname
        target_port: Target port (default 5001)
        
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not os.path.exists(file_path):
        logger.error(f"File '{file_path}' does not exist.")
        return False, "File does not exist."

    file_name = os.path.basename(file_path)
    encryption_utils = EncryptionUtils()
    
    try:
        # Connect to target peer
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.settimeout(30)  # 30 second timeout
            client.connect((target_host, target_port))
            logger.info(f"Connected to peer at {target_host}:{target_port}")

            # Generate Kyber keypair and shared secret
            kyber = create_kyber_instance(security_level=3)
            public_key, private_key = kyber.generate_keypair()
            ciphertext, shared_secret = kyber.encapsulate(public_key)

            # Encrypt file using your encryption utilities
            encryption_result = encryption_utils.encrypt_file(file_path, shared_secret)
            
            if encryption_result['status'] != 'success':
                return False, f"Encryption failed: {encryption_result['error']}"

            # Save encrypted file temporarily
            temp_encrypted_path = file_path + ".tmp_encrypted"
            if not encryption_utils.save_encrypted_file(encryption_result, temp_encrypted_path):
                return False, "Failed to save encrypted file"

            # Read the encrypted file with metadata
            with open(temp_encrypted_path, 'rb') as f:
                encrypted_file_data = f.read()

            # Clean up temp file
            os.remove(temp_encrypted_path)

            # Send data in order: shared_secret, file_name, encrypted_file_data
            send_data(client, shared_secret)
            send_data(client, file_name.encode('utf-8'))
            send_data(client, encrypted_file_data)

            logger.info(f"File '{file_name}' sent successfully to {target_host}:{target_port}")
            
            # Wait for response
            try:
                response_len = struct.unpack('!I', client.recv(4))[0]
                response = client.recv(response_len).decode('utf-8')
                
                if response.startswith('SUCCESS'):
                    return True, f"File sent successfully to {target_host}:{target_port}"
                else:
                    return False, f"Remote error: {response}"
            except:
                # If no response, assume success
                return True, f"File sent to {target_host}:{target_port}"

    except socket.timeout:
        error_msg = f"Connection timeout to {target_host}:{target_port}"
        logger.error(error_msg)
        return False, error_msg
    except ConnectionRefusedError:
        error_msg = f"Connection refused by {target_host}:{target_port}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error sending file: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def test_peer_connection(target_host: str, target_port: int = 5001) -> bool:
    """
    Test if a peer is reachable.
    
    Args:
        target_host: Target host IP or hostname
        target_port: Target port (default 5001)
        
    Returns:
        True if peer is reachable, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(5)  # 5 second timeout for testing
            result = sock.connect_ex((target_host, target_port))
            return result == 0
    except:
        return False