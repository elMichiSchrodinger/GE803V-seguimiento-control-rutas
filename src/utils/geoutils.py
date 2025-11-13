# src/utils/geoutils.py
"""
Utilidades geoespaciales: cálculo de distancias, validación de coordenadas, etc.
"""

import math
from typing import Tuple, List, Optional


EARTH_RADIUS = 6371000  # Radio de la Tierra en metros


def validar_coordenadas(lat: float, lng: float) -> bool:
    """
    Valida que las coordenadas estén dentro de rangos geográficos válidos.
    
    Args:
        lat (float): Latitud (-90 a 90)
        lng (float): Longitud (-180 a 180)
    
    Returns:
        bool: True si son válidas.
    """
    return -90.0 <= lat <= 90.0 and -180.0 <= lng <= 180.0


def distancia_haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calcula la distancia en **metros** entre dos puntos geográficos usando la fórmula de Haversine.
    
    Args:
        lat1, lng1: Coordenadas del punto 1 (en grados decimales)
        lat2, lng2: Coordenadas del punto 2 (en grados decimales)
    
    Returns:
        float: Distancia en metros.
    
    Raises:
        ValueError: Si alguna coordenada es inválida.
    """
    if not (validar_coordenadas(lat1, lng1) and validar_coordenadas(lat2, lng2)):
        raise ValueError("Coordenadas fuera de rango válido.")

    # Convertir grados a radianes
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)

    # Diferencias
    delta_lat = lat2_rad - lat1_rad
    delta_lng = lng2_rad - lng1_rad

    # Fórmula de Haversine
    a = (
        math.sin(delta_lat / 2) ** 2 +
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return EARTH_RADIUS * c


def punto_mas_cercano(
    lat_actual: float,
    lng_actual: float,
    lista_puntos: List[Tuple[float, float, any]]
) -> Optional[Tuple[float, float, any, float]]:
    """
    Encuentra el punto más cercano a la ubicación actual.
    
    Args:
        lat_actual, lng_actual: Ubicación actual
        lista_puntos: Lista de tuplas (lat, lng, datos_adicionales)
    
    Returns:
        (lat, lng, datos, distancia_m) del punto más cercano, o None si la lista está vacía.
    """
    if not lista_puntos:
        return None

    min_dist = float('inf')
    punto_cercano = None

    for lat, lng, datos in lista_puntos:
        try:
            dist = distancia_haversine(lat_actual, lng_actual, lat, lng)
            if dist < min_dist:
                min_dist = dist
                punto_cercano = (lat, lng, datos, dist)
        except ValueError:
            continue  # Saltar coordenadas inválidas

    return punto_cercano


def esta_dentro_de_radio(
    lat1: float,
    lng1: float,
    lat2: float,
    lng2: float,
    radio_metros: float
) -> bool:
    """
    Verifica si dos puntos están dentro de un radio determinado.
    
    Args:
        lat1, lng1: Punto de referencia
        lat2, lng2: Punto a verificar
        radio_metros: Radio en metros
    
    Returns:
        bool: True si la distancia <= radio_metros
    """
    try:
        dist = distancia_haversine(lat1, lng1, lat2, lng2)
        return dist <= radio_metros
    except ValueError:
        return False