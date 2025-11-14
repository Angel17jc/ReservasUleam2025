# Sistema de Reserva de Espacios ULEAM – Frontend

Frontend React/Vite que consume el backend distribuido (REST Python, GraphQL Go, WebSocket NestJS) para reservas, aprobaciones y dashboard en tiempo real.

## Requisitos
- Node.js 20+
- Backend corriendo en local:
  - REST: `http://localhost:8000/api`
  - GraphQL: `http://localhost:8080/graphql`
  - WebSocket (Socket.IO): `http://localhost:3001`

## Configuración de entorno
Crear `./.env.local` en la raíz de `UleamFront`:
```
VITE_REST_BASE_URL=http://localhost:8000
VITE_GRAPHQL_URL=http://localhost:8080/graphql
VITE_WS_URL=http://localhost:3001
```

## Instalación y ejecución
```bash
cd UleamFront
npm install
npm run dev        # http://localhost:5173
```

Build/previsualización:
```bash
npm run build
npm run preview
```

## Funcionalidad clave
- Login real contra REST (`/api/auth/login`) y guardado de JWT.
- Roles y menús: Admin, Profesor, Estudiante (se lee `tipo_usuario_id` y `tipo_usuario.nombre`).
- CRUD admin:
  - Usuarios: cambiar rol/estado.
  - Espacios, Categorías, Tipos de Evento (alta/edición/borrado inline).
  - Aprobaciones de reservas (estado inicial Pendiente; prioridad por rol).
- Reservas de usuario:
  - Crear con slots predefinidos (08–18h HOY) y selección de tipo de evento/espacio.
  - Listar/cancelar/ver detalle.
- Dashboards y reportes:
  - User home: próximas/mis reservas y estado siempre actualizado (WS + refetch).
  - Admin dashboard: métricas, top espacios, pendientes.
  - Admin reportes: métricas (GraphQL + fallback REST), gráficos por estado/tipo, top usuarios/espacios; descarga vía print/PDF.
- Notificaciones:
  - Carga histórica desde REST (`/api/notificaciones`).
  - Tiempo real por Socket.IO (`notificaciones:user:{id}`, `reservas:usuario:{id}`, `dashboard:admin`, etc.).

## Rutas principales
- Usuario: `/app/inicio`, `/app/espacios`, `/app/reservas`, `/app/reservas/nueva`, `/app/notificaciones`, `/app/perfil`, `/app/calendario`.
- Admin: `/admin/dashboard`, `/admin/usuarios`, `/admin/espacios`, `/admin/categorias`, `/admin/eventos`, `/admin/aprobaciones`, `/admin/reportes`.

## Estructura relevante (`client/src`)
- `api/` REST y GraphQL clients.
- `pages/` vistas (usuario y admin).
- `components/` UI y negocio (incluye `components/ui` de shadcn).
- `contexts/` (`AuthContext`) y `hooks/` (`useWebSocket`, etc.).
- `config/env.ts` lee las variables `VITE_*`.

## Usuarios de prueba (backend real)
Todos con contraseña `password123` (según seed del backend):
- Admin: `admin@uleam.edu.ec`
- Profesor: `profesor1@uleam.edu.ec`
- Estudiante: `estudiante1@uleam.edu.ec`

## Notas de integración
- REST base se concatena con `/api` automáticamente.
- WS usa Socket.IO con `auth.token` (JWT). Suscripciones por defecto según rol.
- GraphQL requiere el mismo JWT en `Authorization: Bearer <token>`.

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
