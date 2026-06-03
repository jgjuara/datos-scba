import os
import pdfplumber

# Cabeceras estándar definidas para cada esquema de columnas
HEADERS_11 = [
    "Departamento / Sede", "Ingresadas", "Sentencia", "Conciliación",
    "Allanamiento", "Transacción", "Caducidad", "Desistimiento",
    "Interlocutorios", "Incompetencia", "Total Resueltas"
]

HEADERS_13 = [
    "Departamento / Sede", "Ingresadas", "Sentencia", "Conciliación",
    "Allanamiento", "Transacción", "Caducidad", "Desistimiento",
    "Interlocutorios", "Incompetencia", "Total Resueltas", None, "Cant Juzg."
]


def clean_int(val):
    """
    Limpia y convierte un valor de texto a entero si es numérico.
    Elimina espacios y puntos decorativos de miles.
    Retorna None para valores vacíos o guiones.
    """
    if val is None:
        return None
    val_str = str(val).strip().replace(" ", "")
    if val_str in ["", "-", "None"]:
        return None
    try:
        return int(val_str.replace(".", ""))
    except ValueError:
        return val_str


def parse_pdf_table(pdf_path):
    """
    Extrae la tabla principal del PDF usando pdfplumber.
    Clasifica los datos extraídos en títulos, cabeceras, filas de datos,
    totales, promedios y notas al pie de página.
    """
    with pdfplumber.open(pdf_path) as pdf:
        tbl = pdf.pages[0].extract_tables()[0]
        
    title1 = "Juzgados en lo Civil y Comercial"
    group_header = "Resueltas por"
    
    data_rows = []
    total_row = None
    average_row = None
    footnotes = []
    
    in_data = False
    
    # Determinar el año a partir del nombre del archivo si no está en la tabla
    filename = os.path.basename(pdf_path)
    year_str = "".join(filter(str.isdigit, filename))
    title2 = f"Causas Ingresadas y Resueltas por sede - {year_str}"
    
    for r in tbl:
        if not r or all(c is None or str(c).strip() == "" for c in r):
            continue
        
        # Identificar la fila de cabecera de columnas
        if any(c and "Departamento" in str(c) for c in r):
            in_data = True
            continue
        
        if not in_data:
            val = next((str(x).strip() for x in r if x is not None and str(x).strip() != ""), "")
            if "Juzgados" in val:
                title1 = val
            elif "Causas" in val:
                title2 = val
            elif "Resueltas por" in val:
                group_header = val
        else:
            first_val = str(r[0]).strip() if r[0] is not None else ""
            if "Total Provincial" in first_val:
                total_row = r
            elif "Promedio por Juzgado" in first_val:
                average_row = r
            elif any(f in first_val for f in ["Fuente", "preliminares", "No incluye"]):
                footnotes.append(first_val)
            elif first_val:
                data_rows.append(r)
                
    return {
        "title1": title1,
        "title2": title2,
        "group_header": group_header,
        "data_rows": data_rows,
        "total_row": total_row,
        "average_row": average_row,
        "footnotes": footnotes,
        "num_cols": len(tbl[0])
    }
