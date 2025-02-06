import os
import psycopg2
from psycopg2 import pool
import logging
import time
import random
from contextlib import contextmanager

# Configuración del logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de la conexión
DATABASE_URL = "postgresql://inventario_282d_user:oPdeF5NBcJceRJCyemR5RL96qLEVjKT2@dpg-cuhackbtq21c73ce0n6g-a.oregon-postgres.render.com/inventario_282d"  # Reemplazar con tu URL de Render.com
MAX_RETRIES = 5
INITIAL_RETRY_DELAY = 1

def retry_with_exponential_backoff(func):
    def wrapper(*args, **kwargs):
        retry_delay = INITIAL_RETRY_DELAY
        for retry in range(MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                if retry == MAX_RETRIES - 1:
                    logging.error(f"Error después de {MAX_RETRIES} intentos: {str(e)}")
                    raise
                wait = retry_delay + random.uniform(0, 1)
                logging.warning(f"Error: {str(e)}. Reintentando en {wait:.2f} segundos...")
                time.sleep(wait)
                retry_delay *= 2
    return wrapper

class DatabasePool:
    _instance = None
    _pool = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = DatabasePool()
        return cls._instance

    def __init__(self):
        if self._pool is None:
            try:
                self._pool = psycopg2.pool.SimpleConnectionPool(
                    minconn=1,
                    maxconn=10,
                    dsn=DATABASE_URL
                )
                logging.info("Pool de conexiones creado exitosamente")
            except Exception as e:
                logging.error(f"Error al crear el pool de conexiones: {str(e)}")
                raise

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        finally:
            if conn:
                self._pool.putconn(conn)

@retry_with_exponential_backoff
def create_tables():
    db_pool = DatabasePool.get_instance()
    with db_pool.get_connection() as conn:
        with conn.cursor() as cursor:
            try:
                # Crear tablas una por una
                logging.info("Iniciando creación de tablas...")
                
                # Tabla usuarios
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id SERIAL PRIMARY KEY,
                        nombre TEXT UNIQUE,
                        password TEXT,
                        permisos TEXT,
                        mail TEXT UNIQUE,
                        nombre_usuario TEXT
                    )
                ''')
                logging.info("Tabla usuarios creada")

                # Tabla articulos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS articulos (
                        id SERIAL PRIMARY KEY,
                        codigo TEXT UNIQUE,
                        nombre TEXT UNIQUE,
                        cantidad INTEGER
                    )
                ''')
                logging.info("Tabla articulos creada")

                # Tabla movimientos
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS movimientos (
                        id SERIAL PRIMARY KEY,
                        articulo_id INTEGER REFERENCES articulos(id),
                        tipo TEXT,
                        cantidad INTEGER,
                        fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        observaciones TEXT,
                        usuario TEXT
                    )
                ''')
                logging.info("Tabla movimientos creada")

                # Tabla toners
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS toners (
                        id SERIAL PRIMARY KEY,
                        codigo TEXT UNIQUE,
                        nombre TEXT UNIQUE,
                        cantidad INTEGER
                    )
                ''')
                logging.info("Tabla toners creada")

                # Tabla movimientos_toner
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS movimientos_toner (
                        id SERIAL PRIMARY KEY,
                        toner_id INTEGER REFERENCES toners(id),
                        tipo TEXT,
                        cantidad INTEGER,
                        fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        observaciones TEXT,
                        usuario TEXT
                    )
                ''')
                logging.info("Tabla movimientos_toner creada")

                # Tabla reparaciones
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS reparaciones (
                        id SERIAL PRIMARY KEY,
                        reparacion_id INTEGER REFERENCES reparaciones(id),
                        tipo TEXT,
                        modelo TEXT,
                        SN TEXT,
                        motivo TEXT,
                        estado TEXT,
                        fecha TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        estado_actual TEXT
                    )
                ''')
                logging.info("Tabla reparaciones creada")

                conn.commit()
                logging.info("Todas las tablas creadas exitosamente")
            except Exception as e:
                conn.rollback()
                logging.error(f"Error al crear las tablas: {str(e)}")
                raise

@retry_with_exponential_backoff
def execute_query(query, parameters=()):
    query = query.replace('?', '%s')
    db_pool = DatabasePool.get_instance()
    with db_pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, parameters)
            conn.commit()

@retry_with_exponential_backoff
def fetch_data(query, parameters=()):
    query = query.replace('?', '%s')
    db_pool = DatabasePool.get_instance()
    with db_pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchall()

@retry_with_exponential_backoff
def fetch_one(query, parameters=()):
    query = query.replace('?', '%s')
    db_pool = DatabasePool.get_instance()
    with db_pool.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, parameters)
            return cursor.fetchone()

def create_default_admin():
    try:
        admin = fetch_data("SELECT * FROM usuarios WHERE nombre = %s", ("administrador",))
        if not admin:
            execute_query(
                """
                INSERT INTO usuarios 
                (nombre, password, permisos, mail, nombre_usuario) 
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    "administrador", 
                    "Frig20060920", 
                    "admin,ingresos,egresos,consulta_stock,historico_movimientos,agregar_articulos,admin_screen,egresos_toner",
                    "administrador@example.com",
                    "administrador"  # Agregamos el nombre_usuario igual al nombre
                )
            )
            logging.info("Usuario administrador por defecto creado")
        else:
            execute_query(
                """
                UPDATE usuarios 
                SET permisos = %s, 
                    nombre_usuario = %s 
                WHERE nombre = %s
                """,
                (
                    "admin,ingresos,egresos,consulta_stock,historico_movimientos,agregar_articulos,admin_screen,egresos_toner",
                    "administrador",  # Actualizamos también el nombre_usuario
                    "administrador"
                )
            )
            logging.info("Permisos del administrador actualizados")
    except Exception as e:
        logging.error(f"Error al crear/actualizar administrador: {str(e)}")
        raise

def init_db():
    try:
        logging.info("Iniciando inicialización de la base de datos")
        create_tables()
        check_and_add_column()  # Agregamos esta línea
        create_default_admin()
        logging.info("Base de datos inicializada correctamente")
    except Exception as e:
        logging.error(f"Error en la inicialización de la base de datos: {str(e)}")

# Función para verificar las tablas creadas
@retry_with_exponential_backoff
def list_tables():
    query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    """
    tables = fetch_data(query)
    logging.info("Tablas existentes en la base de datos:")
    for table in tables:
        logging.info(f"- {table[0]}")
    return tables
    
@retry_with_exponential_backoff
def check_and_add_column():
    try:
        # Primero verificamos si la columna existe
        check_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'usuarios' 
        AND column_name = 'nombre_usuario';
        """
        result = fetch_data(check_query)
        
        if not result:
            # Si la columna no existe, la agregamos
            execute_query(
                "ALTER TABLE usuarios ADD COLUMN nombre_usuario TEXT"
            )
            logging.info("Columna nombre_usuario agregada a la tabla usuarios")
            
            # Actualizamos los registros existentes
            execute_query(
                "UPDATE usuarios SET nombre_usuario = nombre WHERE nombre_usuario IS NULL"
            )
            logging.info("Registros existentes actualizados con nombre_usuario")
    except Exception as e:
        logging.error(f"Error al verificar/agregar columna nombre_usuario: {str(e)}")
        raise

# Inicializar la base de datos al inicio
logging.info("Iniciando la aplicación")
init_db()
# Verificar las tablas creadas
list_tables()