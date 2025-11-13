# src/gui/programacion_rutas.py
"""
Ventana para programar rutas SIN autocompletado (versión ligera).
Incluye gestión completa de vehículos (CRUD).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox, QTextEdit, QDialog, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.ruta_service import RutaService
from database.db_manager import (
    obtener_vehiculos_activos, crear_vehiculo,
    actualizar_vehiculo, eliminar_vehiculo
)


class VehiculoDialog(QDialog):
    def __init__(self, vehiculo=None, parent=None):
        super().__init__(parent)
        self.vehiculo = vehiculo
        self.setWindowTitle("Editar Vehículo" if vehiculo else "Nuevo Vehículo")
        self.resize(300, 200)

        layout = QFormLayout()
        self.placa_edit = QLineEdit()
        self.marca_edit = QLineEdit()
        self.modelo_edit = QLineEdit()
        self.capacidad_edit = QLineEdit()

        if vehiculo:
            self.placa_edit.setText(vehiculo.get("placa", ""))
            self.marca_edit.setText(vehiculo.get("marca", ""))
            self.modelo_edit.setText(vehiculo.get("modelo", ""))
            self.capacidad_edit.setText(str(vehiculo.get("capacidad_kg", "")))

        layout.addRow("Placa:", self.placa_edit)
        layout.addRow("Marca:", self.marca_edit)
        layout.addRow("Modelo:", self.modelo_edit)
        layout.addRow("Capacidad (kg):", self.capacidad_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_datos(self):
        capacidad_text = self.capacidad_edit.text().strip()
        capacidad = float(capacidad_text) if capacidad_text.replace('.','',1).isdigit() else 0.0
        return {
            "placa": self.placa_edit.text().strip(),
            "marca": self.marca_edit.text().strip(),
            "modelo": self.modelo_edit.text().strip(),
            "capacidad_kg": capacidad
        }


class ProgramacionRutasWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.ruta_service = RutaService()
        self.init_ui()
        self.cargar_vehiculos()

    def init_ui(self):
        self.setWindowTitle("Programación de Rutas")
        main_layout = QVBoxLayout()

        # === Título ===
        titulo = QLabel("Programar Nueva Ruta")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(titulo)

        # === Panel izquierdo: Gestión de vehículos ===
        vehiculos_layout = QHBoxLayout()
        vehiculos_group = QGroupBox("Flota de Vehículos")
        vehiculos_vlayout = QVBoxLayout()

        self.tabla_vehiculos = QTableWidget(0, 4)
        self.tabla_vehiculos.setHorizontalHeaderLabels(["ID", "Placa", "Marca/Modelo", "Capacidad (kg)"])
        self.tabla_vehiculos.horizontalHeader().setStretchLastSection(True)
        self.tabla_vehiculos.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabla_vehiculos.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        vehiculos_vlayout.addWidget(self.tabla_vehiculos)

        crud_layout = QHBoxLayout()
        self.btn_agregar_veh = QPushButton("Agregar")
        self.btn_editar_veh = QPushButton("Editar")
        self.btn_eliminar_veh = QPushButton("Eliminar")
        self.btn_agregar_veh.clicked.connect(self.agregar_vehiculo)
        self.btn_editar_veh.clicked.connect(self.editar_vehiculo)
        self.btn_eliminar_veh.clicked.connect(self.eliminar_vehiculo)
        crud_layout.addWidget(self.btn_agregar_veh)
        crud_layout.addWidget(self.btn_editar_veh)
        crud_layout.addWidget(self.btn_eliminar_veh)
        vehiculos_vlayout.addLayout(crud_layout)

        vehiculos_group.setLayout(vehiculos_vlayout)
        vehiculos_layout.addWidget(vehiculos_group)

        # === Panel derecho: Programación de ruta ===
        ruta_group = QGroupBox("Detalles de la Ruta")
        ruta_layout = QVBoxLayout()

        nombre_layout = QHBoxLayout()
        nombre_layout.addWidget(QLabel("Nombre de la ruta:"))
        self.input_nombre = QLineEdit()
        self.input_nombre.setPlaceholderText("Ej: Ruta Diaria - Zona Sur")
        nombre_layout.addWidget(self.input_nombre)
        ruta_layout.addLayout(nombre_layout)

        # Origen (sin autocompletado)
        origen_layout = QHBoxLayout()
        origen_layout.addWidget(QLabel("Origen:"))
        self.input_origen = QLineEdit()
        self.input_origen.setPlaceholderText("Ej: Plaza Mayor, Lima, Perú")
        origen_layout.addWidget(self.input_origen)
        ruta_layout.addLayout(origen_layout)

        # Waypoints
        waypoints_layout = QHBoxLayout()
        waypoints_layout.addWidget(QLabel("Paradas (una por línea):"))
        self.text_waypoints = QTextEdit()
        self.text_waypoints.setMaximumHeight(80)
        waypoints_layout.addWidget(self.text_waypoints)
        ruta_layout.addLayout(waypoints_layout)

        # Destino (sin autocompletado)
        destino_layout = QHBoxLayout()
        destino_layout.addWidget(QLabel("Destino:"))
        self.input_destino = QLineEdit()
        self.input_destino.setPlaceholderText("Ej: Aeropuerto Internacional Jorge Chávez, Lima")
        destino_layout.addWidget(self.input_destino)
        ruta_layout.addLayout(destino_layout)

        self.btn_programar = QPushButton("Calcular y Programar Ruta")
        self.btn_programar.clicked.connect(self.programar_ruta)
        ruta_layout.addWidget(self.btn_programar)

        self.resumen_label = QLabel("")
        self.resumen_label.setWordWrap(True)
        self.resumen_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ruta_layout.addWidget(self.resumen_label)

        ruta_group.setLayout(ruta_layout)
        vehiculos_layout.addWidget(ruta_group)

        main_layout.addLayout(vehiculos_layout)
        self.setLayout(main_layout)

    def cargar_vehiculos(self):
        try:
            vehiculos = obtener_vehiculos_activos()
            self.tabla_vehiculos.setRowCount(len(vehiculos))
            for i, v in enumerate(vehiculos):
                self.tabla_vehiculos.setItem(i, 0, QTableWidgetItem(str(v["id"])))
                self.tabla_vehiculos.setItem(i, 1, QTableWidgetItem(v["placa"]))
                self.tabla_vehiculos.setItem(i, 2, QTableWidgetItem(f"{v['marca']} {v['modelo']}"))
                self.tabla_vehiculos.setItem(i, 3, QTableWidgetItem(str(v["capacidad_kg"])))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los vehículos:\n{str(e)}")

    def agregar_vehiculo(self):
        dialog = VehiculoDialog()
        if dialog.exec():
            datos = dialog.get_datos()
            try:
                crear_vehiculo(**datos)
                self.cargar_vehiculos()
                QMessageBox.information(self, "Éxito", "Vehículo agregado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo crear el vehículo:\n{str(e)}")

    def editar_vehiculo(self):
        selected = self.tabla_vehiculos.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Seleccione un vehículo.")
            return
        row = selected[0].row()
        vehiculo_id = int(self.tabla_vehiculos.item(row, 0).text())
        placa = self.tabla_vehiculos.item(row, 1).text()
        marca_modelo = self.tabla_vehiculos.item(row, 2).text()
        capacidad = float(self.tabla_vehiculos.item(row, 3).text())

        partes = marca_modelo.split(" ", 1)
        marca = partes[0]
        modelo = partes[1] if len(partes) > 1 else ""

        vehiculo = {"id": vehiculo_id, "placa": placa, "marca": marca, "modelo": modelo, "capacidad_kg": capacidad}
        dialog = VehiculoDialog(vehiculo=vehiculo)
        if dialog.exec():
            datos = dialog.get_datos()
            try:
                actualizar_vehiculo(vehiculo_id, **datos)
                self.cargar_vehiculos()
                QMessageBox.information(self, "Éxito", "Vehículo actualizado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo actualizar el vehículo:\n{str(e)}")

    def eliminar_vehiculo(self):
        selected = self.tabla_vehiculos.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Seleccione un vehículo.")
            return
        row = selected[0].row()
        vehiculo_id = int(self.tabla_vehiculos.item(row, 0).text())
        placa = self.tabla_vehiculos.item(row, 1).text()
        
        reply = QMessageBox.question(self, "Confirmar eliminación", f"¿Eliminar vehículo {placa}?", 
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                eliminar_vehiculo(vehiculo_id)
                self.cargar_vehiculos()
                QMessageBox.information(self, "Éxito", "Vehículo eliminado correctamente.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"No se pudo eliminar el vehículo:\n{str(e)}")

    def programar_ruta(self):
        selected = self.tabla_vehiculos.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Advertencia", "Seleccione un vehículo.")
            return

        nombre = self.input_nombre.text().strip()
        origen = self.input_origen.text().strip()
        destino = self.input_destino.text().strip()

        if not all([nombre, origen, destino]):
            QMessageBox.warning(self, "Advertencia", "Complete todos los campos obligatorios.")
            return

        waypoints_text = self.text_waypoints.toPlainText().strip()
        waypoints = [line.strip() for line in waypoints_text.split("\n") if line.strip()] if waypoints_text else None

        try:
            self.btn_programar.setEnabled(False)
            self.btn_programar.setText("Calculando...")

            resultado = self.ruta_service.programar_ruta(
                nombre_ruta=nombre,
                vehiculo_id=int(self.tabla_vehiculos.item(selected[0].row(), 0).text()),
                origen=origen,
                destino=destino,
                waypoints=waypoints
            )

            self.resumen_label.setText(f"<b>✅ Ruta programada:</b> {resultado['resumen']}")
            QMessageBox.information(self, "Éxito", f"Ruta creada con ID: {resultado['ruta_id']}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo programar la ruta:\n{str(e)}")
        finally:
            self.btn_programar.setEnabled(True)
            self.btn_programar.setText("Calcular y Programar Ruta")