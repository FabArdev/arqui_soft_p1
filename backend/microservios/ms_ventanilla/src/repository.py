import psycopg2
import os
import time

class VentanillaRepository:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "db_ventanilla")
        self.database = os.getenv("DB_NAME", "db_ventanilla")
        self.user = os.getenv("DB_USER", "admin")
        self.password = os.getenv("DB_PASS", "admin123")

    def get_connection(self):
        retries = 5
        while retries > 0:
            try:
                return psycopg2.connect(host=self.host, database=self.database, user=self.user, password=self.password)
            except psycopg2.OperationalError:
                retries -= 1
                time.sleep(2)
        raise Exception("Error en db_ventanilla")

    def inicializar_db(self):
        conn = self.get_connection()
        cur = conn.cursor()
        # Tabla de Ventanillas
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ventanilla (
                id SERIAL PRIMARY KEY,
                etiqueta VARCHAR(20) NOT NULL,
                descripcion VARCHAR(255),
                activa BOOLEAN DEFAULT TRUE
            );
        """)
        # Tabla de Sesiones
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ventanilla_estado (
                id SERIAL PRIMARY KEY,
                fecha DATE DEFAULT CURRENT_DATE,
                apertura TIME DEFAULT CURRENT_TIME,
                cierre TIME,
                estado BOOLEAN DEFAULT TRUE,
                encargado_id INT NOT NULL,
                ventanilla_id INT NOT NULL,
                CONSTRAINT fk_ventanilla FOREIGN KEY (ventanilla_id) REFERENCES ventanilla(id)
            );
        """)
        conn.commit()
        cur.close()
        conn.close()

    # --- CRUD ADMIN ---
    def crear(self, etiqueta, desc):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO ventanilla (etiqueta, descripcion) VALUES (%s, %s) RETURNING id;", (etiqueta, desc))
        v_id = cur.fetchone()[0]
        conn.commit()
        return v_id

    def obtener_todas(self):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, etiqueta, descripcion FROM ventanilla WHERE activa = TRUE;")
        rows = cur.fetchall()
        return [{"id": r[0], "etiqueta": r[1], "descripcion": r[2]} for r in rows]

    def desactivar(self, v_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE ventanilla SET activa = FALSE WHERE id = %s;", (v_id,))
        conn.commit()
        return cur.rowcount > 0

    # --- LÓGICA CAJERO ---
    def obtener_disponibles(self):
        query = """
            SELECT v.id, v.etiqueta FROM ventanilla v
            WHERE v.activa = TRUE 
            AND v.id NOT IN (SELECT ventanilla_id FROM ventanilla_estado WHERE estado = TRUE);
        """
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        return [{"id": r[0], "etiqueta": r[1]} for r in rows]

    def abrir_sesion(self, v_id, u_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO ventanilla_estado (ventanilla_id, encargado_id) VALUES (%s, %s) RETURNING id;", (v_id, u_id))
        s_id = cur.fetchone()[0]
        conn.commit()
        return s_id

    def cerrar_sesion(self, v_id, u_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE ventanilla_estado SET estado = FALSE, cierre = CURRENT_TIME 
            WHERE ventanilla_id = %s AND encargado_id = %s AND estado = TRUE;
        """, (v_id, u_id))
        conn.commit()
        return cur.rowcount > 0