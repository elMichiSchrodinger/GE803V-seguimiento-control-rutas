# src/core/reportes.py
"""
Módulo para generar reportes y KPIs a partir de los datos almacenados.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from database.db_manager import (
    obtener_rutas_por_estado,
    obtener_eventos_ruta,
    obtener_vehiculos_activos
)


class ReportesService:
    def __init__(self):
        pass

    def kpi_entregas_a_tiempo(self, dias: int = 30) -> Dict[str, Any]:
        """
        Calcula el porcentaje de rutas completadas a tiempo en los últimos N días.
        Por ahora, asumimos "a tiempo" si se completó (futuro: comparar con ventana horaria).
        """
        # Obtener rutas completadas en los últimos N días
        # 👉 NOTA: en este MVP, no almacenamos "hora planificada de entrega",
        #    así que asumimos que "completada = a tiempo".
        #    En una versión avanzada, se compararía started_at + duracion_planificada_s con completed_at.
        rutas_completadas = self._obtener_rutas_completadas_recientes(dias)
        total = len(rutas_completadas)
        a_tiempo = total  # Simplificación temporal

        porcentaje = 100.0 if total > 0 else 0.0
        return {
            "nombre": "Entregas a tiempo (últimos {} días)".format(dias),
            "valor": porcentaje,
            "total": total,
            "a_tiempo": a_tiempo,
            "unidad": "%"
        }

    def kpi_tiempo_promedio_entrega(self, dias: int = 30) -> Dict[str, Any]:
        """
        Calcula el tiempo promedio de entrega (desde inicio hasta fin de ruta).
        """
        rutas = self._obtener_rutas_completadas_recientes(dias)
        if not rutas:
            return {"nombre": "Tiempo promedio de entrega", "valor": 0, "unidad": "min"}

        tiempos_min = []
        for ruta in rutas:
            if ruta["started_at"] and ruta["completed_at"]:
                inicio = datetime.fromisoformat(ruta["started_at"].replace("Z", "+00:00"))
                fin = datetime.fromisoformat(ruta["completed_at"].replace("Z", "+00:00"))
                duracion_seg = (fin - inicio).total_seconds()
                tiempos_min.append(duracion_seg / 60)

        promedio = round(sum(tiempos_min) / len(tiempos_min), 1) if tiempos_min else 0
        return {
            "nombre": "Tiempo promedio de entrega",
            "valor": promedio,
            "unidad": "min"
        }

    def kpi_rutas_por_estado(self) -> Dict[str, int]:
        """Cuenta rutas por estado actual."""
        estados = ["programada", "en_progreso", "completada", "cancelada"]
        conteo = {}
        for estado in estados:
            rutas = obtener_rutas_por_estado(estado)
            conteo[estado] = len(rutas)
        return conteo

    def kpi_vehiculos_activos(self) -> int:
        """Número de vehículos activos en la flota."""
        vehiculos = obtener_vehiculos_activos()
        return len(vehiculos)

    def kpi_eventos_recientes(self, limite: int = 10) -> List[Dict[str, Any]]:
        """
        Últimos eventos registrados (para feed en dashboard).
        """
        # Nota: db_manager no tiene función para "todos los eventos recientes",
        # así que simulamos o mejoramos después.
        # Por ahora, obtenemos eventos de rutas completadas recientes.
        rutas = self._obtener_rutas_completadas_recientes(7)
        todos_eventos = []
        for ruta in rutas:
            eventos = obtener_eventos_ruta(ruta["id"])
            for ev in eventos:
                todos_eventos.append({
                    "tipo": ev["tipo_evento"],
                    "ruta_id": ev["ruta_id"],
                    "timestamp": ev["timestamp_evento"],
                    "obs": ev["observaciones"] or ""
                })
        # Ordenar por timestamp (más reciente primero)
        todos_eventos.sort(key=lambda x: x["timestamp"], reverse=True)
        return todos_eventos[:limite]

    # === Métodos auxiliares ===

    def _obtener_rutas_completadas_recientes(self, dias: int) -> List[Dict[str, Any]]:
        """
        Obtiene rutas completadas en los últimos N días.
        Como SQLite no tiene NOW(), filtramos en Python.
        """
        rutas = obtener_rutas_por_estado("completada")
        desde = datetime.now() - timedelta(days=dias)
        rutas_recientes = []
        for r in rutas:
            if r["completed_at"]:
                comp_time = datetime.fromisoformat(r["completed_at"].replace("Z", "+00:00"))
                if comp_time >= desde:
                    rutas_recientes.append(r)
        return rutas_recientes