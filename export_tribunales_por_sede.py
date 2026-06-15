"""
Extrae la cantidad de tribunales por sede judicial desde los PDFs de Trabajo.

El CSV generado se publica en static/data para consumo directo del frontend u
otros procesos posteriores. La fuente es la columna "Cant Trib." del PDF.
"""

import argparse
import csv
import datetime
import glob
import os
import re

from pdf_parser_trabajo import parse_pdf_table_trabajo
from unify_data import normalize_seat_name


OUTPUT_HEADERS = ["anio", "sede", "cant_tribunales"]
OUTPUT_PATH = os.path.join("static", "data", "tribunales_por_sede.csv")


def clean_int(value) -> int | None:
    """
    Normaliza enteros extraídos desde celdas PDF.

    Precondición: value representa una cantidad entera o está vacío.
    Garantía: retorna un entero no negativo o None si el valor no existe.
    """
    if value is None:
        return None

    normalized = str(value).strip().replace(".", "").replace(" ", "")
    if normalized in ("", "-", "None"):
        return None

    return int(normalized)


def infer_year(pdf_path: str) -> int:
    """
    Infiere el año desde el nombre del PDF.
    """
    filename = os.path.basename(pdf_path)
    match = re.search(r"(20\d{2})", filename)
    if not match:
        raise ValueError(f"No se pudo inferir el año del archivo: {pdf_path}")
    return int(match.group(1))


def find_pdf_files(year: int | None, process_all: bool) -> list[str]:
    """
    Resuelve qué PDFs de tribunales de trabajo debe procesar el paso.
    """
    if year is not None:
        pattern = os.path.join("pdfs", f"tribunales_trabajo_anual_{year}.pdf")
    elif process_all:
        pattern = os.path.join("pdfs", "tribunales_trabajo_anual_*.pdf")
    else:
        target_year = datetime.date.today().year - 1
        pattern = os.path.join("pdfs", f"tribunales_trabajo_anual_{target_year}.pdf")

    return sorted(glob.glob(pattern))


def extract_tribunales_por_sede(pdf_path: str) -> list[dict[str, int | str]]:
    """
    Extrae anio, sede y cant_tribunales desde un PDF de Tribunales de Trabajo.

    La columna "Cant Trib." es la última columna del esquema de 13 columnas
    generado por el parser de trabajo.
    """
    year = infer_year(pdf_path)
    data = parse_pdf_table_trabajo(pdf_path)
    rows = []

    for row in data["data_rows"]:
        sede = normalize_seat_name(str(row[0]).strip()) if row and row[0] is not None else ""
        if not sede:
            continue

        cant_tribunales = clean_int(row[12] if data["num_cols"] >= 13 and len(row) > 12 else None)
        rows.append(
            {
                "anio": year,
                "sede": sede,
                "cant_tribunales": cant_tribunales,
            }
        )

    return rows


def write_csv(rows: list[dict[str, int | str]], output_path: str) -> None:
    """
    Escribe el CSV final en static/data.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_path, mode="w", encoding="utf-8", newline="\n") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=OUTPUT_HEADERS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def read_existing_csv(output_path: str) -> list[dict[str, int | str]]:
    """
    Lee el CSV existente si está disponible para permitir actualizaciones incrementales.
    """
    if not os.path.exists(output_path):
        return []

    with open(output_path, mode="r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        return [row for row in reader]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera static/data/tribunales_por_sede.csv desde PDFs de Trabajo."
    )
    parser.add_argument("--year", type=int, help="Año específico para procesar.")
    parser.add_argument("--all", action="store_true", help="Procesar todos los PDFs disponibles.")
    args = parser.parse_args()

    pdf_files = find_pdf_files(args.year, args.all)
    if not pdf_files:
        print("No se encontraron PDFs de tribunales de trabajo para procesar.")
        return

    extracted_rows = []
    for pdf_path in pdf_files:
        extracted = extract_tribunales_por_sede(pdf_path)
        extracted_rows.extend(extracted)
        print(f"[OK] {pdf_path}: {len(extracted)} sedes")

    rows = extracted_rows
    if not args.all:
        extracted_years = {str(row["anio"]) for row in extracted_rows}
        existing_rows = read_existing_csv(OUTPUT_PATH)
        rows = [
            row
            for row in existing_rows
            if str(row.get("anio", "")) not in extracted_years
        ] + extracted_rows

    rows.sort(key=lambda row: (int(row["anio"]), str(row["sede"])))
    write_csv(rows, OUTPUT_PATH)
    print(f"CSV generado: {OUTPUT_PATH} ({len(rows)} filas)")


if __name__ == "__main__":
    main()
