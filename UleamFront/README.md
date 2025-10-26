# Sistema de Reserva de Espacios ULEAM

Sistema web completo de reserva de espacios para la Universidad Laica Eloy Alfaro de Manabí (ULEAM), desarrollado con React + Vite + Tailwind CSS con sistema de roles diferenciados.

## 🚀 Características Principales

### Sistema de Roles

#### Usuario Normal (Estudiante/Profesor)
- Ver espacios disponibles
- Crear reservas (requiere aprobación según tipo)
- Ver/editar/cancelar sus propias reservas
- Recibir notificaciones
- Gestionar su perfil

#### Administrador
- **Todo lo del usuario normal +**
- Aprobar/rechazar reservas pendientes
- CRUD completo de espacios
- CRUD de categorías y tipos de evento
- Gestionar usuarios (activar/desactivar/cambiar roles)
- Bloquear espacios temporalmente
- Ver reportes y estadísticas
- Configurar disponibilidad de espacios
- Panel de administración completo

### Estados de Reserva
- **Pendiente** (amarillo) - Esperando aprobación admin
- **Aprobada** (verde) - Confirmada por admin
- **Rechazada** (rojo) - Negada por admin
- **Completada** (azul) - Evento ya pasó
- **Cancelada** (gris) - Cancelada por usuario o admin
- **En Curso** (verde brillante) - Evento ocurriendo ahora

## 🎨 Colores Institucionales ULEAM

```javascript
Rojo ULEAM: #E63946 (botones, enlaces, acentos)
Rojo Oscuro: #C1121F (estados hover, modo oscuro)
Rojo Claro: #FFE5E8 (fondos, badges, alertas)
Gris: #8D99AE (texto secundario, bordes)
Gris Oscuro: #2B2D42 (texto, fondos oscuros)
Gris Claro: #EDF2F4 (fondos, tarjetas)
```

## 📋 Requisitos Previos

- Node.js 20 o superior
- npm o yarn

## 🔧 Instalación

1. **Clonar el repositorio** (si aplica)
```bash
git clone <url-del-repositorio>
cd uleam-reservas
```

2. **Instalar dependencias**
```bash
npm install
```

## ▶️ Ejecución

### Modo Desarrollo

```bash
npm run dev
```

La aplicación estará disponible en `http://localhost:5000`

### Modo Producción

```bash
# Construir la aplicación
npm run build

# Ejecutar en producción
npm start
```

## 👤 Usuarios de Prueba

El sistema incluye datos mock para pruebas:

### Administrador
- **Nombre:** Juan Pérez
- **Email:** juan.perez@uleam.edu.ec
- **Rol:** Admin

Para cambiar entre roles, usa el menú de usuario en la esquina superior derecha.

## 🗂️ Estructura del Proyecto

```
uleam-reservas/
├── client/                 # Frontend React
│   ├── src/
│   │   ├── components/    # Componentes reutilizables
│   │   │   ├── ui/       # Componentes base (shadcn)
│   │   │   ├── AdminBadge.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   ├── Navbar.tsx
│   │   │   ├── ReservationCard.tsx
│   │   │   ├── SpaceCard.tsx
│   │   │   ├── StatusBadge.tsx
│   │   │   └── app-sidebar.tsx
│   │   ├── contexts/     # Contextos de React
│   │   │   └── AuthContext.tsx
│   │   ├── pages/        # Páginas de la aplicación
│   │   │   ├── Home.tsx
│   │   │   ├── Espacios.tsx
│   │   │   └── AdminDashboard.tsx
│   │   ├── lib/          # Utilidades
│   │   └── App.tsx       # Componente principal
│   └── index.html
├── server/                # Backend Express
│   ├── routes.ts         # Rutas de la API
│   ├── storage.ts        # Capa de almacenamiento
│   └── index.ts          # Servidor principal
├── shared/               # Código compartido
│   └── schema.ts         # Esquemas de datos
└── README.md
```

## 🎯 Páginas Principales

### Para Todos los Usuarios
- `/` - Dashboard principal
- `/espacios` - Explorar espacios disponibles
- `/reservas` - Mis reservas
- `/reservas/nueva` - Nueva reserva
- `/calendario` - Vista de calendario
- `/notificaciones` - Notificaciones
- `/perfil` - Mi perfil

### Solo para Administradores
- `/admin` - Panel de administración
- `/admin/usuarios` - Gestión de usuarios
- `/admin/espacios` - Gestión de espacios
- `/admin/categorias` - Gestión de categorías
- `/admin/tipos-evento` - Tipos de evento
- `/admin/bloqueos` - Bloqueos de espacios
- `/admin/aprobar-reservas` - Aprobar reservas
- `/admin/reportes` - Reportes y estadísticas
- `/admin/configuracion` - Configuración del sistema

## 🛠️ Tecnologías Utilizadas

### Frontend
- **React 18** - Biblioteca de UI
- **Vite** - Build tool y dev server
- **Tailwind CSS** - Framework de CSS
- **Wouter** - Enrutamiento ligero
- **Shadcn UI** - Componentes de UI
- **Lucide React** - Iconos
- **Recharts** - Gráficas y estadísticas
- **TanStack Query** - Manejo de estado del servidor

### Backend
- **Express.js** - Framework de servidor
- **TypeScript** - Tipado estático
- **Zod** - Validación de esquemas

## 📝 Desarrollo

### Scripts Disponibles

```bash
# Iniciar servidor de desarrollo
npm run dev

# Construir para producción
npm run build

# Iniciar servidor de producción
npm start

# Limpiar build
npm run clean
```

### Estructura de Componentes

Los componentes siguen las mejores prácticas de React y están organizados por funcionalidad:

- **Componentes de UI base** (`/components/ui/`) - Componentes reutilizables de shadcn
- **Componentes de negocio** (`/components/`) - Componentes específicos de la aplicación
- **Páginas** (`/pages/`) - Vistas completas de la aplicación
- **Contextos** (`/contexts/`) - Estado global con Context API

## 🔐 Sistema de Autenticación

El sistema incluye un contexto de autenticación (`AuthContext`) que maneja:
- Estado del usuario actual
- Verificación de roles (usuario/admin)
- Login/Logout
- Cambio de roles (para desarrollo)

## 🎨 Personalización

### Colores

Los colores institucionales están configurados en:
- `tailwind.config.ts` - Configuración de Tailwind
- `client/src/index.css` - Variables CSS personalizadas

### Temas

El sistema soporta modo claro y oscuro (configurado en Tailwind).

## 📱 Responsive

La aplicación está completamente optimizada para:
- 📱 Móviles (< 640px)
- 📱 Tablets (640px - 1024px)
- 💻 Desktop (> 1024px)

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add: nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es propiedad de la Universidad Laica Eloy Alfaro de Manabí (ULEAM).

## 📞 Contacto

Universidad Laica Eloy Alfaro de Manabí (ULEAM)
- Website: https://www.uleam.edu.ec
- Email: info@uleam.edu.ec

---

**Desarrollado con ❤️ para ULEAM**

## 🔄 Arquitectura actualizada (solo frontend)
- Este repo queda como **solo frontend** (React + Vite). Los servicios REST (Python), GraphQL (Go) y WebSocket (TS/Node) se consumen como endpoints externos.
- Variables de entorno (configurar en `.env.local`):
  - `VITE_REST_BASE_URL`: base del servicio REST.
  - `VITE_GRAPHQL_URL`: endpoint del servicio GraphQL.
  - `VITE_WS_URL`: URL del servidor WebSocket.
- Clientes ya preparados: `client/src/api/rest/*`, `client/src/api/graphql/*`, `client/src/api/websocket/*` y hooks (`useWebSocket`, `useNotificaciones`).
- Scripts npm: `npm run dev` (solo Vite), `npm run build`, `npm run preview`.
- El router (`client/src/router/AppRouter.tsx`) protege rutas privadas con AuthContext y deja solo `/login` como pública.
- Rutas protegidas: `/app/*` (usuarios/admin) y `/admin/*` (solo admin). Login desde el header o `/login`.
