# src/gui/seguimiento.py
"""
Ventana para seguimiento en tiempo real de rutas con PyQt6.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QMessageBox,
    QGroupBox, QTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.tracking_service import TrackingService
from database.db_manager import (
    obtener_rutas_por_estado, obtener_puntos_ruta,
    obtener_vehiculos_activos
)
from utils.geoutils import esta_dentro_de_radio
import random


class SeguimientoWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.tracking_service = TrackingService()
        self.ruta_seleccionada = None
        self.puntos_ruta = []
        self.init_ui()
        self.cargar_rutas()

    def init_ui(self):
        self.setWindowTitle("Seguimiento de Rutas en Tiempo Real")
        layout = QVBoxLayout()

        # === Título ===
        titulo = QLabel("Seguimiento de Rutas")
        titulo.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        titulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(titulo)

        # === Selección de ruta en progreso ===
        # === Selección de ruta en progreso ===
        seleccion_group = QGroupBox("Seleccionar ruta en progreso")
        seleccion_layout = QHBoxLayout()
        seleccion_layout.addWidget(QLabel("Ruta:"))
        self.combo_rutas = QComboBox()
        self.combo_rutas.currentIndexChanged.connect(self.cargar_detalles_ruta)  # Se actualiza al cambiar
        seleccion_layout.addWidget(self.combo_rutas)
        seleccion_group.setLayout(seleccion_layout)
        layout.addWidget(seleccion_group)

        # === Detalles de la ruta ===
        self.detalles_group = QGroupBox("Detalles de la ruta")
        detalles_layout = QVBoxLayout()

        self.info_ruta = QLabel("Seleccione una ruta para ver detalles.")
        self.info_ruta.setWordWrap(True)
        detalles_layout.addWidget(self.info_ruta)

        # Tabla de puntos
        self.tabla_puntos = QTableWidget(0, 4)
        self.tabla_puntos.setHorizontalHeaderLabels(["Orden", "Tipo", "Lugar", "Coordenadas"])
        self.tabla_puntos.horizontalHeader().setStretchLastSection(True)
        detalles_layout.addWidget(self.tabla_puntos)

        self.detalles_group.setLayout(detalles_layout)
        self.detalles_group.setVisible(False)
        layout.addWidget(self.detalles_group)

        # === Simulación de posición actual ===
        posicion_group = QGroupBox("Posición actual del vehículo (simulada)")
        posicion_layout = QHBoxLayout()
        self.input_lat = QLineEdit()
        self.input_lat.setPlaceholderText("Latitud")
        self.input_lng = QLineEdit()
        self.input_lng.setPlaceholderText("Longitud")
        self.btn_generar_sim = QPushButton("Generar posición cercana")
        self.btn_generar_sim.clicked.connect(self.generar_posicion_simulada)
        posicion_layout.addWidget(QLabel("Coordenadas:"))
        posicion_layout.addWidget(self.input_lat)
        posicion_layout.addWidget(self.input_lng)
        posicion_layout.addWidget(self.btn_generar_sim)
        posicion_group.setLayout(posicion_layout)
        layout.addWidget(posicion_group)

        # === Registro de eventos ===
        eventos_group = QGroupBox("Registrar evento")
        eventos_layout = QVBoxLayout()

        # Botones de eventos
        botones_layout = QHBoxLayout()
        self.btn_llegada = QPushButton("Llegada a punto")
        self.btn_entrega = QPushButton("Entrega confirmada")
        self.btn_desviacion = QPushButton("Registrar desviación")
        self.btn_iniciar = QPushButton("Iniciar ruta")
        self.btn_finalizar = QPushButton("Finalizar ruta")

        self.btn_llegada.clicked.connect(self.registrar_llegada)
        self.btn_entrega.clicked.connect(self.registrar_entrega)
        self.btn_desviacion.clicked.connect(self.registrar_desviacion)
        self.btn_iniciar.clicked.connect(self.iniciar_ruta)
        self.btn_finalizar.clicked.connect(self.finalizar_ruta)

        for btn in [self.btn_iniciar, self.btn_llegada, self.btn_entrega, self.btn_desviacion, self.btn_finalizar]:
            botones_layout.addWidget(btn)

        eventos_layout.addLayout(botones_layout)

        # Observaciones
        obs_layout = QHBoxLayout()
        obs_layout.addWidget(QLabel("Observaciones:"))
        self.input_obs = QTextEdit()
        self.input_obs.setMaximumHeight(60)
        obs_layout.addWidget(self.input_obs)
        eventos_layout.addLayout(obs_layout)

        eventos_group.setLayout(eventos_layout)
        layout.addWidget(eventos_group)

        self.setLayout(layout)

    def cargar_rutas(self):
        """Carga rutas en estado 'programada' o 'en_progreso'."""
        try:
            rutas_prog = obtener_rutas_por_estado("programada")
            rutas_en_curso = obtener_rutas_por_estado("en_progreso")
            todas = rutas_prog + rutas_en_curso

            self.combo_rutas.clear()
            if not todas:
                self.combo_rutas.addItem("No hay rutas para seguir", -1)
            else:
                for r in todas:
                    estado = "📌 Programada" if r["estado"] == "programada" else "🚚 En progreso"
                    self.combo_rutas.addItem(f"{estado} - ID {r['id']}: {r['nombre']}", r["id"])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar las rutas:\n{str(e)}")

    def cargar_detalles_ruta(self):
        """Carga los puntos y detalles de la ruta seleccionada."""
        ruta_id = self.combo_rutas.currentData()
        if ruta_id == -1 or ruta_id is None:
            self.detalles_group.setVisible(False)
            return

        try:
            # Obtener datos de la ruta (simplificado: asumimos que ya está en memoria)
            rutas = obtener_rutas_por_estado("programada") + obtener_rutas_por_estado("en_progreso")
            ruta = next((r for r in rutas if r["id"] == ruta_id), None)
            if not ruta:
                raise ValueError("Ruta no encontrada.")

            self.ruta_seleccionada = ruta
            self.puntos_ruta = obtener_puntos_ruta(ruta_id)

            # Mostrar info
            vehiculos = {v["id"]: v for v in obtener_vehiculos_activos()}
            vehiculo = vehiculos.get(ruta["vehiculo_id"], {})
            placa = vehiculo.get("placa", "Desconocido")
            self.info_ruta.setText(
                f"<b>Ruta:</b> {ruta['nombre']}<br>"
                f"<b>Vehículo:</b> {placa}<br>"
                f"<b>Estado:</b> {ruta['estado']}"
            )

            # Llenar tabla de puntos
            self.tabla_puntos.setRowCount(len(self.puntos_ruta))
            for i, p in enumerate(self.puntos_ruta):
                self.tabla_puntos.setItem(i, 0, QTableWidgetItem(str(p["orden"])))
                self.tabla_puntos.setItem(i, 1, QTableWidgetItem(p["tipo"]))
                self.tabla_puntos.setItem(i, 2, QTableWidgetItem(p["nombre_lugar"]))
                coords = f"{p['lat']:.4f}, {p['lng']:.4f}"
                self.tabla_puntos.setItem(i, 3, QTableWidgetItem(coords))

            self.detalles_group.setVisible(True)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudieron cargar los detalles:\n{str(e)}")

    def generar_posicion_simulada(self):
        """Genera una posición aleatoria cerca del primer punto (simulación)."""
        if not self.puntos_ruta:
            QMessageBox.warning(self, "Advertencia", "Cargue una ruta primero.")
            return

        # Tomar el primer punto como referencia
        ref = self.puntos_ruta[0]
        lat = ref["lat"] + random.uniform(-0.005, 0.005)  # ~500 metros de variación
        lng = ref["lng"] + random.uniform(-0.005, 0.005)

        self.input_lat.setText(f"{lat:.6f}")
        self.input_lng.setText(f"{lng:.6f}")

    def _obtener_coordenadas(self):
        """Obtiene coordenadas de los campos de entrada."""
        try:
            lat = float(self.input_lat.text())
            lng = float(self.input_lng.text())
            return lat, lng
        except ValueError:
            raise ValueError("Coordenadas inválidas. Ingrese números decimales.")

    def iniciar_ruta(self):
        if not self.ruta_seleccionada:
            QMessageBox.warning(self, "Advertencia", "Seleccione una ruta.")
            return
        try:
            self.tracking_service.iniciar_ruta(self.ruta_seleccionada["id"])
            QMessageBox.information(self, "Éxito", "Ruta iniciada con éxito.")
            self.cargar_rutas()  # Refrescar lista
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo iniciar la ruta:\n{str(e)}")

    def registrar_llegada(self):
        self._registrar_evento_con_punto("llegada")

    def registrar_entrega(self):
        self._registrar_evento_con_punto("entrega")

    def _registrar_evento_con_punto(self, tipo: str):
        if not self.ruta_seleccionada or not self.puntos_ruta:
            QMessageBox.warning(self, "Advertencia", "Seleccione una ruta con puntos.")
            return
        try:
            lat, lng = self._obtener_coordenadas()
            # Encontrar el punto más cercano
            for punto in self.puntos_ruta:
                if esta_dentro_de_radio(lat, lng, punto["lat"], punto["lng"], 100):  # 100 metros
                    obs = self.input_obs.toPlainText() or ("Llegada a " + punto["nombre_lugar"])
                    if tipo == "llegada":
                        self.tracking_service.registrar_llegada_a_punto(
                            self.ruta_seleccionada["id"],
                            punto["id"],
                            lat, lng, obs
                        )
                    else:
                        self.tracking_service.registrar_entrega_confirmada(
                            self.ruta_seleccionada["id"],
                            punto["id"],
                            lat, lng, obs
                        )
                    QMessageBox.information(self, "Éxito", f"Evento registrado en '{punto['nombre_lugar']}'.")
                    self.input_obs.clear()
                    return
            QMessageBox.warning(self, "Advertencia", "No está cerca de ningún punto planificado (radio: 100 m).")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar el evento:\n{str(e)}")

    def registrar_desviacion(self):
        if not self.ruta_seleccionada:
            QMessageBox.warning(self, "Advertencia", "Seleccione una ruta.")
            return
        try:
            lat, lng = self._obtener_coordenadas()
            obs = self.input_obs.toPlainText() or "Desviación de ruta registrada"
            self.tracking_service.registrar_desviacion(
                self.ruta_seleccionada["id"], lat, lng, obs
            )
            QMessageBox.information(self, "Éxito", "Desviación registrada.")
            self.input_obs.clear()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo registrar la desviación:\n{str(e)}")

    def finalizar_ruta(self):
        if not self.ruta_seleccionada:
            QMessageBox.warning(self, "Advertencia", "Seleccione una ruta.")
            return
        try:
            self.tracking_service.finalizar_ruta(self.ruta_seleccionada["id"])
            QMessageBox.information(self, "Éxito", "Ruta finalizada con éxito.")
            self.cargar_rutas()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo finalizar la ruta:\n{str(e)}")