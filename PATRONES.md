# Patrones de Diseño — Segundo Parcial

> INF 423 — Ingeniería de Software II · FICCT · UAGRM

---

## Índice

1. [Chain of Responsibility → CU-01 Registro de Estudiante](#1-chain-of-responsibility--cu-01-registro-de-estudiante)
2. [State → CU-06 Flujo Completo de Atención del Cajero](#2-state--cu-06-flujo-completo-de-atención-del-cajero)

---

## 1. Chain of Responsibility → CU-01 Registro de Estudiante

### Teoría del patrón

**Propósito:** Evitar que el emisor de una solicitud conozca cuál objeto la procesará. Se encadena una serie de objetos receptores y la solicitud avanza por la cadena hasta que alguno la maneje o la rechace.

**Idea central:** Cada eslabón de la cadena hace UNA sola cosa. Si lo que recibe supera su responsabilidad o ya falló, pasa el control al siguiente o corta la cadena.

**Estructura genérica:**

```
┌──────────────────────────────────────────────────────────┐
│                    «abstract»                            │
│                  ValidacionHandler                       │
│  - _siguiente: ValidacionHandler                         │
│  + set_next(handler) → ValidacionHandler                 │
│  + handle(data, pasos_ok)  «abstracto»                   │
│  # _continuar(data, pasos_ok)                            │
└──────────────────────────────────────────────────────────┘
                           ▲
          ┌────────────────┼────────────────┐────────────────┐
          │                │                │                │
┌─────────────────┐ ┌─────────────┐ ┌──────────────┐ ┌──────────────────┐
│ CamposObliga-   │ │ FormatoEmail│ │ RegistroUnico│ │ RegistrarUsuario │
│ toriosHandler   │ │ Handler     │ │ Handler      │ │ Handler          │
│                 │ │             │ │              │ │                  │
│ Valida que      │ │ Valida      │ │ Consulta BD: │ │ Ejecuta INSERT   │
│ nombre, email,  │ │ formato de  │ │ ¿ya existe   │ │ en la BD.        │
│ registro y      │ │ email con   │ │ ese número   │ │ Handler terminal.│
│ password        │ │ regex       │ │ de registro? │ │                  │
│ no sean nulos   │ │             │ │              │ │                  │
└─────────────────┘ └─────────────┘ └──────────────┘ └──────────────────┘
```

**Regla clave:** Si un handler falla → corta la cadena y devuelve el error con `pasos_ok` hasta ese punto. Si pasa → agrega su nombre a `pasos_ok` y llama a `_continuar()` para ceder al siguiente.

---

### Qué cambió en el código

**Antes (Parcial 1):** `handle_registro()` en `controller.py` era un bloque único de validaciones anidadas. Si fallaba algo, el error era genérico y no indicaba en qué paso.

```python
# ANTES — todo mezclado en una función
def handle_registro(data):
    nombre = data.get('nombre')
    email  = data.get('email')
    ...
    if not all([nombre, email, registro, password]):
        return {"error": "Faltan datos obligatorios"}, 400
    # lógica de negocio mezclada con validaciones
    usuario_id = db_manager.registrar(...)
```

**Después (Parcial 2):** `handle_registro()` solo construye la cadena y la dispara. Cada validación vive en su propia clase.

```python
# DESPUÉS — controller solo ensambla la cadena
def handle_registro(data):
    h1 = CamposObligatoriosHandler()
    h2 = FormatoEmailHandler()
    h3 = RegistroUnicoHandler(db_manager)
    h4 = RegistrarUsuarioHandler(db_manager)

    h1.set_next(h2).set_next(h3).set_next(h4)
    return h1.handle(data, [])
```

**Archivos nuevos creados:**
```
ms_usuario/src/handlers/
  validacion_handler.py      ← clase abstracta (Handler)
  campos_handler.py          ← ConcreteHandler 1
  email_handler.py           ← ConcreteHandler 2
  registro_unico_handler.py  ← ConcreteHandler 3 (toca la BD)
  registrar_handler.py       ← ConcreteHandler 4, handler terminal
```

**Archivos modificados:**
```
ms_usuario/src/controller.py   ← handle_registro() usa la cadena
ms_usuario/src/repository.py   ← se agrega existe_registro()
frontend/src/pages/registro.html ← agrega visualización CoR
frontend/src/js/auth.js          ← anima la cadena con pasos_ok
```

El response ahora incluye el campo `pasos_ok` en todos los casos (éxito y error), que lista los nombres de los handlers que pasaron exitosamente. El frontend usa esa lista para animar cada nodo de la cadena visual.

---

### Diagrama Procedimental — CU-01

```
 FRONTEND                API GATEWAY            MS_USUARIO (:8001)
 registro.html
      │
      │  [Usuario llena el formulario y pulsa "Registrarse"]
      │
      │─── POST /usuario/registro ───────────────────────────────────►│
      │    Body: {nombre, email, registro, password, telefono}        │
      │    Header: X-Rol-Id: 1                                        │
      │                                                               │
      │                    ┌──── Verifica whitelist ────┐             │
      │                    │ rol 1 tiene permiso para   │             │
      │                    │ /usuario/registro → OK     │             │
      │                    └────────────────────────────┘             │
      │                                                               │
      │                    ─── Forwarding a ms_usuario:8001/registro ►│
      │                                                               │
      │                                              main.py          │
      │                                         do_POST('/registro')  │
      │                                                ▼              │
      │                                      controller.handle_registro(data)
      │                                                │
      │                                ┌───────────────▼───────────────┐
      │                                │   Construye la cadena CoR     │
      │                                │   h1 → h2 → h3 → h4           │
      │                                │   h1.handle(data, [])         │
      │                                └───────────────┬───────────────┘
      │                                                │
      │                                                ▼
      │                              ┌────────────────────────────────────┐
      │                              │  CamposObligatoriosHandler         │
      │                              │  ¿nombre, email, registro,         │
      │                              │   password presentes?              │
      │                              │                                    │
      │                              │  ✗ falta algo →                   │
      │                              │    return {error, pasos_ok:[]}, 400|
      │                              │                                    │
      │                              │  ✓ pasos_ok = ["campos"]           │
      │                              │    → _continuar() → h2             │
      │                              └────────────────────────────────────┘
      │                                                │
      │                                                ▼
      │                              ┌─────────────────────────────────┐
      │                              │  FormatoEmailHandler            │
      │                              │  regex: ^[a-zA-Z0-9._%+-]+@    │
      │                              │         [a-zA-Z0-9.-]+\.[a-z]{2,}$
      │                              │                                 │
      │                              │  ✗ no cumple →                  │
      │                              │    return {error, pasos_ok:     │
      │                              │    ["campos"]}, 400             │
      │                              │                                 │
      │                              │  ✓ pasos_ok = ["campos","email"]│
      │                              │    → _continuar() → h3          │
      │                              └─────────────────────────────────┘
      │                                                │
      │                                                ▼
      │                              ┌─────────────────────────────────┐
      │                              │  RegistroUnicoHandler           │
      │                              │  db.existe_registro(registro)   │
      │                              │  ──────────────────────────►    │
      │                              │  SELECT id FROM usuario         │  db_usuario
      │                              │  WHERE registro = ?             │◄────────────┐
      │                              │  ◄──────────────────────────    │             │
      │                              │                                 │  PostgreSQL  │
      │                              │  ✗ ya existe →                  │             │
      │                              │    return {error, pasos_ok:     │             │
      │                              │    ["campos","email"]}, 400     │             │
      │                              │                                 │             │
      │                              │  ✓ pasos_ok = [...,             │             │
      │                              │    "registro_disponible"]       │             │
      │                              │    → _continuar() → h4          │             │
      │                              └─────────────────────────────────┘             │
      │                                                │                             │
      │                                                ▼                             │
      │                              ┌─────────────────────────────────┐             │
      │                              │  RegistrarUsuarioHandler        │             │
      │                              │  db.registrar(nombre, email,    │             │
      │                              │    password, registro,          │             │
      │                              │    telefono, rol_id=1)          │             │
      │                              │  ──────────────────────────►    │             │
      │                              │  INSERT INTO usuario (...)      │─────────────┘
      │                              │  RETURNING id                   │
      │                              │  ◄──────────────────────────    │
      │                              │                                 │
      │                              │  pasos_ok = ["campos","email",  │
      │                              │    "registro_disponible",       │
      │                              │    "registrado"]                │
      │                              │                                 │
      │                              │  return {                       │
      │                              │    "mensaje": "Usuario creado", │
      │                              │    "id": X,                     │
      │                              │    "pasos_ok": [...]            │
      │                              │  }, 201                         │
      │                              └─────────────────────────────────┘
      │
      │◄── {mensaje, id, pasos_ok} 201 ──────────────────────────────
      │
      │  [auth.js recibe pasos_ok y anima la cadena visual]
      │
      │  Nodo "Campos"   → ⬤ gris pulsando → ✓ verde
      │  Nodo "Email"    → ⬤ gris pulsando → ✓ verde
      │  Nodo "Registro" → ⬤ gris pulsando → ✓ verde
      │  Nodo "Crear"    → ⬤ gris pulsando → ✓ verde
      │
      │  [Redirección a login.html]
```

**Si falla en el handler 3 (registro duplicado):**
```
  Nodo "Campos"   → ✓ verde
  Nodo "Email"    → ✓ verde
  Nodo "Registro" → ✗ rojo  ← cadena cortada aquí
  Nodo "Crear"    → permanece gris (nunca se ejecutó)
```

---

## 2. State → CU-06 Flujo Completo de Atención del Cajero

### Teoría del patrón

**Propósito:** Permitir que un objeto altere su comportamiento cuando su estado interno cambia. Desde afuera, el objeto parece cambiar de clase.

**Idea central:** En lugar de usar `if estado == "ESPERANDO": ...` por todos lados, el objeto delega su comportamiento a una clase de estado. Cada estado sabe exactamente qué operaciones puede realizar y cuáles no. Las transiciones inválidas se rechazan en código, no solo en la BD.

**Estructura genérica:**

```
┌────────────────────────────────────┐
│           TicketContext            │
│  - ticket_id: int                  │
│  - db: FilaRepository              │
│  - _state: TicketState             │◄────── Estado actual
│                                    │
│  + transicionar(nuevo_estado)      │
│  + llamar(v_id, c_id)              │─┐
│  + validar_qr(qr, v_id)           │ │  Delegan al
│  + completar()                     │ │  estado actual
│  + expirar()                       │─┘
└────────────────────────────────────┘
                    │
                    │ usa
                    ▼
        ┌───────────────────────┐
        │    «abstract»         │
        │     TicketState       │
        │                       │
        │ + llamar()            │
        │ + validar_qr()        │
        │ + completar()         │
        │ + expirar()           │
        │ # _invalida(op)       │
        └───────────────────────┘
                    ▲
     ┌──────────────┼──────────────┬──────────────┐
     │              │              │              │
┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐
│ Estado   │ │  Estado   │ │ Estado  │ │ Estado  │
│Esperando │ │Atendiendo │ │Atendido │ │Expirado │
│          │ │           │ │         │ │         │
│llamar ✓  │ │llamar ✗   │ │todo ✗   │ │todo ✗   │
│validar✗  │ │validar ✓  │ │(terminal│ │(terminal│
│completar✗│ │completar✓ │ │)        │ │)        │
│expirar ✗ │ │expirar ✓  │ │         │ │         │
└──────────┘ └───────────┘ └──────────┘ └──────────┘
```

**Máquina de estados del ticket:**
```
                   llamar()
  [ESPERANDO] ──────────────► [ATENDIENDO]
                                    │
                        completar() │ expirar()
                                    │
                        ┌───────────┴────────────┐
                        ▼                        ▼
                  [ATENDIDO ✓]            [EXPIRADO ✗]
                  (terminal)              (terminal)
```

---

### Qué cambió en el código

**Antes (Parcial 1):** Las transiciones de estado eran condiciones `AND estado = 'ATENDIENDO'` directamente en el SQL de la repository. No había ningún control en el código Python — si la capa SQL fallaba, el error era un booleano sin contexto.

```python
# ANTES — el "estado" solo lo controlaba la BD
def handle_completar(data):
    ticket_id = data.get('ticket_id')
    ok = db.completar_atencion(ticket_id)  # UPDATE WHERE estado='ATENDIENDO'
    if ok:
        return {"mensaje": "Atención completada"}, 200
    return {"error": "Ticket no encontrado o ya fue completado"}, 404
    # → No distingue si falló por "no existe" o por "estado incorrecto"
```

**Después (Parcial 2):** El controller carga el ticket, crea el `TicketContext` con el estado real, y delega. El estado decide si la operación es válida. Si no lo es, devuelve un error 409 con mensaje claro antes de tocar la BD.

```python
# DESPUÉS — State Pattern controla las transiciones
def handle_completar(data):
    ticket = db.obtener_ticket_por_id(ticket_id)       # carga estado actual
    context = TicketContext(ticket, db)                 # instancia el estado correcto
    resultado = context.completar()                     # delega al estado

    if isinstance(resultado, tuple):   # EstadoAtendido/Expirado → _invalida()
        return resultado               # → {"error": "Transición inválida..."}, 409
    if resultado:
        return {"mensaje": "Atención completada exitosamente"}, 200
```

**Archivos nuevos creados:**
```
ms_nucleo_fila/src/estados/
  ticket_state.py        ← clase abstracta (State)
  estado_esperando.py    ← ConcreteState: solo permite llamar()
  estado_atendiendo.py   ← ConcreteState: permite validar_qr, completar, expirar
  estado_atendido.py     ← ConcreteState terminal: rechaza todo
  estado_expirado.py     ← ConcreteState terminal: rechaza todo
ms_nucleo_fila/src/
  ticket_context.py      ← Context: mantiene _state y delega operaciones
```

**Archivos modificados:**
```
ms_nucleo_fila/src/controller.py   ← handle_llamar, handle_validar_qr,
                                      handle_completar, handle_expirar
                                      usan TicketContext
ms_nucleo_fila/src/repository.py   ← se agregan 4 métodos de consulta granular:
                                      obtener_siguiente_esperando()
                                      transicionar_a_atendiendo()
                                      obtener_ticket_por_id()
                                      obtener_ticket_atendiendo_ventanilla()
frontend/src/js/estudiante.js      ← agrega diagrama de máquina de estados visual
frontend/src/css/global.css        ← estilos del diagrama
```

---

### Diagrama Procedimental — CU-06

El CU-06 cubre 4 operaciones del cajero. Se muestran las 3 principales.

---

#### Operación 1: Llamar al siguiente (ESPERANDO → ATENDIENDO)

```
 FRONTEND                API GATEWAY          MS_NUCLEO_FILA (:8002)
 atencion.html
 cajero.js
      │
      │  [Cajero pulsa "Llamar Siguiente"]
      │  llamarSiguiente()
      │
      │─── POST /fila/llamar_siguiente ────────────────────────────►│
      │    Body: {ventanilla_id: 2, cajero_id: 5}                   │
      │    Header: X-Rol-Id: 2                                       │
      │                                                              │
      │                    ┌──── RBAC ────┐                          │
      │                    │ rol 2 tiene  │                          │
      │                    │ permiso → OK │                          │
      │                    └──────────────┘                          │
      │                    ── Forwarding a ms_nucleo_fila:8002 ─────►│
      │                                                              │
      │                                         controller.handle_llamar(data)
      │                                                    │
      │                                     db.obtener_siguiente_esperando()
      │                                                    │
      │                                     SELECT id, posicion, estado, codigo_qr
      │                                     FROM ticket                 db_nucleo_fila
      │                                     WHERE estado='ESPERANDO'  ◄──────────────┐
      │                                     AND fecha=HOY              │              │
      │                                     ORDER BY posicion LIMIT 1  │  PostgreSQL  │
      │                                                    │           │              │
      │                                     siguiente = {id:7,         │              │
      │                                       estado:"ESPERANDO",...}  │              │
      │                                                    │           │              │
      │                          ┌─────────────────────────▼──────────────────────┐  │
      │                          │         TicketContext(siguiente, db)            │  │
      │                          │         → _state = EstadoEsperando()           │  │
      │                          └─────────────────────────┬──────────────────────┘  │
      │                                                    │                          │
      │                                          context.llamar(2, 5)                │
      │                                                    │                          │
      │                          ┌─────────────────────────▼──────────────────────┐  │
      │                          │         EstadoEsperando.llamar()               │  │
      │                          │                                                 │  │
      │                          │  ✓ llamar() ES válido desde ESPERANDO           │  │
      │                          │                                                 │  │
      │                          │  db.transicionar_a_atendiendo(7, 2, 5)         │  │
      │                          │  UPDATE ticket                                  │──┘
      │                          │    SET estado='ATENDIENDO',                    │
      │                          │        ventanilla_id=2, cajero_id=5            │
      │                          │    WHERE id=7 AND estado='ESPERANDO'           │
      │                          │  RETURNING id, registro, codigo_qr, posicion   │
      │                          │                                                 │
      │                          │  context.transicionar("ATENDIENDO")            │
      │                          │  → _state = EstadoAtendiendo()                 │
      │                          └─────────────────────────────────────────────────┘
      │
      │◄── {atendiendo_a: {id:7, registro:221043XXX, posicion:3}} 200
      │
      │  ticketActual = data.atendiendo_a
      │  iniciarEscaner()   → activa cámara
```

---

#### Operación 2: Completar atención (ATENDIENDO → ATENDIDO)

```
 FRONTEND                API GATEWAY          MS_NUCLEO_FILA (:8002)
 cajero.js
      │
      │  [QR validado, cajero llama completarAtencion()]
      │
      │─── POST /fila/completar_atencion ──────────────────────────►│
      │    Body: {ticket_id: 7}                                      │
      │                                                              │
      │                                         controller.handle_completar(data)
      │                                                    │
      │                                     db.obtener_ticket_por_id(7)
      │                                     SELECT ... FROM ticket    db_nucleo_fila
      │                                     WHERE id = 7            ◄──────────────┐
      │                                                    │          │  PostgreSQL  │
      │                                     ticket = {id:7,           │              │
      │                                       estado:"ATENDIENDO",...}│              │
      │                                                    │           │              │
      │                          ┌─────────────────────────▼────────────────────┐   │
      │                          │       TicketContext(ticket, db)              │   │
      │                          │       → _state = EstadoAtendiendo()         │   │
      │                          └─────────────────────────┬────────────────────┘   │
      │                                                    │                         │
      │                                          context.completar()                │
      │                                                    │                         │
      │                          ┌─────────────────────────▼────────────────────┐   │
      │                          │       EstadoAtendiendo.completar()           │   │
      │                          │                                               │   │
      │                          │  ✓ completar() ES válido desde ATENDIENDO    │   │
      │                          │                                               │   │
      │                          │  db.completar_atencion(7)                    │   │
      │                          │  UPDATE ticket SET estado='ATENDIDO'          │───┘
      │                          │  WHERE id=7 AND estado='ATENDIENDO'          │
      │                          │                                               │
      │                          │  context.transicionar("ATENDIDO")            │
      │                          │  → _state = EstadoAtendido()                 │
      │                          └───────────────────────────────────────────────┘
      │
      │◄── {mensaje: "Atención completada exitosamente"} 200
      │
      │  [Estudiante en su próximo polling (10s):
      │   estado ATENDIDO no aparece en consulta → "Sin tickets activos"]
```

---

#### Transición inválida — cómo el patrón la bloquea

```
  ESCENARIO: alguien intenta completar un ticket ya ATENDIDO
             (doble clic, replay de request, etc.)

      │─── POST /fila/completar_atencion {ticket_id: 7} ───────────►│
      │                                                              │
      │                                     db.obtener_ticket_por_id(7)
      │                                     ticket = {estado: "ATENDIDO"}
      │                                                    │
      │                          ┌─────────────────────────▼────────────────┐
      │                          │   TicketContext(ticket, db)              │
      │                          │   → _state = EstadoAtendido()           │
      │                          └─────────────────────────┬────────────────┘
      │                                                    │
      │                                          context.completar()
      │                                                    │
      │                          ┌─────────────────────────▼────────────────┐
      │                          │      EstadoAtendido.completar()          │
      │                          │                                           │
      │                          │  ✗ completar() NO es válido en ATENDIDO  │
      │                          │  → _invalida("completar")                │
      │                          │  → return {                              │
      │                          │      "error": "Transición inválida:      │
      │                          │       'completar' no está permitido      │
      │                          │       en estado ATENDIDO"                │
      │                          │    }, 409                                │
      │                          └───────────────────────────────────────────┘
      │
      │◄── {error: "Transición inválida..."} 409
      │
      │  [La BD nunca fue tocada — el patrón lo rechazó en código]
```

---

#### Operación 3: Expirar ticket (ATENDIENDO → EXPIRADO)

```
  Se activa automáticamente cuando el cajero llama "Siguiente"
  sin haber completado el ticket anterior (estudiante no se presentó).

  cajero.js — llamarSiguiente():
    if (ticketActual) await expirarTicketActual()

      │─── POST /fila/expirar_ticket {ticket_id: 7} ───────────────►│
      │                                                              │
      │                                     db.obtener_ticket_por_id(7)
      │                                     ticket = {estado: "ATENDIENDO"}
      │                                                    │
      │                          ┌─────────────────────────▼────────────────┐
      │                          │   TicketContext → EstadoAtendiendo()     │
      │                          └─────────────────────────┬────────────────┘
      │                                                    │
      │                                          context.expirar()
      │                                                    │
      │                          ┌─────────────────────────▼────────────────┐
      │                          │    EstadoAtendiendo.expirar()            │
      │                          │                                           │
      │                          │  ✓ expirar() ES válido desde ATENDIENDO  │
      │                          │                                           │
      │                          │  db.expirar_ticket(7)                    │
      │                          │  UPDATE ticket                            │
      │                          │    SET estado='EXPIRADO',                │
      │                          │        codigo_qr=NULL                    │
      │                          │    WHERE id=7 AND estado='ATENDIENDO'    │
      │                          │                                           │
      │                          │  context.transicionar("EXPIRADO")        │
      │                          │  → _state = EstadoExpirado()             │
      │                          └───────────────────────────────────────────┘
      │
      │◄── {mensaje: "Ticket expirado."} 200
      │
      │  [Estudiante en su próximo polling ve estado EXPIRADO
      │   → diagrama State se ilumina en rojo → botón "Sacar Nuevo Ticket"]
```

---

## Visual en el Frontend

### Chain of Responsibility (registro.html)

Al pulsar "Registrarse", los 4 nodos aparecen pulsando en gris. El backend responde con `pasos_ok` y el frontend los anima uno por uno:

```
  Éxito total:
  [✓ Campos] ──── [✓ Email] ──── [✓ Registro] ──── [✓ Crear]
   (verde)          (verde)         (verde)           (verde)

  Falla en email:
  [✓ Campos] ──── [✗ Email]      [· Registro]        [· Crear]
   (verde)          (rojo)          (gris, nunca        (gris, nunca
                    cadena          ejecutado)           ejecutado)
                    cortada
```

### State Pattern (dashboard.html — vista estudiante)

Diagrama siempre visible debajo del ticket, el nodo activo pulsa:

```
  Estado ESPERANDO:          Estado ATENDIENDO:
  [● ESPERANDO] → [ATENDIENDO] → [ATENDIDO ✓]     [ESPERANDO] → [● ATENDIENDO] → [ATENDIDO ✓]
                       ↓                                                ↓
                  [EXPIRADO ✗]                                    [EXPIRADO ✗]

  Estado EXPIRADO:
  [ESPERANDO] → [ATENDIENDO] → [ATENDIDO ✓]
                     ↓
               [● EXPIRADO ✗]     ← rojo pulsando
```

El círculo `●` indica el estado activo con color y animación pulse.

---

*Segundo Parcial — INF 423 Ingeniería de Software II · FICCT · UAGRM*
