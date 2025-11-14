# Credenciales de prueba (backend real)

Usuarios sembrados en el backend (REST/GraphQL/WS). Contraseña para todos: `password123`.

| Rol        | Email                   |
|------------|-------------------------|
| Admin      | `admin@uleam.edu.ec`    |
| Profesor   | `profesor1@uleam.edu.ec`|
| Estudiante | `estudiante1@uleam.edu.ec`|

Notas:
- El JWT es el mismo para REST/GraphQL/Socket.IO.
- El menú admin solo aparece si `tipo_usuario_id === 1`.
- Si quieres probar notificaciones/WS, inicia sesión y realiza reservas; los eventos llegan a `notificaciones:user:{id}` y `reservas:usuario:{id}`.
