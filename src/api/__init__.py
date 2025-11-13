# src/api/__init__.py
"""
Paquete de integración con proveedores de mapas.
Actualmente solo soporta OpenStreetMap (gratuito).
"""

# Imports opcionales para acceso directo
from .base import MapsAPI
from .osm_maps import OsmMapsAPI

# Define qué se importa con "from api import *"
__all__ = ["MapsAPI", "OsmMapsAPI"]