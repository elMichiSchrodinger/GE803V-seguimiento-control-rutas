# src/api/osm_maps.py
"""
API gratuita de mapas basada en OpenStreetMap:
- Geocodificación: Nominatim
- Rutas: OSRM (Open Source Routing Machine)

No requiere clave de API. Solo conexión a internet.
Respetar límites de uso razonable (1 solicitud/segundo).
"""

import requests
from typing import Optional, Tuple, List, Dict, Any
from api.base import MapsAPI

# URLs públicas
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_ROUTE_URL = "http://router.project-osrm.org/route/v1/driving/"

# User-Agent obligatorio para Nominatim
HEADERS = {
    "User-Agent": "SeguimientoRutasApp/1.0 (jahir.hernandez.h@uni.pe)"
}


class OsmMapsAPI(MapsAPI):
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convierte una dirección en texto a coordenadas (lat, lng).
        
        Args:
            address (str): Ej. "Av. Arequipa 123, Lima, Perú"
        
        Returns:
            (lat, lng) o None si no se encuentra.
        """
        if not address or not isinstance(address, str):
            return None

        params = {
            "q": address.strip(),
            "format": "json",
            "limit": 1,
            "addressdetails": 1
        }

        try:
            response = requests.get(
                NOMINATIM_URL,
                params=params,
                headers=HEADERS,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data and len(data) > 0:
                return (float(data[0]["lat"]), float(data[0]["lon"]))
            else:
                print(f"📍 No se encontró la dirección: {address}")
                return None
        except Exception as e:
            print(f"❌ Error en geocodificación: {e}")
            return None

    def _coords_to_osrm_string(self, coords: List[Tuple[float, float]]) -> str:
        """
        Convierte lista de (lat, lng) a string para OSRM: "lng,lat;lng,lat;..."
        OSRM espera coordenadas en orden (longitud, latitud).
        """
        return ";".join([f"{lng},{lat}" for lat, lng in coords])

    def get_directions(
        self,
        origin: str,
        destination: str,
        waypoints: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene una ruta detallada desde origen a destino, con paradas opcionales.
        """
        # Validar entradas
        if not origin or not destination:
            print("❌ Origen o destino vacíos.")
            return None

        # Geocodificar todos los puntos
        addresses = [origin]
        if waypoints:
            addresses.extend(waypoints)
        addresses.append(destination)

        coords = []
        for addr in addresses:
            coord = self.geocode(addr)
            if coord is None:
                print(f"❌ Cancelado: no se pudo geocodificar '{addr}'")
                return None
            # Validación adicional: asegurar que sea numérico
            lat, lng = coord
            if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                print(f"❌ Coordenada inválida para '{addr}': {coord}")
                return None
            coords.append(coord)

        # Convertir a formato OSRM
        coord_str = self._coords_to_osrm_string(coords)

        # Llamar a OSRM
        url = f"{OSRM_ROUTE_URL}{coord_str}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "steps": "false"
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            if data.get("code") != "Ok":
                print(f"❌ OSRM error: {data.get('message', 'Desconocido')}")
                return None

            route = data["routes"][0]
            geometry = route["geometry"]["coordinates"]
            polyline = [(pt[1], pt[0]) for pt in geometry]  # (lat, lng)

            return {
                "distance_m": int(route["distance"]),
                "duration_s": int(route["duration"]),
                "polyline": polyline,
                "legs": route.get("legs", [])
            }

        except Exception as e:
            print(f"❌ Error al obtener ruta: {e}")
            return None

    def get_route_summary(
        self,
        origin: str,
        destination: str,
        waypoints: Optional[List[str]] = None
    ) -> str:
        print(f"\n🔍 Calculando ruta:")
        print(f"   Origen: {origin}")
        print(f"   Destino: {destination}")
        if waypoints:
            print(f"   Waypoints: {waypoints}")

        route = self.get_directions(origin, destination, waypoints)
        if not route:
            return "❌ No se pudo calcular la ruta."

        dist_km = route["distance_m"] / 1000
        dur_min = route["duration_s"] / 60
        return f"✅ Distancia: {dist_km:.1f} km | Duración: {dur_min:.0f} min"