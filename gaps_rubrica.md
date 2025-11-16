# Checklist de Brechas vs. Rúbrica (Front + Back)

Este documento detalla los faltantes detectados respecto a integración de tecnologías, funcionalidad, UX, seguridad y documentación. Incluye acciones sugeridas y pequeños diagramas donde aporta claridad.

---

## 1) Integración tiempo real (WS)

**Brechas**
- Reconexión WS y manejo de token expirado: no se documenta ni reintenta con backoff. Si el JWT expira, el cliente queda desconectado.
- Estadísticas en vivo: falta verificar que `WEBSOCKET_SERVICE_URL` esté configurado en REST/GraphQL para generar `stats_update`.
- Notificaciones offline: cuando el cliente está desconectado, solo se cargan al recargar por REST; no hay aclaración de política offline.

**Acciones**
1. Implementar en `useWebSocket`:
   - Backoff exponencial en reconexión.
   - En 401/invalid token, limpiar sesión y redirigir a login.
2. Documentar en README back/Front:
   - Webhooks esperados por WS: `reserva-creada`, `reserva-actualizada`, `reserva-cancelada`, `notificacion`, `stats-update`, `disponibilidad-actualizada`.
   - Requisito: `WEBSOCKET_SERVICE_URL=http://localhost:3001` en REST/GraphQL.
3. Nota de “offline”: historial se obtiene con `GET /api/notificaciones`; los eventos en vivo no se reenvían si no hay conexión activa.

**Diagrama (estadísticas en vivo)**
```
REST/GraphQL --stats_update--> WS --emit stats_update--> canal dashboard:admin
Front (admin) --refetch--> métricas/Reportes
```

---

## 2) Disponibilidad y UX en reservas

**Brechas**
- Slots fijos (08–18) sin reflejar disponibilidad real de `/api/disponibilidad`.
- Validación visual de conflictos: solo mensaje genérico si el backend rechaza.

**Acciones**
1. En “Nueva Reserva”: consultar `/api/disponibilidad?espacio_id=...&fecha=...` y marcar ocupados/libres en el selector de horas.
2. Mostrar feedback claro si hay conflicto: “Horario ocupado (Pendiente/Aprobada)”.

**Diagrama (consulta disponibilidad)**
```
Front --> GET /api/disponibilidad?espacio_id=X&fecha=YYYY-MM-DD
Respuesta: { libres[], ocupados[] } 
UI: deshabilita ocupados, muestra colores por estado
```

---

## 3) GraphQL (capa de reportes)

**Brechas**
- Solo lectura; si la rúbrica exige acciones/mutations de aprobación vía GraphQL, no existen.
- `stats_update` opcional no documentado cómo habilitarlo.

**Acciones**
1. Documentar que GraphQL es de solo lectura (reportes). Si se requiere, añadir mutation `actualizarEstadoReserva`.
2. Indicar cómo habilitar `WEBSOCKET_SERVICE_URL` para `stats_update`.

---

## 4) Pruebas y CI

**Brechas**
- REST tests mínimos ausentes (auth, crear reserva, cambiar estado).
- Front sin scripts documentados de lint/test (solo `tsc`).

**Acciones**
1. Añadir `pytest` básicos en `rest-service/tests` (auth OK/KO, reserva OK, cambio estado OK, conflicto horario).
2. Añadir scripts en front:
   ```json
   "lint": "tsc --noEmit"
   ```
   y documentar cómo correrlos en README.

---

## 5) Gestión de usuarios (Admin)

**Brechas**
- UI solo cambia rol/estado; no hay crear/borrar usuario si se exige CRUD completo.

**Acciones**
1. Decidir si se expone alta/baja de usuario en UI admin; si sí, agregar formularios y usar `POST/DELETE /api/usuarios`.

---

## 6) Seguridad y despliegue

**Brechas**
- CORS/ALLOWED_ORIGINS no documentado.
- HTTPS y variables de producción no descritas.
- Sin manejo de expiración JWT en front (solo falla silenciosa en 401).

**Acciones**
1. Documentar en README Back:
   - `ALLOWED_ORIGINS` ejemplo para front prod.
   - Recomendación HTTPS/Reverse proxy.
2. En front: si 401, limpiar token y enviar a `/login`; reconectar WS tras login.

---

## 7) Documentación (Front/WS)

**Brechas**
- No hay sección en README Front detallando canales/eventos Socket.IO y flujo de notificaciones.
- Falta guía de despliegue (build + servir estático + apontar a backend prod).

**Acciones**
1. Añadir a README Front:
   - Canales: `notificaciones:user:{id}`, `reservas:usuario:{id}`, `reservas:todas`, `dashboard:admin`, `disponibilidad:all`.
   - Eventos: `reserva_creada/aprobada/rechazada/cancelada`, `nueva_notificacion`, `stats_update`.
2. Guía de despliegue: `npm run build`, servir `dist/` en host estático apuntando a URLs del backend productivo.

---

## 8) Calidad de UX/Accesibilidad

**Brechas**
- No hay revisión de ARIA/focus states/shadcn defaults.

**Acciones**
1. Revisar inputs/selects críticos (reservas, aprobaciones) con labels y focus visibles.
2. Mensajes de error/éxito consistentes.

---

## Resumen Visual Rápido

```
[Pendiente] WS robusto: reconexión, expiro JWT, stats_update documentado
[Pendiente] Disponibilidad real en UI (consulta /api/disponibilidad)
[Pendiente] Tests REST básicos (auth, reservas, cambio estado)
[Pendiente] Doc WS en README Front (canales/eventos) + despliegue
[Opcional] CRUD completo de usuarios en UI Admin (alta/baja)
[Opcional] Mutations GraphQL si se exige acciones (aprobación) por DEC2
[Mejora] Handling 401 en front (limpiar token/redirigir)
[Mejora] CORS/HTTPS en README Back
```
