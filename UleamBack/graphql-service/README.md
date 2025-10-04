# ULEAM Reservas – GraphQL Service (Go)

Servicio GraphQL (DEC2) para consultas y reportes. Comparte la BD y clave JWT con el REST.

## Puesta en marcha rápida
```bash
cd graphql-service
go run ./cmd/server   # expone http://localhost:8080/graphql
```

### Entorno
- `DATABASE_URL` (PostgreSQL)
- `SECRET_KEY` o `JWT_SECRET` (misma que REST/WS)
- `PORT` (opcional, default 8080)
- `WEBSOCKET_SERVICE_URL` (opcional, para emitir `stats_update` al WS)

### Autenticación
- JWT obligatorio en `Authorization: Bearer <token>`.
- Queries de analítica requieren admin (`tipo_usuario_id == 1`).

## Esquema y queries clave
- `reservas(limit, offset, usuario_id, espacio_id, estado_id, tipo_evento_id, fecha_desde, fecha_hasta)`  
  - Si no eres admin, se filtra automáticamente por tu `usuario_id`.
  - Devuelve `id, codigo, usuario_id, espacio_id, tipo_evento, estado, fecha, hora_inicio, hora_fin, titulo, descripcion, es_bloqueo`.
- `reserva(id: ID!)`  
  - Sólo admin o dueño de la reserva.
- `estadisticas` (admin)  
  - Totales por estado y conteos de usuarios/espacios activos.
- `espaciosMasReservados(fecha_desde, fecha_hasta, limit)` (admin)  
  - Top de espacios por cantidad de reservas.
- `usuariosMasActivos(fecha_desde, fecha_hasta, limit)` (admin)  
  - Top usuarios por reservas.
- `reservasPorEstado(fecha_desde, fecha_hasta)` (admin)  
  - Conteo agrupado por estado.
- `reservasPorTipoEvento(fecha_desde, fecha_hasta)` (admin)  
  - Conteo agrupado por tipo de evento.
- `disponibilidad(espacio_id: ID!, fecha: String!, incluir_pendientes: Boolean = true)`  
  - Calcula ocupados y libres 08:00–18:00 en base a reservas Aprobadas y, opcionalmente, Pendientes.

## Ejemplo de petición
POST `http://localhost:8080/graphql`
```json
{
  "query": "query ($fecha:String!){ reservas(limit:5){id codigo estado fecha hora_inicio} disponibilidad(espacio_id:1,fecha:$fecha){libres{hora_inicio hora_fin} ocupados{hora_inicio hora_fin estado}} }",
  "variables": { "fecha": "2025-11-15" }
}
```
Header: `Authorization: Bearer <JWT>`

## Integración con REST/WS
- Usa la misma BD que REST, por lo que refleja estados y disponibilidad real.
- Disponibilidad se calcula igual que en REST (bloqueo por Aprobada y, opcionalmente, Pendiente).
- `stats_update`: si configuras `WEBSOCKET_SERVICE_URL`, la query `estadisticas` emitirá un webhook `POST /api/webhooks/stats-update` al servicio WebSocket.

## Pendiente / mejoras futuras
- Tests de resolvers y paginación.
- Cache/DataLoader para evitar N+1 en campos anidados si se amplía el esquema.
- Mutations si se desea exponer acciones (actualmente sólo lectura/reportes).
## Tests
- Ejecuta: `go test ./...`
