# ULEAM Reservas – WebSocket Service (TypeScript/NestJS)

Servicio Socket.IO para tiempo real consumido por el frontend y el dashboard.

## Puesta en marcha rápida
```bash
cd websocket-service
npm install
npm run dev    # o npm run start
```
Puerto por defecto: `3001`.

## Autenticación y roles
- Handshake requiere JWT del servicio REST. Se puede enviar como:
  - Header `Authorization: Bearer <token>`
  - Query `token=<token>`
  - `auth.token` en el cliente Socket.IO
- El token se valida con `JWT_SECRET`/`SECRET_KEY`.  
- Roles: `nivel_prioridad == 1` es admin. Admin puede entrar a canales `dashboard:*`, `reservas:todas`, `disponibilidad:all` y a cualquier `notificaciones:user:{id}` / `reservas:usuario:{id}`. Los usuarios normales solo a sus propios canales.

## Canales útiles
- `notificaciones:user:{id}`: notificaciones personales, `notificacion_actualizada`, `nueva_notificacion`, `recordatorio`.
- `reservas:usuario:{id}`: eventos de reservas del usuario.
- `reservas:espacio:{id}` y `reservas:todas`: stream de reservas por espacio o global (admins).
- `disponibilidad:espacio:{id}` y `disponibilidad:all`: disponibilidad recalculada tras cambios.
- `dashboard:admin`: stats, presencia (`usuario_online/offline`), reservas, disponibilidad global.

## Eventos emitidos
- Reservas: `reserva_creada`, `reserva_actualizada`, `reserva_aprobada`, `reserva_rechazada`, `reserva_cancelada`.
- Notificaciones: `nueva_notificacion`, `notificacion_actualizada`, `recordatorio`.
- Disponibilidad: `disponibilidad_actualizada` (libres/ocupados por espacio/fecha). Payload ejemplo:
  ```json
  {
    "espacio_id": 1,
    "espacio_nombre": "Auditorio A",
    "fecha": "2025-11-15",
    "dia_semana": "Monday",
    "ocupados": [{"hora_inicio": "09:00", "hora_fin": "10:00", "estado": "Aprobada"}],
    "libres": [{"hora_inicio": "08:00", "hora_fin": "09:00"}]
  }
  ```
- Stats/presencia: `stats_update`, `usuario_online`, `usuario_offline`.

## Webhooks HTTP de entrada
REST/GraphQL emiten JSON hacia:
- `POST /api/webhooks/reserva-creada`
- `POST /api/webhooks/reserva-actualizada`
- `POST /api/webhooks/reserva-cancelada`
- `POST /api/webhooks/notificacion`
- `POST /api/webhooks/stats-update`
- `POST /api/webhooks/disponibilidad-actualizada`
- `POST /api/webhooks/recordatorio-evento`

Los payloads se re-emiten en los canales correspondientes con un `timestamp`.

## Ejemplo de conexión (cliente Socket.IO)
```js
const socket = io('http://localhost:3001', { auth: { token: '<JWT>' } });
socket.on('connected', console.log);
socket.emit('subscribe', { channels: ['notificaciones:user:5', 'reservas:usuario:5'] });
```

## Entorno
- `JWT_SECRET` (o `SECRET_KEY`) debe coincidir con el REST.
- `PORT` (opcional, default 3001)
- Otros: `DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME` si el gateway consulta notificaciones/usuarios.
