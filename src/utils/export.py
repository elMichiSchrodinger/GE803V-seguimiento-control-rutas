# src/utils/export.py
"""
Utilidades para exportar datos a CSV y PDF.
"""

import csv
import os
from datetime import datetime
from typing import List, Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from database.db_manager import obtener_rutas_por_estado, obtener_eventos_ruta, obtener_puntos_ruta


def exportar_rutas_a_csv(rutas: List[Dict[str, Any]], ruta_archivo: str):
    """
    Exporta una lista de rutas a un archivo CSV.
    """
    if not rutas:
        raise ValueError("No hay rutas para exportar.")

    # Asegurar que el directorio existe
    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)

    with open(ruta_archivo, mode='w', newline='', encoding='utf-8') as csvfile:
        campos = [
            "id", "nombre", "vehiculo_id", "estado",
            "distancia_planificada_m", "duracion_planificada_s",
            "created_at", "started_at", "completed_at"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=campos)
        writer.writeheader()
        for ruta in rutas:
            # Filtrar solo los campos deseados
            fila = {k: v for k, v in ruta.items() if k in campos}
            writer.writerow(fila)


def exportar_eventos_ruta_a_csv(ruta_id: int, ruta_archivo: str):
    """
    Exporta todos los eventos de una ruta específica a CSV.
    """
    eventos = obtener_eventos_ruta(ruta_id)
    if not eventos:
        raise ValueError(f"No hay eventos para la ruta {ruta_id}.")

    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)

    with open(ruta_archivo, mode='w', newline='', encoding='utf-8') as csvfile:
        campos = ["id", "ruta_id", "tipo_evento", "punto_ruta_id", "lat", "lng", "timestamp_evento", "observaciones"]
        writer = csv.DictWriter(csvfile, fieldnames=campos)
        writer.writeheader()
        for ev in eventos:
            fila = {k: v for k, v in ev.items() if k in campos}
            writer.writerow(fila)


def exportar_rutas_a_pdf(rutas: List[Dict[str, Any]], ruta_archivo: str):
    """
    Exporta una lista de rutas a un archivo PDF profesional.
    Requiere: pip install reportlab
    """
    if not rutas:
        raise ValueError("No hay rutas para exportar.")

    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)

    doc = SimpleDocTemplate(ruta_archivo, pagesize=LETTER)
    elementos = []
    estilos = getSampleStyleSheet()

    # Título
    titulo = Paragraph("Reporte de Rutas - Seguimiento y Control", estilos['Title'])
    elementos.append(titulo)
    elementos.append(Spacer(1, 12))

    # Tabla de rutas
    datos_tabla = [["ID", "Nombre", "Vehículo", "Estado", "Distancia (km)", "Duración (min)", "Completada"]]
    for r in rutas:
        dist_km = (r["distancia_planificada_m"] or 0) / 1000
        dur_min = (r["duracion_planificada_s"] or 0) / 60
        completada = r["completed_at"][:10] if r["completed_at"] else "Pendiente"
        datos_tabla.append([
            str(r["id"]),
            r["nombre"],
            str(r["vehiculo_id"]),
            r["estado"],
            f"{dist_km:.1f}",
            f"{dur_min:.0f}",
            completada
        ])

    tabla = Table(datos_tabla)
    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elementos.append(tabla)
    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(f"Generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", estilos['Normal']))

    doc.build(elementos)


def exportar_trazabilidad_ruta_a_pdf(ruta_id: int, ruta_archivo: str):
    """
    Exporta la trazabilidad completa de una ruta a PDF (puntos + eventos).
    """
    # Obtener datos
    puntos = obtener_puntos_ruta(ruta_id)
    eventos = obtener_eventos_ruta(ruta_id)
    
    if not puntos and not eventos:
        raise ValueError(f"No hay datos para la ruta {ruta_id}.")

    os.makedirs(os.path.dirname(ruta_archivo), exist_ok=True)

    doc = SimpleDocTemplate(ruta_archivo, pagesize=LETTER)
    elementos = []
    estilos = getSampleStyleSheet()

    # Título
    elementos.append(Paragraph(f"Trazabilidad de la Ruta #{ruta_id}", estilos['Title']))
    elementos.append(Spacer(1, 12))

    # Sección: Puntos de la ruta
    if puntos:
        elementos.append(Paragraph("Puntos Planificados:", estilos['Heading2']))
        datos_puntos = [["Orden", "Tipo", "Lugar", "Dirección", "Coordenadas"]]
        for p in puntos:
            coords = f"{p['lat']:.4f}, {p['lng']:.4f}"
            datos_puntos.append([str(p["orden"]), p["tipo"], p["nombre_lugar"], p["direccion"], coords])
        
        tabla_puntos = Table(datos_puntos)
        tabla_puntos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elementos.append(tabla_puntos)
        elementos.append(Spacer(1, 12))

    # Sección: Eventos
    if eventos:
        elementos.append(Paragraph("Eventos Registrados:", estilos['Heading2']))
        datos_eventos = [["Evento", "Coordenadas", "Fecha/Hora", "Observaciones"]]
        for ev in eventos:
            coords = f"{ev['lat']:.4f}, {ev['lng']:.4f}" if ev['lat'] and ev['lng'] else "N/A"
            fecha = ev['timestamp_evento'][:19] if ev['timestamp_evento'] else ""
            obs = ev['observaciones'] or ""
            datos_eventos.append([ev["tipo_evento"], coords, fecha, obs[:50] + ("..." if len(obs) > 50 else "")])
        
        tabla_eventos = Table(datos_eventos, colWidths=[120, 100, 120, 180])
        tabla_eventos.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        elementos.append(tabla_eventos)

    elementos.append(Spacer(1, 12))
    elementos.append(Paragraph(f"Reporte generado el: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", estilos['Normal']))

    doc.build(elementos)