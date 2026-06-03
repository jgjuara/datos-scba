import sys
import subprocess


def run_pipeline_step(script_name: str) -> None:
    """
    Executes a pipeline step as a separate Python subprocess.

    Assumptions:
        - script_name is a valid file name of a script in the root directory.

    Guarantees:
        - Raises CalledProcessError if the script fails (non-zero return code).
    """
    print(f"=== Starting step: {script_name} ===")
    
    # Run script with current python interpreter to isolate execution context
    result = subprocess.run([sys.executable, script_name], check=True)
    
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, [sys.executable, script_name])
    
    print(f"=== Completed step: {script_name} ===\n")


def main() -> None:
    """
    Orchestrates the entire data pipeline flow from PDF downloading to Parquet unifications.
    """
    pipeline_steps = [
        "download_pdfs.py",
        "extract_juzgados_civiles.py",
        "extract_tribunales_trabajo.py",
        "export_all_to_csv.py",
        "unify_data.py"
    ]

    try:
        for step in pipeline_steps:
            run_pipeline_step(step)
        print("Data pipeline executed successfully from end to end.")
    except subprocess.CalledProcessError as exc:
        print(f"Pipeline failed at step {exc.cmd[1]} with exit code {exc.returncode}.", file=sys.stderr)
        sys.exit(exc.returncode)
    except Exception as exc:
        print(f"Unexpected error in pipeline: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

