# src/database/db_manager.py
"""
Gestor de la base de datos SQLite para el aplicativo de rutas.
"""

import sqlite3
import os
from typing import Optional, List, Tuple, Dict, Any
from .models import create_tables

# Ruta de la base de datos (en la carpeta raíz del proyecto o junto al .exe)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "rutas.db")

def get_connection():
    """Devuelve una conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
    return conn

def init_db():
    """Inicializa la base de datos: crea el archivo y las tablas si no existen."""
    conn = get_connection()
    create_tables(conn)
    conn.close()
    crear_datos_ejemplo()

# === VEHÍCULOS ===

def crear_vehiculo(placa: str, marca: str = "", modelo: str = "", capacidad_kg: float = 0.0) -> int:
    """Crea un vehículo y devuelve su ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO vehiculos (placa, marca, modelo, capacidad_kg)
            VALUES (?, ?, ?, ?)
        ''', (placa, marca, modelo, capacidad_kg))
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        raise ValueError(f"Error al crear vehículo: placa '{placa}' ya existe.") from e
    finally:
        conn.close()

def obtener_vehiculos_activos() -> List[Dict[str, Any]]:
    """Devuelve una lista de vehículos activos."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehiculos WHERE activo = 1")
    filas = cursor.fetchall()
    conn.close()
    return [dict(fila) for fila in filas]

def actualizar_vehiculo(id_vehiculo: int, placa: str = None, marca: str = None, 
                       modelo: str = None, capacidad_kg: float = None, activo: bool = None):
    """Actualiza los datos de un vehículo."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Construir SET dinámicamente
    campos = []
    valores = []
    if placa is not None:
        campos.append("placa = ?")
        valores.append(placa)
    if marca is not None:
        campos.append("marca = ?")
        valores.append(marca)
    if modelo is not None:
        campos.append("modelo = ?")
        valores.append(modelo)
    if capacidad_kg is not None:
        campos.append("capacidad_kg = ?")
        valores.append(capacidad_kg)
    if activo is not None:
        campos.append("activo = ?")
        valores.append(1 if activo else 0)
    
    if not campos:
        conn.close()
        return
    
    valores.append(id_vehiculo)
    query = f"UPDATE vehiculos SET {', '.join(campos)} WHERE id = ?"
    cursor.execute(query, valores)
    conn.commit()
    conn.close()


def eliminar_vehiculo(id_vehiculo: int):
    """Elimina lógicamente un vehículo (lo marca como inactivo)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE vehiculos SET activo = 0 WHERE id = ?", (id_vehiculo,))
    conn.commit()
    conn.close()

# === RUTAS ===

def crear_ruta(nombre: str, vehiculo_id: int, distancia_m: int = None, 
               duracion_s: int = None, geometria: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO rutas (nombre, vehiculo_id, distancia_planificada_m, 
                          duracion_planificada_s, geometria)
        VALUES (?, ?, ?, ?, ?)
    ''', (nombre, vehiculo_id, distancia_m, duracion_s, geometria))
    conn.commit()
    ruta_id = cursor.lastrowid
    conn.close()
    return ruta_id

def obtener_rutas_por_estado(estado: str = "programada") -> List[Dict[str, Any]]:
    """Obtiene rutas por estado (programada, en_progreso, etc.)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rutas WHERE estado = ?", (estado,))
    filas = cursor.fetchall()
    conn.close()
    return [dict(fila) for fila in filas]

def actualizar_estado_ruta(ruta_id: int, estado: str):
    """Actualiza el estado de una ruta (y marca inicio/fin si aplica)."""
    conn = get_connection()
    cursor = conn.cursor()
    if estado == "en_progreso":
        cursor.execute("UPDATE rutas SET estado = ?, started_at = CURRENT_TIMESTAMP WHERE id = ?", (estado, ruta_id))
    elif estado == "completada":
        cursor.execute("UPDATE rutas SET estado = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?", (estado, ruta_id))
    else:
        cursor.execute("UPDATE rutas SET estado = ? WHERE id = ?", (estado, ruta_id))
    conn.commit()
    conn.close()

# === PUNTOS DE RUTA ===

def agregar_punto_ruta(ruta_id: int, tipo: str, orden: int, direccion: str, lat: float, lng: float, nombre_lugar: str = ""):
    """Agrega un punto (origen, waypoint o destino) a una ruta."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO puntos_ruta (ruta_id, tipo, orden, direccion, lat, lng, nombre_lugar)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ruta_id, tipo, orden, direccion, lat, lng, nombre_lugar))
    conn.commit()
    conn.close()

def obtener_puntos_ruta(ruta_id: int) -> List[Dict[str, Any]]:
    """Devuelve todos los puntos de una ruta, ordenados."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM puntos_ruta WHERE ruta_id = ? ORDER BY orden", (ruta_id,))
    filas = cursor.fetchall()
    conn.close()
    return [dict(fila) for fila in filas]

# === EVENTOS DE TRAZABILIDAD ===

def registrar_evento(
    ruta_id: int,
    tipo_evento: str,
    lat: float = None,
    lng: float = None,
    punto_ruta_id: int = None,
    observaciones: str = ""
):
    """Registra un evento durante la ejecución de la ruta."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO eventos (ruta_id, tipo_evento, punto_ruta_id, lat, lng, observaciones)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (ruta_id, tipo_evento, punto_ruta_id, lat, lng, observaciones))
    conn.commit()
    conn.close()

def obtener_eventos_ruta(ruta_id: int) -> List[Dict[str, Any]]:
    """Obtiene todos los eventos de una ruta, en orden cronológico."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM eventos WHERE ruta_id = ? ORDER BY timestamp_evento", (ruta_id,))
    filas = cursor.fetchall()
    conn.close()
    return [dict(fila) for fila in filas]

# src/database/db_manager.py

def crear_datos_ejemplo():
    """
    Crea 5 vehículos y 15 rutas de ejemplo (5 programadas, 5 en progreso, 5 completadas).
    """
    vehiculos = obtener_vehiculos_activos()
    rutas = (obtener_rutas_por_estado("programada") + 
             obtener_rutas_por_estado("en_progreso") + 
             obtener_rutas_por_estado("completada"))
    
    if vehiculos or rutas:
        return

    print("🔍 Creando datos de ejemplo...")

    # === 1. Crear 5 VEHÍCULOS ===
    try:
        vehiculos_ids = [
            crear_vehiculo("TDR-789", "Ford", "Transit", 1200),
            crear_vehiculo("ABC-123", "Toyota", "Hilux", 1000),
            crear_vehiculo("XYZ-456", "Mercedes", "Sprinter", 1500),
            crear_vehiculo("LMN-789", "Nissan", "Vanette", 800),
            crear_vehiculo("OPQ-012", "Volkswagen", "Transporter", 1300)
        ]
        print(f"✅ 5 vehículos creados: {vehiculos_ids}")
    except Exception as e:
        print(f"⚠️ Error al crear vehículos: {e}")
        return

    # === 2. Crear RUTAS ===
    try:
        from core.ruta_service import RutaService
        from core.tracking_service import TrackingService
        service = RutaService()
        tracking = TrackingService()

        # Ubicaciones confiables
        ubicaciones = [
            "Plaza Mayor, Lima, Perú",
            "Parque Kennedy, Miraflores",
            "Aeropuerto Internacional Jorge Chávez, Lima",
            "Jockey Plaza, Santiago de Surco, Lima, Perú",
            "Larcomar, Miraflores, Lima, Perú",
            "Real Plaza Puruchuco, Ate, Lima, Perú",
            "Terminal Terrestre Plaza Norte, Lima, Perú",
            "Plaza San Martín, Lima, Perú",
            "Universidad Nacional de Ingeniería, Lima, Perú",
            "Museo Larco, Lima, Perú",
            "Centro Comercial Plaza Lima Sur, Chorrillos, Lima, Perú",
            "Mega Plaza, Independencia, Lima, Perú",
            "Parque de la Reserva, Lima, Perú",
            "Ministerio de Transportes y Comunicaciones, Lima, Perú",
            "Universidad de Lima, Surco, Lima, Perú",
            "Plaza de Armas de Arequipa, Perú",
            "Plaza de Armas de Trujillo, Perú",
            "Plaza de Armas del Cusco, Perú"
        ]

        # Rutas COMPLETADAS (5)
        print("🛠️ Creando rutas COMPLETADAS...")
        for i in range(5):
            resultado = service.programar_ruta(
                nombre_ruta=f"Ruta Completada {i+1}",
                vehiculo_id=vehiculos_ids[i % 5],
                origen=ubicaciones[i % 18],
                destino=ubicaciones[(i + 1) % 18],
                waypoints=[ubicaciones[(i + 2) % 18]] if (i + 2) < 18 else []
            )
            # ✅ Marcar directamente como completada
            actualizar_estado_ruta(resultado["ruta_id"], "completada")
            print(f"✅ Ruta Completada {i+1} creada y finalizada")


        # Rutas EN PROGRESO (5)
        print("🛠️ Creando rutas EN PROGRESO...")
        for i in range(5, 10):
            resultado = service.programar_ruta(
                nombre_ruta=f"Ruta en Progreso {i-4}",
                vehiculo_id=vehiculos_ids[i % 5],
                origen=ubicaciones[i % 18],
                destino=ubicaciones[(i + 1) % 18],
                waypoints=[ubicaciones[(i + 2) % 18]] if (i + 2) < 18 else []
            )
            tracking.iniciar_ruta(resultado["ruta_id"])

        # Rutas PROGRAMADAS (5)
        print("🛠️ Creando rutas PROGRAMADAS...")
        for i in range(10, 15):
            service.programar_ruta(
                nombre_ruta=f"Ruta Programada {i-9}",
                vehiculo_id=vehiculos_ids[i % 5],
                origen=ubicaciones[i % 18],
                destino=ubicaciones[(i + 1) % 18],
                waypoints=[ubicaciones[(i + 2) % 18]] if (i + 2) < 18 else []
            )

        print("✅ 15 rutas de ejemplo creadas exitosamente.")

    except Exception as e:
        print(f"⚠️ Error al crear rutas: {e}")

    print("✅ Datos de ejemplo procesados.")