# src/test_ubicaciones.py
"""
Script para probar qué ubicaciones son reconocidas por OpenStreetMap (Nominatim).
"""

from api.osm_maps import OsmMapsAPI

# Lista de ubicaciones comunes en Lima (y Perú) para probar
UBICACIONES_A_PROBAR = [
    "Plaza Mayor, Lima, Perú",
    "Parque Kennedy, Miraflores",
    "Aeropuerto Internacional Jorge Chávez, Lima",
    "Jockey Plaza, Santiago de Surco, Lima, Perú",
    "Larcomar, Miraflores, Lima, Perú",
    "Real Plaza Puruchuco, Ate, Lima, Perú",
    "Terminal Terrestre Plaza Norte, Lima, Perú",
    "Plaza San Martín, Lima, Perú",
    "Universidad Nacional de Ingeniería, Lima, Perú",
    "Museo Larco, Lima, Perú",
    "Estadio Nacional del Perú, Lima, Perú",
    "Centro Comercial Plaza Lima Sur, Chorrillos, Lima, Perú",
    "Mega Plaza, Independencia, Lima, Perú",
    "Parque de la Reserva, Lima, Perú",
    "Banco de la Nación - Sede Central, Lima, Perú",
    "Ministerio de Transportes y Comunicaciones, Lima, Perú",
    "Universidad de Lima, Surco, Lima, Perú",
    "Plaza de Armas de Arequipa, Perú",
    "Plaza de Armas de Trujillo, Perú",
    "Plaza de Armas del Cusco, Perú",
    "Centro de Lima",  # ← Este probablemente falle
    "Jr. Huallaga 131, Lima"  # ← Este probablemente falle
]

def probar_ubicaciones():
    api = OsmMapsAPI()
    ubicaciones_validas = []
    print("🔍 Probando ubicaciones con OpenStreetMap...\n")

    for ubicacion in UBICACIONES_A_PROBAR:
        coord = api.geocode(ubicacion)
        if coord:
            print(f"✅ {ubicacion} → {coord}")
            ubicaciones_validas.append(ubicacion)
        else:
            print(f"❌ {ubicacion} → NO RECONOCIDA")

    print(f"\n✅ Ubicaciones válidas ({len(ubicaciones_validas)}):")
    for u in ubicaciones_validas:
        print(f"  - '{u}'")

    # Guardar en un archivo para usar en datos de ejemplo
    with open("ubicaciones_validas.txt", "w", encoding="utf-8") as f:
        for u in ubicaciones_validas:
            f.write(f"'{u}',\n")
    print("\n📄 Lista guardada en 'ubicaciones_validas.txt'")

if __name__ == "__main__":
    probar_ubicaciones()