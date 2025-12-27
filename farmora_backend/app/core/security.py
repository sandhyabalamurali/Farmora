"""
JWT and password security module for Farmora backend.
Handles authentication, token generation, and password verification.
"""

import logging
import warnings
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
import bcrypt
from farmora_backend.app.config import settings

# Suppress passlib bcrypt version warning
warnings.filterwarnings("ignore", message=".*error reading bcrypt version.*")
logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _truncate_password_to_72(password: str) -> str:
    """Truncate password so its UTF-8 encoded bytes are at most 72 bytes.

    bcrypt has a 72-byte input limit; to avoid errors we truncate the
    password at the byte level and return a UTF-8 string that decodes
    the truncated bytes (ignoring partial codepoints).
    """
    if password is None:
        return ""
    encoded = password.encode("utf-8")
    if len(encoded) <= 72:
        return password
    truncated = encoded[:72]
    # decode ignoring partial characters at the end
    safe = truncated.decode("utf-8", errors="ignore")
    logger.warning("Password exceeded 72 bytes and was truncated for bcrypt hashing")
    return safe


def hash_password(password: str) -> str:
    """Hash a plain text password, truncating to 72 bytes if necessary."""
    try:
        safe_pw = _truncate_password_to_72(password)
        # Debug info: log byte lengths to help diagnose bcrypt length issues
        try:
            orig_len = len(password.encode('utf-8')) if password is not None else 0
        except Exception:
            orig_len = None
        try:
            safe_len = len(safe_pw.encode('utf-8')) if safe_pw is not None else 0
        except Exception:
            safe_len = None
        logger.debug(f"Password length bytes before truncation: {orig_len}, after truncation: {safe_len}")
        try:
            return pwd_context.hash(safe_pw)
        except Exception as e:
            # If bcrypt complains about 72 bytes, attempt a direct bcrypt fallback
            msg = str(e)
            logger.warning(f"Primary hashing failed: {msg}")
            if "72 bytes" in msg or "longer than 72" in msg or isinstance(e, ValueError):
                try:
                    pw_bytes = safe_pw.encode('utf-8')[:72]
                    hashed = bcrypt.hashpw(pw_bytes, bcrypt.gensalt())
                    return hashed.decode('utf-8')
                except Exception as e2:
                    logger.error(f"Fallback bcrypt.hashpw also failed: {e2}")
                    raise
            raise
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against its hash.

    The incoming plain password is truncated the same way as when
    it was hashed to ensure consistent verification.
    """
    try:
        safe_pw = _truncate_password_to_72(plain_password)
        try:
            return pwd_context.verify(safe_pw, hashed_password)
        except Exception as e:
            # Fallback: try direct bcrypt check
            try:
                pw_bytes = safe_pw.encode('utf-8')[:72]
                # hashed_password may be str; ensure bytes
                hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
                return bcrypt.checkpw(pw_bytes, hashed_bytes)
            except Exception as e2:
                logger.error(f"Error in fallback bcrypt.verify: {e2}")
                return False
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Dictionary containing claim data (typically user_id, email)
        expires_delta: Optional expiration time delta (default 24 hours)
    
    Returns:
        Encoded JWT token as string
    """
    try:
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        
        # Use a secret key from config; provide fallback for development
        secret_key = getattr(settings, "SECRET_KEY", "your-secret-key-change-in-production")
        
        encoded_jwt = jwt.encode(
            to_encode,
            secret_key,
            algorithm="HS256"
        )
        
        logger.info(f"Access token created for user: {data.get('user_id')}")
        return encoded_jwt
        
    except Exception as e:
        logger.error(f"Error creating access token: {e}")
        raise


def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token payload as dictionary, or None if invalid
    """
    try:
        secret_key = getattr(settings, "SECRET_KEY", "your-secret-key-change-in-production")
        
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=["HS256"]
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return None


def extract_token_from_header(authorization_header: str) -> Optional[str]:
    """
    Extract JWT token from Authorization header.
    Expected format: "Bearer <token>"
    
    Args:
        authorization_header: Authorization header value
    
    Returns:
        Token string or None if invalid format
    """
    try:
        if not authorization_header:
            return None
        
        parts = authorization_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            logger.warning("Invalid authorization header format")
            return None
        
        return parts[1]
        
    except Exception as e:
        logger.error(f"Error extracting token: {e}")
        return None
