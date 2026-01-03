# Plan de Implementación - Payment Service (Pilar 2)
## 4 Commits Detallados

---

## 📋 COMMIT 1: Setup Inicial y Estructura Base

### Objetivo
Establecer la estructura del proyecto, configurar FastAPI, definir modelos de base de datos y preparar el entorno de desarrollo.

### Archivos a Crear

```
payment-service/
├── .env.example
├── .gitignore
├── requirements.txt
├── alembic.ini
├── README.md
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   └── models/
│       ├── __init__.py
│       ├── payment.py
│       ├── partner.py
│       ├── payment_provider.py
│       └── webhook_event.py
└── alembic/
    ├── env.py
    ├── script.py.mako
    └── versions/
        └── 001_initial_schema.py
```

### Contenido Detallado

#### `requirements.txt`
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.9.2
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
httpx==0.25.1
python-dotenv==1.0.0
alembic==1.13.1
pytest==7.4.2
pytest-asyncio==0.23.8
email-validator==2.1.0
stripe==7.0.0
```

#### `.env.example`
```env
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/payment_service_db

# JWT (compartido con auth-service)
SECRET_KEY=mi-secreto-auth-service-super-seguro-2025
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15

# Payment Providers
STRIPE_API_KEY=sk_test_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
MERCADOPAGO_ACCESS_TOKEN=TEST-your-mp-token
MOCK_PROVIDER_ENABLED=true

# Integrations
REST_SERVICE_URL=http://localhost:8000
WEBSOCKET_SERVICE_URL=http://localhost:3001

# Server
PORT=8001
API_PREFIX=api/v1
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# Logging
LOG_LEVEL=INFO
```

#### `app/config.py`
```python
import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/payment_service_db")
    
    # JWT
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    
    # Payment Providers
    STRIPE_API_KEY: str = os.getenv("STRIPE_API_KEY", "")
    STRIPE_WEBHOOK_SECRET: str = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    MERCADOPAGO_ACCESS_TOKEN: str = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
    MOCK_PROVIDER_ENABLED: bool = os.getenv("MOCK_PROVIDER_ENABLED", "true").lower() == "true"
    
    # Integrations
    REST_SERVICE_URL: str = os.getenv("REST_SERVICE_URL", "http://localhost:8000")
    WEBSOCKET_SERVICE_URL: str = os.getenv("WEBSOCKET_SERVICE_URL", "http://localhost:3001")
    
    # Server
    PORT: int = int(os.getenv("PORT", "8001"))
    API_PREFIX: str = os.getenv("API_PREFIX", "api/v1")
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

#### `app/database.py`
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.LOG_LEVEL == "DEBUG"
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Dependency para obtener sesión de BD"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### `app/models/payment.py`
```python
from sqlalchemy import Column, Integer, String, Numeric, TIMESTAMP, func, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from ..database import Base
import enum

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"
    cancelled = "cancelled"

class Payment(Base):
    __tablename__ = "payment"
    
    id = Column(Integer, primary_key=True, index=True)
    external_payment_id = Column(String(255), unique=True, nullable=False, index=True, comment="ID del provider externo")
    reserva_id = Column(Integer, nullable=False, index=True, comment="FK a rest-service.reserva")
    usuario_id = Column(Integer, nullable=False, index=True, comment="FK a rest-service.usuario")
    provider_name = Column(String(50), nullable=False, comment="stripe, mercadopago, mock")
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(SQLEnum(PaymentStatus), nullable=False, default=PaymentStatus.pending, index=True)
    metadata_json = Column(JSONB, default={}, comment="Datos adicionales del pago")
    error_message = Column(Text, nullable=True)
    creado_en = Column(TIMESTAMP, server_default=func.current_timestamp())
    actualizado_en = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
```

#### `app/models/partner.py`
```python
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func, Text
from sqlalchemy.dialects.postgresql import JSONB
from ..database import Base

class Partner(Base):
    __tablename__ = "partner"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), nullable=False, unique=True)
    webhook_url = Column(String(500), nullable=False)
    shared_secret = Column(String(128), nullable=False, comment="Secret para HMAC")
    eventos_suscritos = Column(JSONB, default=[], comment="Array de eventos: booking.confirmed, payment.success")
    is_active = Column(Boolean, default=True, index=True)
    descripcion = Column(Text, nullable=True)
    creado_en = Column(TIMESTAMP, server_default=func.current_timestamp())
    actualizado_en = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())


class PartnerWebhookLog(Base):
    __tablename__ = "partner_webhook_log"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, nullable=False, index=True, comment="FK a partner.id")
    event_type = Column(String(100), nullable=False, index=True)
    payload_json = Column(JSONB, nullable=False)
    response_status = Column(Integer, nullable=True, comment="HTTP status code de la respuesta")
    response_body = Column(Text, nullable=True)
    signature_valid = Column(Boolean, nullable=True)
    error_message = Column(Text, nullable=True)
    direction = Column(String(10), nullable=False, default="outgoing", comment="outgoing o incoming")
    creado_en = Column(TIMESTAMP, server_default=func.current_timestamp())
```

#### `app/models/payment_provider.py`
```python
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import JSONB
from ..database import Base

class PaymentProviderConfig(Base):
    __tablename__ = "payment_provider_config"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, comment="stripe, mercadopago, mock")
    is_active = Column(Boolean, default=True)
    config_json = Column(JSONB, default={}, comment="API keys y configuración específica")
    creado_en = Column(TIMESTAMP, server_default=func.current_timestamp())
    actualizado_en = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
```

#### `app/models/webhook_event.py`
```python
from sqlalchemy import Column, Integer, String, Boolean, TIMESTAMP, func, Text
from sqlalchemy.dialects.postgresql import JSONB
from ..database import Base

class WebhookEvent(Base):
    __tablename__ = "webhook_event"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    source = Column(String(50), nullable=False, comment="stripe, mercadopago, mock, partner")
    payload_json = Column(JSONB, nullable=False)
    processed = Column(Boolean, default=False, index=True)
    error_message = Column(Text, nullable=True)
    creado_en = Column(TIMESTAMP, server_default=func.current_timestamp())
    actualizado_en = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
```

#### `app/models/__init__.py`
```python
from .payment import Payment, PaymentStatus
from .partner import Partner, PartnerWebhookLog
from .payment_provider import PaymentProviderConfig
from .webhook_event import WebhookEvent

__all__ = [
    "Payment",
    "PaymentStatus",
    "Partner",
    "PartnerWebhookLog",
    "PaymentProviderConfig",
    "WebhookEvent"
]
```

#### `app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from .config import settings

# Configurar logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="ULEAM Payment Service",
    description="Servicio de pagos con abstracción de pasarelas y webhooks B2B - Pilar 2",
    version="1.0.0",
    docs_url=f"/{settings.API_PREFIX}/docs",
    redoc_url=f"/{settings.API_PREFIX}/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "service": "ULEAM Payment Service",
        "version": "1.0.0",
        "pilar": 2,
        "status": "online"
    }

@app.get(f"/{settings.API_PREFIX}/health")
def health_check():
    return {
        "status": "healthy",
        "database": "connected"  # TODO: verificar conexión real
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
```

#### `alembic.ini`
```ini
[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url = postgresql://postgres:postgres@localhost:5432/payment_service_db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

#### `alembic/versions/001_initial_schema.py`
```python
"""Initial schema for payment service

Revision ID: 001
Revises: 
Create Date: 2025-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # payment_provider_config
    op.create_table(
        'payment_provider_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('config_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_payment_provider_config_id'), 'payment_provider_config', ['id'], unique=False)

    # payment
    op.create_table(
        'payment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_payment_id', sa.String(length=255), nullable=False),
        sa.Column('reserva_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('provider_name', sa.String(length=50), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('status', sa.Enum('pending', 'completed', 'failed', 'refunded', 'cancelled', name='paymentstatus'), nullable=False),
        sa.Column('metadata_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_payment_id')
    )
    op.create_index(op.f('ix_payment_external_payment_id'), 'payment', ['external_payment_id'], unique=True)
    op.create_index(op.f('ix_payment_id'), 'payment', ['id'], unique=False)
    op.create_index(op.f('ix_payment_reserva_id'), 'payment', ['reserva_id'], unique=False)
    op.create_index(op.f('ix_payment_usuario_id'), 'payment', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_payment_status'), 'payment', ['status'], unique=False)

    # partner
    op.create_table(
        'partner',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=200), nullable=False),
        sa.Column('webhook_url', sa.String(length=500), nullable=False),
        sa.Column('shared_secret', sa.String(length=128), nullable=False),
        sa.Column('eventos_suscritos', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre')
    )
    op.create_index(op.f('ix_partner_id'), 'partner', ['id'], unique=False)
    op.create_index(op.f('ix_partner_is_active'), 'partner', ['is_active'], unique=False)

    # partner_webhook_log
    op.create_table(
        'partner_webhook_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('partner_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('response_status', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('signature_valid', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('direction', sa.String(length=10), nullable=False),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_partner_webhook_log_id'), 'partner_webhook_log', ['id'], unique=False)
    op.create_index(op.f('ix_partner_webhook_log_partner_id'), 'partner_webhook_log', ['partner_id'], unique=False)
    op.create_index(op.f('ix_partner_webhook_log_event_type'), 'partner_webhook_log', ['event_type'], unique=False)

    # webhook_event
    op.create_table(
        'webhook_event',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('payload_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('processed', sa.Boolean(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('creado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('actualizado_en', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_event_id'), 'webhook_event', ['id'], unique=False)
    op.create_index(op.f('ix_webhook_event_event_type'), 'webhook_event', ['event_type'], unique=False)
    op.create_index(op.f('ix_webhook_event_processed'), 'webhook_event', ['processed'], unique=False)

def downgrade():
    op.drop_table('webhook_event')
    op.drop_table('partner_webhook_log')
    op.drop_table('partner')
    op.drop_table('payment')
    op.drop_table('payment_provider_config')
```

#### `README.md` (básico)
```markdown
# Payment Service - Pilar 2

Microservicio de pagos con abstracción de pasarelas y webhooks B2B para el sistema de reservas ULEAM.

## Características

- ✅ Abstracción de payment providers (Adapter Pattern)
- ✅ Mock Adapter para desarrollo
- ✅ Stripe Adapter (opcional)
- ✅ Sistema de webhooks bidireccionales
- ✅ Autenticación HMAC-SHA256
- ✅ Registro de partners externos

## Instalación

```bash
cd payment-service
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración

```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

## Migraciones

```bash
# Crear base de datos
createdb payment_service_db

# Ejecutar migraciones
alembic upgrade head
```

## Ejecutar

```bash
uvicorn app.main:app --reload --port 8001
```

Documentación: http://localhost:8001/api/v1/docs

## Estado

**Commit 1:** Setup inicial completado ✅
```

#### `.gitignore`
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
.env
*.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# Database
*.db
*.sqlite

# Logs
*.log

# Alembic
alembic/versions/*.pyc
```

### Tareas del Commit 1

1. Crear estructura de directorios
2. Configurar FastAPI con CORS
3. Definir modelos SQLAlchemy (4 tablas)
4. Configurar Alembic
5. Crear migración inicial
6. Configurar variables de entorno
7. Endpoint básico de health check
8. README inicial

### Verificación

```bash
# Instalar dependencias
pip install -r requirements.txt

# Crear BD
createdb payment_service_db

# Aplicar migraciones
alembic upgrade head

# Verificar tablas
psql payment_service_db -c "\dt"

# Ejecutar servidor
uvicorn app.main:app --reload --port 8001

# Probar health check
curl http://localhost:8001/api/v1/health
```

### Mensaje del Commit 1

```
feat(payment-service): Setup inicial - estructura base y modelos de BD

- Configuración de FastAPI con CORS y logging
- Modelos SQLAlchemy: Payment, Partner, PartnerWebhookLog, PaymentProviderConfig, WebhookEvent
- Migraciones de Alembic configuradas
- Variables de entorno estructuradas
- Health check endpoint
- Requirements.txt con todas las dependencias
- README básico

Pilar 2 - Commit 1/4
```

---

## 📋 COMMIT 2: Payment Provider Layer (Adapter Pattern)

### Objetivo
Implementar el patrón Adapter para payment providers, crear MockAdapter completo, StripeAdapter básico, schemas Pydantic y servicio de pagos.

### Archivos a Crear

```
payment-service/app/
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   ├── mock_adapter.py
│   ├── stripe_adapter.py
│   └── adapter_factory.py
├── schemas/
│   ├── __init__.py
│   ├── payment.py
│   └── webhook.py
└── services/
    ├── __init__.py
    └── payment_service.py
```

### Contenido Detallado

#### `app/adapters/base.py`
```python
from abc import ABC, abstractmethod
from typing import Dict, Any
from ..schemas.webhook import NormalizedWebhookEvent

class PaymentProvider(ABC):
    """
    Abstract Base Class que define el contrato para todos los payment providers.
    Implementa el Adapter Pattern para abstraer diferentes pasarelas de pago.
    
    Principios aplicados:
    - Open/Closed Principle: Abierto para extensión (nuevos adapters), cerrado para modificación
    - Dependency Inversion: Dependencia de abstracción, no de implementaciones concretas
    - Interface Segregation: Interface mínima pero suficiente
    """
    
    @abstractmethod
    def create_payment(
        self, 
        amount: float, 
        currency: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea un pago en el provider externo.
        
        Args:
            amount: Monto del pago
            currency: Moneda (USD, EUR, MXN, etc.)
            metadata: Datos adicionales (reserva_id, usuario_id, etc.)
        
        Returns:
            Dict con: payment_id, status, amount, currency, metadata
        
        Raises:
            Exception: Si falla la creación del pago
        """
        pass
    
    @abstractmethod
    def get_payment_status(self, payment_id: str) -> str:
        """
        Consulta el estado actual de un pago.
        
        Args:
            payment_id: ID del pago en el provider
        
        Returns:
            str: Estado del pago (pending, completed, failed, etc.)
        """
        pass
    
    @abstractmethod
    def normalize_webhook(self, raw_data: Dict[str, Any]) -> NormalizedWebhookEvent:
        """
        Normaliza el webhook del provider a un formato común.
        
        Esta es la clave del patrón Adapter: cada provider tiene su propio
        formato de webhook, pero todos deben convertirse a NormalizedWebhookEvent.
        
        Args:
            raw_data: Payload raw del webhook del provider
        
        Returns:
            NormalizedWebhookEvent: Evento normalizado
        """
        pass
    
    @abstractmethod
    def validate_webhook_signature(
        self, 
        payload: bytes, 
        signature: str
    ) -> bool:
        """
        Valida la firma del webhook del provider.
        
        Args:
            payload: Payload en bytes del webhook
            signature: Firma recibida en el header
        
        Returns:
            bool: True si la firma es válida
        """
        pass
```

#### `app/schemas/webhook.py`
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class NormalizedWebhookEvent(BaseModel):
    """
    Evento de webhook normalizado.
    Todos los adapters deben convertir sus webhooks a este formato.
    """
    event_type: str = Field(..., description="payment.success, payment.failed, etc.")
    payment_id: str = Field(..., description="ID del pago en el provider")
    status: str = Field(..., description="pending, completed, failed, refunded")
    amount: float = Field(..., description="Monto del pago")
    currency: str = Field(..., description="Moneda (USD, EUR, etc.)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Datos adicionales")
    error_message: Optional[str] = Field(None, description="Mensaje de error si aplica")
    timestamp: Optional[datetime] = Field(None, description="Timestamp del evento")
    
    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "payment.success",
                "payment_id": "pay_abc123",
                "status": "completed",
                "amount": 50.00,
                "currency": "USD",
                "metadata": {
                    "reserva_id": 123,
                    "usuario_id": 5
                },
                "timestamp": "2025-01-15T10:00:00Z"
            }
        }
```

#### `app/schemas/payment.py`
```python
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from decimal import Decimal

class PaymentCreate(BaseModel):
    """Schema para crear un nuevo pago"""
    reserva_id: int = Field(..., description="ID de la reserva")
    amount: Decimal = Field(..., gt=0, description="Monto mayor a 0")
    currency: str = Field(default="USD", max_length=3, description="Código de moneda ISO")
    provider: str = Field(..., description="mock, stripe, mercadopago")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        allowed = ["USD", "EUR", "MXN", "COP", "PEN"]
        if v.upper() not in allowed:
            raise ValueError(f"Currency must be one of {allowed}")
        return v.upper()
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v):
        allowed = ["mock", "stripe", "mercadopago"]
        if v.lower() not in allowed:
            raise ValueError(f"Provider must be one of {allowed}")
        return v.lower()

class PaymentResponse(BaseModel):
    """Schema de respuesta de pago"""
    id: int
    external_payment_id: str
    reserva_id: int
    usuario_id: int
    provider_name: str
    amount: Decimal
    currency: str
    status: str
    metadata_json: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "external_payment_id": "mock_abc123",
                "reserva_id": 123,
                "usuario_id": 5,
                "provider_name": "mock",
                "amount": 50.00,
                "currency": "USD",
                "status": "pending",
                "metadata_json": {},
                "created_at": "2025-01-15T10:00:00Z"
            }
        }

class PaymentStatusUpdate(BaseModel):
    """Schema para actualizar estado de pago"""
    status: str = Field(..., description="pending, completed, failed, refunded")
    error_message: Optional[str] = None
```

#### `app/adapters/mock_adapter.py`
```python
import uuid
from typing import Dict, Any
from datetime import datetime
from .base import PaymentProvider
from ..schemas.webhook import NormalizedWebhookEvent

class MockAdapter(PaymentProvider):
    """
    Adapter de prueba que simula un payment provider sin APIs externas.
    Útil para desarrollo y testing.
    """
    
    def __init__(self):
        self.payments: Dict[str, Dict[str, Any]] = {}  # In-memory storage
    
    def create_payment(
        self, 
        amount: float, 
        currency: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Simula la creación de un pago.
        Auto-completa el pago instantáneamente (para facilitar testing).
        """
        payment_id = f"mock_{uuid.uuid4().hex[:12]}"
        
        payment_data = {
            "payment_id": payment_id,
            "status": "completed",  # Mock auto-completa
            "amount": amount,
            "currency": currency,
            "metadata": metadata,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Almacenar en memoria
        self.payments[payment_id] = payment_data
        
        return payment_data
    
    def get_payment_status(self, payment_id: str) -> str:
        """Obtiene el estado de un pago simulado"""
        if payment_id not in self.payments:
            raise ValueError(f"Payment {payment_id} not found")
        
        return self.payments[payment_id]["status"]
    
    def normalize_webhook(self, raw_data: Dict[str, Any]) -> NormalizedWebhookEvent:
        """
        Mock adapter ya recibe datos en formato normalizado.
        """
        return NormalizedWebhookEvent(
            event_type=raw_data.get("event_type", "payment.success"),
            payment_id=raw_data["payment_id"],
            status=raw_data.get("status", "completed"),
            amount=raw_data["amount"],
            currency=raw_data["currency"],
            metadata=raw_data.get("metadata", {}),
            error_message=raw_data.get("error_message"),
            timestamp=datetime.utcnow()
        )
    
    def validate_webhook_signature(
        self, 
        payload: bytes, 
        signature: str
    ) -> bool:
        """
        Mock adapter acepta cualquier firma (para testing).
        En producción nunca usar mock.
        """
        return True
```

#### `app/adapters/stripe_adapter.py`
```python
import stripe
from typing import Dict, Any
from datetime import datetime
from .base import PaymentProvider
from ..schemas.webhook import NormalizedWebhookEvent
from ..config import settings

class StripeAdapter(PaymentProvider):
    """
    Adapter para Stripe payment provider.
    Implementa la integración real con la API de Stripe.
    """
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_API_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    def create_payment(
        self, 
        amount: float, 
        currency: str, 
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea un PaymentIntent en Stripe.
        """
        try:
            # Stripe maneja montos en centavos
            amount_cents = int(amount * 100)
            
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata=metadata,
                automatic_payment_methods={"enabled": True}
            )
            
            return {
                "payment_id": payment_intent.id,
                "status": "pending",  # Stripe inicia como requires_payment_method
                "amount": amount,
                "currency": currency,
                "metadata": metadata,
                "client_secret": payment_intent.client_secret
            }
        
        except stripe.error.StripeError as e:
            raise Exception(f"Stripe error: {str(e)}")
    
    def get_payment_status(self, payment_id: str) -> str:
        """Consulta el estado de un PaymentIntent"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_id)
            
            # Mapear estados de Stripe a nuestros estados
            status_map = {
                "succeeded": "completed",
                "processing": "pending",
                "requires_payment_method": "pending",
                "requires_confirmation": "pending",
                "requires_action": "pending",
                "canceled": "cancelled",
                "requires_capture": "pending"
            }
            
            return status_map.get(payment_intent.status, "pending")
        
        except stripe.error.StripeError as e:
            raise Exception(f"Error retrieving payment: {str(e)}")
    
    def normalize_webhook(self, raw_data: Dict[str, Any]) -> NormalizedWebhookEvent:
        """
        Normaliza webhooks de Stripe al formato común.
        """
        event_type_map = {
            "payment_intent.succeeded": "payment.success",
            "payment_intent.payment_failed": "payment.failed",
            "payment_intent.canceled": "payment.cancelled",
            "charge.refunded": "payment.refunded"
        }
        
        stripe_event_type = raw_data.get("type", "")
        normalized_type = event_type_map.get(stripe_event_type, "payment.unknown")
        
        payment_intent = raw_data.get("data", {}).get("object", {})
        
        return NormalizedWebhookEvent(
            event_type=normalized_type,
            payment_id=payment_intent.get("id", ""),
            status=self._map_stripe_status(payment_intent.get("status", "")),
            amount=payment_intent.get("amount", 0) / 100,  # Convertir centavos a unidades
            currency=payment_intent.get("currency", "usd").upper(),
            metadata=payment_intent.get("metadata", {}),
            error_message=payment_intent.get("last_payment_error", {}).get("message"),
            timestamp=datetime.utcnow()
        )
    
    def validate_webhook_signature(
        self, 
        payload: bytes, 
        signature: str
    ) -> bool:
        """
        Valida la firma del webhook de Stripe.
        """
        try:
            stripe.Webhook.construct_event(
                payload, 
                signature, 
                self.webhook_secret
            )
            return True
        except stripe.error.SignatureVerificationError:
            return False
        except Exception:
            return False
    
    def _map_stripe_status(self, stripe_status: str) -> str:
        """Mapea estados de Stripe a nuestros estados internos"""
        status_map = {
            "succeeded": "completed",
            "processing": "pending",
            "canceled": "cancelled",
            "requires_payment_method": "pending",
        }
        return status_map.get(stripe_status, "pending")
```

#### `app/adapters/adapter_factory.py`
```python
from .base import PaymentProvider
from .mock_adapter import MockAdapter
from .stripe_adapter import StripeAdapter
from ..config import settings

class AdapterFactory:
    """
    Factory para crear instancias de payment adapters.
    Implementa el patrón Factory Method.
    """
    
    _adapters: dict[str, PaymentProvider] = {}
    
    @classmethod
    def get_adapter(cls, provider_name: str) -> PaymentProvider:
        """
        Obtiene o crea una instancia del adapter solicitado.
        
        Args:
            provider_name: "mock", "stripe", "mercadopago"
        
        Returns:
            PaymentProvider: Instancia del adapter
        
        Raises:
            ValueError: Si el provider no es soportado
        """
        provider_name = provider_name.lower()
        
        # Singleton pattern: reutilizar instancias
        if provider_name in cls._adapters:
            return cls._adapters[provider_name]
        
        # Crear nueva instancia según el provider
        if provider_name == "mock":
            if not settings.MOCK_PROVIDER_ENABLED:
                raise ValueError("Mock provider is disabled in production")
            adapter = MockAdapter()
        
        elif provider_name == "stripe":
            if not settings.STRIPE_API_KEY:
                raise ValueError("Stripe API key not configured")
            adapter = StripeAdapter()
        
        elif provider_name == "mercadopago":
            # TODO: Implementar MercadoPagoAdapter
            raise NotImplementedError("MercadoPago adapter not implemented yet")
        
        else:
            raise ValueError(f"Unsupported payment provider: {provider_name}")
        
        # Almacenar en cache
        cls._adapters[provider_name] = adapter
        return adapter
```

#### `app/adapters/__init__.py`
```python
from .base import PaymentProvider
from .mock_adapter import MockAdapter
from .stripe_adapter import StripeAdapter
from .adapter_factory import AdapterFactory

__all__ = [
    "PaymentProvider",
    "MockAdapter",
    "StripeAdapter",
    "AdapterFactory"
]
```

#### `app/services/payment_service.py`
```python
import logging
from sqlalchemy.orm import Session
from typing import Optional
from ..models.payment import Payment, PaymentStatus
from ..schemas.payment import PaymentCreate
from ..adapters.adapter_factory import AdapterFactory

logger = logging.getLogger(__name__)

class PaymentService:
    """
    Servicio que orquesta la lógica de negocio de pagos.
    Utiliza los adapters para comunicarse con payment providers.
    """
    
    @staticmethod
    def create_payment(
        db: Session,
        usuario_id: int,
        payment_data: PaymentCreate
    ) -> Payment:
        """
        Crea un nuevo pago utilizando el provider especificado.
        
        Args:
            db: Sesión de BD
            usuario_id: ID del usuario que crea el pago
            payment_data: Datos del pago
        
        Returns:
            Payment: Registro del pago creado
        
        Raises:
            Exception: Si falla la creación en el provider
        """
        try:
            # 1. Obtener adapter del provider
            adapter = AdapterFactory.get_adapter(payment_data.provider)
            
            # 2. Crear pago en el provider externo
            metadata = payment_data.metadata or {}
            metadata.update({
                "reserva_id": payment_data.reserva_id,
                "usuario_id": usuario_id
            })
            
            provider_response = adapter.create_payment(
                amount=float(payment_data.amount),
                currency=payment_data.currency,
                metadata=metadata
            )
            
            # 3. Almacenar en BD local
            payment = Payment(
                external_payment_id=provider_response["payment_id"],
                reserva_id=payment_data.reserva_id,
                usuario_id=usuario_id,
                provider_name=payment_data.provider,
                amount=payment_data.amount,
                currency=payment_data.currency,
                status=PaymentStatus.pending,
                metadata_json=metadata
            )
            
            db.add(payment)
            db.commit()
            db.refresh(payment)
            
            logger.info(f"Payment created: {payment.id} ({payment.external_payment_id})")
            
            return payment
        
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating payment: {str(e)}")
            raise
    
    @staticmethod
    def get_payment(
        db: Session,
        payment_id: int,
        usuario_id: Optional[int] = None
    ) -> Optional[Payment]:
        """
        Obtiene un pago por ID.
        
        Args:
            db: Sesión de BD
            payment_id: ID del pago
            usuario_id: Si se proporciona, valida que el pago pertenezca al usuario
        
        Returns:
            Payment o None
        """
        query = db.query(Payment).filter(Payment.id == payment_id)
        
        if usuario_id:
            query = query.filter(Payment.usuario_id == usuario_id)
        
        return query.first()
    
    @staticmethod
    def update_payment_status(
        db: Session,
        external_payment_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[Payment]:
        """
        Actualiza el estado de un pago.
        
        Args:
            db: Sesión de BD
            external_payment_id: ID del pago en el provider
            status: Nuevo estado
            error_message: Mensaje de error si aplica
        
        Returns:
            Payment actualizado o None
        """
        payment = db.query(Payment).filter(
            Payment.external_payment_id == external_payment_id
        ).first()
        
        if not payment:
            logger.warning(f"Payment not found: {external_payment_id}")
            return None
        
        payment.status = PaymentStatus(status)
        if error_message:
            payment.error_message = error_message
        
        db.commit()
        db.refresh(payment)
        
        logger.info(f"Payment {payment.id} updated to status: {status}")
        
        return payment
```

### Tareas del Commit 2

1. Crear interface `PaymentProvider` (ABC)
2. Implementar `MockAdapter` completo
3. Implementar `StripeAdapter` básico
4. Crear schemas Pydantic (payment, webhook)
5. Implementar `AdapterFactory` (Factory Pattern)
6. Crear `PaymentService` con lógica de negocio
7. Actualizar `__init__.py` en cada módulo

### Verificación

```python
# Probar adapter factory
from app.adapters.adapter_factory import AdapterFactory

adapter = AdapterFactory.get_adapter("mock")
payment = adapter.create_payment(50.0, "USD", {"reserva_id": 123})
print(payment)
```

### Mensaje del Commit 2

```
feat(payment-service): Implementación de Payment Provider Layer con Adapter Pattern

- Interface abstracta PaymentProvider (patrón Adapter)
- MockAdapter completo para desarrollo/testing
- StripeAdapter con integración real de Stripe API
- AdapterFactory para instanciar providers (patrón Factory)
- Schemas Pydantic: PaymentCreate, PaymentResponse, NormalizedWebhookEvent
- PaymentService con lógica de negocio de pagos
- Normalización de webhooks de diferentes providers

Pilar 2 - Commit 2/4
```

---

*(Continuará en siguiente mensaje con Commits 3 y 4)*
