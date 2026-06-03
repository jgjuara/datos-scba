import os
import glob
from pdf_parser_trabajo import parse_pdf_table_trabajo
from excel_generator_trabajo import create_excel_trabajo

def main():
    """
    Busca todos los archivos PDF de Tribunales de Trabajo y los procesa uno por uno
    generando los archivos Excel en la carpeta sibling 'xlsx'.
    """
    pdf_files = glob.glob(os.path.join("pdfs", "tribunales_trabajo_anual_*.pdf"))
    if not pdf_files:
        print("No se encontraron archivos PDF de trabajo en pdfs/.")
        return

    os.makedirs("xlsx", exist_ok=True)
    for pdf_path in sorted(pdf_files):
        filename = os.path.basename(pdf_path)
        excel_path = os.path.join("xlsx", filename.replace(".pdf", ".xlsx"))
        print(f"Procesando {pdf_path} -> {excel_path}...")
        try:
            data = parse_pdf_table_trabajo(pdf_path)
            create_excel_trabajo(data, excel_path)
            print(f"Completado exitosamente: {excel_path}")
        except Exception as e:
            print(f"Error al procesar {pdf_path}: {e}")

if __name__ == "__main__":
    main()
