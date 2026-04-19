import psycopg2
import os
import time

class UsuarioRepository:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "db_usuario")
        self.database = os.getenv("DB_NAME", "db_usuario")
        self.user = os.getenv("DB_USER", "admin")
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
                print(f"Esperando a la DB... reintentos restantes: {retries}")
                time.sleep(3)
        raise Exception("No se pudo conectar a la base de datos después de varios intentos")

    def inicializar_db(self):
        conn = self.get_connection()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS rol (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(50) NOT NULL,
                descripcion VARCHAR(255)
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuario (
                id SERIAL PRIMARY KEY,
                nombre VARCHAR(100) NOT NULL,
                email VARCHAR(150) NOT NULL,
                password VARCHAR(255) NOT NULL,
                registro INT NOT NULL UNIQUE,
                telefono VARCHAR(20),
                activo BOOLEAN DEFAULT TRUE,
                rol_id INT NOT NULL,
                CONSTRAINT fk_rol FOREIGN KEY (rol_id) REFERENCES rol(id) 
                ON UPDATE CASCADE ON DELETE RESTRICT
            );
        """)

        cur.execute("SELECT COUNT(*) FROM rol;")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO rol (nombre) VALUES ('estudiante'), ('cajero'), ('admin');")
            print("Roles base insertados.")

        cur.execute("SELECT id FROM usuario WHERE registro = 221043721;")
        if not cur.fetchone():
            cur.execute("""
                INSERT INTO usuario (nombre, email, password, registro, telefono, rol_id)
                VALUES (%s, %s, %s, %s, %s, %s);
            """, ("Fabio Arnez", "fabioarnez2002f@gmail.com", "123123", 221043721, "64437475", 3))
            print("Usuario Administrador (Fabio) creado con éxito.")
        
        conn.commit()
        cur.close()
        conn.close()

    def registrar(self, nombre, email, password, registro, telefono, rol_id):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO usuario (nombre, email, password, registro, telefono, rol_id)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
            """, (nombre, email, password, registro, telefono, rol_id))
            nuevo_id = cur.fetchone()[0]
            conn.commit()
            return nuevo_id
        except Exception as e:
            print(f"Error en registro: {e}")
            return None
        finally:
            cur.close()
            conn.close()
            
    def verificar_credenciales(self, registro, password):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                SELECT id, nombre, email, rol_id, password 
                FROM usuario 
                WHERE registro = %s AND activo = TRUE;
            """, (registro,))
            user_data = cur.fetchone()
            
            if user_data and user_data[4] == password:
                return {
                    "id": user_data[0], "nombre": user_data[1],
                    "email": user_data[2], "rol_id": user_data[3]
                }
            return None
        except Exception as e:
            print(f"Error en login: {e}")
            return None
        finally:
            cur.close()
            conn.close()
    
    def obtener_usuario_por_id(self, user_id):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, nombre, email, registro, telefono, rol_id FROM usuario WHERE id = %s AND activo = TRUE;", (user_id,))
            u = cur.fetchone()
            if u:
                return {"id": u[0], "nombre": u[1], "email": u[2], "registro": u[3], "telefono": u[4], "rol_id": u[5]}
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
        finally:
            cur.close()
            conn.close()
    
    def obtener_usuarios(self):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, nombre, email, registro, telefono, rol_id FROM usuario WHERE activo = TRUE;")
            rows = cur.fetchall()
            return [{"id": r[0], "nombre": r[1], "email": r[2], "registro": r[3], "telefono": r[4], "rol_id": r[5]} for r in rows]
        except Exception as e:
            print(f"Error: {e}")
            return []
        finally:
            cur.close()
            conn.close()

    def actualizar_usuario(self, user_id, campos_dict:dict):
        if not campos_dict: return False
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            sets = ", ".join([f"{key} = %s" for key in campos_dict.keys()])
            valores = list(campos_dict.values())
            valores.append(user_id)
            cur.execute(f"UPDATE usuario SET {sets} WHERE id = %s", valores)
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            cur.close()
            conn.close()
            
    def desactivar_usuario(self, user_id):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE usuario SET activo = FALSE WHERE id = %s", (user_id,))
            conn.commit()
            return cur.rowcount > 0
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            cur.close()
            conn.close()