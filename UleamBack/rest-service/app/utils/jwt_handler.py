from datetime import datetime, timedelta
from typing import Optional
import logging
import jwt  # PyJWT library
from ..config import settings

# Log via the uvicorn.error logger so messages appear in the uvicorn stdout/stderr
logger = logging.getLogger("uvicorn.error")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token with an expiration.
    
    Compatible with auth-service (NestJS) token format.
    """
    to_encode = data.copy()
    # Ensure 'sub' is a string for compatibility
    if "sub" in to_encode and to_encode["sub"] is not None:
        to_encode["sub"] = str(to_encode["sub"])
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error encoding JWT: {e}")
        raise


def decode_access_token(token: str):
    """Decode a JWT token and return the payload or None on failure.
    
    Compatible with tokens from auth-service (NestJS) which may have numeric 'sub'.
    Uses PyJWT which is more permissive than python-jose.
    """
    try:
        # Decode with PyJWT (handles both string and numeric 'sub')
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Normalize 'sub' to string for consistency
        if "sub" in payload and not isinstance(payload["sub"], str):
            payload["sub"] = str(payload["sub"])
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected JWT decode error: {e}")
        return None

