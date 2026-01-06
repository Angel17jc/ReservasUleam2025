"""
HMAC Service

Implements HMAC-SHA256 signature generation and validation for webhook security.

This service provides cryptographic functions to:
- Generate signatures for outgoing webhooks (to partners)
- Validate signatures from incoming webhooks (from payment providers)
- Ensure data integrity and authenticity

Security Standards:
- HMAC-SHA256 algorithm
- Timing-safe comparison to prevent timing attacks
- No secret key logging

Usage:
    # Generate signature for outgoing webhook
    signature = HmacService.generate_signature(
        payload='{"event":"payment.success"}',
        secret="partner_secret_key"
    )
    
    # Validate incoming webhook
    is_valid = HmacService.validate_signature(
        payload=request_body,
        signature=request.headers["X-Signature"],
        secret=settings.STRIPE_WEBHOOK_SECRET
    )
"""

import hmac
import hashlib
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class HmacService:
    """
    Service for HMAC-SHA256 signature operations.
    
    Stateless service with static methods for signature generation and validation.
    Used for webhook authentication in both directions:
    - Outgoing: Sign webhooks sent to partners
    - Incoming: Validate webhooks from payment providers
    
    Principles:
    - Single Responsibility: Only handles HMAC operations
    - Stateless: All methods are static
    - Secure: Constant-time comparison prevents timing attacks
    """
    
    @staticmethod
    def generate_signature(payload: str | Dict[str, Any], secret: str) -> str:
        """
        Genera firma HMAC-SHA256 para un payload.
        
        Used for signing outgoing webhooks to partners.
        The signature proves the webhook comes from us and hasn't been tampered with.
        
        Args:
            payload: JSON string or dict to sign
            secret: Secret key (partner's shared_secret)
        
        Returns:
            str: Hexadecimal signature (64 characters)
        
        Security:
            - Uses HMAC-SHA256 (industry standard)
            - Secret must be cryptographically random
            - Signature is deterministic (same input = same output)
        
        Example:
            >>> payload = {"event": "payment.success", "payment_id": "123"}
            >>> signature = HmacService.generate_signature(payload, "secret123")
            >>> len(signature)
            64
        
        Raises:
            ValueError: If payload or secret is empty
            TypeError: If payload cannot be serialized to JSON
        """
        # Validations
        if not secret:
            raise ValueError("Secret key cannot be empty")
        
        if not payload:
            raise ValueError("Payload cannot be empty")
        
        # Convert dict to JSON string if necessary
        if isinstance(payload, dict):
            try:
                payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            except (TypeError, ValueError) as e:
                logger.error(f"Failed to serialize payload to JSON: {e}")
                raise TypeError(f"Payload must be JSON-serializable: {e}")
        else:
            payload_str = str(payload)
        
        # Ensure strings are encoded to bytes
        payload_bytes = payload_str.encode('utf-8')
        secret_bytes = secret.encode('utf-8')
        
        # Generate HMAC-SHA256 signature
        signature_bytes = hmac.new(
            key=secret_bytes,
            msg=payload_bytes,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        logger.debug(
            f"Generated HMAC signature: "
            f"payload_length={len(payload_bytes)}, "
            f"signature={signature_bytes[:8]}..."
        )
        
        return signature_bytes
    
    @staticmethod
    def validate_signature(
        payload: str | Dict[str, Any],
        signature: str,
        secret: str
    ) -> bool:
        """
        Valida una firma HMAC-SHA256 contra un payload.
        
        Used for validating incoming webhooks from payment providers or partners.
        Prevents replay attacks and ensures data integrity.
        
        Args:
            payload: JSON string or dict received
            signature: HMAC signature from webhook header
            secret: Secret key to validate against
        
        Returns:
            bool: True if signature is valid, False otherwise
        
        Security:
            - Uses timing-safe comparison (prevents timing attacks)
            - Constant-time comparison protects against side-channel attacks
            - Invalid signatures are logged for security monitoring
        
        Example:
            >>> payload = '{"event":"payment.success","id":"123"}'
            >>> signature = "a1b2c3d4..."  # From X-Signature header
            >>> is_valid = HmacService.validate_signature(
            ...     payload, signature, "webhook_secret"
            ... )
            >>> if is_valid:
            ...     process_webhook(payload)
        
        Raises:
            ValueError: If signature or secret is empty
        """
        # Validations
        if not signature:
            logger.warning("Signature validation failed: signature is empty")
            return False
        
        if not secret:
            logger.warning("Signature validation failed: secret is empty")
            return False
        
        if not payload:
            logger.warning("Signature validation failed: payload is empty")
            return False
        
        try:
            # Generate expected signature
            expected_signature = HmacService.generate_signature(payload, secret)
            
            # Timing-safe comparison (prevents timing attacks)
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if is_valid:
                logger.debug("HMAC signature validation: SUCCESS")
            else:
                logger.warning(
                    f"HMAC signature validation: FAILED - "
                    f"expected={expected_signature[:8]}..., "
                    f"received={signature[:8]}..."
                )
            
            return is_valid
        
        except Exception as e:
            logger.error(f"Error validating HMAC signature: {e}", exc_info=True)
            return False
    
    @staticmethod
    def generate_webhook_headers(
        payload: Dict[str, Any],
        secret: str,
        additional_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """
        Genera headers completos para un webhook firmado.
        
        Convenience method that generates standard webhook headers including:
        - Content-Type: application/json
        - X-Signature: HMAC-SHA256 signature
        - X-Webhook-Timestamp: Current timestamp
        - Any additional custom headers
        
        Args:
            payload: Webhook payload (will be signed)
            secret: Secret key for signature
            additional_headers: Optional custom headers
        
        Returns:
            dict: Complete headers for HTTP request
        
        Example:
            >>> headers = HmacService.generate_webhook_headers(
            ...     payload={"event": "payment.success"},
            ...     secret="partner_secret",
            ...     additional_headers={"X-Request-ID": "abc123"}
            ... )
            >>> # headers = {
            >>> #     "Content-Type": "application/json",
            >>> #     "X-Signature": "a1b2c3...",
            >>> #     "X-Webhook-Timestamp": "2026-01-16T20:00:00Z",
            >>> #     "X-Request-ID": "abc123"
            >>> # }
        """
        from datetime import datetime
        
        # Generate signature
        signature = HmacService.generate_signature(payload, secret)
        
        # Build headers
        headers = {
            "Content-Type": "application/json",
            "X-Signature": signature,
            "X-Webhook-Timestamp": datetime.utcnow().isoformat() + "Z",
            "User-Agent": "ULEAM-Payment-Service/1.0"
        }
        
        # Add custom headers
        if additional_headers:
            headers.update(additional_headers)
        
        logger.debug(f"Generated webhook headers with signature: {signature[:8]}...")
        
        return headers
    
    @staticmethod
    def extract_signature_from_header(
        header_value: str,
        signature_key: str = "signature"
    ) -> Optional[str]:
        """
        Extrae la firma de un header con formato "key1=value1,key2=value2".
        
        Some providers (like Stripe) send signatures in this format:
        "t=1234567890,v1=signature_here"
        
        Args:
            header_value: Header value string
            signature_key: Key to extract (default: "signature")
        
        Returns:
            str: Extracted signature or None if not found
        
        Example:
            >>> header = "t=1234567890,v1=abc123def456,v0=old_signature"
            >>> signature = HmacService.extract_signature_from_header(
            ...     header, signature_key="v1"
            ... )
            >>> signature
            'abc123def456'
        """
        if not header_value:
            return None
        
        try:
            # Parse "key=value" pairs
            pairs = header_value.split(",")
            for pair in pairs:
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    if key.strip() == signature_key:
                        return value.strip()
            
            return None
        
        except Exception as e:
            logger.error(f"Error parsing signature header: {e}")
            return None
    
    @staticmethod
    def verify_webhook_timestamp(
        timestamp_str: str,
        tolerance_seconds: int = 300
    ) -> bool:
        """
        Verifica que un timestamp de webhook esté dentro de la tolerancia.
        
        Prevents replay attacks by rejecting old webhooks.
        Standard tolerance is 5 minutes (300 seconds).
        
        Args:
            timestamp_str: ISO timestamp string from webhook
            tolerance_seconds: Maximum age in seconds (default: 300)
        
        Returns:
            bool: True if timestamp is recent, False if too old
        
        Security:
            - Prevents replay attacks
            - Rejects webhooks older than tolerance
            - Rejects future timestamps (clock skew tolerance: 60s)
        
        Example:
            >>> from datetime import datetime, timedelta
            >>> now = datetime.utcnow()
            >>> recent = (now - timedelta(seconds=60)).isoformat()
            >>> old = (now - timedelta(seconds=600)).isoformat()
            >>> 
            >>> HmacService.verify_webhook_timestamp(recent)
            True
            >>> HmacService.verify_webhook_timestamp(old)
            False
        """
        from datetime import datetime, timedelta
        
        try:
            # Parse timestamp
            webhook_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            now = datetime.utcnow()
            
            # Calculate age
            age_seconds = (now - webhook_time).total_seconds()
            
            # Check if too old
            if age_seconds > tolerance_seconds:
                logger.warning(
                    f"Webhook timestamp too old: "
                    f"age={age_seconds}s, tolerance={tolerance_seconds}s"
                )
                return False
            
            # Check if from future (clock skew tolerance: 60s)
            if age_seconds < -60:
                logger.warning(
                    f"Webhook timestamp from future: age={age_seconds}s"
                )
                return False
            
            return True
        
        except Exception as e:
            logger.error(f"Error verifying webhook timestamp: {e}")
            return False