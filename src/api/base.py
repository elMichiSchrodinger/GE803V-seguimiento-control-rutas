# src/api/base.py
"""
Interfaz base para proveedores de servicios de mapas.
Define los métodos que toda implementación debe cumplir.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple, List, Dict, Any


class MapsAPI(ABC):
    """
    Clase abstracta que define la interfaz común para APIs de mapas.
    """

    @abstractmethod
    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convierte una dirección en texto a coordenadas (latitud, longitud).
        
        Args:
            address (str): Dirección a geocodificar.
        
        Returns:
            Tuple[float, float] | None: (lat, lng) o None si falla.
        """
        pass

    @abstractmethod
    def get_directions(
        self,
        origin: str,
        destination: str,
        waypoints: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene una ruta detallada desde origen a destino, con paradas opcionales.
        
        Args:
            origin (str): Dirección de inicio.
            destination (str): Dirección de fin.
            waypoints (List[str], opcional): Lista de direcciones intermedias.
        
        Returns:
            dict | None: Contiene al menos:
                - 'distance_m': distancia total en metros (int)
                - 'duration_s': duración total en segundos (int)
                - 'polyline': lista de (lat, lng) que describe el trayecto
        """
        pass

    def get_route_summary(
        self,
        origin: str,
        destination: str,
        waypoints: Optional[List[str]] = None
    ) -> str:
        """
        Método concreto (no abstracto): genera un resumen legible de la ruta.
        Puede ser sobrescrito, pero por defecto usa get_directions.
        """
        route = self.get_directions(origin, destination, waypoints)
        if not route:
            return "❌ No se pudo calcular la ruta."

        dist_km = route["distance_m"] / 1000
        dur_min = route["duration_s"] / 60
        return f"✅ Distancia: {dist_km:.1f} km | Duración: {dur_min:.0f} min"