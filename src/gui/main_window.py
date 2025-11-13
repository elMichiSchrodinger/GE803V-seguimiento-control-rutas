# src/gui/main_window.py
"""
Ventana principal de la aplicación con menú de navegación.
Refresca los datos al cambiar de vista.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QStackedWidget, QMenuBar, QMenu, QWidget,
    QVBoxLayout, QLabel, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction
from gui.dashboard import DashboardWidget
from gui.programacion_rutas import ProgramacionRutasWidget
from gui.seguimiento import SeguimientoWidget
from gui.trazabilidad import TrazabilidadWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SEGUIMIENTO Y CONTROL DE RUTAS")
        self.resize(1000, 700)

        # Área central con vistas apiladas
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Crear instancias de cada vista
        self.dashboard_view = DashboardWidget()
        self.programacion_view = ProgramacionRutasWidget()
        self.seguimiento_view = SeguimientoWidget()
        self.trazabilidad_view = TrazabilidadWidget()

        # Añadir vistas al stack
        self.stacked_widget.addWidget(self.dashboard_view)
        self.stacked_widget.addWidget(self.programacion_view)
        self.stacked_widget.addWidget(self.seguimiento_view)
        self.stacked_widget.addWidget(self.trazabilidad_view)

        # Crear menú
        self._crear_menu()

        # Mostrar vista inicial: Dashboard
        self.stacked_widget.setCurrentWidget(self.dashboard_view)

    def _crear_menu(self):
        """Crea la barra de menú superior."""
        menu_bar = self.menuBar()

        # Menú Rutas
        menu_rutas = menu_bar.addMenu("Rutas")
        action_programar = QAction("Programar Ruta", self)
        action_programar.triggered.connect(self._mostrar_programacion)
        menu_rutas.addAction(action_programar)

        # Menú Seguimiento
        menu_seguimiento = menu_bar.addMenu("Seguimiento")
        action_seguimiento = QAction("Seguimiento en Tiempo Real", self)
        action_seguimiento.triggered.connect(self._mostrar_seguimiento)
        menu_seguimiento.addAction(action_seguimiento)

        action_trazabilidad = QAction("Trazabilidad Detallada", self)
        action_trazabilidad.triggered.connect(self._mostrar_trazabilidad)
        menu_seguimiento.addAction(action_trazabilidad)

        # Menú Dashboard
        menu_dashboard = menu_bar.addMenu("Dashboard")
        action_dashboard = QAction("Panel de Control", self)
        action_dashboard.triggered.connect(self._mostrar_dashboard)
        menu_dashboard.addAction(action_dashboard)

        # Menú Ayuda
        menu_ayuda = menu_bar.addMenu("Ayuda")
        action_acerca = QAction("Acerca de", self)
        action_acerca.triggered.connect(self._mostrar_acerca_de)
        menu_ayuda.addAction(action_acerca)

    def _mostrar_programacion(self):
        """Muestra la vista de programación de rutas."""
        self.stacked_widget.setCurrentWidget(self.programacion_view)

    def _mostrar_seguimiento(self):
        """Muestra y refresca la vista de seguimiento."""
        self.stacked_widget.setCurrentWidget(self.seguimiento_view)
        self.seguimiento_view.cargar_rutas()  # ← Refrescar datos

    def _mostrar_trazabilidad(self):
        """Muestra y refresca la vista de trazabilidad."""
        self.stacked_widget.setCurrentWidget(self.trazabilidad_view)
        self.trazabilidad_view.cargar_rutas()  # ← Refrescar datos

    def _mostrar_dashboard(self):
        """Muestra y refresca el dashboard."""
        self.stacked_widget.setCurrentWidget(self.dashboard_view)
        self.dashboard_view.cargar_datos()  # ← Refrescar datos

    def _mostrar_acerca_de(self):
        """Muestra un cuadro de diálogo 'Acerca de'."""
        msg = QMessageBox()
        msg.setWindowTitle("Acerca de")
        msg.setText("SEGUIMIENTO Y CONTROL DE RUTAS\n\n"
                    "Aplicativo para gestión logística de transporte y distribución.\n"
                    "Desarrollado con Python + PyQt6 + OpenStreetMap.")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()