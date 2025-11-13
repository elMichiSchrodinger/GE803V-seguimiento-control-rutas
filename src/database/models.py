# src/database/models.py
"""
Definición de las tablas de la base de datos SQLite.
"""

def create_tables(conn):
    """
    Crea todas las tablas si no existen.
    """
    cursor = conn.cursor()

    # 1. Vehículos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vehiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            placa TEXT UNIQUE NOT NULL,
            marca TEXT,
            modelo TEXT,
            capacidad_kg REAL,
            activo BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Rutas planificadas (¡una sola vez, con geometria!)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rutas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            vehiculo_id INTEGER NOT NULL,
            estado TEXT CHECK(estado IN ('programada', 'en_progreso', 'completada', 'cancelada')) DEFAULT 'programada',
            distancia_planificada_m INTEGER,
            duracion_planificada_s INTEGER,
            geometria TEXT,  -- ← Columna añadida
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            started_at TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (vehiculo_id) REFERENCES vehiculos(id) ON DELETE RESTRICT
        )
    ''')

    # 3. Puntos de la ruta
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS puntos_ruta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ruta_id INTEGER NOT NULL,
            tipo TEXT CHECK(tipo IN ('origen', 'waypoint', 'destino')) NOT NULL,
            orden INTEGER NOT NULL,
            direccion TEXT NOT NULL,
            lat REAL,
            lng REAL,
            nombre_lugar TEXT,
            FOREIGN KEY (ruta_id) REFERENCES rutas(id) ON DELETE CASCADE
        )
    ''')

    # 4. Eventos de trazabilidad
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eventos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ruta_id INTEGER NOT NULL,
            tipo_evento TEXT CHECK(tipo_evento IN (
                'salida_almacen',
                'llegada_punto',
                'salida_punto',
                'entrega_confirmada',
                'desviacion_ruta',
                'parada_no_planificada',
                'fin_ruta'
            )) NOT NULL,
            punto_ruta_id INTEGER,
            lat REAL,
            lng REAL,
            timestamp_evento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            observaciones TEXT,
            FOREIGN KEY (ruta_id) REFERENCES rutas(id) ON DELETE CASCADE,
            FOREIGN KEY (punto_ruta_id) REFERENCES puntos_ruta(id) ON DELETE SET NULL
        )
    ''')

    conn.commit()