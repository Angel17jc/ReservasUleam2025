from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload
from ..database import get_db, get_auth_db
from ..models.usuario import Usuario
from ..models.tipo_usuario import TipoUsuario
from .jwt_handler import decode_access_token
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    auth_db: Session = Depends(get_auth_db),
) -> Usuario:
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        # Log minimal info to help debugging (do not log token value). Use WARNING
        # so the message appears in normal server logs.
        logger.warning(
            "Authentication failed while decoding token (scheme=%s, token_len=%d)",
            credentials.scheme,
            len(token) if token else 0,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    raw_sub = payload.get("sub")
    if raw_sub is None:
        logger.warning("Token payload missing 'sub' claim: %s", payload)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # ensure we have an integer user id for DB lookup
    try:
        user_id = int(raw_sub)
    except Exception:
        logger.warning("Token 'sub' claim is not an integer: %s", raw_sub)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # Validate user exists and is active in auth_service_db (source of truth for auth)
    auth_row = auth_db.execute(
        text(
            "SELECT id, email, nombre, apellido, tipo_usuario_id, estado "
            "FROM usuario WHERE id = :id"
        ),
        {"id": user_id},
    ).fetchone()

    if auth_row is None:
        logger.warning("User not found in auth_service_db (user_id=%s)", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in auth service"
        )

    if str(auth_row.estado).lower() != "activo":
        logger.warning("User is not active in auth_service_db (user_id=%s, estado=%s)", user_id, auth_row.estado)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not active"
        )

    # Validate user is provisioned in reservas DB (FK integrity) without auto-creating
    user = db.query(Usuario).options(joinedload(Usuario.tipo_usuario)).filter(Usuario.id == user_id).first()
    if user is None:
        logger.warning("User referenced in token not provisioned in reservas DB (user_id=%s)", user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not provisioned in reservas"
        )

    # Sync basic fields from auth row (without writes) so downstream logic can rely on them
    user.email = auth_row.email
    user.nombre = auth_row.nombre
    user.apellido = auth_row.apellido
    user.tipo_usuario_id = auth_row.tipo_usuario_id

    # Ensure tipo_usuario relationship is present; if missing, fallback to lookup
    if user.tipo_usuario is None:
        tipo = db.query(TipoUsuario).filter(TipoUsuario.id == auth_row.tipo_usuario_id).first()
        if tipo:
            user.tipo_usuario = tipo
        else:
            logger.warning("tipo_usuario_id missing in reservas DB (id=%s)", auth_row.tipo_usuario_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User role not configured"
            )

    return user

def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.tipo_usuario.nivel_prioridad != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
