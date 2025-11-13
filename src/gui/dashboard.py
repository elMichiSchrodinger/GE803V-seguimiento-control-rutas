# src/gui/dashboard.py
"""
Dashboard de control y seguimiento con PyQt6.
Muestra KPIs, estado de rutas y eventos recientes.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.reportes import ReportesService
from utils.export import exportar_rutas_a_csv, exportar_rutas_a_pdf
from database.db_manager import obtener_rutas_por_estado
import os


class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.reportes = ReportesService()
        self.init_ui()
        self.cargar_datos()

    def init_ui(self):
        self.setWindowTitle("Dashboard - Seguimiento y Control de Rutas")
        layout = QVBoxLayout()

        # === Título ===
        titulo = QLabel("Dashboard de Gestión Logística")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # === KPIs (fila de tarjetas) ===
        self.kpi_layout = QHBoxLayout()
        self.kpi_widgets = {}
        kpis = ["entregas_tiempo", "tiempo_promedio", "rutas_activas", "vehiculos_activos"]
        for kpi in kpis:
            card = self.crear_tarjeta_kpi("Cargando...", "...")
            self.kpi_widgets[kpi] = card
            self.kpi_layout.addWidget(card)
        layout.addLayout(self.kpi_layout)

        # === Últimas rutas completadas ===
        rutas_group = QGroupBox("Últimas Rutas Completadas")
        rutas_layout = QVBoxLayout()
        self.tabla_rutas = QTableWidget(0, 5)
        self.tabla_rutas.setHorizontalHeaderLabels(["ID", "Nombre", "Vehículo", "Distancia (km)", "Duración (min)"])
        self.tabla_rutas.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        rutas_layout.addWidget(self.tabla_rutas)
        rutas_group.setLayout(rutas_layout)
        layout.addWidget(rutas_group)

        # === Eventos recientes ===
        eventos_group = QGroupBox("Eventos Recientes")
        eventos_layout = QVBoxLayout()
        self.tabla_eventos = QTableWidget(0, 3)
        self.tabla_eventos.setHorizontalHeaderLabels(["Evento", "Ruta", "Hora"])
        self.tabla_eventos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        eventos_layout.addWidget(self.tabla_eventos)
        eventos_group.setLayout(eventos_layout)
        layout.addWidget(eventos_group)

        # === Botones de exportación ===
        export_layout = QHBoxLayout()
        self.btn_export_csv = QPushButton("Exportar Rutas a CSV")
        self.btn_export_pdf = QPushButton("Exportar Rutas a PDF")
        self.btn_export_csv.clicked.connect(self.exportar_csv)
        self.btn_export_pdf.clicked.connect(self.exportar_pdf)
        export_layout.addWidget(self.btn_export_csv)
        export_layout.addWidget(self.btn_export_pdf)
        layout.addLayout(export_layout)

        self.setLayout(layout)

    def crear_tarjeta_kpi(self, titulo: str, valor: str) -> QGroupBox:
        """Crea una tarjeta visual para un KPI."""
        group = QGroupBox()
        layout = QVBoxLayout()
        title_label = QLabel(titulo)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 10))
        value_label = QLabel(valor)
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        group.setLayout(layout)
        return group

    def cargar_datos(self):
        """Carga todos los datos del dashboard."""
        try:
            # --- KPIs ---
            kpi_tiempo = self.reportes.kpi_entregas_a_tiempo(7)
            self.kpi_widgets["entregas_tiempo"].findChild(QLabel).setText("Entregas a tiempo (7 días)")
            self.kpi_widgets["entregas_tiempo"].findChildren(QLabel)[1].setText(f"{kpi_tiempo['valor']:.1f}%")

            kpi_tiempo_prom = self.reportes.kpi_tiempo_promedio_entrega(7)
            self.kpi_widgets["tiempo_promedio"].findChild(QLabel).setText("Tiempo promedio")
            self.kpi_widgets["tiempo_promedio"].findChildren(QLabel)[1].setText(f"{kpi_tiempo_prom['valor']} min")

            kpi_rutas = self.reportes.kpi_rutas_por_estado()
            rutas_activas = kpi_rutas.get("en_progreso", 0) + kpi_rutas.get("programada", 0)
            self.kpi_widgets["rutas_activas"].findChild(QLabel).setText("Rutas activas")
            self.kpi_widgets["rutas_activas"].findChildren(QLabel)[1].setText(str(rutas_activas))

            kpi_vehiculos = self.reportes.kpi_vehiculos_activos()
            self.kpi_widgets["vehiculos_activos"].findChild(QLabel).setText("Vehículos activos")
            self.kpi_widgets["vehiculos_activos"].findChildren(QLabel)[1].setText(str(kpi_vehiculos))

            # --- Últimas rutas completadas ---
            rutas = obtener_rutas_por_estado("completada")[-5:]  # Últimas 5
            self.tabla_rutas.setRowCount(len(rutas))
            for i, r in enumerate(rutas):
                self.tabla_rutas.setItem(i, 0, QTableWidgetItem(str(r["id"])))
                self.tabla_rutas.setItem(i, 1, QTableWidgetItem(r["nombre"]))
                self.tabla_rutas.setItem(i, 2, QTableWidgetItem(str(r["vehiculo_id"])))
                dist_km = (r["distancia_planificada_m"] or 0) / 1000
                dur_min = (r["duracion_planificada_s"] or 0) / 60
                self.tabla_rutas.setItem(i, 3, QTableWidgetItem(f"{dist_km:.1f}"))
                self.tabla_rutas.setItem(i, 4, QTableWidgetItem(f"{dur_min:.0f}"))

            # --- Eventos recientes ---
            eventos = self.reportes.kpi_eventos_recientes(10)
            self.tabla_eventos.setRowCount(len(eventos))
            for i, ev in enumerate(eventos):
                self.tabla_eventos.setItem(i, 0, QTableWidgetItem(ev["tipo"]))
                self.tabla_eventos.setItem(i, 1, QTableWidgetItem(str(ev["ruta_id"])))
                # Mostrar solo hora y fecha corta
                hora = ev["timestamp"].split(" ")[1] if ev["timestamp"] else ""
                fecha = ev["timestamp"].split(" ")[0] if ev["timestamp"] else ""
                self.tabla_eventos.setItem(i, 2, QTableWidgetItem(f"{fecha} {hora}"))

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los datos:\n{str(e)}")

    def exportar_csv(self):
        """Exporta rutas completadas a CSV."""
        try:
            rutas = obtener_rutas_por_estado("completada")
            if not rutas:
                QMessageBox.warning(self, "Advertencia", "No hay rutas completadas para exportar.")
                return
            ruta_archivo = os.path.join(os.getcwd(), "exports", "rutas_dashboard.csv")
            exportar_rutas_a_csv(rutas, ruta_archivo)
            QMessageBox.information(self, "Éxito", f"Archivo CSV guardado en:\n{ruta_archivo}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Falló la exportación:\n{str(e)}")

    def exportar_pdf(self):
        """Exporta rutas completadas a PDF."""
        try:
            rutas = obtener_rutas_por_estado("completada")
            if not rutas:
                QMessageBox.warning(self, "Advertencia", "No hay rutas completadas para exportar.")
                return
            ruta_archivo = os.path.join(os.getcwd(), "exports", "rutas_dashboard.pdf")
            exportar_rutas_a_pdf(rutas, ruta_archivo)
            QMessageBox.information(self, "Éxito", f"Archivo PDF guardado en:\n{ruta_archivo}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Falló la exportación:\n{str(e)}")