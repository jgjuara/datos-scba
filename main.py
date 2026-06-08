import sys
import subprocess
import argparse
import datetime


def run_pipeline_step(script_name: str, args_list: list[str]) -> None:
    """
    Executes a pipeline step as a separate Python subprocess.

    Assumptions:
        - script_name is a valid file name of a script in the root directory.
        - args_list is a list of string arguments to pass to the script.

    Guarantees:
        - Raises CalledProcessError if the script fails (non-zero return code).
    """
    print(f"=== Starting step: {script_name} ===")
    
    command = [sys.executable, script_name] + args_list
    # Run script with current python interpreter to isolate execution context
    result = subprocess.run(command, check=True)
    
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command)
    
    print(f"=== Completed step: {script_name} ===\n")


def main() -> None:
    """
    Orchestrates the entire data pipeline flow from PDF downloading to Parquet unifications.
    """
    parser = argparse.ArgumentParser(description="Orquesta el pipeline completo de estadísticas judiciales.")
    parser.add_argument("--year", type=int, help="Año específico para procesamiento incremental.")
    parser.add_argument("--all", action="store_true", help="Procesar todo el histórico desde cero (2017-presente).")
    args = parser.parse_args()

    pipeline_steps = [
        "download_pdfs.py",
        "extract_juzgados_civiles.py",
        "extract_tribunales_trabajo.py",
        "export_all_to_csv.py",
        "unify_data.py",
        "aggregate_data.py",
        "export_parquet_to_csv.py",
        "export_tribunales_por_sede.py"
    ]

    # Determinar qué argumentos propagar a cada paso
    sub_args = []
    if args.year:
        sub_args = ["--year", str(args.year)]
    elif args.all:
        sub_args = ["--all"]
    else:
        # Por defecto, ejecutar incrementalmente para el último año disponible
        current_year = datetime.date.today().year
        sub_args = ["--year", str(current_year - 1)]

    print(f"Iniciando ejecución del pipeline con argumentos: {' '.join(sub_args)}")

    try:
        for step in pipeline_steps:
            step_args = [] if step in ("export_parquet_to_csv.py", "aggregate_data.py") else sub_args
            run_pipeline_step(step, step_args)
        print("Data pipeline executed successfully from end to end.")
    except subprocess.CalledProcessError as exc:
        print(f"Pipeline failed at step {exc.cmd[1]} with exit code {exc.returncode}.", file=sys.stderr)
        sys.exit(exc.returncode)
    except Exception as exc:
        print(f"Unexpected error in pipeline: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

