# n8n Setup - Instalación y Guía Local

## ✅ Instalación Completada

n8n ha sido instalado globalmente en tu Windows. Ya está listo para usar.

## 🚀 Cómo Ejecutar n8n Localmente

### Opción 1: Usando el script PowerShell (Recomendado)

Desde PowerShell, navega a la carpeta `UleamBack/` y ejecuta:

```powershell
cd C:\Users\ASUS\Desktop\ReservasUleam2026\ReservasUleam2025\UleamBack
.\run-n8n.ps1
```

Esto:
- Inicia n8n en `http://localhost:5678`
- Guarda datos en `n8n-data/` (persistencia local)
- Usa las variables de entorno configuradas

### Opción 2: Comando directo (sin script)

```powershell
$env:N8N_USER_FOLDER = "C:\Users\ASUS\Desktop\ReservasUleam2026\ReservasUleam2025\UleamBack\n8n-data"
n8n start
```

### Opción 3: Abrir n8n globalmente (sin carpeta específica)

```powershell
n8n start
```

## 📂 Estructura de Carpetas

```
UleamBack/
├── n8n-workflows/
│   ├── CONTRACT_EVENTS.md           # Contrato normalizado de eventos
│   ├── README.md                    # Esta guía
│   ├── payment_handler.json         # Workflow 1
│   ├── partner_handler.json         # Workflow 2
│   ├── mcp_input_handler.json       # Workflow 3 (opcional)
│   └── scheduled_tasks.json         # Workflow 4
├── n8n-data/                        # Almacenamiento local (generado por n8n)
├── run-n8n.ps1                      # Script para ejecutar n8n
└── docker-compose.n8n.yml           # (No usado en setup local)
```

## 🌐 Acceso

Una vez ejecutado:
- **URL**: `http://localhost:5678`
- **Primera ejecución**: Te pedirá crear usuario/contraseña
- **Dashboard**: Verás panel principal de n8n

## 🔧 Variables de Entorno Importantes

Las siguientes variables pueden configurarse al ejecutar n8n:

```powershell
$env:N8N_HOST = "localhost"                     # Host
$env:N8N_PORT = "5678"                          # Puerto
$env:N8N_USER_FOLDER = "path/to/n8n-data"      # Almacenamiento
$env:NODE_ENV = "development"                   # Modo desarrollo
$env:N8N_PROTOCOL = "http"                      # Protocolo
```

## 📝 Próximos Pasos

1. **Iniciar n8n** usando el script
2. **Crear workflows** para:
   - Payment Handler
   - Partner Handler
   - MCP Input Handler
   - Scheduled Tasks
3. **Configurar integraciones** con:
   - REST API (localhost:8000)
   - GraphQL (localhost:8080)
   - WebSocket (localhost:3001)
   - SMTP (email)
4. **Exportar workflows** como JSON

## 🧪 Testing Rápido

Una vez que n8n esté corriendo:

```powershell
# Verificar que n8n está accesible
curl http://localhost:5678
```

## ❌ Si Hay Problemas

**n8n no inicia**:
```powershell
# Limpiar caché y reintentar
rm -r C:\Users\ASUS\.n8n
n8n start
```

**Puerto 5678 en uso**:
```powershell
# Cambiar puerto temporalmente
$env:N8N_PORT = "5679"
n8n start
```

**Permiso denegado en PowerShell**:
```powershell
# Ejecutar como administrador o cambiar política de ejecución
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## 📚 Documentación Oficial

- [n8n Docs](https://docs.n8n.io/)
- [n8n Docker](https://docs.n8n.io/hosting/installation/docker/)
- [n8n Node Reference](https://docs.n8n.io/nodes/)
