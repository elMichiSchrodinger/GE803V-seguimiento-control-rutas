# src/main.py
"""
Punto de entrada principal de la aplicación.
Compatible con PyInstaller para generar .exe.
"""

import sys
import os

# Determinar la ruta base (para desarrollo y .exe)
if getattr(sys, 'frozen', False):
    # Ejecutando como .exe
    base_path = sys._MEIPASS
    application_path = os.path.dirname(sys.executable)
else:
    # Ejecutando como script
    base_path = os.path.dirname(os.path.abspath(__file__))
    application_path = base_path
    sys.path.insert(0, application_path)

# 🔴 ¡IMPORTANTE! Importar WebEngine antes de QApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView

from PyQt6.QtWidgets import QApplication
from database.db_manager import init_db
from gui.main_window import MainWindow


def main():
    # Inicializar la base de datos
    try:
        init_db()
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        sys.exit(1)

    # Crear la APLICACIÓN (solo una vez)
    app = QApplication(sys.argv)
    app.setApplicationName("Seguimiento y Control de Rutas")
    app.setApplicationVersion("1.0")

    # 🔵 Aplicar estilo global (funciona en desarrollo y .exe)
    style_file = os.path.join(base_path, "gui", "styles.qss")
    if os.path.exists(style_file):
        with open(style_file, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    else:
        print("⚠️ Advertencia: No se encontró el archivo de estilos 'gui/styles.qss'")

    # Crear y mostrar la ventana principal
    try:
        window = MainWindow()
        window.show()
    except Exception as e:
        print(f"❌ Error al crear la ventana principal: {e}")
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()