# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Start everything:**
```bash
docker compose up --build
```

**Rebuild a single service after code changes:**
```bash
docker compose up --build ms_nucleo_fila
docker compose up --build api_gateway
```

**Stop and remove containers:**
```bash
docker compose down
```

**View logs for a specific service:**
```bash
docker compose logs -f ms_usuario
docker compose logs -f api_gateway
```

**Reset a service's database (deletes all data):**
```bash
# Stop the service, delete its db folder, restart
docker compose down
rm -rf backend/microservios/ms_nucleo_fila/db/*
docker compose up --build ms_nucleo_fila
```

There are no tests or linters configured in this project.

## Architecture

This is a university queue management system (sistema de turnos/filas) composed of entirely **stdlib-only Python microservices** — no Flask, FastAPI, or any web framework. Each service uses `http.server.BaseHTTPRequestHandler` directly.

```
Browser (port 80)
  └─► nginx (frontend static files)
        └─► API Gateway :8000  (RBAC + reverse proxy)
              ├─► ms_usuario    :8001  ── db_usuario    (PostgreSQL)
              ├─► ms_nucleo_fila :8002 ── db_nucleo_fila (PostgreSQL)
              └─► ms_ventanilla  :8003 ── db_ventanilla  (PostgreSQL)
```

### Request flow

1. Frontend sends requests to `http://localhost:8000` with `X-Rol-Id` header set from `localStorage`.
2. The API Gateway checks RBAC via a whitelist (`RUTAS_PERMITIDAS` in `backend/api_geteway/src/main.py`) then strips the service prefix and proxies to the correct microservice.
3. Path routing: `/usuario/*` → ms_usuario, `/fila/*` → ms_nucleo_fila, `/ventanilla/*` → ms_ventanilla.

### Microservice pattern

Every microservice has the same 3-file structure under `src/`:
- `main.py` — HTTP routing (maps URL paths to controller calls)
- `controller.py` — Business logic; returns `(dict, int)` tuples of (response, HTTP status)
- `repository.py` — Direct SQL via `psycopg2`; creates tables on startup via `inicializar_db()`

Database schemas are created automatically when each microservice starts. No migrations tool is used.

### RBAC

The gateway enforces role-based access via the `X-Rol-Id` header (sent by the frontend from `localStorage`):
- `1` = estudiante — can register, login, take a ticket, check their status
- `2` = cajero — can open/close ventanilla sessions, call next in queue, validate QR, complete/expire tickets
- `3` = admin — unrestricted access

The seed admin account is seeded in `ms_usuario/src/repository.py:inicializar_db()` (registro `221043721`, password `123123`).

### Ticket lifecycle

Tickets in `ms_nucleo_fila` transition through these states:
```
ESPERANDO → ATENDIENDO → ATENDIDO   (normal flow)
                       → EXPIRADO   (student called but didn't show up)
```

`ATENDIDO` and `EXPIRADO` are terminal. A student can only take a new ticket once their previous one has reached a terminal state. QR codes are formatted as `QR-{registro}-{posicion}` and are cleared when a ticket expires.

Estimated wait time is computed as `personas_delante × 2.5 minutes` (hardcoded in `ms_nucleo_fila/src/controller.py`).

### Frontend

Vanilla HTML/JS/CSS served by nginx — no build step, no framework. All API calls go through `frontend/src/js/api.js:apiFetch()`, which attaches the `X-Rol-Id` header from `localStorage`. Session state (user id, name, role, registro) is stored entirely in `localStorage`; there are no server-side sessions or JWT tokens.

Passwords are stored and compared in plaintext.

---

## Segundo Parcial — Patrones de Diseño

Se implementaron dos patrones de diseño GoF. La documentación completa (teoría, diagramas genéricos y diagramas procedimentales) está en `PATRONES.md`.

### Patrón 1: Chain of Responsibility → CU-01 (Registro de Estudiante)

**Microservicio:** `ms_usuario`

La función `handle_registro()` ya no valida inline. Construye una cadena de 4 handlers y la dispara:

```
CamposObligatoriosHandler → FormatoEmailHandler → RegistroUnicoHandler → RegistrarUsuarioHandler
```

Cada handler hace una sola validación. Si falla, corta la cadena y devuelve `{"error": "...", "pasos_ok": [...]}`. Si pasa, agrega su nombre a `pasos_ok` y cede al siguiente. El campo `pasos_ok` en el response permite al frontend animar visualmente qué handlers pasaron y dónde se cortó la cadena.

**Archivos nuevos:**
```
ms_usuario/src/handlers/
  validacion_handler.py       ← clase abstracta (set_next, handle, _continuar)
  campos_handler.py
  email_handler.py
  registro_unico_handler.py   ← consulta DB con existe_registro()
  registrar_handler.py        ← handler terminal, hace el INSERT
```

**Archivos modificados:** `controller.py` (handle_registro), `repository.py` (+ existe_registro), `registro.html`, `auth.js`.

### Patrón 2: State → CU-06 (Flujo Completo de Atención del Cajero)

**Microservicio:** `ms_nucleo_fila`

El ciclo de vida del ticket (ESPERANDO → ATENDIENDO → ATENDIDO/EXPIRADO) está ahora controlado por clases de estado. El `TicketContext` mantiene el estado actual y delega cada operación. Los estados terminales (`EstadoAtendido`, `EstadoExpirado`) rechazan cualquier operación con HTTP 409 antes de tocar la BD.

```
TicketContext._state = EstadoEsperando | EstadoAtendiendo | EstadoAtendido | EstadoExpirado
```

El controller carga el ticket de la BD, construye el context con el estado real, y llama la operación. Si la transición es inválida, el estado la rechaza en código (no en SQL).

**Archivos nuevos:**
```
ms_nucleo_fila/src/estados/
  ticket_state.py       ← ABC con llamar(), validar_qr(), completar(), expirar(), _invalida()
  estado_esperando.py   ← solo permite llamar()
  estado_atendiendo.py  ← permite validar_qr(), completar(), expirar()
  estado_atendido.py    ← estado terminal, todo devuelve 409
  estado_expirado.py    ← estado terminal, todo devuelve 409
ms_nucleo_fila/src/
  ticket_context.py     ← Context: instancia el estado correcto y delega
```

**Archivos modificados:** `controller.py` (handle_llamar, handle_validar_qr, handle_completar, handle_expirar), `repository.py` (+ obtener_siguiente_esperando, transicionar_a_atendiendo, obtener_ticket_por_id, obtener_ticket_atendiendo_ventanilla), `estudiante.js`, `global.css`.

### Visual frontend de los patrones

- **CoR (registro.html):** 4 nodos circulares conectados por líneas. Al registrar, pulsan en gris → se animan verde ✓ o rojo ✗ según `pasos_ok`. La cadena se detiene visualmente en el handler que falló.
- **State (dashboard.html):** diagrama de máquina de estados debajo del ticket del estudiante. El nodo activo pulsa con el color del estado (amarillo=ESPERANDO, azul=ATENDIENDO, verde=ATENDIDO, rojo=EXPIRADO). Se actualiza con cada ciclo de polling (10s).
