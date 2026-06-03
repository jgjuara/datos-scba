import datetime
import os
from pathlib import Path
import httpx

# URL base y plantillas para las descargas de estadísticas
BASE_URL = "https://www.scba.gov.ar/planificacion"

CIVIL_TEMPLATE = (
    "{base}/Estads{year}/juzgados%20civiles%20-%20anual%20{year}%20ingresadas%20y%20resueltas.pdf"
)
TRABAJO_TEMPLATE = (
    "{base}/Estads{year}/tribunales%20de%20trabajo%20-%20anual%20{year}%20iniciadas%20y%20resueltas.pdf"
)


def download_pdf(client: httpx.Client, url: str, target_path: Path) -> bool:
    """
    Descarga un archivo PDF de la URL provista y lo guarda en la ruta de destino.

    Precondición:
        - El cliente HTTP debe estar inicializado y abierto.
        - La ruta del directorio padre de target_path debe existir.

    Postcondición:
        - Retorna True si la descarga fue exitosa y se guardó el archivo.
        - Retorna False en caso de error.
    """
    try:
        response = client.get(url, follow_redirects=True)

        if response.status_code != 200:
            print(f"Error {response.status_code} al descargar: {url}")
            return False

        target_path.write_bytes(response.content)
        print(f"Descargado con éxito: {target_path.name}")
        return True

    except httpx.HTTPError as exc:
        print(f"Excepción de red al descargar {url}: {exc}")
        return False
    except IOError as exc:
        print(f"Error de E/S al escribir en {target_path}: {exc}")
        return False


def main() -> None:
    """
    Función principal que coordina la descarga de estadísticas para los años 2017 al año anterior al actual.
    """
    # Definir y crear el directorio de destino para los PDFs
    project_dir = Path(__file__).parent.resolve()
    pdf_dir = project_dir / "pdfs"
    pdf_dir.mkdir(exist_ok=True)

    current_year = datetime.date.today().year
    years = range(2017, current_year)

    # Crear lista de descargas planeadas
    downloads = []
    for year in years:
        downloads.append({
            "url": CIVIL_TEMPLATE.format(base=BASE_URL, year=year),
            "path": pdf_dir / f"juzgados_civiles_anual_{year}.pdf"
        })
        downloads.append({
            "url": TRABAJO_TEMPLATE.format(base=BASE_URL, year=year),
            "path": pdf_dir / f"tribunales_trabajo_anual_{year}.pdf"
        })

    # Ejecutar las descargas usando una sesión persistente de HTTPX
    success_count = 0
    total_count = len(downloads)

    with httpx.Client(timeout=30.0) as client:
        for item in downloads:
            success = download_pdf(client, item["url"], item["path"])
            if success:
                success_count += 1

    print(f"\nDescarga finalizada. Éxito: {success_count}/{total_count}")


if __name__ == "__main__":
    main()
