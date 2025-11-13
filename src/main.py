# src/main.py
import sys
import os

# Asegurar que el directorio 'src' esté en el path
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
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

    # 🔵 Aplicar estilo global
    style_file = os.path.join(application_path, "gui", "styles.qss")
    if os.path.exists(style_file):
        with open(style_file, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

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