# Import all models to ensure relationships are properly resolved
# Order matters: import base models first, then dependent models

# Base models (no foreign keys)
from .tipo_usuario import TipoUsuario
from .categoria_espacio import CategoriaEspacio
from .tipo_evento import TipoEvento
from .estado_reserva import EstadoReserva
from .caracteristica_espacio import CaracteristicaEspacio

# Models with foreign keys
from .usuario import Usuario
from .espacio import Espacio
from .reserva import Reserva
from .notificacion import Notificacion

__all__ = [
    "TipoUsuario",
    "Usuario",
    "CategoriaEspacio",
    "Espacio",
    "CaracteristicaEspacio",
    "TipoEvento",
    "EstadoReserva",
    "Reserva",
    "Notificacion",
]
