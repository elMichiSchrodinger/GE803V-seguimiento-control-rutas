# prueba_ruta_service.py
from database.db_manager import init_db, crear_vehiculo
from core.ruta_service import RutaService

# Inicializar base de datos
init_db()

# Crear un vehículo de prueba (si no existe)
try:
    vehiculo_id = crear_vehiculo("XYZ-789", "Ford", "Transit", 1500)
except ValueError:
    # Si ya existe, obtén el ID manualmente o mejora con búsqueda
    vehiculo_id = 1  # Asumimos que ya hay uno

# Programar ruta
service = RutaService()
resultado = service.programar_ruta(
    nombre_ruta="Distribución Diaria - Lima Centro",
    vehiculo_id=vehiculo_id,
    origen="Plaza Mayor, Lima, Perú",
    destino="Aeropuerto Internacional Jorge Chávez, Lima",
    waypoints=["Parque Kennedy, Miraflores"]
)

print("✅ Ruta programada con éxito!")
print("ID:", resultado["ruta_id"])
print("Resumen:", resultado["resumen"])
print("Puntos geocodificados:")
for p in resultado["puntos"]:
    print(f"  - {p['tipo']}: {p['direccion']} → ({p['lat']:.4f}, {p['lng']:.4f})")