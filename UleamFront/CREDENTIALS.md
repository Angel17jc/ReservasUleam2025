# Credenciales de prueba (Mock)

Estas credenciales funcionan con el backend mock actual (sin servidor real). Úsalas para probar el flujo de login y roles.

| Rol   | Email               | Password |
|-------|---------------------|----------|
| User  | `demo@uleam.edu.ec` | `demo123` |
| Admin | `admin@uleam.edu.ec`| `admin123` |

Cómo usarlas:
- Inicia sesión desde el botón **“Iniciar sesión”** en el header (modal) o visita `/login`.
- Si entras como admin serás redirigido a `/admin/dashboard`; como user a `/app/inicio`.
- El header mostrará el menú de usuario y, si eres admin, la opción **Ir al Panel de Administración**.
