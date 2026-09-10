# n8n — Orquestación de eventos (Pilar 4)

n8n es el bus de eventos del sistema: recibe webhooks de pago y de partners externos,
los valida, y encadena las llamadas a los demás microservicios.

Este archivo es el **punto de entrada único**. Los cuatro documentos de referencia que
lo acompañan están enlazados al final.

---

## Puesta en marcha

n8n forma parte del `docker-compose.yml` de la raíz. No se instala ni se arranca aparte:

```bash
docker compose up -d n8n
```

| Dato | Valor |
| :--- | :--- |
| Interfaz web | http://localhost:5684 |
| Usuario / contraseña | `N8N_BASIC_AUTH_USER` / `N8N_BASIC_AUTH_PASSWORD` del `.env` raíz |
| Puerto interno | `5678` |
| Persistencia | volumen `n8n_data` (sobrevive a `docker compose down`) |
| Imagen | `n8nio/n8n:1.64.3` — **versión fijada a propósito**, ver más abajo |

> **No cambiar la imagen a `:latest`.** Esa etiqueta falla al extraerse con el
> snapshotter de Docker Desktop en Windows (`UtimesNanoAt ... node_modules/n8n/bin`)
> y aborta el arranque de todo el stack.

### Importar los workflows

Los cuatro `.json` de esta carpeta se importan desde la interfaz:
**Workflows → Import from File**. No se cargan solos al levantar el contenedor.

---

## Los 4 workflows

| # | Archivo | Disparador | Qué hace |
| :-: | :--- | :--- | :--- |
| 1 | `payment_handler.json` | Webhook `/webhook/payment-handler` | Valida el payload del pago, confirma la reserva en REST y notifica por WebSocket |
| 2 | `partner_handler.json` | Webhook `/webhook/partner-handler` | Verifica la firma HMAC del partner, normaliza el evento, ejecuta la acción y responde ACK |
| 3 | `mcp_input_handler.json` | Telegram | Extrae el mensaje, lo manda al AI service y responde por el mismo canal. **Desactivado por defecto** |
| 4 | `scheduled_tasks.json` | Cron (23:59 diario / cada 6 h) | Reporte diario y health-check de los servicios |

---

## Direcciones dentro de Docker

Los workflows corren **dentro** del contenedor de n8n, así que `localhost` apunta al
propio n8n, no al host. Hay que usar el nombre del servicio y su **puerto interno**:

| Servicio | URL desde n8n |
| :--- | :--- |
| REST | `http://rest-service:8000` |
| Auth | `http://auth-service:9000` |
| GraphQL | `http://graphql-service:8081` |
| AI | `http://ai-service:5000` |
| Payment | `http://payment-service:8001` |
| WebSocket | `http://websocket-service:3001` |

Los puertos `8004`, `3004`, `5684`… son el mapeo **al host**: sirven para el navegador
y para `curl` desde tu máquina, nunca para las llamadas entre contenedores.

---

## Endpoints que los workflows invocan

Verificado contra el código el 2026-09-09:

| Endpoint invocado | Servicio | ¿Existe? |
| :--- | :--- | :--- |
| `POST /api/webhooks/reserva-actualizada` | websocket | ✅ Sí |
| `POST /api/reservas/{id}/confirm` | rest | ❌ **No.** El equivalente real es `PATCH /api/reservas/{id}/estado` |
| `POST /api/orders` | rest | ❌ **No existe** |
| `GET /api/reports/daily` | rest | ❌ **No existe** |
| `POST /api/chat/process` | ai | ❌ **No.** El real es `POST /api/v1/chat/message` |

Los workflows 1, 2 y 4 fallarán en esos nodos hasta que se implementen los endpoints
o se reescriban los nodos. Ver [REQUIRED_ENDPOINTS.md](REQUIRED_ENDPOINTS.md), que
detalla el contrato esperado de cada uno.

---

## Seguridad

Todos los webhooks entrantes de partners van firmados con **HMAC-SHA256** sobre el
cuerpo serializado de forma canónica:

```python
payload_str = json.dumps(payload, sort_keys=True, separators=(',', ':'))
signature   = hmac.new(secret.encode(), payload_str.encode(), hashlib.sha256).hexdigest()
```

Los dos extremos deben serializar **exactamente igual** — un espacio de diferencia
invalida la firma. La receta completa, con implementaciones en Python, JavaScript y
PowerShell, está en [HMAC_UTILS.md](HMAC_UTILS.md).

El secreto compartido se inyecta por entorno. Nunca se escribe en un workflow ni se
versiona.

---

## Si algo falla

| Síntoma | Causa habitual |
| :--- | :--- |
| `ECONNREFUSED` en un nodo HTTP | La URL usa `localhost` en vez del nombre del servicio |
| `401` en un webhook de partner | Serialización JSON distinta en los dos extremos (ver HMAC_UTILS) |
| n8n no arranca | La imagen no está fijada a `1.64.3` |
| Los workflows desaparecieron | Se levantó con `docker compose down -v`, que borra el volumen `n8n_data` |
| `404` en un nodo HTTP | El endpoint no existe todavía — ver la tabla de arriba |

```bash
docker compose logs -f n8n
```

---

## Documentos de referencia

| Documento | Contenido |
| :--- | :--- |
| [CONTRACT_EVENTS.md](CONTRACT_EVENTS.md) | Contrato normalizado de eventos: estructura, campos obligatorios y tipos |
| [HMAC_UTILS.md](HMAC_UTILS.md) | Firma y verificación HMAC-SHA256 en cada lenguaje |
| [REQUIRED_ENDPOINTS.md](REQUIRED_ENDPOINTS.md) | Endpoints que los workflows necesitan, con su contrato |
| [DEMO_STEPS.md](DEMO_STEPS.md) | Guion paso a paso para demostrar los flujos |
