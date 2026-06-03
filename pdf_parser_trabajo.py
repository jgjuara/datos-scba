import os
import pdfplumber

def parse_pdf_table_trabajo(pdf_path: str) -> dict:
    """
    Parsea el PDF de Tribunales de Trabajo y extrae los datos tabulares e institucionales.

    Pre-condición: pdf_path debe ser una ruta válida a un archivo PDF existente.
    Post-condición: Retorna un diccionario con títulos, filas de datos, totales,
                    promedios, notas al pie y fecha del pie de página.
    """
    # Abrir el PDF y extraer la primera página
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        tables = page.extract_tables()
        if not tables:
            raise ValueError(f"No se encontraron tablas en el PDF: {pdf_path}")
        tbl = tables[0]
        text = page.extract_text() or ""

    title1 = "Tribunales de Trabajo"
    title2 = ""
    group_header = "Resueltas por"
    
    data_rows = []
    total_row = None
    average_row = None
    footnotes = []
    
    in_data = False
    
    # Determinar el año a partir del nombre del archivo por si no se extrae correctamente
    filename = os.path.basename(pdf_path)
    year_str = "".join(filter(str.isdigit, filename))
    title2 = f"Causas Ingresadas y Resueltas por sede - {year_str}"
    
    for r in tbl:
        # Omitir filas vacías o con celdas vacías
        if not r or all(c is None or str(c).strip() == "" for c in r):
            continue
            
        first_val = str(r[0]).strip() if r[0] is not None else ""
        
        # Identificar la fila de cabeceras de columnas
        if "Departamento" in first_val:
            in_data = True
            continue
            
        if not in_data:
            # Extraer títulos antes del cuerpo de la tabla
            val = next((str(x).strip() for x in r if x is not None and str(x).strip() != ""), "")
            if "Tribunales" in val:
                title1 = val
            elif "Causas" in val:
                title2 = val
            elif "Resueltas por" in val:
                group_header = val
        else:
            # Procesar filas del cuerpo de la tabla
            if "Total Provincial" in first_val:
                total_row = r
            elif "Promedio por Tribunal" in first_val:
                average_row = r
            elif any(f in first_val for f in ["Fuente", "preliminares", "No incluye"]):
                footnotes.append(first_val)
            elif first_val:
                data_rows.append(r)
                
    # Extraer la fecha y texto del pie de página institucional del texto de la página
    date_str = ""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines:
        if "Area de Estadísticas" in line or "Secretaría de Planificación" in line:
            parts = line.split()
            if parts:
                date_str = parts[-1]
            break
            
    return {
        "title1": title1,
        "title2": title2,
        "group_header": group_header,
        "data_rows": data_rows,
        "total_row": total_row,
        "average_row": average_row,
        "footnotes": footnotes,
        "date_str": date_str,
        "num_cols": len(tbl[0]) if tbl else 13
    }
