"""
AES-GCM encryption utilities for secure file encryption and decryption.
Provides quantum-resistant encryption using AES-256-GCM with proper key derivation.
"""

import os
import hashlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
import logging

logger = logging.getLogger(__name__)

class EncryptionUtils:
    """Utility class for AES-GCM encryption and decryption operations."""
    
    def __init__(self):
        self.key_length = 32  # 256 bits for AES-256
        self.nonce_length = 12  # 96 bits for GCM
        self.salt_length = 16  # 128 bits for salt
    
    def derive_key_from_shared_secret(self, shared_secret: bytes, salt: bytes = None) -> tuple[bytes, bytes]:
        """
        Derive AES key from shared secret using PBKDF2.
        
        Args:
            shared_secret: The shared secret from key exchange
            salt: Optional salt, will generate random if not provided
            
        Returns:
            tuple: (derived_key, salt_used)
        """
        if salt is None:
            salt = os.urandom(self.salt_length)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.key_length,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        key = kdf.derive(shared_secret)
        logger.debug(f"Derived AES key from shared secret, salt length: {len(salt)}")
        return key, salt
    
    def encrypt_file(self, file_path: str, shared_secret: bytes) -> dict:
        """
        Encrypt a file using AES-GCM with derived key from shared secret.
        
        Args:
            file_path: Path to the file to encrypt
            shared_secret: Shared secret from key exchange
            
        Returns:
            dict: Contains encrypted_data, salt, nonce, and metadata
        """
        try:
            # Read the file
            with open(file_path, 'rb') as f:
                plaintext = f.read()
            
            # Derive key from shared secret
            key, salt = self.derive_key_from_shared_secret(shared_secret)
            
            # Generate random nonce
            nonce = os.urandom(self.nonce_length)
            
            # Initialize AES-GCM cipher
            aesgcm = AESGCM(key)
            
            # Encrypt the data
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)
            
            # Calculate file hash for integrity verification
            file_hash = hashlib.sha256(plaintext).hexdigest()
            
            logger.info(f"Successfully encrypted file: {file_path}")
            
            return {
                'encrypted_data': ciphertext,
                'salt': salt,
                'nonce': nonce,
                'original_size': len(plaintext),
                'encrypted_size': len(ciphertext),
                'file_hash': file_hash,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Encryption failed for {file_path}: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def decrypt_file(self, encrypted_data: bytes, salt: bytes, nonce: bytes, shared_secret: bytes) -> dict:
        """
        Decrypt data using AES-GCM with shared secret.
        
        Args:
            encrypted_data: The encrypted data
            salt: Salt used for key derivation
            nonce: Nonce used for encryption
            shared_secret: Shared secret from key exchange
            
        Returns:
            dict: Contains decrypted_data and metadata
        """
        try:
            # Derive the same key using salt and shared secret
            key, _ = self.derive_key_from_shared_secret(shared_secret, salt)
            
            # Initialize AES-GCM cipher
            aesgcm = AESGCM(key)
            
            # Decrypt the data
            plaintext = aesgcm.decrypt(nonce, encrypted_data, None)
            
            # Calculate hash for verification
            file_hash = hashlib.sha256(plaintext).hexdigest()
            
            logger.info("Successfully decrypted data")
            
            return {
                'decrypted_data': plaintext,
                'size': len(plaintext),
                'file_hash': file_hash,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Decryption failed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def save_encrypted_file(self, encrypted_result: dict, output_path: str) -> bool:
        """
        Save encrypted file with metadata to disk.
        
        Args:
            encrypted_result: Result from encrypt_file method
            output_path: Path where to save the encrypted file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if encrypted_result['status'] != 'success':
                return False
            
            # Create metadata header
            metadata = {
                'salt': encrypted_result['salt'],
                'nonce': encrypted_result['nonce'],
                'original_size': encrypted_result['original_size'],
                'file_hash': encrypted_result['file_hash']
            }
            
            with open(output_path, 'wb') as f:
                # Write salt (16 bytes)
                f.write(metadata['salt'])
                # Write nonce (12 bytes)
                f.write(metadata['nonce'])
                # Write original size (8 bytes, big-endian)
                f.write(metadata['original_size'].to_bytes(8, 'big'))
                # Write file hash length (1 byte) and hash
                hash_bytes = metadata['file_hash'].encode('utf-8')
                f.write(len(hash_bytes).to_bytes(1, 'big'))
                f.write(hash_bytes)
                # Write encrypted data
                f.write(encrypted_result['encrypted_data'])
            
            logger.info(f"Encrypted file saved to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save encrypted file: {str(e)}")
            return False
    
    def load_encrypted_file(self, file_path: str) -> dict:
        """
        Load encrypted file and extract metadata.
        
        Args:
            file_path: Path to the encrypted file
            
        Returns:
            dict: Contains encrypted_data, salt, nonce, and metadata
        """
        try:
            with open(file_path, 'rb') as f:
                # Read salt (16 bytes)
                salt = f.read(16)
                # Read nonce (12 bytes)
                nonce = f.read(12)
                # Read original size (8 bytes)
                original_size = int.from_bytes(f.read(8), 'big')
                # Read hash length and hash
                hash_length = int.from_bytes(f.read(1), 'big')
                file_hash = f.read(hash_length).decode('utf-8')
                # Read encrypted data
                encrypted_data = f.read()
            
            logger.info(f"Loaded encrypted file: {file_path}")
            
            return {
                'encrypted_data': encrypted_data,
                'salt': salt,
                'nonce': nonce,
                'original_size': original_size,
                'file_hash': file_hash,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Failed to load encrypted file: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
