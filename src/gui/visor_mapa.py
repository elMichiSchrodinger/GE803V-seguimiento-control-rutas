# src/gui/visor_mapa.py
"""
Visor de mapas para mostrar rutas con Folium + PyQt6 WebEngine.
"""

import sys
import os
import json
from PyQt6.QtWidgets import QDialog, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtCore import QUrl


class MapaRutaDialog(QDialog):
    def __init__(self, ruta_info, puntos, geometria, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Mapa de la Ruta: {ruta_info['nombre']}")
        self.resize(900, 700)

        # Crear mapa con Folium
        import folium
        if puntos:
            primer_punto = puntos[0]
            mapa = folium.Map(
                location=[primer_punto["lat"], primer_punto["lng"]],
                zoom_start=12
            )
        else:
            mapa = folium.Map(location=[-12.0464, -77.0428], zoom_start=10)

        # Añadir marcadores
        for i, p in enumerate(puntos):
            color = "green" if p["tipo"] == "origen" else ("blue" if p["tipo"] == "destino" else "orange")
            folium.Marker(
                location=[p["lat"], p["lng"]],
                popup=f"{p['nombre_lugar']}<br>{p['direccion']}",
                icon=folium.Icon(color=color, icon="info-sign")
            ).add_to(mapa)

        # Añadir ruta (polyline)
        if geometria:
            folium.PolyLine(
                locations=geometria,
                color="red",
                weight=3,
                opacity=0.8
            ).add_to(mapa)

        # Guardar en HTML temporal
        self.ruta_html = os.path.join(os.getcwd(), "temp_mapa.html")
        mapa.save(self.ruta_html)

        # Mostrar en QWebEngineView
        layout = QVBoxLayout()
        self.web_view = QWebEngineView()
        
        # ✅ ¡Configuración clave para permitir recursos externos!
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        self.web_view.settings().setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        
        self.web_view.setUrl(QUrl.fromLocalFile(self.ruta_html))
        layout.addWidget(self.web_view)
        self.setLayout(layout)

    def closeEvent(self, event):
        # Limpiar archivo temporal
        try:
            if os.path.exists(self.ruta_html):
                os.remove(self.ruta_html)
        except:
            pass
        super().closeEvent(event)