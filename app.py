import base64
import io
import json
import logging
import random
import re
import tempfile
import time
import uuid
from datetime import date
from html import escape
from pathlib import Path
from typing import Dict, List, Tuple

import requests
import streamlit as st
from PIL import Image


st.set_page_config(page_title="Descargador de periódicos", layout="wide")


LOGGER = logging.getLogger("ediciones")
MAX_IMAGE_BYTES = 12 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
MAX_PDF_BYTES = 100 * 1024 * 1024
# Umbral de la descarga por la app. Los PDF directos de 100 MB o más
# se abren desde su URL de origen, sin limitar su tamaño en el navegador.
MAX_DIRECT_PDF_BYTES = 100_000_000
MAX_SESSION_BYTES = 500 * 1024 * 1024
AUTO_FILE_BYTES = 8 * 1024 * 1024
AUTO_BATCH_BYTES = 16 * 1024 * 1024


class ResourceLimitError(RuntimeError):
    """Detiene una descarga antes de que agote los recursos de la aplicación."""


class PdfWriteError(RuntimeError):
    """Un error al guardar no puede tratarse como una página ausente."""


EDITIONS: Dict[str, Dict[str, object]] = {
    # =========================
    # DIARIOS INTELICAST
    # =========================
    "Reforma (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "Reforma5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "El Universal (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "ElUniversal5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "Excelsior (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "Excelsior5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "El Financiero (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "ElFinanciero5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "La Cronica (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "LaCronica5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "El Economista (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "ElEconomista5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "Publimetro (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "Publimetro5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "24 Horas (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "24Horas.pdf",
        "published_weekdays": {0, 1, 2, 3, 4},
    },
    "Reporte Indigo (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "Indigo.pdf",
        "published_weekdays": {0, 1, 2, 3, 4},
    },
    "ContraReplica (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "ContraReplica5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "El Heraldo (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "ElHeraldo5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "El Sol de México (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "ElSol5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "La Razon (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "LaRazon5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "Milenio (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "Milenio5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "La Jornada (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "LaJornada5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "Diario de Mexico (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "Diariodemexico.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "Ovaciones (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "Ovaciones.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "Unomasuno (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "Unomasuno.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "Metro (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "Metro.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "La Prensa (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "Laprensa.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },

    # =========================
    # EDICIONES ORIGINALES
    # =========================
    "El Universal": {
        "type": "el_universal",
        "start_page": 1,
        "default_attempts": 80,
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "El Financiero": {
        "type": "elfinanciero_pdf",
        "published_weekdays": {0, 1, 2, 3, 4},
    },
    "Excelsior": {
        "type": "direct_pdf_template",
        "url_template": "https://impreso.excelsior.com.mx/Periodico/flip-nacional/{DD}-{MM}-{YYYY}/portada.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
     "Adrenalina": {
        "type": "direct_pdf_template",
        "url_template": "https://impreso.excelsior.com.mx/Periodico/flip-adrenalina/{DD}-{MM}-{YYYY}/portada.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "La Jornada": {
        "type": "direct_pdf_template",
        "url_template": "https://wp.lajornada.prod.andes.news/wp-content/uploads/{YYYY}/{MM}/La_Jornada_{YYYY}_{MM}_{DD}.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "Milenio Nacional": {
        "type": "milenio",
        "folder": "Nacional",
        "code": "NAC",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio León": {
        "type": "milenio",
        "folder": "Leon",
        "code": "LEO",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Tamaulipas": {
        "type": "milenio",
        "folder": "Tamaulipas",
        "code": "TAM",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Jalisco": {
        "type": "milenio",
        "folder": "Jalisco",
        "code": "JAL",
        "start_page": 0,
        "default_attempts": 86,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Puebla": {
        "type": "milenio",
        "folder": "Puebla",
        "code": "PUE",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Monterrey": {
        "type": "milenio",
        "folder": "Monterrey",
        "code": "MON",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Edomex": {
        "type": "milenio",
        "folder": "Edomex",
        "code": "MEX",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Hidalgo": {
        "type": "milenio",
        "folder": "Hidalgo",
        "code": "HID",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Laguna": {
        "type": "milenio",
        "folder": "Laguna",
        "code": "LAG",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "La Jornada EdoMex": {
        "type": "direct_pdf_template",
        "url_template": "https://wp.lajornada.prod.andes.news/wp-content/uploads/{YYYY}/{MM}/EdomexImpresion-{DD}{MM}{YYYY}.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
}


ORDERED_EDITIONS = [
    # Originales
    "El Universal",
    "El Financiero",
    "La Jornada",
    "Excelsior",
    "Adrenalina",
    "Milenio Nacional",
    "Milenio León",
    "Milenio Tamaulipas",
    "Milenio Jalisco",
    "Milenio Puebla",
    "Milenio Monterrey",
    "Milenio Edomex",
    "Milenio Hidalgo",
    "Milenio Laguna",
    "La Jornada EdoMex",    
    # Intelicast
    "Reforma (escaneado)",
    "El Universal (escaneado)",
    "Excelsior (escaneado)",
    "El Financiero (escaneado)",
    "La Cronica (escaneado)",
    "El Economista (escaneado)",
    "Publimetro (escaneado)",
    "24 Horas (escaneado)",
    "Reporte Indigo (escaneado)",
    "ContraReplica (escaneado)",
    "El Heraldo (escaneado)",
    "El Sol de México (escaneado)",
    "La Razon (escaneado)",
    "Milenio (escaneado)",
    "La Jornada (escaneado)",
    "Diario de Mexico (escaneado)",
    "Ovaciones (escaneado)",
    "Unomasuno (escaneado)",
    "Metro (escaneado)",
    "La Prensa (escaneado)",
]


def init_state() -> None:
    # Al actualizar el formato de resultados, liberar la sesión anterior.
    if st.session_state.get("result_schema") != 3:
        old_directory = st.session_state.pop("download_directory", None)
        if old_directory is not None:
            old_directory.cleanup()
        st.session_state.results = {}
        st.session_state.statuses = {}
        st.session_state.last_bulk_key = None
        st.session_state.auto_downloaded = set()
        st.session_state.result_schema = 3
    if "results" not in st.session_state:
        st.session_state.results = {}
    if "statuses" not in st.session_state:
        st.session_state.statuses = {}
    if "last_bulk_key" not in st.session_state:
        st.session_state.last_bulk_key = None
    if "last_single_auto_key" not in st.session_state:
        st.session_state.last_single_auto_key = None
    if "download_directory" not in st.session_state:
        # TemporaryDirectory se limpia cuando Streamlit libera la sesión.
        st.session_state.download_directory = tempfile.TemporaryDirectory(
            prefix="ediciones_"
        )


def new_pdf_path() -> Path:
    return Path(st.session_state.download_directory.name) / f"{uuid.uuid4().hex}.pdf"


def remove_result(edition_name: str) -> None:
    result = st.session_state.results.pop(edition_name, None)
    if result and result.get("pdf_path"):
        Path(str(result["pdf_path"])).unlink(missing_ok=True)
    if result:
        st.session_state.auto_downloaded.discard(str(result["auto_key"]))
    st.session_state.statuses.pop(edition_name, None)


def clear_results() -> None:
    for edition_name in list(st.session_state.results):
        remove_result(edition_name)
    st.session_state.statuses = {}
    st.session_state.auto_downloaded = set()
    st.session_state.last_bulk_key = None
    st.session_state.last_single_auto_key = None


def sanitize_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^\w.-]", "", name, flags=re.UNICODE)
    return name


def format_yyyymmdd(dt: date) -> str:
    return dt.strftime("%Y%m%d")


def format_ddmmyy(dt: date) -> str:
    return dt.strftime("%d%m%y")


def format_ddmmyyyy(dt: date) -> str:
    return dt.strftime("%d%m%Y")


def build_milenio_or_universal_url(edition_name: str, dt: date, page: int) -> str:
    edition = EDITIONS[edition_name]
    edition_type = edition["type"]

    if edition_type == "milenio":
        folder = edition["folder"]
        code = edition["code"]
        return (
            f"https://api-epaper.milenio.com/file/"
            f"{folder}/{code}/{format_yyyymmdd(dt)}/images/{page}.jpg"
        )

    if edition_type == "el_universal":
        return (
            f"https://edicionimpresa.eluniversal.com.mx/archive/"
            f"eu{format_ddmmyy(dt)}/files/pages/tablet/{page}.jpg"
        )

    raise ValueError("Edición no soportada para descarga por imágenes")


def generate_elfinanciero_query() -> str:
    digits = "".join(str(random.randint(0, 9)) for _ in range(19))
    return f"0.{digits}"


def build_direct_pdf_url(edition_name: str, dt: date) -> str:
    edition = EDITIONS[edition_name]
    edition_type = edition["type"]

    if edition_type == "direct_pdf_template":
        template = str(edition["url_template"])
        return template.format(
            DD=dt.strftime("%d"),
            MM=dt.strftime("%m"),
            YYYY=dt.strftime("%Y"),
        )

    if edition_type == "intelicast_pdf":
        return (
            f"https://documentos.intelicast.net/pdfs/"
            f"{format_ddmmyyyy(dt)}{edition['pdf_name']}"
        )

    if edition_name == "El Financiero":
        return (
            "https://www.elfinanciero.com.mx/graficos/edicion-impresa/"
            f"edicion-digital.pdf?{generate_elfinanciero_query()}"
        )

    raise ValueError("Edición no soportada para descarga directa PDF")


def build_headers(url: str) -> Dict[str, str]:
    base_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    if "eluniversal.com.mx" in url:
        return {
            **base_headers,
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": "https://edicionimpresa.eluniversal.com.mx/",
        }

    if "milenio.com" in url:
        return {
            **base_headers,
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        }

    if "excelsior.com.mx" in url:
        return {
            **base_headers,
            "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
            "Referer": "https://impreso.excelsior.com.mx/",
        }

    if "elfinanciero.com.mx" in url:
        return {
            **base_headers,
            "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
            "Referer": "https://www.elfinanciero.com.mx/",
        }

    if "lajornada.prod.andes.news" in url:
        return {
            **base_headers,
            "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
            "Referer": "https://www.jornada.com.mx/",
        }

    if "documentos.intelicast.net" in url:
        return {
            **base_headers,
            "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
            "Referer": "https://documentos.intelicast.net/",
        }

    return base_headers


def is_publication_day(edition_name: str, dt: date) -> bool:
    allowed_days = EDITIONS[edition_name]["published_weekdays"]
    return dt.weekday() in allowed_days


def response_chunks(response, max_bytes: int, *, exclusive: bool = False):
    """Limita también respuestas sin Content-Length o comprimidas por HTTP."""
    limit_message = (
        f"El archivo alcanza o supera {max_bytes / 1_000_000:g} MB; abre el enlace de origen."
        if exclusive else
        f"El archivo supera el límite de {max_bytes // (1024 * 1024)} MB."
    )
    declared_length = response.headers.get("Content-Length", "")
    if declared_length.isdigit():
        size = int(declared_length)
        if size > max_bytes or (exclusive and size == max_bytes):
            raise ResourceLimitError(limit_message)
    total = 0
    for chunk in response.iter_content(chunk_size=64 * 1024):
        if not chunk:
            continue
        total += len(chunk)
        if total > max_bytes or (exclusive and total == max_bytes):
            raise ResourceLimitError(limit_message)
        yield chunk
    if total == 0:
        raise RuntimeError("Respuesta vacía")


def fetch_image(url: str, timeout: int = 30) -> Tuple[bytes, str]:
    with requests.get(
        url,
        headers=build_headers(url),
        timeout=(10, timeout),
        allow_redirects=True,
        verify=True,
        stream=True,
    ) as response:
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}")
        content_type = (response.headers.get("Content-Type") or "").lower()
        if "image" not in content_type:
            raise RuntimeError(f"Contenido no es imagen: {content_type or 'desconocido'}")
        with io.BytesIO() as buffer:
            for chunk in response_chunks(response, MAX_IMAGE_BYTES):
                buffer.write(chunk)
            return buffer.getvalue(), content_type


def fetch_pdf(url: str, output_path: Path, timeout: int = 60) -> None:
    """Transfiere el PDF a disco sin conservar la respuesta completa en RAM."""
    try:
        with requests.get(
            url,
            headers=build_headers(url),
            timeout=(10, timeout),
            allow_redirects=True,
            verify=True,
            stream=True,
        ) as response:
            if response.status_code != 200:
                raise RuntimeError(f"HTTP {response.status_code}")
            with output_path.open("wb") as destination:
                for chunk in response_chunks(response, MAX_DIRECT_PDF_BYTES, exclusive=True):
                    destination.write(chunk)
        with output_path.open("rb") as source:
            if b"%PDF-" not in source.read(1024):
                raise RuntimeError("El servidor no devolvió un PDF válido")
    except BaseException:
        output_path.unlink(missing_ok=True)
        raise


def append_image_to_pdf(image_bytes: bytes, output_path: Path, append: bool) -> None:
    """Decodifica y cierra una sola página; Pillow añade el PDF en disco."""
    previous_size = output_path.stat().st_size if append else 0
    with io.BytesIO(image_bytes) as source, Image.open(source) as image:
        if image.width * image.height > MAX_IMAGE_PIXELS:
            raise ResourceLimitError("La imagen supera el límite de 20 megapíxeles.")
        # Validar antes de escribir evita añadir páginas de imágenes corruptas.
        image.load()
        rgb_image = image if image.mode == "RGB" else image.convert("RGB")
        try:
            rgb_image.save(output_path, format="PDF", append=append)
        except BaseException as exc:
            # Un fallo de escritura no debe dañar las páginas ya terminadas.
            try:
                if append:
                    with output_path.open("r+b") as destination:
                        destination.truncate(previous_size)
                else:
                    output_path.unlink(missing_ok=True)
            except OSError:
                LOGGER.exception("No se pudo restaurar el PDF tras un fallo de escritura")
            if isinstance(exc, Exception):
                raise PdfWriteError("No se pudo guardar el PDF. Vuelve a intentar esta edición.") from exc
            raise
        finally:
            if rgb_image is not image:
                rgb_image.close()
    if output_path.stat().st_size > MAX_PDF_BYTES:
        raise ResourceLimitError("El PDF generado supera el límite de 100 MB.")


def save_result(
    edition_name: str,
    selected_date: date,
    pdf_path: Path,
    logs: List[str],
    source_url: str | None = None,
) -> None:
    filename = f"{sanitize_name(edition_name)}_{selected_date.isoformat()}.pdf"
    size = pdf_path.stat().st_size
    retained_size = sum(int(result["size_bytes"]) for result in st.session_state.results.values())
    if retained_size + size > MAX_SESSION_BYTES:
        raise ResourceLimitError(
            "Los resultados de esta sesión superan 500 MB. "
            "Descarga los archivos listos y pulsa 'Limpiar resultados' antes de continuar."
        )
    st.session_state.results[edition_name] = {
        "edition_name": edition_name,
        "filename": filename,
        "pdf_path": str(pdf_path),
        "size_bytes": size,
        "logs": logs,
        "date": selected_date.isoformat(),
        "auto_key": pdf_path.stem,
        "source_url": source_url,
    }


def save_source_link(
    edition_name: str, selected_date: date, source_url: str, logs: List[str]
) -> None:
    """Un enlace de origen no consume la cuota de archivos de la sesión."""
    st.session_state.results[edition_name] = {
        "edition_name": edition_name,
        "filename": f"{sanitize_name(edition_name)}_{selected_date.isoformat()}.pdf",
        "pdf_path": None,
        "size_bytes": 0,
        "source_url": source_url,
        "logs": logs,
        "date": selected_date.isoformat(),
        "auto_key": f"source_{uuid.uuid4().hex}",
    }


def emit_auto_downloads(results: List[Dict[str, object]], key: str) -> None:
    """Solo recibe lotes pequeños; nunca vuelve a emitirlos en un rerun."""
    files = []
    for result in results:
        file_b64 = base64.b64encode(Path(str(result["pdf_path"])).read_bytes()).decode("ascii")
        files.append({
            "href": f"data:application/pdf;base64,{file_b64}",
            "download": str(result["filename"]),
        })
    st.iframe(
        f"""
        <script>
        (function() {{
            const key = {json.dumps(key)};
            try {{ if (sessionStorage.getItem(key)) return; }} catch (e) {{}}
            const files = {json.dumps(files)};
            files.forEach((file, index) => {{
                setTimeout(() => {{
                    const a = document.createElement('a');
                    a.href = file.href;
                    a.download = file.download;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                }}, index * 500);
            }});
            try {{ sessionStorage.setItem(key, '1'); }} catch (e) {{}}
        }})();
        </script>
        """,
        height=1,
        tab_index=-1,
    )
    st.session_state.auto_downloaded.add(key)
    st.session_state.auto_downloaded.update(str(result["auto_key"]) for result in results)


def auto_download_one(result: Dict[str, object]) -> None:
    if not result.get("pdf_path"):
        return
    key = str(result["auto_key"])
    if key in st.session_state.auto_downloaded:
        return
    if int(result["size_bytes"]) > AUTO_FILE_BYTES:
        st.caption("Para este archivo grande, utiliza el botón de descarga.")
        return
    emit_auto_downloads([result], key)


def auto_download_many(results: List[Dict[str, object]], key: str) -> None:
    if not results or key in st.session_state.auto_downloaded:
        return
    eligible = []
    total_bytes = 0
    for result in results:
        if not result.get("pdf_path"):
            continue
        size = int(result["size_bytes"])
        if str(result["auto_key"]) in st.session_state.auto_downloaded:
            continue
        if size <= AUTO_FILE_BYTES and total_bytes + size <= AUTO_BATCH_BYTES:
            eligible.append(result)
            total_bytes += size
    if eligible:
        emit_auto_downloads(eligible, key)
    else:
        st.session_state.auto_downloaded.add(key)
    st.caption(
        "La descarga automática se limita a archivos de hasta 8 MB y a 16 MB por lote. "
        "Todos los archivos listos pueden descargarse con sus botones."
    )


def render_download_button(result: Dict[str, object], key: str) -> None:
    if result.get("source_url"):
        url = escape(str(result["source_url"]), quote=True)
        st.markdown(
            f'<a href="{url}" target="_blank" rel="noopener noreferrer">'
            'Abrir / descargar PDF desde el sitio de origen ↗</a>',
            unsafe_allow_html=True,
        )
    if not result.get("pdf_path"):
        return
    path = Path(str(result["pdf_path"]))
    st.download_button(
        label=f"Descargar: {result['filename']}",
        # Pasar la función, sin ejecutarla: Streamlit lee solo al hacer clic.
        data=path.read_bytes,
        file_name=str(result["filename"]),
        mime="application/pdf",
        key=key,
        on_click="ignore",
        width="stretch",
    )


def process_images_workflow(
    edition_name: str,
    selected_date: date,
    max_attempts: int,
    max_consecutive_failures: int,
    delay_seconds: float,
    progress_bar,
    status_box,
    info_box,
) -> Tuple[Path, List[str]]:
    edition = EDITIONS[edition_name]
    start_page = int(edition["start_page"])
    output_path = new_pdf_path()
    valid_pages = 0
    logs: List[str] = []
    consecutive_failures = 0
    attempts = 0
    page = start_page

    try:
        while attempts < int(max_attempts):
            url = build_milenio_or_universal_url(edition_name, selected_date, page)
            attempts += 1
            try:
                image_bytes, _ = fetch_image(url)
                try:
                    append_image_to_pdf(image_bytes, output_path, append=valid_pages > 0)
                finally:
                    del image_bytes
                valid_pages += 1
                consecutive_failures = 0
                logs.append(f"✓ Página {page} descargada y añadida al PDF")
            except (ResourceLimitError, PdfWriteError):
                # No presentar como completo un archivo interrumpido por tamaño.
                raise
            except Exception as exc:
                consecutive_failures += 1
                logs.append(
                    f"✗ Página {page} falló ({consecutive_failures}/{int(max_consecutive_failures)}): {exc}"
                )
                if consecutive_failures >= int(max_consecutive_failures):
                    logs.append("Se alcanzó el límite de fallos consecutivos. Fin del proceso.")
                    progress_bar.progress(min(attempts / int(max_attempts), 1.0))
                    status_box.text("\n".join(logs[-5:]))
                    break

            progress_bar.progress(min(attempts / int(max_attempts), 1.0))
            status_box.text("\n".join(logs[-5:]))
            info_box.info(
                f"{edition_name} | Páginas válidas: {valid_pages} | "
                f"Intento: {attempts}/{int(max_attempts)} | Página actual: {page}"
            )
            page += 1
            if delay_seconds > 0:
                time.sleep(float(delay_seconds))

        if valid_pages == 0:
            raise RuntimeError("No se encontró ninguna imagen válida")
        logs.append(f"✓ PDF generado con {valid_pages} páginas")
        status_box.text("\n".join(logs[-5:]))
        progress_bar.progress(1.0)
        return output_path, logs
    except BaseException:
        output_path.unlink(missing_ok=True)
        raise


def process_direct_pdf_workflow(
    edition_name: str,
    selected_date: date,
    status_box,
    info_box,
    source_url: str | None = None,
) -> Tuple[Path, List[str]]:
    logs: List[str] = []
    url = source_url if source_url is not None else build_direct_pdf_url(edition_name, selected_date)
    logs.append(f"Intentando descarga directa del PDF: {url}")
    status_box.text("\n".join(logs[-5:]))
    info_box.info(f"{edition_name} | Descargando PDF...")
    output_path = new_pdf_path()
    try:
        fetch_pdf(url, output_path)
        logs.append("✓ PDF descargado correctamente")
        status_box.text("\n".join(logs[-5:]))
        return output_path, logs
    except BaseException:
        output_path.unlink(missing_ok=True)
        raise


def process_one_edition(
    edition_name: str,
    selected_date: date,
    max_attempts: int,
    max_consecutive_failures: int,
    delay_seconds: float,
    progress_bar,
    status_box,
    info_box,
) -> None:
    remove_result(edition_name)

    if not is_publication_day(edition_name, selected_date):
        msg = "Hoy no se publica"
        logs = [msg]
        if EDITIONS[edition_name]["type"] not in {"milenio", "el_universal"}:
            source_url = build_direct_pdf_url(edition_name, selected_date)
            msg = "El calendario no indica publicación. Puedes consultar el enlace de origen."
            logs.append(msg)
            save_source_link(edition_name, selected_date, source_url, logs)
        st.session_state.statuses[edition_name] = {
            "state": "skipped",
            "message": msg,
            "logs": logs,
        }
        info_box.warning(msg)
        progress_bar.progress(1.0)
        return

    pdf_path = None
    source_url = None
    logs: List[str] = []
    try:
        edition_type = EDITIONS[edition_name]["type"]
        if edition_type in {"milenio", "el_universal"}:
            pdf_path, logs = process_images_workflow(
                edition_name=edition_name,
                selected_date=selected_date,
                max_attempts=max_attempts,
                max_consecutive_failures=max_consecutive_failures,
                delay_seconds=delay_seconds,
                progress_bar=progress_bar,
                status_box=status_box,
                info_box=info_box,
            )
        else:
            # Construir una sola vez; El Financiero incluye un parámetro variable.
            source_url = build_direct_pdf_url(edition_name, selected_date)
            pdf_path, logs = process_direct_pdf_workflow(
                edition_name=edition_name,
                selected_date=selected_date,
                status_box=status_box,
                info_box=info_box,
                source_url=source_url,
            )
            progress_bar.progress(1.0)

        save_result(edition_name, selected_date, pdf_path, logs, source_url=source_url)
        st.session_state.statuses[edition_name] = {
            "state": "ok",
            "message": "Archivo listo",
            "logs": logs,
        }
        st.session_state.last_single_auto_key = st.session_state.results[edition_name]["auto_key"]
        info_box.success("Archivo listo")
    except Exception as exc:
        remove_result(edition_name)
        if pdf_path is not None:
            pdf_path.unlink(missing_ok=True)
        use_source = bool(source_url)
        external_only = use_source and isinstance(exc, ResourceLimitError)
        if external_only:
            msg = "Abre el PDF desde el sitio de origen para descargarlo."
        else:
            LOGGER.exception("Error al procesar %s, fecha %s", edition_name, selected_date)
            msg = f"No se pudo completar la descarga en la app: {exc}"
            if use_source:
                msg += " Puedes intentar abrir el enlace de origen."
        logs = [*logs, str(exc), msg]
        if use_source:
            save_source_link(edition_name, selected_date, source_url, logs)
        st.session_state.statuses[edition_name] = {
            "state": "external" if external_only else "error",
            "message": msg,
            "logs": logs,
        }
        if external_only:
            info_box.info(msg)
        else:
            info_box.error(msg)
        progress_bar.progress(1.0)
    finally:
        # Una cancelación/rerun de Streamlit hereda de BaseException. Si ocurre
        # después de generar el archivo pero antes de registrarlo, limpiarlo.
        registered = st.session_state.results.get(edition_name, {})
        if pdf_path is not None and registered.get("pdf_path") != str(pdf_path):
            pdf_path.unlink(missing_ok=True)


def run_bulk_download(
    edition_names: List[str],
    selected_date: date,
    max_attempts: int,
    max_consecutive_failures: int,
    delay_seconds: float,
) -> None:
    if not edition_names:
        st.warning("Selecciona al menos una edición para la descarga masiva.")
        return

    clear_results()

    overall_progress = st.progress(0)
    overall_info = st.empty()
    edition_boxes: Dict[str, Dict[str, object]] = {}

    for edition_name in edition_names:
        with st.container(border=True):
            st.subheader(edition_name)
            edition_boxes[edition_name] = {
                "status": st.empty(),
                "info": st.empty(),
                "progress": st.progress(0),
            }

    total = len(edition_names)

    for idx, edition_name in enumerate(edition_names, start=1):
        overall_info.info(f"Procesando {idx}/{total}: {edition_name}")
        status_box = edition_boxes[edition_name]["status"]
        info_box = edition_boxes[edition_name]["info"]
        progress_bar = edition_boxes[edition_name]["progress"]

        process_one_edition(
            edition_name=edition_name,
            selected_date=selected_date,
            max_attempts=max_attempts,
            max_consecutive_failures=max_consecutive_failures,
            delay_seconds=delay_seconds,
            progress_bar=progress_bar,
            status_box=status_box,
            info_box=info_box,
        )

        overall_progress.progress(idx / total)

    failed = sum(status["state"] == "error" for status in st.session_state.statuses.values())
    if failed:
        overall_info.warning(f"Proceso masivo terminado: {failed} edición(es) con error.")
    else:
        overall_info.success("Proceso masivo terminado")
    st.session_state.last_bulk_key = f"bulk_{uuid.uuid4().hex}"


def render_result_cards() -> None:
    st.subheader("Resultados")

    display_editions = [
        edition_name
        for edition_name in ORDERED_EDITIONS
        if edition_name in st.session_state.statuses or edition_name in st.session_state.results
    ]

    if not display_editions:
        return

    ready_results: List[Dict[str, object]] = []
    for edition_name in display_editions:
        with st.container(border=True):
            st.markdown(f"**{edition_name}**")
            status = st.session_state.statuses.get(edition_name)
            result = st.session_state.results.get(edition_name)

            if status:
                state = status.get("state")
                message = status.get("message", "")
                if state == "ok":
                    st.success(message)
                elif state == "external":
                    st.info(message)
                elif state == "skipped":
                    st.warning(message)
                else:
                    st.error(message)

            if result:
                if result.get("pdf_path"):
                    ready_results.append(result)
                render_download_button(result, key=f"manual_{result['auto_key']}")

                with st.expander("Ver log del proceso"):
                    st.text("\n".join(result.get("logs", [])))
            elif status:
                with st.expander("Ver log del proceso"):
                    st.text("\n".join(status.get("logs", [])))

    if ready_results and st.session_state.last_bulk_key:
        st.info("Los archivos pequeños intentarán descargarse automáticamente. Usa los botones para los demás.")
        auto_download_many(ready_results, st.session_state.last_bulk_key)


def render_single_result(edition_name: str) -> None:
    result = st.session_state.results.get(edition_name)
    status = st.session_state.statuses.get(edition_name)

    if not status:
        return
    if st.session_state.last_bulk_key:
        # Los resultados de un lote ya tienen sus botones en la sección inferior.
        return

    st.subheader(f"Resultado individual: {edition_name}")
    with st.container(border=True):
        state = status.get("state")
        message = status.get("message", "")
        if state == "ok":
            st.success(message)
        elif state == "external":
            st.info(message)
        elif state == "skipped":
            st.warning(message)
        else:
            st.error(message)

        if result:
            if result.get("pdf_path"):
                st.info("Puedes descargar el archivo con el botón. Si es pequeño, también se intentará la descarga automática.")
            auto_download_one(result)
            render_download_button(result, key=f"single_manual_{result['auto_key']}")

        with st.expander("Ver log del proceso"):
            logs = result.get("logs", []) if result else status.get("logs", [])
            st.text("\n".join(logs))


def main() -> None:
    init_state()

    st.title("Descargador de periódicos")
    st.write(
        "Descarga masiva o individual para diarios Intelicast y otras ediciones "
        "como Milenio, El Universal, Excelsior, La Jornada y El Financiero."
    )

    selected_date = st.date_input("Fecha", value=date.today())
    # No mezclar los archivos de una fecha anterior con la fecha seleccionada.
    if st.session_state.get("results_date") != selected_date.isoformat():
        clear_results()
        st.session_state.results_date = selected_date.isoformat()
    if st.button("Limpiar resultados"):
        clear_results()

    col1, col2, col3 = st.columns(3)
    with col1:
        max_attempts = st.number_input(
            "Intentos máximos (Milenio y El Universal por imágenes)",
            min_value=10,
            max_value=300,
            value=80,
            step=1,
        )
    with col2:
        max_consecutive_failures = st.number_input(
            "Fallos consecutivos para detenerse",
            min_value=1,
            max_value=10,
            value=2,
            step=1,
        )
    with col3:
        delay_seconds = st.number_input(
            "Pausa entre intentos",
            min_value=0.0,
            max_value=5.0,
            value=0.0,
            step=0.1,
        )

    st.divider()

    st.subheader("Descarga individual")
    selected_edition = st.selectbox(
        "Selecciona una edición",
        ORDERED_EDITIONS,
        index=0,
        key="selected_edition",
    )

    single_col1, single_col2 = st.columns([1, 2])
    with single_col1:
        run_single = st.button(
            "Descargar edición seleccionada",
            width="stretch",
            type="primary",
        )
    with single_col2:
        st.caption(
            "PDF directos menores de 100 MB: descarga desde la app. "
            "De 100 MB o más: enlace de origen en una nueva pestaña."
        )

    if run_single:
        st.session_state.last_bulk_key = None
        with st.container(border=True):
            st.subheader(selected_edition)
            status_box = st.empty()
            info_box = st.empty()
            progress_bar = st.progress(0)
            process_one_edition(
                edition_name=selected_edition,
                selected_date=selected_date,
                max_attempts=int(max_attempts),
                max_consecutive_failures=int(max_consecutive_failures),
                delay_seconds=float(delay_seconds),
                progress_bar=progress_bar,
                status_box=status_box,
                info_box=info_box,
            )

    single_result_box = st.empty()

    st.divider()
    st.subheader("Descarga masiva")

    bulk_select_all = st.checkbox(
        "Incluir todas las ediciones en la descarga masiva",
        value=True,
        key="bulk_select_all",
    )

    bulk_editions = st.multiselect(
        "Elige qué ediciones incluir",
        ORDERED_EDITIONS,
        default=ORDERED_EDITIONS,
        disabled=bulk_select_all,
        key="bulk_editions",
    )

    selected_bulk_editions = ORDERED_EDITIONS if bulk_select_all else bulk_editions

    st.caption(f"Se procesarán {len(selected_bulk_editions)} edición(es) en la masiva.")

    if st.button("Iniciar descarga masiva", width="stretch"):
        run_bulk_download(
            edition_names=selected_bulk_editions,
            selected_date=selected_date,
            max_attempts=int(max_attempts),
            max_consecutive_failures=int(max_consecutive_failures),
            delay_seconds=float(delay_seconds),
        )

    # Renderizar después de procesar los botones evita mostrar descargas de
    # archivos que el inicio de un lote acaba de eliminar.
    with single_result_box.container():
        render_single_result(selected_edition)

    if st.session_state.statuses:
        st.divider()
        render_result_cards()


if __name__ == "__main__":
    main()
