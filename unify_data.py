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
    csv_dir = "csv"
    output_dir = "parquet"
    os.makedirs(output_dir, exist_ok=True)

    civil_pattern = os.path.join(csv_dir, "juzgados_civiles_anual_*.csv")
    trabajo_pattern = os.path.join(csv_dir, "tribunales_trabajo_anual_*.csv")

    civil_files = sorted(glob.glob(civil_pattern))
    trabajo_files = sorted(glob.glob(trabajo_pattern))

    # Raise explicit error if no data files are found
    if not civil_files:
        raise FileNotFoundError("No civil court CSV files found in directory: " + csv_dir)
    if not trabajo_files:
        raise FileNotFoundError("No labor court CSV files found in directory: " + csv_dir)

    print("Processing civil court files...")
    civil_df = process_csv_files(civil_files)

    print("Processing labor court files...")
    trabajo_df = process_csv_files(trabajo_files)

    # Establish and save unified list of seats and departments
    civil_seats = set(civil_df["departamento/sede"].unique())
    trabajo_seats = set(trabajo_df["departamento/sede"].unique())
    unified_seats = sorted(list(civil_seats | trabajo_seats))

    seats_df = pd.DataFrame({"departamento/sede": unified_seats})

    # Save to parquet files
    seats_path = os.path.join(output_dir, "sedes_departamentos.parquet")
    civil_path = os.path.join(output_dir, "juzgados_civiles_unificados.parquet")
    trabajo_path = os.path.join(output_dir, "tribunales_trabajo_unificados.parquet")

    seats_df.to_parquet(seats_path, index=False)
    civil_df.to_parquet(civil_path, index=False)
    trabajo_df.to_parquet(trabajo_path, index=False)

    print(f"Success! Saved unified files to '{output_dir}/':")
    print(f"  - sedes_departamentos.parquet ({len(seats_df)} records)")
    print(f"  - juzgados_civiles_unificados.parquet ({len(civil_df)} records)")
    print(f"  - tribunales_trabajo_unificados.parquet ({len(trabajo_df)} records)")


if __name__ == "__main__":
    main()
