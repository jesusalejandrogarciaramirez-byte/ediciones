import base64
import io
import random
import re
import time
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List, Tuple

import requests
import streamlit as st
from PIL import Image


APP_TIMEZONE = ZoneInfo("America/Mexico_City")
TODAY_LOCAL = datetime.now(APP_TIMEZONE).date()

st.set_page_config(page_title="Descargador y visor de periódicos", layout="wide")


EDITIONS: Dict[str, Dict[str, object]] = {
    # =========================
    # DIARIOS INTELICAST (ESCANEADO)
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
        "published_weekdays": {0, 1, 2, 3, 4},
    },
    "La Cronica (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "LaCronica5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "El Economista (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "ElEconomista5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4},
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
    "Indigo (escaneado)": {
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
    "El Sol (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "ElSol5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "La Razon (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "LaRazon5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio (escaneado)": {
        "type": "intelicast_pdf",
        "pdf_name": "Milenio5.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5},
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
    "El Universal (digital)": {
        "type": "el_universal",
        "start_page": 1,
        "default_attempts": 80,
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "El Financiero (digital)": {
        "type": "elfinanciero_pdf",
        "published_weekdays": {0, 1, 2, 3, 4},
    },
    "Excelsior (digital)": {
        "type": "direct_pdf_template",
        "url_template": "https://impreso.excelsior.com.mx/Periodico/flip-nacional/{DD}-{MM}-{YYYY}/portada.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "La Jornada (digital)": {
        "type": "direct_pdf_template",
        "url_template": "https://wp.lajornada.prod.andes.news/wp-content/uploads/{YYYY}/{MM}/La_Jornada_{YYYY}_{MM}_{DD}.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "Milenio Nacional (digital)": {
        "type": "milenio",
        "folder": "Nacional",
        "code": "NAC",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio León (digital)": {
        "type": "milenio",
        "folder": "Leon",
        "code": "LEO",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Tamaulipas (digital)": {
        "type": "milenio",
        "folder": "Tamaulipas",
        "code": "TAM",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Jalisco (digital)": {
        "type": "milenio",
        "folder": "Jalisco",
        "code": "JAL",
        "start_page": 0,
        "default_attempts": 86,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Puebla (digital)": {
        "type": "milenio",
        "folder": "Puebla",
        "code": "PUE",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Monterrey (digital)": {
        "type": "milenio",
        "folder": "Monterrey",
        "code": "MON",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Edomex (digital)": {
        "type": "milenio",
        "folder": "Edomex",
        "code": "MEX",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Hidalgo (digital)": {
        "type": "milenio",
        "folder": "Hidalgo",
        "code": "HID",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Milenio Laguna (digital)": {
        "type": "milenio",
        "folder": "Laguna",
        "code": "LAG",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "La Afición (digital)": {
        "type": "milenio",
        "folder": "Nacional",
        "code": "LFNE",
        "start_page": 0,
        "default_attempts": 60,
        "published_weekdays": {0, 1, 2, 3, 4, 5},
    },
    "Adrenalina (digital)": {
        "type": "direct_pdf_template",
        "url_template": "https://impreso.excelsior.com.mx/Periodico/flip-adrenalina/{DD}-{MM}-{YYYY}/portada.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
    "La Jornada EdoMex (digital)": {
        "type": "direct_pdf_template",
        "url_template": "https://wp.lajornada.prod.andes.news/wp-content/uploads/{YYYY}/{MM}/EdomexImpresion-{DD}{MM}{YYYY}.pdf",
        "published_weekdays": {0, 1, 2, 3, 4, 5, 6},
    },
}


ORDERED_EDITIONS = [
    "Reforma (escaneado)",
    "El Universal (escaneado)",
    "Excelsior (escaneado)",
    "El Financiero (escaneado)",
    "La Cronica (escaneado)",
    "El Economista (escaneado)",
    "Publimetro (escaneado)",
    "24 Horas (escaneado)",
    "Indigo (escaneado)",
    "ContraReplica (escaneado)",
    "El Heraldo (escaneado)",
    "El Sol (escaneado)",
    "La Razon (escaneado)",
    "Milenio (escaneado)",
    "La Jornada (escaneado)",
    "Diario de Mexico (escaneado)",
    "Ovaciones (escaneado)",
    "Unomasuno (escaneado)",
    "Metro (escaneado)",
    "La Prensa (escaneado)",
    "El Universal (digital)",
    "El Financiero (digital)",
    "La Jornada (digital)",
    "Excelsior (digital)",
    "Adrenalina (digital)",
    "Milenio Nacional (digital)",
    "Milenio León (digital)",
    "Milenio Tamaulipas (digital)",
    "Milenio Jalisco (digital)",
    "Milenio Puebla (digital)",
    "Milenio Monterrey (digital)",
    "Milenio Edomex (digital)",
    "Milenio Hidalgo (digital)",
    "Milenio Laguna (digital)",
    "La Afición (digital)",
    "La Jornada EdoMex (digital)",
]


def init_state() -> None:
    if "results" not in st.session_state:
        st.session_state.results = {}
    if "statuses" not in st.session_state:
        st.session_state.statuses = {}
    if "last_bulk_key" not in st.session_state:
        st.session_state.last_bulk_key = None


def sanitize_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^\w.-]", "", name, flags=re.UNICODE)
    return name


def format_yyyymmdd(dt) -> str:
    return dt.strftime("%Y%m%d")


def format_ddmmyy(dt) -> str:
    return dt.strftime("%d%m%y")


def format_ddmmyyyy(dt) -> str:
    return dt.strftime("%d%m%Y")


def build_milenio_or_universal_url(edition_name: str, dt, page: int) -> str:
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


def build_pdf_link_url(edition_name: str, dt) -> str:
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

    if edition_type == "elfinanciero_pdf":
        return "https://www.elfinanciero.com.mx/graficos/edicion-impresa/edicion-digital.pdf"

    raise ValueError("Edición no soportada para enlace PDF directo")


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

    return base_headers


def is_publication_day(edition_name: str, dt) -> bool:
    allowed_days = EDITIONS[edition_name]["published_weekdays"]
    return dt.weekday() in allowed_days


def fetch_image(url: str, timeout: int = 30) -> Tuple[bytes, str]:
    response = requests.get(
        url,
        headers=build_headers(url),
        timeout=timeout,
        allow_redirects=True,
        verify=True,
    )

    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}")

    content_type = (response.headers.get("Content-Type") or "").lower()
    if "image" not in content_type:
        raise RuntimeError(f"Contenido no es imagen: {content_type or 'desconocido'}")

    if not response.content:
        raise RuntimeError("Respuesta vacía")

    return response.content, content_type


def generate_pdf(images_data: List[Dict[str, object]]) -> bytes:
    if not images_data:
        raise ValueError("No hay imágenes para generar el PDF")

    pil_images: List[Image.Image] = []
    for item in images_data:
        image_bytes = item["bytes"]
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")
        pil_images.append(img)

    buffer = io.BytesIO()
    first_image, *rest = pil_images
    first_image.save(buffer, format="PDF", save_all=True, append_images=rest)
    buffer.seek(0)
    return buffer.read()


def save_result(edition_name: str, selected_date, pdf_bytes: bytes, logs: List[str]) -> None:
    filename = f"{sanitize_name(edition_name)}_{selected_date.isoformat()}.pdf"
    st.session_state.results[edition_name] = {
        "edition_name": edition_name,
        "filename": filename,
        "pdf_bytes": pdf_bytes,
        "logs": logs,
        "date": selected_date.isoformat(),
        "auto_key": f"{sanitize_name(edition_name)}_{selected_date.isoformat()}_{len(pdf_bytes)}",
    }


def auto_download_many(results: List[Dict[str, object]], key: str) -> None:
    if not results:
        return

    anchors = []
    for result in results:
        file_b64 = base64.b64encode(result["pdf_bytes"]).decode()
        filename = str(result["filename"]).replace('"', "")
        anchors.append(
            f'{{href: "data:application/pdf;base64,{file_b64}", download: "{filename}"}}'
        )

    js_array = ",\n".join(anchors)
    st.components.v1.html(
        f'''
        <script>
        (function() {{
            const batchKey = "bulk_download_{key}";
            if (sessionStorage.getItem(batchKey)) return;
            const files = [{js_array}];
            files.forEach((file, index) => {{
                setTimeout(() => {{
                    const a = document.createElement('a');
                    a.href = file.href;
                    a.download = file.download;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                }}, index * 500);
            }});
            sessionStorage.setItem(batchKey, '1');
        }})();
        </script>
        ''',
        height=0,
    )


def render_external_link_button(label: str, url: str) -> None:
    html = f'''
    <a href="{url}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;">
        <div style="
            background-color:#1f77b4;
            color:white;
            padding:0.75rem 1rem;
            border-radius:0.5rem;
            text-align:center;
            font-weight:600;
            margin-top:0.5rem;
            margin-bottom:0.25rem;
        ">
            {label}
        </div>
    </a>
    '''
    st.markdown(html, unsafe_allow_html=True)


def compact_logs(logs: List[str], limit: int = 5) -> str:
    if len(logs) <= limit:
        return "\n".join(logs)
    return "\n".join(logs[-limit:])


def process_images_workflow(
    edition_name: str,
    selected_date,
    max_attempts: int,
    max_consecutive_failures: int,
    delay_seconds: float,
    progress_bar,
    status_box,
    info_box,
) -> Tuple[bytes, List[str]]:
    edition = EDITIONS[edition_name]
    start_page = int(edition["start_page"])
    images_data: List[Dict[str, object]] = []
    logs: List[str] = []
    consecutive_failures = 0
    attempts = 0
    page = start_page

    while attempts < int(max_attempts):
        url = build_milenio_or_universal_url(edition_name, selected_date, page)
        attempts += 1

        try:
            image_bytes, content_type = fetch_image(url)
            filename = f"pagina_{str(page).zfill(2)}.jpg"
            images_data.append(
                {
                    "page_number": page,
                    "url": url,
                    "bytes": image_bytes,
                    "filename": filename,
                    "content_type": content_type,
                }
            )
            consecutive_failures = 0
            logs.append(f"✓ Página {page} descargada")
        except Exception as exc:
            consecutive_failures += 1
            logs.append(
                f"✗ Página {page} falló ({consecutive_failures}/{int(max_consecutive_failures)}): {exc}"
            )
            if consecutive_failures >= int(max_consecutive_failures):
                logs.append("Se alcanzó el límite de fallos consecutivos. Fin del proceso.")
                progress_bar.progress(min(attempts / int(max_attempts), 1.0))
                status_box.text(compact_logs(logs))
                break

        progress_bar.progress(min(attempts / int(max_attempts), 1.0))
        status_box.text(compact_logs(logs))
        info_box.info(
            f"{edition_name} | Páginas válidas: {len(images_data)} | "
            f"Intento: {attempts}/{int(max_attempts)} | Página actual: {page}"
        )

        page += 1
        if delay_seconds > 0:
            time.sleep(float(delay_seconds))

    if not images_data:
        raise RuntimeError("No se encontró ninguna imagen válida")

    info_box.info(f"{edition_name} | Generando PDF con {len(images_data)} páginas...")
    pdf_bytes = generate_pdf(images_data)
    logs.append(f"✓ PDF generado con {len(images_data)} páginas")
    status_box.text(compact_logs(logs))
    return pdf_bytes, logs


def process_one_edition(
    edition_name: str,
    selected_date,
    max_attempts: int,
    max_consecutive_failures: int,
    delay_seconds: float,
    progress_bar,
    status_box,
    info_box,
) -> None:
    st.session_state.results.pop(edition_name, None)
    st.session_state.statuses.pop(edition_name, None)

    if not is_publication_day(edition_name, selected_date):
        msg = "Hoy no se publica"
        st.session_state.statuses[edition_name] = {
            "state": "skipped",
            "message": msg,
            "logs": [msg],
        }
        info_box.warning(msg)
        progress_bar.progress(1.0)
        return

    edition_type = EDITIONS[edition_name]["type"]

    if edition_type in {"intelicast_pdf", "direct_pdf_template", "elfinanciero_pdf"}:
        url = build_pdf_link_url(edition_name, selected_date)
        logs = [f"✓ Enlace generado: {url}"]
        st.session_state.statuses[edition_name] = {
            "state": "link",
            "message": "Enlace listo",
            "logs": logs,
            "url": url,
        }
        status_box.text(compact_logs(logs))
        info_box.success("Enlace listo")
        progress_bar.progress(1.0)
        return

    try:
        pdf_bytes, logs = process_images_workflow(
            edition_name=edition_name,
            selected_date=selected_date,
            max_attempts=max_attempts,
            max_consecutive_failures=max_consecutive_failures,
            delay_seconds=delay_seconds,
            progress_bar=progress_bar,
            status_box=status_box,
            info_box=info_box,
        )
        save_result(edition_name, selected_date, pdf_bytes, logs)
        st.session_state.statuses[edition_name] = {
            "state": "ok",
            "message": "Archivo listo",
            "logs": logs,
        }
        info_box.success("Archivo listo")
    except Exception as exc:
        msg = f"No se pudo completar: {exc}"
        st.session_state.statuses[edition_name] = {
            "state": "error",
            "message": msg,
            "logs": [msg],
        }
        status_box.text(compact_logs([msg]))
        info_box.error(msg)
        progress_bar.progress(1.0)


def run_bulk_download(
    edition_names: List[str],
    selected_date,
    max_attempts: int,
    max_consecutive_failures: int,
    delay_seconds: float,
) -> None:
    st.session_state.results = {}
    st.session_state.statuses = {}

    if not edition_names:
        st.warning("Selecciona al menos una edición para el proceso masivo.")
        return

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
                "action": st.empty(),
            }

    total = len(edition_names)

    for idx, edition_name in enumerate(edition_names, start=1):
        overall_info.info(f"Procesando {idx}/{total}: {edition_name}")
        status_box = edition_boxes[edition_name]["status"]
        info_box = edition_boxes[edition_name]["info"]
        progress_bar = edition_boxes[edition_name]["progress"]
        action_box = edition_boxes[edition_name]["action"]

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

        status = st.session_state.statuses.get(edition_name)
        result = st.session_state.results.get(edition_name)

        with action_box.container():
            if status and status.get("state") == "link":
                url = status.get("url", "")
                if url:
                    render_external_link_button(f"Abrir {edition_name}", url)
            elif result:
                st.download_button(
                    label=f"Descargar {result['filename']}",
                    data=result["pdf_bytes"],
                    file_name=result["filename"],
                    mime="application/pdf",
                    key=f"bulk_manual_{sanitize_name(edition_name)}_{result['date']}",
                    use_container_width=True,
                )

        overall_progress.progress(idx / total)

    overall_info.success("Proceso masivo terminado")
    ready_results = list(st.session_state.results.values())
    if ready_results:
        st.session_state.last_bulk_key = f"{selected_date.isoformat()}_{len(ready_results)}"
        auto_download_many(ready_results, st.session_state.last_bulk_key)


def render_single_result(edition_name: str) -> None:
    result = st.session_state.results.get(edition_name)
    status = st.session_state.statuses.get(edition_name)

    if not status:
        return

    st.subheader(f"Resultado individual: {edition_name}")
    with st.container(border=True):
        state = status.get("state")
        message = status.get("message", "")
        if state == "ok":
            st.success(message)
        elif state == "link":
            st.success(message)
        elif state == "skipped":
            st.warning(message)
        else:
            st.error(message)

        with st.expander("Ver log del proceso"):
            logs = result.get("logs", []) if result else status.get("logs", [])
            st.text(compact_logs(logs))

        if state == "link":
            url = status.get("url", "")
            if url:
                render_external_link_button(f"Abrir {edition_name} en una nueva pestaña", url)
        elif result:
            st.download_button(
                label=f"Descargar {result['filename']}",
                data=result["pdf_bytes"],
                file_name=result["filename"],
                mime="application/pdf",
                key=f"single_manual_{sanitize_name(edition_name)}_{result['date']}",
                use_container_width=True,
            )


def main() -> None:
    init_state()

    st.title("Descargador y visor de periódicos")
    st.caption("Zona horaria usada para la fecha por defecto: America/Guadalajara (UTC-6).")
    st.write(
        "Los periódicos escaneados y los digitales con PDF directo generan un enlace para abrirse en una nueva pestaña. "
        "Los periódicos digitales por imágenes siguen descargándose desde la app."
    )

    selected_date = st.date_input("Fecha", value=TODAY_LOCAL)

    col1, col2, col3 = st.columns(3)
    with col1:
        max_attempts = st.number_input(
            "Intentos máximos (solo para digitales por imágenes)",
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

    st.subheader("Descarga individual / enlace individual")
    selected_edition = st.selectbox(
        "Selecciona una edición",
        ORDERED_EDITIONS,
        index=0,
        key="selected_edition",
    )

    single_col1, single_col2 = st.columns([1, 2])
    with single_col1:
        run_single = st.button(
            "Procesar edición seleccionada",
            use_container_width=True,
            type="primary",
        )
    with single_col2:
        st.caption("Los PDF directos se abren por enlace. Los diarios por imágenes se descargan en la app.")

    if run_single:
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

    render_single_result(selected_edition)

    st.divider()
    st.subheader("Proceso masivo")

    bulk_select_all = st.checkbox(
        "Incluir todas las ediciones en el proceso masivo",
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

    st.caption(f"Se procesarán {len(selected_bulk_editions)} edición(es).")

    if st.button("Iniciar proceso masivo", use_container_width=True):
        run_bulk_download(
            edition_names=selected_bulk_editions,
            selected_date=selected_date,
            max_attempts=int(max_attempts),
            max_consecutive_failures=int(max_consecutive_failures),
            delay_seconds=float(delay_seconds),
        )


if __name__ == "__main__":
    main()
