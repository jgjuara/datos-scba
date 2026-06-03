import os
import glob
from pdf_parser_civiles import parse_pdf_table
from excel_generator_civiles import create_excel


import argparse
import datetime


def main():
    """
    Busca los archivos PDF civiles correspondientes (según los parámetros de entrada)
    y los procesa uno por uno generando los archivos Excel en la carpeta sibling 'xlsx'.
    """
    parser = argparse.ArgumentParser(description="Extrae datos de PDFs civiles a Excel.")
    parser.add_argument("--year", type=int, help="Año específico para procesar.")
    parser.add_argument("--all", action="store_true", help="Procesar todos los PDFs disponibles.")
    args = parser.parse_args()

    current_year = datetime.date.today().year

    # Determinar qué archivos procesar según los parámetros provistos
    if args.year:
        pdf_pattern = os.path.join("pdfs", f"juzgados_civiles_anual_{args.year}.pdf")
    elif args.all:
        pdf_pattern = os.path.join("pdfs", "juzgados_civiles_anual_*.pdf")
    else:
        # Por defecto procesa el último año disponible
        target_year = current_year - 1
        pdf_pattern = os.path.join("pdfs", f"juzgados_civiles_anual_{target_year}.pdf")

    pdf_files = glob.glob(pdf_pattern)
    if not pdf_files:
        print(f"No se encontraron archivos PDF civiles que coincidan con: {pdf_pattern}")
        return

    os.makedirs("xlsx", exist_ok=True)
    for pdf_path in sorted(pdf_files):
        filename = os.path.basename(pdf_path)
        excel_path = os.path.join("xlsx", filename.replace(".pdf", ".xlsx"))
        print(f"Procesando {pdf_path} -> {excel_path}...")
        try:
            data = parse_pdf_table(pdf_path)
            create_excel(data, excel_path)
            print(f"Completado exitosamente: {excel_path}")
        except Exception as e:
            print(f"Error al procesar {pdf_path}: {e}")


if __name__ == "__main__":
    main()

