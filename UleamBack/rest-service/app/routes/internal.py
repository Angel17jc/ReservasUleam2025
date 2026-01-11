from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from ..database import get_db
from ..models.usuario import Usuario
from ..models.tipo_usuario import TipoUsuario
from ..models.reserva import Reserva
from ..models.estado_reserva import EstadoReserva
from ..config import settings

router = APIRouter(prefix="/api/internal", tags=["internal"])


class ProvisionUserRequest(BaseModel):
    id: int
    email: EmailStr
    nombre: str
    apellido: str
    tipo_usuario_id: int
    estado: str = "activo"


class ReservaEstadoInternalRequest(BaseModel):
    estado_nombre: str
    payment_code: str | None = None


@router.post("/provision-user", status_code=201)
def provision_user(
    payload: ProvisionUserRequest,
    db: Session = Depends(get_db),
    # Accepts standard header `X-Internal-Token`
    x_internal_token: str | None = Header(None),
):
    if not x_internal_token or x_internal_token != settings.INTERNAL_PROVISION_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    tipo = db.query(TipoUsuario).filter(TipoUsuario.id == payload.tipo_usuario_id).first()
    if not tipo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="tipo_usuario_id not found")

    user = db.query(Usuario).filter(Usuario.id == payload.id).first()
    if user:
        user.email = payload.email
        user.nombre = payload.nombre
        user.apellido = payload.apellido
        user.tipo_usuario_id = payload.tipo_usuario_id
        user.estado = payload.estado
    else:
        user = Usuario(
            id=payload.id,
            email=payload.email,
            password_hash="!",  # marcador, no se usa en este servicio
            nombre=payload.nombre,
            apellido=payload.apellido,
            tipo_usuario_id=payload.tipo_usuario_id,
            estado=payload.estado,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    return {"status": "ok", "id": user.id}


@router.post("/reservas/{reserva_id}/estado", status_code=200)
def update_reserva_estado_internal(
    reserva_id: int,
    payload: ReservaEstadoInternalRequest,
    db: Session = Depends(get_db),
    x_internal_token: str | None = Header(None),
):
    if not x_internal_token or x_internal_token != settings.INTERNAL_PROVISION_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    estado = (
        db.query(EstadoReserva)
        .filter(EstadoReserva.nombre == payload.estado_nombre)
        .first()
    )
    if not estado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Estado not found")

    reserva = db.query(Reserva).filter(Reserva.id == reserva_id).first()
    if not reserva:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reserva not found")

    reserva.estado_id = estado.id
    db.add(reserva)
    db.commit()
    db.refresh(reserva)

    return {
        "status": "ok",
        "reserva_id": reserva.id,
        "estado": estado.nombre,
        "payment_code": payload.payment_code,
    }
