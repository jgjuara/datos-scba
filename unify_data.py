"""
Module for unifying civil and labor court CSV data into normalized long-format Parquet files.

This script processes annual reports from 2017-2025, normalizes court seat and department names,
filters out provincial totals/averages, reshapes the data into a long format,
and outputs Parquet tables.
"""

import os
import glob
import re
import pandas as pd


def normalize_seat_name(name: str) -> str:
    """
    Normalizes court department and seat names for consistency across years and forums.

    Assumptions:
        - name is a string representing a department/seat name.

    Guarantees:
        - Returns a clean string with stripped footnotes, corrected typos,
          and consistent uppercase/capitalization.
    """
    if not isinstance(name, str):
        return ""

    # Remove extra spaces
    name = " ".join(name.split())

    # Remove footnote numbers (e.g., " (1)" or " (2)") at the end of the text
    name = re.sub(r"\s*\(\d+\)$", "", name)

    # Standardize Moreno-General Rodriguez abbreviations
    if name == "MORENO-GENERAL RODRIGUEZ":
        name = "MORENO-GRAL.RODRIGUEZ"

    # Standardize Bahia Blanca Tres Arroyos naming mismatch
    if name == "B. BLANCA Sede TRES ARROYOS":
        name = "BAHIA BLANCA Sede TRES ARROYOS"

    # Standardize case mismatch in Lomas de Zamora seats
    if name in ("LOMAS DE ZAMORA Sede Avellaneda", "LOMAS DE ZAMORA Sede AVELLANEDA"):
        name = "LOMAS DE ZAMORA Sede AVELLANEDA"
    if name in ("LOMAS DE ZAMORA Sede Lanús", "LOMAS DE ZAMORA Sede LANUS"):
        name = "LOMAS DE ZAMORA Sede LANUS"

    return name


def is_summary_row(name: str) -> bool:
    """
    Checks if a row is a summary or average row rather than a specific court/seat.

    Assumptions:
        - name is a normalized department/seat name.
    """
    lower_name = name.lower()
    return "total provincial" in lower_name or "promedio por" in lower_name


def process_csv_files(file_paths: list[str]) -> pd.DataFrame:
    """
    Loads, cleans, and merges multiple CSV files into a single long-format DataFrame.

    Assumptions:
        - file_paths contains valid paths to court CSV files.

    Guarantees:
        - Returns a unified long-format DataFrame containing 'anio',
          'departamento/sede', 'tipo', and 'valor' columns.
    """
    # Guard clause for empty file list
    if not file_paths:
        raise ValueError("No file paths provided for processing.")

    all_dfs = []
    value_vars = [
        "Ingresadas",
        "Sentencia",
        "Conciliación",
        "Allanamiento",
        "Transacción",
        "Caducidad",
        "Desistimiento",
        "Interlocutorios",
        "Incompetencia",
        "Total Resueltas"
    ]

    for path in file_paths:
        df = pd.read_csv(path)

        # Ensure correct column casing and names
        df.rename(columns={"Anio": "anio"}, inplace=True)
        df["departamento/sede"] = df["Departamento / Sede"].apply(normalize_seat_name)

        # Filter out aggregate total and average rows
        df = df[~df["departamento/sede"].apply(is_summary_row)]

        # Melt wide columns (the court activity types) into a long format
        melted_df = df.melt(
            id_vars=["anio", "departamento/sede"],
            value_vars=value_vars,
            var_name="tipo",
            value_name="valor"
        )

        all_dfs.append(melted_df)

    # Combine all individual year DataFrames
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Cast types and fill missing values with 0
    combined_df["anio"] = combined_df["anio"].astype(int)
    combined_df["valor"] = combined_df["valor"].fillna(0).astype(int)
    combined_df["departamento/sede"] = combined_df["departamento/sede"].astype(str)
    combined_df["tipo"] = combined_df["tipo"].astype(str)

    # Rearrange columns to match requested tuple structure
    return combined_df[["anio", "departamento/sede", "tipo", "valor"]]


def main() -> None:
    """
    Main execution flow. Searches for files, orchestrates processing, and saves Parquet output.
    """
    import argparse
    import datetime

    parser = argparse.ArgumentParser(description="Unifica datos CSV civiles y laborales en archivos Parquet.")
    parser.add_argument("--year", type=int, help="Año específico para procesar de forma incremental.")
    parser.add_argument("--all", action="store_true", help="Procesar todos los años desde cero.")
    args = parser.parse_args()

    csv_dir = "csv"
    output_dir = "parquet"
    os.makedirs(output_dir, exist_ok=True)

    current_year = datetime.date.today().year
    target_year = args.year if args.year else (None if args.all else current_year - 1)

    seats_path = os.path.join(output_dir, "sedes_departamentos.parquet")
    civil_parquet_path = os.path.join(output_dir, "juzgados_civiles_unificados.parquet")
    trabajo_parquet_path = os.path.join(output_dir, "tribunales_trabajo_unificados.parquet")

    # Determinar si hacemos procesamiento incremental
    is_incremental = (
        target_year is not None 
        and os.path.exists(civil_parquet_path) 
        and os.path.exists(trabajo_parquet_path)
    )

    if is_incremental:
        print(f"Modo incremental: actualizando datos para el año {target_year}...")
        
        # 1. Cargar Parquet existentes
        civil_existing_df = pd.read_parquet(civil_parquet_path)
        trabajo_existing_df = pd.read_parquet(trabajo_parquet_path)

        # 2. Filtrar filas del año a actualizar para asegurar idempotencia
        civil_existing_df = civil_existing_df[civil_existing_df["anio"] != target_year]
        trabajo_existing_df = trabajo_existing_df[trabajo_existing_df["anio"] != target_year]

        # 3. Identificar nuevos archivos CSV
        civil_csv = os.path.join(csv_dir, f"juzgados_civiles_anual_{target_year}.csv")
        trabajo_csv = os.path.join(csv_dir, f"tribunales_trabajo_anual_{target_year}.csv")

        # Procesar e integrar civil si el archivo existe
        if os.path.exists(civil_csv):
            print(f"Procesando civil: {civil_csv}")
            new_civil_df = process_csv_files([civil_csv])
            civil_df = pd.concat([civil_existing_df, new_civil_df], ignore_index=True)
        else:
            print(f"Advertencia: No se encontró {civil_csv}. Se conserva el histórico civil.")
            civil_df = civil_existing_df

        # Procesar e integrar trabajo si el archivo existe
        if os.path.exists(trabajo_csv):
            print(f"Procesando trabajo: {trabajo_csv}")
            new_trabajo_df = process_csv_files([trabajo_csv])
            trabajo_df = pd.concat([trabajo_existing_df, new_trabajo_df], ignore_index=True)
        else:
            print(f"Advertencia: No se encontró {trabajo_csv}. Se conserva el histórico trabajo.")
            trabajo_df = trabajo_existing_df

    else:
        print("Modo completo: procesando todos los archivos CSV históricos...")
        civil_pattern = os.path.join(csv_dir, "juzgados_civiles_anual_*.csv")
        trabajo_pattern = os.path.join(csv_dir, "tribunales_trabajo_anual_*.csv")

        civil_files = sorted(glob.glob(civil_pattern))
        trabajo_files = sorted(glob.glob(trabajo_pattern))

        # Si se busca un año específico pero no hay parquet previo, filtramos para procesar solo ese
        if target_year is not None:
            civil_files = [f for f in civil_files if f"_{target_year}.csv" in f]
            trabajo_files = [f for f in trabajo_files if f"_{target_year}.csv" in f]

        if not civil_files:
            raise FileNotFoundError(f"No se encontraron archivos CSV civiles para procesar.")
        if not trabajo_files:
            raise FileNotFoundError(f"No se encontraron archivos CSV de trabajo para procesar.")

        print(f"Procesando archivos civiles: {civil_files}")
        civil_df = process_csv_files(civil_files)

        print(f"Procesando archivos de trabajo: {trabajo_files}")
        trabajo_df = process_csv_files(trabajo_files)

    # 4. Actualizar lista maestra de sedes y departamentos unificada
    civil_seats = set(civil_df["departamento/sede"].unique())
    trabajo_seats = set(trabajo_df["departamento/sede"].unique())
    unified_seats = sorted(list(civil_seats | trabajo_seats))

    seats_df = pd.DataFrame({"departamento/sede": unified_seats})

    # Guardar
    seats_df.to_parquet(seats_path, index=False)
    civil_df.to_parquet(civil_parquet_path, index=False)
    trabajo_df.to_parquet(trabajo_parquet_path, index=False)

    print(f"¡Éxito! Archivos guardados en '{output_dir}/':")
    print(f"  - sedes_departamentos.parquet ({len(seats_df)} registros)")
    print(f"  - juzgados_civiles_unificados.parquet ({len(civil_df)} registros)")
    print(f"  - tribunales_trabajo_unificados.parquet ({len(trabajo_df)} registros)")


if __name__ == "__main__":
    main()

