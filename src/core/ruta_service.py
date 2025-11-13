# src/core/ruta_service.py
"""
Servicio principal para la programación y gestión de rutas.
Integra mapas (OSM) y base de datos.
"""
import json
from typing import List, Optional
from api.osm_maps import OsmMapsAPI
from database.db_manager import (
    crear_ruta,
    agregar_punto_ruta,
    obtener_vehiculos_activos
)


class RutaService:
    def __init__(self):
        self.maps_api = OsmMapsAPI()

    def programar_ruta(
        self,
        nombre_ruta: str,
        vehiculo_id: int,
        origen: str,
        destino: str,
        waypoints: Optional[List[str]] = None
    ) -> dict:
        """
        Programa una ruta completa:
        1. Geocodifica todos los puntos.
        2. Calcula la ruta con OSRM.
        3. Guarda la ruta y sus puntos en la base de datos.
        
        Returns:
            dict con:
                - 'ruta_id': ID de la ruta creada
                - 'resumen': mensaje legible (ej: "Distancia: 27.7 km...")
                - 'puntos': lista de puntos con coordenadas
        """
        # Validar que el vehículo exista (opcional: podrías verificar en BD)
        vehiculos = obtener_vehiculos_activos()
        if not any(v["id"] == vehiculo_id for v in vehiculos):
            raise ValueError(f"Vehículo con ID {vehiculo_id} no existe o no está activo.")

        # Preparar lista de direcciones en orden
        direcciones = [origen]
        if waypoints:
            direcciones.extend(waypoints)
        direcciones.append(destino)

        # Geocodificar todos los puntos
        puntos_geocoded = []
        for i, addr in enumerate(direcciones):
            coord = self.maps_api.geocode(addr)
            if coord is None:
                raise ValueError(f"No se pudo geocodificar la dirección: '{addr}'")
            lat, lng = coord

            if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
                raise ValueError(f"Coordenadas inválidas para: '{addr}'")

            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                raise ValueError(f"Coordenadas fuera de rango para: '{addr}'")
            # Determinar tipo
            if i == 0:
                tipo = "origen"
            elif i == len(direcciones) - 1:
                tipo = "destino"
            else:
                tipo = "waypoint"

            puntos_geocoded.append({
                "direccion": addr,
                "lat": lat,
                "lng": lng,
                "tipo": tipo,
                "orden": i,
                "nombre_lugar": addr.split(",")[0].strip()  # Mejorable, pero funcional
            })

        # Calcular ruta para obtener distancia y duración
        ruta_data = self.maps_api.get_directions(origen, destino, waypoints)
        if ruta_data is None:
            raise RuntimeError("No se pudo calcular la ruta con los puntos dados.")

        # Convertir polyline a JSON
        geometria_json = json.dumps(ruta_data["polyline"])

        # Guardar ruta en base de datos
        ruta_id = crear_ruta(
            nombre=nombre_ruta,
            vehiculo_id=vehiculo_id,
            distancia_m=ruta_data["distance_m"],
            duracion_s=ruta_data["duration_s"],
            geometria=geometria_json  # ← Aquí
        )

        # Guardar cada punto
        for punto in puntos_geocoded:
            print(f"Guardando punto: {punto['direccion']} → ({punto['lat']}, {punto['lng']})")
            agregar_punto_ruta(
                ruta_id=ruta_id,
                tipo=punto["tipo"],
                orden=punto["orden"],
                direccion=punto["direccion"],
                lat=punto["lat"],
                lng=punto["lng"],
                nombre_lugar=punto["nombre_lugar"]
            )

        # Generar resumen legible
        resumen = self.maps_api.get_route_summary(origen, destino, waypoints)

        return {
            "ruta_id": ruta_id,
            "resumen": resumen,
            "puntos": puntos_geocoded,
            "distancia_m": ruta_data["distance_m"],
            "duracion_s": ruta_data["duration_s"]
        }