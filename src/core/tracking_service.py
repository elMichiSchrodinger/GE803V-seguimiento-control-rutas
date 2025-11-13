# src/core/tracking_service.py
"""
Servicio para el seguimiento y trazabilidad de rutas en ejecución.
"""

import math
from typing import Optional, Tuple, List
from database.db_manager import (
    actualizar_estado_ruta,
    registrar_evento,
    obtener_puntos_ruta,
    obtener_rutas_por_estado
)
from utils.geoutils import distancia_haversine


class TrackingService:
    def __init__(self):
        pass

    def iniciar_ruta(self, ruta_id: int):
        """Marca una ruta como 'en_progreso' y registra la salida del almacén."""
        # Verificar que esté programada
        rutas = obtener_rutas_por_estado("programada")
        if not any(r["id"] == ruta_id for r in rutas):
            raise ValueError(f"La ruta {ruta_id} no está en estado 'programada'.")

        # Actualizar estado
        actualizar_estado_ruta(ruta_id, "en_progreso")

        # Registrar evento de salida
        registrar_evento(
            ruta_id=ruta_id,
            tipo_evento="salida_almacen",
            observaciones="Ruta iniciada desde el almacén."
        )

    def registrar_llegada_a_punto(
        self,
        ruta_id: int,
        punto_ruta_id: int,
        lat: float,
        lng: float,
        observaciones: str = ""
    ):
        """
        Registra la llegada a un punto planificado (waypoint o destino).
        """
        registrar_evento(
            ruta_id=ruta_id,
            tipo_evento="llegada_punto",
            punto_ruta_id=punto_ruta_id,
            lat=lat,
            lng=lng,
            observaciones=observaciones
        )

    def registrar_entrega_confirmada(
        self,
        ruta_id: int,
        punto_ruta_id: int,
        lat: float,
        lng: float,
        observaciones: str = "Entrega confirmada"
    ):
        """
        Confirma la entrega en un punto (normalmente el destino o un waypoint de entrega).
        """
        registrar_evento(
            ruta_id=ruta_id,
            tipo_evento="entrega_confirmada",
            punto_ruta_id=punto_ruta_id,
            lat=lat,
            lng=lng,
            observaciones=observaciones
        )

        # Verificar si es el último punto → marcar ruta como completada
        puntos = obtener_puntos_ruta(ruta_id)
        if not puntos:
            return

        # Obtener el último punto (destino)
        destino = max(puntos, key=lambda p: p["orden"])
        if destino["id"] == punto_ruta_id:
            # Es el destino final → completar ruta
            self.finalizar_ruta(ruta_id)

    def registrar_posicion_actual(
        self,
        ruta_id: int,
        lat: float,
        lng: float,
        tolerancia_m: int = 50
    ):
        """
        Registra la posición actual del vehículo (simulación o GPS real).
        Opcional: detecta si está cerca de algún punto planificado.
        
        En una versión avanzada, detectaría desviaciones de la ruta planificada.
        """
        # Por ahora, solo registra la posición (útil para trazabilidad)
        registrar_evento(
            ruta_id=ruta_id,
            tipo_evento="posicion_actual",
            lat=lat,
            lng=lng,
            observaciones=f"Posición GPS actual (tolerancia: {tolerancia_m}m)"
        )

        # Opcional: verificar proximidad a puntos planificados
        self._verificar_proximidad_a_puntos(ruta_id, lat, lng, tolerancia_m)

    def _verificar_proximidad_a_puntos(
        self,
        ruta_id: int,
        lat_actual: float,
        lng_actual: float,
        tolerancia_m: int = 50
    ):
        """
        Verifica si la posición actual está cerca de algún punto no visitado.
        """
        puntos = obtener_puntos_ruta(ruta_id)
        if not puntos:
            return

        for punto in puntos:
            # Saltar si ya se registró entrega en este punto
            # (en una versión avanzada, se verificaría en eventos)
            dist = distancia_haversine(lat_actual, lng_actual, punto["lat"], punto["lng"])
            if dist <= tolerancia_m:
                # Podrías auto-registrar llegada, pero mejor dejarlo manual o con confirmación
                print(f"🔍 Cerca del punto '{punto['nombre_lugar']}' ({dist:.1f} m)")

    def registrar_desviacion(
        self,
        ruta_id: int,
        lat: float,
        lng: float,
        observaciones: str = "Desviación detectada de la ruta planificada"
    ):
        """
        Registra manualmente una desviación (ej: por tráfico, cierre de vía).
        """
        registrar_evento(
            ruta_id=ruta_id,
            tipo_evento="desviacion_ruta",
            lat=lat,
            lng=lng,
            observaciones=observaciones
        )

    def finalizar_ruta(self, ruta_id: int):
        """Marca la ruta como completada."""
        # Verificar que esté en progreso
        rutas = obtener_rutas_por_estado("en_progreso")
        if not any(r["id"] == ruta_id for r in rutas):
            raise ValueError(f"La ruta {ruta_id} no está en progreso.")

        actualizar_estado_ruta(ruta_id, "completada")
        registrar_evento(
            ruta_id=ruta_id,
            tipo_evento="fin_ruta",
            observaciones="Ruta finalizada con éxito."
        )