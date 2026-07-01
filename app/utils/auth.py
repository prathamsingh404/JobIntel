import hashlib
import hmac
import base64
import json
import time
from typing import Dict, Any, Optional
from app.config.settings import settings

SECRET_KEY = settings.pipeline_config.get("security", {}).get("secret_key", "jobintel-v2-super-secret-key-change-me")

class AuthHandler:
    """Handles secure password hashing and HMAC-SHA256 signed JWT tokens in JobIntel V2."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using PBKDF2 with a SHA256 signature."""
        salt = b"jobintel_v2_salt"  # In production, use os.urandom(16) per user
        iterations = 100_000
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return f"pbkdf2_sha256${iterations}${base64.b64encode(salt).decode('utf-8')}${base64.b64encode(key).decode('utf-8')}"

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verifies a plain text password against the hashed string."""
        try:
            parts = hashed.split('$')
            if len(parts) != 4:
                return False
            algo, iterations, salt_b64, key_b64 = parts
            salt = base64.b64decode(salt_b64.encode('utf-8'))
            key = base64.b64decode(key_b64.encode('utf-8'))
            new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, int(iterations))
            return hmac.compare_digest(key, new_key)
        except Exception:
            return False

    @staticmethod
    def create_jwt(payload: Dict[str, Any], expires_in_seconds: int = 3600) -> str:
        """Generates a signed HMAC-SHA256 token payload."""
        header = {"alg": "HS256", "typ": "JWT"}
        
        # Add expiration timestamp
        payload_copy = payload.copy()
        payload_copy["exp"] = int(time.time()) + expires_in_seconds
        
        # Base64 encode header and payload
        header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode('utf-8')).decode('utf-8').rstrip('=')
        payload_b64 = base64.urlsafe_b64encode(json.dumps(payload_copy).encode('utf-8')).decode('utf-8').rstrip('=')
        
        # Create signature
        message = f"{header_b64}.{payload_b64}".encode('utf-8')
        signature = hmac.new(SECRET_KEY.encode('utf-8'), message, hashlib.sha256).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
        
        return f"{header_b64}.{payload_b64}.{signature_b64}"

    @staticmethod
    def verify_jwt(token: str) -> Optional[Dict[str, Any]]:
        """Validates and decodes a signed token. Returns the payload dict if valid."""
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            header_b64, payload_b64, signature_b64 = parts
            
            # Recreate signature to verify match
            message = f"{header_b64}.{payload_b64}".encode('utf-8')
            signature = hmac.new(SECRET_KEY.encode('utf-8'), message, hashlib.sha256).digest()
            expected_sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
            
            if not hmac.compare_digest(signature_b64.encode('utf-8'), expected_sig_b64.encode('utf-8')):
                return None
                
            # Decode payload
            # Add padding back if necessary
            payload_padded = payload_b64 + '=' * (4 - len(payload_b64) % 4)
            payload_data = json.loads(base64.urlsafe_b64decode(payload_padded).decode('utf-8'))
            
            # Check expiration
            if payload_data.get("exp", 0) < int(time.time()):
                return None
                
            return payload_data
        except Exception:
            return None
