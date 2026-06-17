# Sistema de Gestión de Filas — Cursos de Verano FICCT

> **Universidad Autónoma Gabriel René Moreno**  
> Facultad de Ingeniería en Ciencias de la Computación y Telecomunicaciones  
> Materia: INF 423 — Ingeniería de Software II  

---

## Índice

1. [Contexto Académico](#1-contexto-académico)  
2. [Problema que Resuelve](#2-problema-que-resuelve)  
3. [Objetivos Técnicos del Proyecto](#3-objetivos-técnicos-del-proyecto)  
4. [Stack Tecnológico](#4-stack-tecnológico)  
5. [Arquitectura del Sistema](#5-arquitectura-del-sistema)  
6. [Estructura de Archivos](#6-estructura-de-archivos)  
7. [Descripción de Cada Archivo](#7-descripción-de-cada-archivo)  
8. [Casos de Uso y Flujos de Trabajo](#8-casos-de-uso-y-flujos-de-trabajo)  
9. [Modelo de Datos](#9-modelo-de-datos)  
10. [Control de Acceso (RBAC)](#10-control-de-acceso-rbac)  
11. [Estados del Ticket](#11-estados-del-ticket)  
12. [Cómo Levantar el Proyecto](#12-cómo-levantar-el-proyecto)  
13. [Decisiones de Diseño Relevantes](#13-decisiones-de-diseño-relevantes)  
14. [Requisitos del Sistema](#14-requisitos-del-sistema)  

---

## 1. Contexto Académico

Este proyecto fue desarrollado como trabajo práctico integrador para la materia **INF 423 - Ingeniería de Software II** en la FICCT (UAGRM). El objetivo académico central es que el estudiante comprenda y aplique de forma práctica los principios de la **arquitectura de microservicios**, en particular:

- Cómo se descompone un sistema en servicios autónomos con responsabilidades únicas.
- Cómo se comunican esos servicios entre sí exclusivamente a través de interfaces HTTP.
- Cómo un **API Gateway** centraliza el acceso, el enrutamiento y el control de seguridad.
- Cómo se implementa un servidor HTTP desde cero en Python puro, sin depender de frameworks como Django, Flask o FastAPI, para entender la lógica de bajo nivel de las comunicaciones cliente-servidor.
- Cómo se containeriza una aplicación con Docker para garantizar la reproducibilidad del entorno.

La restricción de **no usar frameworks web** es intencional y didáctica: obliga a manejar manualmente el parseo de rutas, la lectura del body de las peticiones, el manejo de headers CORS, y la serialización de respuestas JSON, conceptos que los frameworks abstractan y ocultan.

---

## 2. Problema que Resuelve

En la Facultad de Computación (FICCT) de la UAGRM, la inscripción a los cursos de verano genera cada año largas colas físicas frente a las ventanillas de pago. Los estudiantes deben presentarse en persona sin saber cuánto tiempo esperarán, se producen aglomeraciones, y existe el problema de la "venta de lugares" en la fila.

**El sistema reemplaza esta fila física por un sistema digital de turnos con QR**, permitiendo que:

- El estudiante solicite su turno desde cualquier dispositivo con navegador.
- Vea en tiempo real su posición en la fila y el tiempo estimado de espera.
- Presente únicamente un código QR al llegar a la ventanilla para verificar su identidad.
- El cajero gestione el flujo de atención de forma ordenada y verificable.
- El administrador configure el sistema (ventanillas, roles) sin tocar el código.

---

## 3. Objetivos Técnicos del Proyecto

| Objetivo | Cómo se implementa |
|---|---|
| Microservicios desacoplados | Tres MS independientes, cada uno con su propia BD PostgreSQL |
| Comunicación HTTP pura | `urllib.request` en el Gateway, `http.server` en cada MS |
| Sin frameworks | Python stdlib exclusivamente en el backend |
| Control de acceso centralizado | Gateway con RBAC por whitelist de rutas por rol |
| Contenerización completa | Docker + docker-compose con red interna dedicada |
| Frontend simple y funcional | HTML + CSS + JavaScript Vanilla |
| Generación y validación de QR | QR generado en backend, validado contra BD en el escaneo |

---

## 4. Stack Tecnológico

```
Backend:    Python 3.x (stdlib: http.server, socketserver, json, urllib)
Base de datos: PostgreSQL 15 (psycopg2 como driver)
Frontend:   HTML5, CSS3, JavaScript Vanilla (sin frameworks ni bundlers)
Librería QR cliente: qrcode.js (generación visual en el navegador)
Librería escáner: html5-qrcode (acceso a cámara del dispositivo)
Contenerización: Docker + Docker Compose
Red interna: ficct_red_verano (bridge network)
```

---

## 5. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENTE (Browser)                            │
│   registro.html  login.html  dashboard.html  atencion.html          │
│   api.js  auth.js  estudiante.js  cajero.js  admin.js  dashboard.js │
└────────────────────────────┬────────────────────────────────────────┘
                              │ HTTP :80
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY  :8000                                 │
│   • Proxy reverso HTTP puro (urllib.request)                        │
│   • Enrutamiento por prefijo de URL                                  │
│   • RBAC por whitelist (X-Rol-Id header)                            │
│   • Validación de JSON body                                          │
│   • Manejo de CORS (do_OPTIONS)                                     │
│   • Timeout de 10s por MS, devuelve 503 si no responde             │
└──────────┬──────────────────┬──────────────────┬───────────────────┘
           │ /usuario         │ /fila            │ /ventanilla
           ▼                  ▼                  ▼
┌────────────────┐  ┌────────────────┐  ┌────────────────┐
│  MS Usuario    │  │ MS Nucleo Fila │  │ MS Ventanilla  │
│  :8001         │  │  :8002         │  │  :8003         │
│                │  │                │  │                │
│ main.py        │  │ main.py        │  │ main.py        │
│ controller.py  │  │ controller.py  │  │ controller.py  │
│ repository.py  │  │ repository.py  │  │ repository.py  │
└───────┬────────┘  └───────┬────────┘  └───────┬────────┘
        │                   │                    │
        ▼                   ▼                    ▼
┌────────────┐     ┌────────────┐      ┌────────────┐
│ db_usuario │     │ db_nucleo  │      │db_ventanilla│
│ PostgreSQL │     │ PostgreSQL │      │ PostgreSQL  │
└────────────┘     └────────────┘      └────────────┘
        │                   │                    │
        └───────────────────┴────────────────────┘
                    ficct_red_verano (Docker bridge)
```

**Principio clave:** No existe comunicación directa entre microservicios. El MS Ventanilla nunca llama al MS Fila ni viceversa. Toda la orquestación la realiza el frontend a través del Gateway. Esto simplifica el sistema y hace que los MS sean completamente independientes.

---

## 6. Estructura de Archivos

```
Parcial1/
├── docker-compose.yml                  # Orquestación de todos los contenedores
│
├── backend/
│   ├── api_geteway/
│   │   ├── Dockerfile
│   │   └── src/
│   │       └── main.py                 # API Gateway (GatewayHandler)
│   │
│   └── microservios/
│       ├── ms_usuario/
│       │   ├── Dockerfile
│       │   └── src/
│       │       ├── main.py             # HTTP Handler de usuario
│       │       ├── controller.py       # Lógica de negocio de usuario
│       │       └── repository.py       # Acceso a db_usuario
│       │
│       ├── ms_nucleo_fila/
│       │   ├── Dockerfile
│       │   └── src/
│       │       ├── main.py             # HTTP Handler de fila
│       │       ├── controller.py       # Lógica de negocio de fila
│       │       └── repository.py       # Acceso a db_nucleo_fila
│       │
│       └── ms_ventanilla/
│           ├── Dockerfile
│           └── src/
│               ├── main.py             # HTTP Handler de ventanilla
│               ├── controller.py       # Lógica de negocio de ventanilla
│               └── repository.py       # Acceso a db_ventanilla
│
└── frontend/
    ├── Dockerfile
    └── src/
        ├── pages/
        │   ├── registro.html           # Formulario de registro de estudiante
        │   ├── login.html              # Formulario de login
        │   ├── dashboard.html          # Vista principal (rol-aware)
        │   └── atencion.html           # Panel de atención del cajero
        ├── js/
        │   ├── api.js                  # Función apiFetch() centralizada
        │   ├── auth.js                 # Login, logout, checkAuth()
        │   ├── dashboard.js            # Inicialización por rol
        │   ├── estudiante.js           # Polling de estado + solicitar ticket
        │   ├── cajero.js               # Flujo de atención + escáner QR
        │   └── admin.js                # Gestión de usuarios y ventanillas
        ├── css/
        │   └── global.css              # Estilos unificados + sistema de toast
        └── lib/
            ├── qrcode.min.js           # Generación de imagen QR en el cliente
            └── html5-qrcode.min.js     # Escáner de cámara para el cajero
```

---

## 7. Descripción de Cada Archivo

### API Gateway — `api_geteway/src/main.py`

Implementa `GatewayHandler` extendiendo `http.server.BaseHTTPRequestHandler`. Es el único punto de entrada al sistema desde el exterior.

Responsabilidades: parsear el prefijo de la URL (`/usuario`, `/fila`, `/ventanilla`) para determinar el microservicio destino; verificar el header `X-Rol-Id` contra la whitelist de rutas permitidas por rol; validar que el body sea JSON válido antes de forwarding; hacer la petición al MS destino con `urllib.request.urlopen(timeout=10)`; retransmitir la respuesta al cliente; y responder a preflight CORS con `do_OPTIONS`.

Manejo de errores distingue `urllib.error.HTTPError` (el MS respondió con error, se retransmite el status code) de `urllib.error.URLError` (el MS no está disponible, devuelve 503).

---

### MS Usuario — `ms_usuario/src/`

**`main.py`**: Enruta peticiones HTTP a las funciones del controller. Rutas registradas: `POST /registro`, `POST /login`, `GET /obtener_usuarios`, `GET /usuarios/{id}`, `PATCH /usuarios/{id}`, `DELETE /usuarios/{id}`.

**`controller.py`**: Implementa la lógica de negocio. `handle_registro()` fuerza `rol_id = 1` independientemente de lo que envíe el cliente (un estudiante no puede registrarse como admin). `handle_update_user()` filtra los campos permitidos a modificar con una lista blanca (`campos_permitidos`). `handle_delete_user()` realiza baja lógica (`activo = FALSE`) sin borrar el registro.

**`repository.py`**: Gestiona la conexión a `db_usuario` con reintentos (5 intentos, 3 segundos entre cada uno). Inicializa las tablas `rol` y `usuario` con `CREATE TABLE IF NOT EXISTS`. Siembra los 3 roles y un usuario administrador inicial (`registro: 221043721`) si no existen. El campo `registro` tiene constraint `UNIQUE`.

---

### MS Nucleo Fila — `ms_nucleo_fila/src/`

**`main.py`**: Enruta a: `POST /tomar_ticket`, `POST /llamar_siguiente`, `POST /validar_qr`, `POST /completar_atencion`, `POST /expirar_ticket`, `GET /estado/{est_id}`. Implementa `leer_body()` que maneja robustamente la ausencia de `Content-Length`.

**`controller.py`**: 
- `handle_tomar_ticket()`: verifica que el estudiante no tenga ya un ticket activo del día antes de crear uno nuevo.
- `handle_ver_estado()`: calcula personas delante y tiempo estimado (`count × 2.5 min`).
- `handle_llamar()`: toma el ticket con menor posición en estado `ESPERANDO`.
- `handle_validar_qr()`: verifica que el QR escaneado coincida con el ticket en `ATENDIENDO` para esa ventanilla.
- `handle_completar()`: transición `ATENDIENDO → ATENDIDO` (flujo exitoso).
- `handle_expirar()`: transición `ATENDIENDO → EXPIRADO`, borra el `codigo_qr` (estudiante no se presentó).

**`repository.py`**: La tabla `ticket` tiene un `CHECK constraint` que limita los estados a `ESPERANDO`, `ATENDIENDO`, `ATENDIDO`, `EXPIRADO`. El código QR se genera con el patrón `QR-{registro}-{posicion}`. La posición se calcula como `COALESCE(MAX(posicion), 0) + 1` filtrando por `fecha_creacion::date = CURRENT_DATE`, lo que garantiza que las posiciones se reinician cada día.

---

### MS Ventanilla — `ms_ventanilla/src/`

**`main.py`**: Enruta a: `GET /listar`, `GET /disponibles`, `POST /crear`, `DELETE /eliminar/{id}`, `POST /abrir`, `POST /cerrar`.

**`controller.py`**: `handle_disponibles()` devuelve solo ventanillas activas que no tienen una sesión abierta en ese momento. `handle_abrir()` crea un registro en `ventanilla_estado`. `handle_cerrar()` actualiza ese registro con la hora de cierre.

**`repository.py`**: Maneja dos tablas: `ventanilla` (catálogo de cajas) y `ventanilla_estado` (sesiones activas). Una ventanilla puede tener múltiples sesiones históricas pero solo una activa (`estado = TRUE`).

---

### Frontend — `frontend/src/`

**`api.js`**: Función central `apiFetch(endpoint, method, data)` que agrega el header `X-Rol-Id` desde `localStorage` en todas las peticiones. Devuelve siempre `{ data, error }` para manejo uniforme de errores.

**`auth.js`**: Maneja login y registro. Al autenticar, guarda en `localStorage`: `usuario_id`, `nombre`, `rol_id`, `registro`. `checkAuth()` redirige al login si no hay sesión activa. `logout()` limpia el storage y redirige.

**`dashboard.js`**: Punto de entrada de `dashboard.html`. Lee `rol_id` del storage y llama a `initEstudiante()`, `initCajero()` o `initAdmin()` según corresponda, mostrando la vista adecuada y ocultando las otras.

**`estudiante.js`**: Llama a `actualizarEstadoTicket()` inmediatamente y luego cada 10 segundos con `setInterval`. Incluye guard `if(!estId) return` para evitar peticiones con ID nulo. Maneja los 4 estados posibles del ticket: sin ticket (muestra botón "Sacar Ticket"), `ESPERANDO` (muestra posición y QR), `ATENDIENDO` (alerta roja "dirígete a la ventanilla"), `EXPIRADO` (banner rojo, detiene el polling, botón "Sacar Nuevo Ticket").

**`cajero.js`**: Implementa el flujo completo de 6 pasos: (1) cargar ventanillas disponibles en `initCajero()`, (2) abrir sesión con `abrirCaja()`, (3) verificar si hay turno pendiente y expirarlo antes de llamar al siguiente, (4) `llamarSiguiente()` obtiene el próximo turno, (5) `iniciarEscaner()` activa la cámara con `html5-qrcode`, (6) `validarQR()` verifica el código contra el backend y llama a `completarAtencion()`. Gestiona el ciclo de vida del escáner con `detenerEscaner()` para evitar errores al reiniciar.

**`admin.js`**: Implementa `cargarUsuarios()`, `ascenderCajero()`, `eliminarUsuario()`, `cargarVentanillas()`, `crearVentanilla()` y `eliminarVentanilla()`. Usa `showToast()` en lugar de `alert()` para no bloquear el hilo del navegador.

**`global.css`**: Define las variables de color (`--primary-color: #003366`), las 4 capas de layout (`app-header`, `dashboard-main`, `custom-card`, `admin-container`), el sistema de banners de estado para `atencion.html` (`.estado-espera`, `.estado-atendiendo`, `.estado-listo`, `.estado-expirado`), y el sistema de toast no bloqueante (`.toast`, `.toast-success`, `.toast-error`).

**`dashboard.html`**: La vista principal diferenciada por rol. Contiene: formulario de registro para estudiantes, panel de selección de ventanilla para cajeros, y dos secciones para el admin (tabla de usuarios con acciones RBAC y tabla de ventanillas con botón de creación inline). Carga todos los archivos JS al final del body para que el DOM esté disponible.

**`atencion.html`**: Vista exclusiva del cajero durante la atención. Muestra el banner de estado, el texto del turno actual, el contenedor del escáner QR (`div#reader`) y los dos botones de acción. El header muestra el número de ventanilla leído desde `localStorage`. Implementa `cerrarCaja()` inline que llama a `POST /ventanilla/cerrar` antes de redirigir al dashboard.

---

### `docker-compose.yml`

Define 8 servicios: `db_usuario`, `db_nucleo_fila`, `db_ventanilla` (PostgreSQL 15 con healthcheck `pg_isready`), `ms_usuario`, `ms_nucleo_fila`, `ms_ventanilla` (cada uno con `depends_on: condition: service_healthy` hacia su BD), `api_gateway` (depende de los 3 MS), y `frontend` (nginx, depende del gateway). Todos conectados a la red `ficct_red_verano`. Los MS reciben las credenciales de BD como variables de entorno.

---

## 8. Casos de Uso y Flujos de Trabajo

### CU-01: Registro de Estudiante

```
Estudiante                   Gateway              MS Usuario          db_usuario
    │                           │                     │                   │
    │── POST /usuario/registro ─▶│                     │                   │
    │   {nombre, email,         │ X-Rol-Id=1           │                   │
    │    registro, password}    │─▶ Whitelist OK        │                   │
    │                           │─── POST /registro ──▶│                   │
    │                           │                      │── INSERT usuario ─▶│
    │                           │                      │◀─ {id} ────────────│
    │◀── {mensaje, id} 201 ─────│◀── {mensaje, id} ───│                   │
```

El `rol_id` se fija en 1 (Estudiante) en el controller, ignorando cualquier valor enviado por el cliente.

---

### CU-02: Login

```
Usuario                     Gateway              MS Usuario
   │── POST /usuario/login ─▶│                      │
   │   {registro, password}  │─── POST /login ─────▶│
   │                         │                       │── SELECT WHERE registro=? AND activo=TRUE
   │                         │                       │── compara password
   │◀── {usuario: {id,       │◀── {usuario} 200 ────│
   │     nombre, rol_id}} ───│                       │
   │
   │ Guarda en localStorage:
   │   usuario_id, nombre, rol_id, registro
```

---

### CU-03: Gestión de Ventanillas (Admin)

El Admin crea ventanillas desde `dashboard.html`. Ingresa una etiqueta y pulsa "+ Nueva". El sistema hace `POST /ventanilla/crear {etiqueta}` y recarga la tabla. Para dar de baja, `DELETE /ventanilla/eliminar/{id}` hace baja lógica (`activa = FALSE`).

El Cajero ve solo las ventanillas disponibles (activas y sin sesión abierta) a través de `GET /ventanilla/disponibles`. Al pulsar "Abrir Ventanilla", `POST /ventanilla/abrir` crea un registro en `ventanilla_estado` y el frontend redirige a `atencion.html`. Al cerrar, `POST /ventanilla/cerrar` registra la hora de cierre y libera la ventanilla.

---

### CU-04: Solicitar Ticket con QR (Estudiante)

```
1. Estudiante pulsa "Sacar Ticket"
2. POST /fila/tomar_ticket {estudiante_id, registro}
3. MS Fila verifica: ¿tiene ticket activo hoy? Si sí → error 400
4. Calcula posición = MAX(posicion)+1 WHERE fecha=HOY
5. Genera codigo_qr = "QR-{registro}-{posicion}"
6. INSERT ticket RETURNING id, posicion, codigo_qr
7. Frontend recibe ticket y llama actualizarEstadoTicket()
8. QRCode.js renderiza la imagen QR en pantalla
```

---

### CU-05: Consulta de Estado en Tiempo Real (Polling)

```
Cada 10 segundos (setInterval):
1. GET /fila/estado/{usuario_id}
2. MS Fila: SELECT ticket WHERE estado IN (ESPERANDO, ATENDIENDO, EXPIRADO) AND fecha=HOY
3. Si existe ticket:
   - COUNT personas delante (posicion < ticket.posicion AND estado=ESPERANDO)
   - tiempo_estimado = count × 2.5 minutos
   - Devuelve {ticket, personas_delante, tiempo_estimado}
4. Frontend actualiza la UI según estado:
   - ESPERANDO  → posición, tiempo, imagen QR
   - ATENDIENDO → alerta roja "¡Ve a la ventanilla!"
   - EXPIRADO   → banner rojo, clearInterval, botón "Sacar Nuevo Ticket"
```

---

### CU-06: Flujo Completo de Atención (Cajero)

```
Cajero                       Gateway              MS Fila           db_nucleo_fila
  │                             │                    │                    │
  │ [Si hay turno previo sin    │                    │                    │
  │  completar]:                │                    │                    │
  │── POST /fila/expirar_ticket▶│─── POST /expirar ─▶│                    │
  │   {ticket_id}               │                    │── UPDATE SET       │
  │                             │                    │   estado=EXPIRADO  │
  │                             │                    │   codigo_qr=NULL   │
  │                             │                    │   WHERE id=? AND   │
  │                             │                    │   estado=ATENDIENDO│
  │◀── {mensaje} 200 ───────────│◀── {mensaje} ─────│                    │
  │                             │                    │                    │
  │── POST /fila/llamar_siguiente▶│── POST /llamar ──▶│                   │
  │   {ventanilla_id,cajero_id} │                    │── SELECT MIN(pos)  │
  │                             │                    │   WHERE ESPERANDO  │
  │                             │                    │── UPDATE ATENDIENDO│
  │◀── {atendiendo_a:{id,       │◀─────────────────│                    │
  │     registro,posicion}} ────│                    │                    │
  │                             │                    │                    │
  │ [Cámara lee QR]             │                    │                    │
  │── POST /fila/validar_qr ───▶│── POST /validar ──▶│                   │
  │   {codigo_qr, ventanilla_id}│                    │── SELECT WHERE     │
  │                             │                    │   qr=? AND v_id=?  │
  │                             │                    │   AND ATENDIENDO   │
  │◀── {mensaje, datos} 200 ────│◀─────────────────│                    │
  │                             │                    │                    │
  │── POST /fila/completar ─────▶│── POST /completar▶│                   │
  │   {ticket_id}               │                    │── UPDATE ATENDIDO  │
  │◀── {mensaje} 200 ───────────│◀─────────────────│                    │
```

Cuando el estudiante refresca (próximo polling en 10s), el estado `ATENDIDO` ya no aparece en la consulta, y el sistema muestra "Sin tickets activos".

---

### CU-07: Expiración por Inasistencia

Si el cajero llama a un siguiente turno sin haber completado el anterior (el estudiante no se presentó):

1. `cajero.js` detecta que `ticketActual !== null` al inicio de `llamarSiguiente()`
2. Llama automáticamente a `expirarTicketActual()` → `POST /fila/expirar_ticket {ticket_id}`
3. MS Fila hace `UPDATE ticket SET estado='EXPIRADO', codigo_qr=NULL WHERE id=? AND estado='ATENDIENDO'`
4. El estudiante en su próximo polling (10s) ve el estado `EXPIRADO`
5. El frontend muestra banner rojo, detiene el polling, y ofrece botón "Sacar Nuevo Ticket"

---

### CU-08: Gestión de Roles (Admin)

```
Admin ve tabla de usuarios con badge de rol actual.
Para cada usuario rol_id != 2 (no cajero) aparece botón "Hacer Cajero".

PATCH /usuario/usuarios/{id}  {rol_id: 2}

MS Usuario → controller filtra campos_permitidos=['nombre','email','rol_id',...]
           → UPDATE usuario SET rol_id=2 WHERE id=?
           → {mensaje: 'Usuario actualizado correctamente'} 200

Admin ve tabla actualizada con badge "Cajero".
```

---

## 9. Modelo de Datos

### db_usuario

```sql
CREATE TABLE rol (
    id     SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL
);
-- Datos iniciales: 'estudiante' (1), 'cajero' (2), 'admin' (3)

CREATE TABLE usuario (
    id       SERIAL PRIMARY KEY,
    nombre   VARCHAR(100) NOT NULL,
    email    VARCHAR(100),
    password VARCHAR(255) NOT NULL,  -- texto plano (simplificación académica)
    registro INT NOT NULL UNIQUE,    -- número de registro universitario
    telefono INT,
    rol_id   INT NOT NULL REFERENCES rol(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    activo   BOOLEAN DEFAULT TRUE
);
```

### db_nucleo_fila

```sql
CREATE TABLE ticket (
    id                  SERIAL PRIMARY KEY,
    codigo_qr           VARCHAR(100),        -- NULL cuando está EXPIRADO
    estudiante_id       INT NOT NULL,
    registro_estudiante INT NOT NULL,
    posicion            INT NOT NULL,
    estado              VARCHAR(20) DEFAULT 'ESPERANDO'
                        CHECK (estado IN ('ESPERANDO','ATENDIENDO','ATENDIDO','EXPIRADO')),
    ventanilla_id       INT,
    cajero_id           INT,
    fecha_creacion      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### db_ventanilla

```sql
CREATE TABLE ventanilla (
    id          SERIAL PRIMARY KEY,
    etiqueta    VARCHAR(50) NOT NULL,
    descripcion VARCHAR(200),
    activa      BOOLEAN DEFAULT TRUE
);

CREATE TABLE ventanilla_estado (
    id            SERIAL PRIMARY KEY,
    ventanilla_id INT NOT NULL,
    encargado_id  INT NOT NULL,
    estado        BOOLEAN DEFAULT TRUE,   -- TRUE = sesión abierta
    apertura      TIME DEFAULT CURRENT_TIME,
    cierre        TIME
);
```

---

## 10. Control de Acceso (RBAC)

El Gateway implementa una **whitelist por rol** (estrategia más segura que una blacklist). Lo que no está explícitamente permitido, está denegado.

| Ruta | Rol 1 (Estudiante) | Rol 2 (Cajero) | Rol 3 (Admin) |
|---|:---:|:---:|:---:|
| `POST /usuario/registro` | ✅ | — | ✅ |
| `POST /usuario/login` | ✅ | ✅ | ✅ |
| `GET /usuario/obtener_usuarios` | ❌ 403 | ❌ 403 | ✅ |
| `PATCH /usuario/usuarios/{id}` | ❌ 403 | ❌ 403 | ✅ |
| `DELETE /usuario/usuarios/{id}` | ❌ 403 | ❌ 403 | ✅ |
| `POST /fila/tomar_ticket` | ✅ | ❌ 403 | ✅ |
| `GET /fila/estado/{id}` | ✅ | ✅ | ✅ |
| `POST /fila/llamar_siguiente` | ❌ 403 | ✅ | ✅ |
| `POST /fila/validar_qr` | ❌ 403 | ✅ | ✅ |
| `POST /fila/completar_atencion` | ❌ 403 | ✅ | ✅ |
| `POST /fila/expirar_ticket` | ❌ 403 | ✅ | ✅ |
| `GET /ventanilla/disponibles` | ❌ 403 | ✅ | ✅ |
| `POST /ventanilla/abrir` | ❌ 403 | ✅ | ✅ |
| `POST /ventanilla/cerrar` | ❌ 403 | ✅ | ✅ |
| `POST /ventanilla/crear` | ❌ 403 | ❌ 403 | ✅ |
| `DELETE /ventanilla/eliminar/{id}` | ❌ 403 | ❌ 403 | ✅ |
| `GET /ventanilla/listar` | ❌ 403 | ❌ 403 | ✅ |

El rol se transporta en el header `X-Rol-Id`. El Gateway usa `int(self.headers.get('X-Rol-Id', '1'))`, es decir, el default en ausencia del header es rol 1 (Estudiante), que es el más restrictivo y por tanto seguro.

---

## 11. Estados del Ticket

```
                    ┌─────────────┐
                    │  ESPERANDO  │◀── creado al solicitar turno
                    └──────┬──────┘
                           │ cajero llama_siguiente()
                           ▼
                    ┌─────────────┐
                    │ ATENDIENDO  │◀── ticket vinculado a ventanilla y cajero
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │ QR validado             │ cajero llama siguiente sin
              │ + completar_atencion()  │ completar (estudiante no llegó)
              ▼                         ▼
       ┌────────────┐           ┌────────────┐
       │  ATENDIDO  │           │  EXPIRADO  │
       │ (fin OK)   │           │ QR = NULL  │
       └────────────┘           └────────────┘
                                      │
                                      │ estudiante debe sacar nuevo ticket
                                      ▼
                               (nuevo ESPERANDO)
```

La tabla `obtener_ticket_activo_estudiante` busca estados `(ESPERANDO, ATENDIENDO, EXPIRADO)` y excluye `ATENDIDO`. Esto permite que el estudiante vea el mensaje de expiración antes de poder sacar un nuevo ticket, pero que no vea tickets ya completados de días anteriores (filtra por `fecha_creacion::date = CURRENT_DATE`).

---

## 12. Cómo Levantar el Proyecto

### Requisitos

- Docker Desktop (o Docker Engine + Docker Compose)
- Puerto 80 libre (frontend)
- Puerto 8000 libre (gateway)
- Puertos 8001, 8002, 8003 libres (MS, opcionales para debug directo)

### Primer arranque

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd Parcial1

# 2. Levantar todo el sistema
docker-compose up --build

# Esto construye los 8 contenedores y los conecta en ficct_red_verano.
# Los healthchecks garantizan que cada MS espera a que su BD esté lista.
# Las BDs se inicializan automáticamente (CREATE TABLE IF NOT EXISTS).

# 3. Acceder al sistema
# Frontend: http://localhost
# Gateway:  http://localhost:8000 (para pruebas con Postman o curl)
```

### Usuario administrador inicial

El sistema crea automáticamente un admin al inicializar `db_usuario`:

```
Registro: 221043721
Password: (definido en repository.py, campo password inicial)
```

### Comandos útiles

```bash
# Ver logs de un servicio específico
docker-compose logs -f ms_nucleo_fila

# Reiniciar un servicio sin reconstruir
docker-compose restart ms_usuario

# Detener y eliminar todo (incluyendo volúmenes de BD)
docker-compose down -v

# Reconstruir un servicio tras cambios en el código
docker-compose up --build ms_nucleo_fila
```

> **Nota importante:** Si vas a actualizar desde una versión anterior del código que no tenía el estado `EXPIRADO` en el `CHECK constraint`, primero ejecuta `docker-compose down -v` para limpiar los volúmenes de las BDs. De lo contrario, la tabla antigua (sin la nueva constraint) causará errores al intentar insertar el estado `EXPIRADO`.

---

## 13. Decisiones de Diseño Relevantes

**¿Por qué Python puro sin frameworks?**  
Es un requisito académico deliberado. Implementar `do_GET`, `do_POST`, leer el body con `self.rfile.read(content_length)`, serializar con `json.dumps` y manejar `Content-Type` manualmente expone la mecánica real de HTTP que frameworks como Django o Flask abstraen. Esto cumple el objetivo de la materia de entender la comunicación a bajo nivel.

**¿Por qué no hay comunicación directa entre microservicios?**  
Para mantener el aislamiento completo. Si el MS Fila llamara al MS Ventanilla, crearía una dependencia de red implícita que dificultaría el despliegue independiente, el testing y la comprensión del sistema. El frontend como orquestador es más simple para un proyecto académico.

**¿Por qué una BD por microservicio?**  
Es el patrón canónico de microservicios ("Database per Service"). Garantiza que el esquema de una BD solo puede cambiar modificando su microservicio propietario, lo que fuerza el desacoplamiento real y no solo arquitectónico.

**¿Por qué polling y no WebSockets?**  
Los WebSockets requieren una infraestructura de conexiones persistentes (un servidor ASGI como Daphne, o un broker como Redis Pub/Sub). Para este sistema con carga baja y contexto académico, el polling cada 10 segundos es suficiente, más simple de implementar correctamente, y más fácil de depurar.

**¿Por qué el QR se genera en el backend?**  
El patrón `QR-{registro}-{posicion}` es predecible intencionalmente para facilitar la comprensión. En producción se usaría un hash criptográfico. Lo importante arquitecturalmente es que la **validación siempre ocurre en el backend** (MS Fila), nunca en el cliente, por lo que la predictibilidad del token no es un vector de ataque en este modelo donde el cajero escanea con su cámara y el backend verifica.

---

## 14. Requisitos del Sistema

### Funcionales

| ID | Descripción |
|---|---|
| RF-01 | Registro de estudiante con número de registro universitario único |
| RF-02 | Autenticación por registro + contraseña, solo usuarios activos |
| RF-03 | Control de acceso por roles (RBAC) en el Gateway |
| RF-04 | Gestión completa de cuentas (ABM) por el Administrador |
| RF-05 | Asignación de rol Cajero por el Administrador |
| RF-06 | Creación y baja lógica de ventanillas por el Administrador |
| RF-07 | Apertura y cierre de sesión de ventanilla por el Cajero |
| RF-08 | Generación de ticket con QR único por posición y día |
| RF-09 | Consulta de estado del turno en tiempo real (polling 10s) |
| RF-10 | Llamada al siguiente turno por orden de posición |
| RF-11 | Validación de identidad por escaneo QR con cámara |
| RF-12 | Cierre de atención (ATENDIDO) como estado final exitoso |
| RF-13 | Expiración automática de turno por inasistencia (EXPIRADO) |
| RF-14 | Notificaciones visuales por estado (ESPERANDO/ATENDIENDO/EXPIRADO) |

### No Funcionales

| ID | Descripción |
|---|---|
| RNF-01 | Arquitectura de microservicios con BD independiente por servicio |
| RNF-02 | Backend en Python puro sin frameworks web |
| RNF-03 | Contenerización completa con Docker y docker-compose |
| RNF-04 | Reinicio automático de contenedores (`restart: always`) |
| RNF-05 | Timeout de 10s en el Gateway con respuesta 503 si el MS no responde |
| RNF-06 | Comunicación interna por red Docker privada |
| RNF-07 | Control de acceso centralizado en el Gateway |
| RNF-08 | Compatibilidad CORS para consumo desde el puerto 80 |
| RNF-09 | Separación de capas dentro de cada MS (Handler / Controller / Repository) |
| RNF-10 | Integridad referencial en BD con FK y CHECK constraints |
| RNF-11 | Notificaciones toast no bloqueantes en el frontend |
| RNF-12 | Consultas de fila filtradas por fecha del día para rendimiento |

---

*Proyecto desarrollado para INF 423 — Ingeniería de Software II, FICCT, UAGRM.*