# src/gui/trazabilidad.py
"""
Ventana para ver la trazabilidad detallada de una ruta específica.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox, QTextBrowser
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from database.db_manager import (
    obtener_rutas_por_estado, obtener_puntos_ruta,
    obtener_eventos_ruta, obtener_vehiculos_activos
)
from utils.export import exportar_trazabilidad_ruta_a_pdf, exportar_eventos_ruta_a_csv
import os


class TrazabilidadWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.ruta_seleccionada = None
        self.puntos_ruta = []
        self.init_ui()
        self.cargar_rutas()

    def init_ui(self):
        self.setWindowTitle("Trazabilidad de Rutas")
        layout = QVBoxLayout()

        # === Título ===
        titulo = QLabel("Trazabilidad Detallada de Rutas")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # === Selección de ruta ===
        seleccion_group = QGroupBox("Seleccionar ruta")
        seleccion_layout = QHBoxLayout()
        seleccion_layout.addWidget(QLabel("Ruta:"))
        self.combo_rutas = QComboBox()
        self.combo_rutas.currentIndexChanged.connect(self.cargar_trazabilidad)
        seleccion_layout.addWidget(self.combo_rutas)
        self.btn_cargar = QPushButton("Cargar Trazabilidad")
        self.btn_cargar.clicked.connect(self.cargar_trazabilidad)
        seleccion_layout.addWidget(self.btn_cargar)
        seleccion_group.setLayout(seleccion_layout)
        layout.addWidget(seleccion_group)

        # === Resumen de la ruta ===
        self.resumen_group = QGroupBox("Resumen de la ruta")
        resumen_layout = QVBoxLayout()
        self.resumen_text = QTextBrowser()
        self.resumen_text.setMaximumHeight(100)
        resumen_layout.addWidget(self.resumen_text)
        self.resumen_group.setLayout(resumen_layout)
        self.resumen_group.setVisible(False)
        layout.addWidget(self.resumen_group)

        # === Puntos planificados ===
        self.puntos_group = QGroupBox("Puntos Planificados")
        puntos_layout = QVBoxLayout()
        self.tabla_puntos = QTableWidget(0, 5)
        self.tabla_puntos.setHorizontalHeaderLabels(["Orden", "Tipo", "Lugar", "Dirección", "Coordenadas"])
        self.tabla_puntos.horizontalHeader().setStretchLastSection(True)
        puntos_layout.addWidget(self.tabla_puntos)
        self.puntos_group.setLayout(puntos_layout)
        self.puntos_group.setVisible(False)
        layout.addWidget(self.puntos_group)

        # === Eventos registrados ===
        self.eventos_group = QGroupBox("Eventos Registrados (Cronológico)")
        eventos_layout = QVBoxLayout()
        self.tabla_eventos = QTableWidget(0, 5)
        self.tabla_eventos.setHorizontalHeaderLabels(["Evento", "Punto", "Coordenadas", "Fecha/Hora", "Observaciones"])
        self.tabla_eventos.horizontalHeader().setStretchLastSection(True)
        self.tabla_eventos.setMaximumHeight(200)
        eventos_layout.addWidget(self.tabla_eventos)
        self.eventos_group.setLayout(eventos_layout)
        self.eventos_group.setVisible(False)
        layout.addWidget(self.eventos_group)

        # === Botones: Ver en Mapa + Exportar ===
        export_layout = QHBoxLayout()
        self.btn_ver_mapa = QPushButton("Ver en Mapa")
        self.btn_ver_mapa.clicked.connect(self.ver_en_mapa)
        self.btn_export_pdf = QPushButton("Exportar trazabilidad a PDF")
        self.btn_export_csv = QPushButton("Exportar eventos a CSV")
        self.btn_export_pdf.clicked.connect(self.exportar_pdf)
        self.btn_export_csv.clicked.connect(self.exportar_csv)

        export_layout.addWidget(self.btn_ver_mapa)
        export_layout.addWidget(self.btn_export_pdf)
        export_layout.addWidget(self.btn_export_csv)

        self.export_buttons_group = QGroupBox()
        self.export_buttons_group.setLayout(export_layout)
        self.export_buttons_group.setVisible(False)
        layout.addWidget(self.export_buttons_group)

        self.setLayout(layout)

    def cargar_rutas(self):
        """Carga todas las rutas (programadas, en progreso, completadas)."""
        try:
            estados = ["programada", "en_progreso", "completada"]
            todas_rutas = []
            for estado in estados:
                todas_rutas.extend(obtener_rutas_por_estado(estado))

            self.combo_rutas.clear()
            if not todas_rutas:
                self.combo_rutas.addItem("No hay rutas disponibles", -1)
            else:
                for r in todas_rutas:
                    estado_icon = {
                        "programada": "📌",
                        "en_progreso": "🚚",
                        "completada": "✅"
                    }.get(r["estado"], "❓")
                    self.combo_rutas.addItem(f"{estado_icon} ID {r['id']}: {r['nombre']} ({r['estado']})", r["id"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las rutas:\n{str(e)}")

    def cargar_trazabilidad(self):
        """Carga puntos y eventos de la ruta seleccionada."""
        ruta_id = self.combo_rutas.currentData()
        if ruta_id == -1 or ruta_id is None:
            self._ocultar_todo()
            return

        try:
            # Obtener la ruta completa
            todas_rutas = []
            for estado in ["programada", "en_progreso", "completada"]:
                todas_rutas.extend(obtener_rutas_por_estado(estado))
            ruta = next((r for r in todas_rutas if r["id"] == ruta_id), None)
            if not ruta:
                raise ValueError("Ruta no encontrada.")
            self.ruta_seleccionada = ruta

            # Cargar puntos para usar en el mapa
            self.puntos_ruta = obtener_puntos_ruta(ruta_id)

            # --- Resumen ---
            vehiculos = {v["id"]: v for v in obtener_vehiculos_activos()}
            vehiculo = vehiculos.get(ruta["vehiculo_id"], {})
            placa = vehiculo.get("placa", "Desconocido")
            distancia = f"{(ruta['distancia_planificada_m'] or 0) / 1000:.1f} km" if ruta['distancia_planificada_m'] else "N/A"
            duracion = f"{(ruta['duracion_planificada_s'] or 0) / 60:.0f} min" if ruta['duracion_planificada_s'] else "N/A"
            resumen_html = (
                f"<b>Nombre:</b> {ruta['nombre']}<br>"
                f"<b>Vehículo:</b> {placa}<br>"
                f"<b>Estado:</b> {ruta['estado']}<br>"
                f"<b>Distancia planificada:</b> {distancia}<br>"
                f"<b>Duración estimada:</b> {duracion}"
            )
            self.resumen_text.setHtml(resumen_html)
            self.resumen_group.setVisible(True)

            # --- Puntos planificados ---
            self.tabla_puntos.setRowCount(len(self.puntos_ruta))
            for i, p in enumerate(self.puntos_ruta):
                self.tabla_puntos.setItem(i, 0, QTableWidgetItem(str(p["orden"])))
                self.tabla_puntos.setItem(i, 1, QTableWidgetItem(p["tipo"]))
                self.tabla_puntos.setItem(i, 2, QTableWidgetItem(p["nombre_lugar"]))
                self.tabla_puntos.setItem(i, 3, QTableWidgetItem(p["direccion"]))
                coords = f"{p['lat']:.4f}, {p['lng']:.4f}"
                self.tabla_puntos.setItem(i, 4, QTableWidgetItem(coords))
            self.puntos_group.setVisible(True)

            # --- Eventos ---
            eventos = obtener_eventos_ruta(ruta_id)
            self.tabla_eventos.setRowCount(len(eventos))
            for i, ev in enumerate(eventos):
                self.tabla_eventos.setItem(i, 0, QTableWidgetItem(ev["tipo_evento"]))
                punto_id = str(ev["punto_ruta_id"]) if ev["punto_ruta_id"] else "N/A"
                self.tabla_eventos.setItem(i, 1, QTableWidgetItem(punto_id))
                coords = f"{ev['lat']:.4f}, {ev['lng']:.4f}" if ev["lat"] and ev["lng"] else "N/A"
                self.tabla_eventos.setItem(i, 2, QTableWidgetItem(coords))
                timestamp = ev["timestamp_evento"] if ev["timestamp_evento"] else ""
                self.tabla_eventos.setItem(i, 3, QTableWidgetItem(timestamp))
                obs = ev["observaciones"] or ""
                self.tabla_eventos.setItem(i, 4, QTableWidgetItem(obs))
            self.eventos_group.setVisible(True)

            # --- Botones de exportación y mapa ---
            self.export_buttons_group.setVisible(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo cargar la trazabilidad:\n{str(e)}")
            self._ocultar_todo()

    def _ocultar_todo(self):
        """Oculta todos los grupos de contenido."""
        self.resumen_group.setVisible(False)
        self.puntos_group.setVisible(False)
        self.eventos_group.setVisible(False)
        self.export_buttons_group.setVisible(False)

    def exportar_pdf(self):
        """Exporta la trazabilidad completa a PDF."""
        if not self.ruta_seleccionada:
            QMessageBox.warning(self, "Advertencia", "Seleccione una ruta primero.")
            return
        try:
            ruta_archivo = os.path.join(os.getcwd(), "exports", f"trazabilidad_ruta_{self.ruta_seleccionada['id']}.pdf")
            exportar_trazabilidad_ruta_a_pdf(self.ruta_seleccionada["id"], ruta_archivo)
            QMessageBox.information(self, "Éxito", f"PDF guardado en:\n{ruta_archivo}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Falló la exportación a PDF:\n{str(e)}")

    def exportar_csv(self):
        """Exporta los eventos a CSV."""
        if not self.ruta_seleccionada:
            QMessageBox.warning(self, "Advertencia", "Seleccione una ruta primero.")
            return
        try:
            ruta_archivo = os.path.join(os.getcwd(), "exports", f"eventos_ruta_{self.ruta_seleccionada['id']}.csv")
            exportar_eventos_ruta_a_csv(self.ruta_seleccionada["id"], ruta_archivo)
            QMessageBox.information(self, "Éxito", f"CSV guardado en:\n{ruta_archivo}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Falló la exportación a CSV:\n{str(e)}")

    def ver_en_mapa(self):
        if not self.ruta_seleccionada:
            QMessageBox.warning(self, "Advertencia", "Seleccione una ruta primero.")
            return

        try:
            # Recargar la ruta completa desde la base de datos para obtener 'geometria'
            from database.db_manager import obtener_rutas_por_estado
            todas_rutas = []
            for estado in ["programada", "en_progreso", "completada"]:
                todas_rutas.extend(obtener_rutas_por_estado(estado))
            ruta_completa = next((r for r in todas_rutas if r["id"] == self.ruta_seleccionada["id"]), None)

            if not ruta_completa or not ruta_completa.get("geometria"):
                QMessageBox.warning(self, "Advertencia", "La ruta no tiene datos de trazado.")
                return

            import json
            geometria = json.loads(ruta_completa["geometria"])

            from gui.visor_mapa import MapaRutaDialog
            dialog = MapaRutaDialog(
                ruta_info=self.ruta_seleccionada,
                puntos=self.puntos_ruta,
                geometria=geometria
            )
            dialog.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo mostrar el mapa:\n{str(e)}")