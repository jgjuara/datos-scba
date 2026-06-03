import os
import glob
import csv
import re
from export_civil_xlsx_to_csv import export_xlsx_to_csv, CSV_HEADERS


def validate_csv(csv_path: str, expected_year: int) -> bool:
    """
    Valida la integridad de un archivo CSV generado.

    Precondiciones:
        - csv_path es la ruta de un archivo CSV existente.
        - expected_year es el año entero esperado para todos los registros del archivo.

    Postcondiciones:
        - Retorna True si todas las validaciones son exitosas, de lo contrario False.
    """
    if not os.path.exists(csv_path):
        print(f"  [ERROR] El archivo no existe: {csv_path}")
        return False

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    if not rows:
        print(f"  [ERROR] El archivo está vacío: {csv_path}")
        return False

    # 1. Validar Cabeceras
    headers = rows[0]
    if headers != CSV_HEADERS:
        print(f"  [ERROR] Cabeceras incorrectas. Esperado: {CSV_HEADERS}, Obtenido: {headers}")
        return False

    data_rows = rows[1:]
    if not data_rows:
        print(f"  [ERROR] El archivo solo contiene cabeceras: {csv_path}")
        return False

    has_total = False
    has_avg = False

    for idx, row in enumerate(data_rows, 1):
        # 2. Validar cantidad de columnas (debe ser exactamente 12)
        if len(row) != 12:
            print(f"  [ERROR] Fila {idx} tiene {len(row)} columnas en lugar de 12.")
            return False

        dept = row[0].strip()

        # 3. Validar que la sede no esté vacía
        if not dept:
            print(f"  [ERROR] Fila {idx} tiene la sede vacía.")
            return False

        # 4. Validar el año
        year_str = row[11].strip()
        if year_str != str(expected_year):
            print(f"  [ERROR] Fila {idx} tiene un año incorrecto. Esperado: {expected_year}, Obtenido: {year_str}")
            return False

        if "Total Provincial" in dept:
            has_total = True
        elif "Promedio por Juzgado" in dept or "Promedio por Tribunal" in dept:
            has_avg = True

    # 5. Validar existencia de filas especiales
    if not has_total:
        print(f"  [ERROR] No se encontró la fila 'Total Provincial'.")
        return False
    if not has_avg:
        print(f"  [ERROR] No se encontró la fila de promedio ('Promedio por Juzgado' o 'Promedio por Tribunal').")
        return False

    return True


def main():
    """
    Busca, exporta y valida todos los archivos Excel de juzgados civiles y
    tribunales de trabajo.
    """
    # 1. Buscar archivos Excel de Civil y Trabajo
    civil_patterns = os.path.join("xlsx", "juzgados_civiles_anual_*.xlsx")
    trabajo_patterns = os.path.join("xlsx", "tribunales_trabajo_anual_*.xlsx")

    excel_files = sorted(glob.glob(civil_patterns)) + sorted(glob.glob(trabajo_patterns))

    if not excel_files:
        print("No se encontraron archivos Excel en la carpeta xlsx/.")
        return

    print(f"Se encontraron {len(excel_files)} archivos para procesar.")
    success_count = 0
    failure_count = 0

    for xlsx_path in excel_files:
        filename = os.path.basename(xlsx_path)
        # Inferir año
        year_match = re.search(r"(20\d{2})", filename)
        if not year_match:
            print(f"[FALLA] No se pudo inferir el año de {filename}. Se omite.")
            failure_count += 1
            continue

        year = int(year_match.group(1))
        csv_name = filename.replace(".xlsx", ".csv")
        csv_path = os.path.join("csv", csv_name)

        print(f"\nProcesando: {xlsx_path} -> {csv_path}")
        try:
            export_xlsx_to_csv(xlsx_path, csv_path)

            # Validar integridad del CSV generado
            if validate_csv(csv_path, year):
                print(f"  [OK] Exportación y validación exitosa para el año {year}.")
                success_count += 1
            else:
                print(f"  [FALLA] Validación fallida para {csv_path}.")
                failure_count += 1
        except Exception as e:
            print(f"  [FALLA] Error al procesar {xlsx_path}: {e}")
            failure_count += 1

    print("\n" + "="*40)
    print(f"Procesamiento Finalizado:")
    print(f"  Exitosos: {success_count}")
    print(f"  Fallidos: {failure_count}")
    print("="*40)


if __name__ == "__main__":
    main()
