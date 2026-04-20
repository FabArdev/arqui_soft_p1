import psycopg2
import os
import time


class FilaRepository:

    def __init__(self):
        self.host     = os.getenv("DB_HOST", "db_fila")
        self.database = os.getenv("DB_NAME", "db_fila")
        self.user     = os.getenv("DB_USER", "admin")
        self.password = os.getenv("DB_PASS", "admin123")

    def get_connection(self):
        retries = 5
        while retries > 0:
            try:
                return psycopg2.connect(
                    host=self.host,
                    database=self.database,
                    user=self.user,
                    password=self.password
                )
            except psycopg2.OperationalError:
                retries -= 1
                print(f"[REPO_FILA] Esperando DB... reintentos restantes: {retries}")
                time.sleep(3)
        raise Exception("No se pudo conectar a la base de datos después de varios intentos")

    def inicializar_db(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ticket (
                id                   SERIAL PRIMARY KEY,
                codigo_qr            VARCHAR(100) NOT NULL,
                estudiante_id        INT NOT NULL,
                registro_estudiante  INT NOT NULL,
                posicion             INT NOT NULL,
                -- CORREGIDO: Se añade 'ATENDIDO' como estado final válido.
                -- Sin este estado, los tickets quedaban bloqueados en 'ATENDIENDO'
                -- e impedían al estudiante tomar nuevos tickets.
                estado               VARCHAR(20) DEFAULT 'ESPERANDO'
                                     CHECK (estado IN ('ESPERANDO', 'ATENDIENDO', 'ATENDIDO', 'EXPIRADO')),
                ventanilla_id        INT,
                cajero_id            INT,
                fecha_creacion       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("[REPO_FILA] Base de datos inicializada correctamente.")

    def crear_ticket(self, estudiante_id, registro):
        conn = self.get_connection()
        cur = conn.cursor()
        # La posición se calcula solo entre tickets del día actual
        cur.execute("""
            SELECT COALESCE(MAX(posicion), 0) + 1
            FROM ticket
            WHERE fecha_creacion::date = CURRENT_DATE;
        """)
        nueva_pos = cur.fetchone()[0]
        codigo_qr = f"QR-{registro}-{nueva_pos}"

        cur.execute("""
            INSERT INTO ticket (estudiante_id, registro_estudiante, posicion, codigo_qr)
            VALUES (%s, %s, %s, %s)
            RETURNING id, posicion, codigo_qr;
        """, (estudiante_id, registro, nueva_pos, codigo_qr))

        datos = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {"id": datos[0], "posicion": datos[1], "codigo_qr": datos[2]}

    def obtener_ticket_activo_estudiante(self, estudiante_id):
        conn = self.get_connection()
        cur = conn.cursor()
        # Devuelve el ticket más reciente del día en estados visibles:
        # ESPERANDO y ATENDIENDO = activos normales
        # EXPIRADO = llamado pero no presentado — se muestra al estudiante
        #            para que sepa que debe sacar uno nuevo
        # ATENDIDO queda excluido (flujo completado, no hay nada que mostrar)
        cur.execute("""
            SELECT id, posicion, estado, codigo_qr, ventanilla_id
            FROM ticket
            WHERE estudiante_id = %s
              AND estado IN ('ESPERANDO', 'ATENDIENDO', 'EXPIRADO')
              AND fecha_creacion::date = CURRENT_DATE
            ORDER BY fecha_creacion DESC
            LIMIT 1;
        """, (estudiante_id,))
        res = cur.fetchone()
        cur.close()
        conn.close()
        if res:
            return {
                "id": res[0],
                "posicion": res[1],
                "estado": res[2],
                "codigo_qr": res[3],
                "ventanilla_id": res[4]
            }
        return None

    def llamar_siguiente(self, ventanilla_id, cajero_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id FROM ticket
            WHERE estado = 'ESPERANDO'
              AND fecha_creacion::date = CURRENT_DATE
            ORDER BY posicion ASC
            LIMIT 1;
        """)
        ticket = cur.fetchone()
        if not ticket:
            cur.close()
            conn.close()
            return None

        cur.execute("""
            UPDATE ticket
            SET estado = 'ATENDIENDO',
                ventanilla_id = %s,
                cajero_id     = %s
            WHERE id = %s
            RETURNING id, registro_estudiante, codigo_qr, posicion;
        """, (ventanilla_id, cajero_id, ticket[0]))

        datos = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {
            "id":       datos[0],
            "registro": datos[1],
            "qr":       datos[2],
            "posicion": datos[3]
        }

    def contar_delante(self, posicion):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM ticket
            WHERE estado = 'ESPERANDO'
              AND posicion < %s
              AND fecha_creacion::date = CURRENT_DATE;
        """, (posicion,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count

    def validar_ticket_qr(self, codigo_qr, ventanilla_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, registro_estudiante FROM ticket
            WHERE codigo_qr    = %s
              AND ventanilla_id = %s
              AND estado        = 'ATENDIENDO';
        """, (codigo_qr, ventanilla_id))
        res = cur.fetchone()
        cur.close()
        conn.close()
        if res:
            return {"id": res[0], "registro": res[1]}
        return None

    def expirar_ticket(self, ticket_id):
        """
        Marca el ticket como EXPIRADO y borra su codigo_qr.
        Se usa cuando el cajero llama a alguien y esa persona no se presenta
        a tiempo para escanear su QR. El ticket queda inválido y el estudiante
        deberá sacar un ticket nuevo para volver a la fila.
        """
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE ticket
            SET estado    = 'EXPIRADO',
                codigo_qr = NULL
            WHERE id     = %s
              AND estado = 'ATENDIENDO';
        """, (ticket_id,))
        conn.commit()
        affected = cur.rowcount > 0
        cur.close()
        conn.close()
        return affected

    def completar_atencion(self, ticket_id):
        """
        NUEVO MÉTODO: Transiciona el ticket de ATENDIENDO → ATENDIDO.
        Es el estado final del flujo. Sin esto, el estudiante no podía
        tomar un nuevo ticket porque el sistema lo veía como aún activo.
        """
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE ticket
            SET estado = 'ATENDIDO'
            WHERE id     = %s
              AND estado = 'ATENDIENDO';
        """, (ticket_id,))
        conn.commit()
        affected = cur.rowcount > 0
        cur.close()
        conn.close()
        return affected