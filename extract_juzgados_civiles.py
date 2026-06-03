import os
import glob
from pdf_parser_civiles import parse_pdf_table
from excel_generator_civiles import create_excel


def main():
    """
    Busca todos los archivos PDF civiles y los procesa uno por uno
    generando los archivos Excel en la carpeta sibling 'xlsx'.
    """
    pdf_files = glob.glob(os.path.join("pdfs", "juzgados_civiles_anual_*.pdf"))
    if not pdf_files:
        print("No se encontraron archivos PDF civiles en pdfs/.")
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
