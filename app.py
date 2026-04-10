import base64
import io
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
    "Reforma (escaneado)": {"type": "intelicast_pdf", "pdf_name": "Reforma5.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "El Universal (escaneado)": {"type": "intelicast_pdf", "pdf_name": "ElUniversal5.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "Excelsior (escaneado)": {"type": "intelicast_pdf", "pdf_name": "Excelsior5.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "El Financiero (escaneado)": {"type": "intelicast_pdf", "pdf_name": "ElFinanciero5.pdf", "published_weekdays": {0, 1, 2, 3, 4}},
    "La Cronica (escaneado)": {"type": "intelicast_pdf", "pdf_name": "LaCronica5.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "El Economista (escaneado)": {"type": "intelicast_pdf", "pdf_name": "ElEconomista5.pdf", "published_weekdays": {0, 1, 2, 3, 4}},
    "Publimetro (escaneado)": {"type": "intelicast_pdf", "pdf_name": "Publimetro5.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "24 Horas (escaneado)": {"type": "intelicast_pdf", "pdf_name": "24Horas.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "Indigo (escaneado)": {"type": "intelicast_pdf", "pdf_name": "Indigo.pdf", "published_weekdays": {0, 1, 2, 3, 4}},
    "ContraReplica (escaneado)": {"type": "intelicast_pdf", "pdf_name": "ContraReplica5.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "El Heraldo (escaneado)": {"type": "intelicast_pdf", "pdf_name": "ElHeraldo5.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "El Sol (escaneado)": {"type": "intelicast_pdf", "pdf_name": "ElSol5.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "La Razon (escaneado)": {"type": "intelicast_pdf", "pdf_name": "LaRazon5.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5}},
    "Milenio (escaneado)": {"type": "intelicast_pdf", "pdf_name": "Milenio5.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5}},
    "La Jornada (escaneado)": {"type": "intelicast_pdf", "pdf_name": "LaJornada5.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "Diario de Mexico (escaneado)": {"type": "intelicast_pdf", "pdf_name": "Diariodemexico.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "Ovaciones (escaneado)": {"type": "intelicast_pdf", "pdf_name": "Ovaciones.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "Unomasuno (escaneado)": {"type": "intelicast_pdf", "pdf_name": "Unomasuno.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "Metro (escaneado)": {"type": "intelicast_pdf", "pdf_name": "Metro.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "La Prensa (escaneado)": {"type": "intelicast_pdf", "pdf_name": "Laprensa.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "El Universal (digital)": {"type": "el_universal", "start_page": 1, "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "El Financiero (digital)": {"type": "elfinanciero_pdf", "published_weekdays": {0, 1, 2, 3, 4}},
    "Excelsior (digital)": {"type": "direct_pdf_template", "url_template": "https://impreso.excelsior.com.mx/Periodico/flip-nacional/{DD}-{MM}-{YYYY}/portada.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "La Jornada (digital)": {"type": "direct_pdf_template", "url_template": "https://wp.lajornada.prod.andes.news/wp-content/uploads/{YYYY}/{MM}/La_Jornada_{YYYY}_{MM}_{DD}.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "Milenio Nacional (digital)": {"type": "milenio", "folder": "Nacional", "code": "NAC", "start_page": 0, "published_weekdays": {0, 1, 2, 3, 4, 5}},
    "Milenio León (digital)": {"type": "milenio", "folder": "Leon", "code": "LEO", "start_page": 0, "published_weekdays": {0, 1, 2, 3, 4, 5}},
    "Milenio Tamaulipas (digital)": {"type": "milenio", "folder": "Tamaulipas", "code": "TAM", "start_page": 0, "published_weekdays": {0, 1, 2, 3, 4, 5}},
    "Milenio Jalisco (digital)": {"type": "milenio", "folder": "Jalisco", "code": "JAL", "start_page": 0, "published_weekdays": {0, 1, 2, 3, 4, 5}},
    "Milenio Puebla (digital)": {"type": "milenio", "folder": "Puebla", "code": "PUE", "start_page": 0, "published_weekdays": {0, 1, 2, 3, 4, 5}},
    "Milenio Monterrey (digital)": {"type": "milenio", "folder": "Monterrey", "code": "MON", "start_page": 0, "published_weekdays": {0, 1, 2, 3, 4, 5}},
    "Milenio Edomex (digital)": {"type": "milenio", "folder": "Edomex", "code": "MEX", "start_page": 0, "published_weekdays": {0, 1, 2, 3, 4, 5}},
    "Milenio Hidalgo (digital)": {"type": "milenio", "folder": "Hidalgo", "code": "HID", "start_page": 0, "published_weekdays": {0, 1, 2, 3, 4, 5}},
    "Milenio Laguna (digital)": {"type": "milenio", "folder": "Laguna", "code": "LAG", "start_page": 0, "published_weekdays": {0, 1, 2, 3, 4, 5}},
    "La Afición (digital)": {"type": "milenio", "folder": "Nacional", "code": "LFNE", "start_page": 0, "published_weekdays": {0, 1, 2, 3, 4, 5}},
    "Adrenalina (digital)": {"type": "direct_pdf_template", "url_template": "https://impreso.excelsior.com.mx/Periodico/flip-adrenalina/{DD}-{MM}-{YYYY}/portada.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
    "La Jornada EdoMex (digital)": {"type": "direct_pdf_template", "url_template": "https://wp.lajornada.prod.andes.news/wp-content/uploads/{YYYY}/{MM}/EdomexImpresion-{DD}{MM}{YYYY}.pdf", "published_weekdays": {0, 1, 2, 3, 4, 5, 6}},
}

ORDERED_EDITIONS = list(EDITIONS.keys())


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
    if edition["type"] == "milenio":
        return f"https://api-epaper.milenio.com/file/{edition['folder']}/{edition['code']}/{format_yyyymmdd(dt)}/images/{page}.jpg"
    if edition["type"] == "el_universal":
        return f"https://edicionimpresa.eluniversal.com.mx/archive/eu{format_ddmmyy(dt)}/files/pages/tablet/{page}.jpg"
    raise ValueError("Edición no soportada para descarga por imágenes")


def build_pdf_link_url(edition_name: str, dt) -> str:
    edition = EDITIONS[edition_name]
    edition_type = edition["type"]
    if edition_type == "direct_pdf_template":
        return str(edition["url_template"]).format(DD=dt.strftime("%d"), MM=dt.strftime("%m"), YYYY=dt.strftime("%Y"))
    if edition_type == "intelicast_pdf":
        return f"https://documentos.intelicast.net/pdfs/{format_ddmmyyyy(dt)}{edition['pdf_name']}"
    if edition_type == "elfinanciero_pdf":
        return "https://www.elfinanciero.com.mx/graficos/edicion-impresa/edicion-digital.pdf"
    raise ValueError("Edición no soportada para enlace PDF directo")


def build_headers(url: str) -> Dict[str, str]:
    base_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }
    if "eluniversal.com.mx" in url:
        return {**base_headers, "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8", "Referer": "https://edicionimpresa.eluniversal.com.mx/"}
    if "milenio.com" in url:
        return {**base_headers, "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8"}
    return base_headers


def is_publication_day(edition_name: str, dt) -> bool:
    return dt.weekday() in EDITIONS[edition_name]["published_weekdays"]


def fetch_image(url: str, timeout: int = 30) -> Tuple[bytes, str]:
    response = requests.get(url, headers=build_headers(url), timeout=timeout, allow_redirects=True, verify=True)
    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code}")
    content_type = (response.headers.get("Content-Type") or "").lower()
    if "image" not in content_type:
        raise RuntimeError(f"Contenido no es imagen: {content_type or 'desconocido'}")
    if not response.content:
        raise RuntimeError("Respuesta vacía")
    return response.content, content_type


def generate_pdf(images_data: List[Dict[str, object]]) -> bytes:
    pil_images: List[Image.Image] = []
    for item in images_data:
        img = Image.open(io.BytesIO(item["bytes"]))
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


def compact_logs(logs: List[str], limit: int = 5) -> str:
    return "\n".join(logs[-limit:])


def render_external_link_button(label: str, url: str) -> None:
    html = (
        f'<a href="{url}" target="_blank" rel="noopener noreferrer" style="text-decoration:none;">'
        f'<div style="background-color:#1f77b4;color:white;padding:0.75rem 1rem;border-radius:0.5rem;'
        f'text-align:center;font-weight:600;margin-top:0.5rem;margin-bottom:0.25rem;">{label}</div></a>'
    )
    st.markdown(html, unsafe_allow_html=True)


def auto_download_many(results: List[Dict[str, object]], key: str) -> None:
    if not results:
        return
    anchors = []
    for result in results:
        file_b64 = base64.b64encode(result["pdf_bytes"]).decode()
        filename = str(result["filename"]).replace('"', "")
        anchors.append(f'{{href: "data:application/pdf;base64,{file_b64}", download: "{filename}"}}')
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


def process_images_workflow(edition_name: str, selected_date, max_attempts: int, max_consecutive_failures: int, delay_seconds: float, progress_bar, status_box, info_box):
    edition = EDITIONS[edition_name]
    page = int(edition["start_page"])
    images_data: List[Dict[str, object]] = []
    logs: List[str] = []
    consecutive_failures = 0
    attempts = 0

    while attempts < int(max_attempts):
        url = build_milenio_or_universal_url(edition_name, selected_date, page)
        attempts += 1
        try:
            image_bytes, content_type = fetch_image(url)
            images_data.append({"page_number": page, "url": url, "bytes": image_bytes, "content_type": content_type})
            consecutive_failures = 0
            logs.append(f"✓ Página {page} descargada")
        except Exception as exc:
            consecutive_failures += 1
            logs.append(f"✗ Página {page} falló ({consecutive_failures}/{int(max_consecutive_failures)}): {exc}")
            if consecutive_failures >= int(max_consecutive_failures):
                logs.append("Se alcanzó el límite de fallos consecutivos. Fin del proceso.")
                progress_bar.progress(min(attempts / int(max_attempts), 1.0))
                status_box.text(compact_logs(logs))
                break

        progress_bar.progress(min(attempts / int(max_attempts), 1.0))
        status_box.text(compact_logs(logs))
        info_box.info(f"{edition_name} | Páginas válidas: {len(images_data)} | Intento: {attempts}/{int(max_attempts)} | Página actual: {page}")
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


def process_one_edition(edition_name: str, selected_date, max_attempts: int, max_consecutive_failures: int, delay_seconds: float, progress_bar, status_box, info_box, action_box, action_key_prefix: str):
    if not is_publication_day(edition_name, selected_date):
        info_box.warning("Hoy no se publica")
        progress_bar.progress(1.0)
        return None

    edition_type = EDITIONS[edition_name]["type"]

    if edition_type in {"intelicast_pdf", "direct_pdf_template", "elfinanciero_pdf"}:
        url = build_pdf_link_url(edition_name, selected_date)
        status_box.success("Enlace listo")
        progress_bar.progress(1.0)
        with action_box.container():
            render_external_link_button(f"Abrir {edition_name}", url)
        return {"type": "link", "url": url}

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
    filename = f"{sanitize_name(edition_name)}_{selected_date.isoformat()}.pdf"
    with action_box.container():
        st.download_button(
            label=f"Descargar {filename}",
            data=pdf_bytes,
            file_name=filename,
            mime="application/pdf",
            key=f"{action_key_prefix}_{sanitize_name(edition_name)}_{selected_date.isoformat()}",
            use_container_width=True,
        )
    info_box.success("Archivo listo")
    return {"type": "file", "pdf_bytes": pdf_bytes, "filename": filename}


def main() -> None:
    st.title("Descargador y visor de periódicos")
    st.caption("Zona horaria usada para la fecha por defecto: America/Guadalajara (UTC-6).")
    st.write("Los PDFs directos dejan el enlace en el mismo bloque donde se procesan. Los diarios por imágenes dejan ahí mismo su botón de descarga.")

    selected_date = st.date_input("Fecha", value=TODAY_LOCAL)

    col1, col2, col3 = st.columns(3)
    with col1:
        max_attempts = st.number_input("Intentos máximos (solo para digitales por imágenes)", min_value=10, max_value=300, value=80, step=1)
    with col2:
        max_consecutive_failures = st.number_input("Fallos consecutivos para detenerse", min_value=1, max_value=10, value=2, step=1)
    with col3:
        delay_seconds = st.number_input("Pausa entre intentos", min_value=0.0, max_value=5.0, value=0.0, step=0.1)

    st.divider()
    st.subheader("Descarga individual / enlace individual")
    selected_edition = st.selectbox("Selecciona una edición", ORDERED_EDITIONS, index=0, key="selected_edition")

    c1, c2 = st.columns([1, 2])
    with c1:
        run_single = st.button("Procesar edición seleccionada", use_container_width=True, type="primary")
    with c2:
        st.caption("Los PDF directos se abren por enlace. Los diarios por imágenes se descargan en la app.")

    if run_single:
        with st.container(border=True):
            st.subheader(selected_edition)
            status_box = st.empty()
            info_box = st.empty()
            progress_bar = st.progress(0)
            action_box = st.empty()
            try:
                process_one_edition(
                    edition_name=selected_edition,
                    selected_date=selected_date,
                    max_attempts=int(max_attempts),
                    max_consecutive_failures=int(max_consecutive_failures),
                    delay_seconds=float(delay_seconds),
                    progress_bar=progress_bar,
                    status_box=status_box,
                    info_box=info_box,
                    action_box=action_box,
                    action_key_prefix="single",
                )
            except Exception as exc:
                status_box.error(f"No se pudo completar: {exc}")
                progress_bar.progress(1.0)

    st.divider()
    st.subheader("Proceso masivo")

    bulk_select_all = st.checkbox("Incluir todas las ediciones en el proceso masivo", value=True, key="bulk_select_all")
    bulk_editions = st.multiselect("Elige qué ediciones incluir", ORDERED_EDITIONS, default=ORDERED_EDITIONS, disabled=bulk_select_all, key="bulk_editions")
    selected_bulk_editions = ORDERED_EDITIONS if bulk_select_all else bulk_editions
    st.caption(f"Se procesarán {len(selected_bulk_editions)} edición(es).")

    if st.button("Iniciar proceso masivo", use_container_width=True):
        if not selected_bulk_editions:
            st.warning("Selecciona al menos una edición para el proceso masivo.")
            return

        overall_progress = st.progress(0)
        overall_info = st.empty()
        download_results = []

        edition_boxes = {}
        for edition_name in selected_bulk_editions:
            with st.container(border=True):
                st.subheader(edition_name)
                edition_boxes[edition_name] = {
                    "status": st.empty(),
                    "info": st.empty(),
                    "progress": st.progress(0),
                    "action": st.empty(),
                }

        total = len(selected_bulk_editions)
        for idx, edition_name in enumerate(selected_bulk_editions, start=1):
            overall_info.info(f"Procesando {idx}/{total}: {edition_name}")
            box = edition_boxes[edition_name]
            try:
                result = process_one_edition(
                    edition_name=edition_name,
                    selected_date=selected_date,
                    max_attempts=int(max_attempts),
                    max_consecutive_failures=int(max_consecutive_failures),
                    delay_seconds=float(delay_seconds),
                    progress_bar=box["progress"],
                    status_box=box["status"],
                    info_box=box["info"],
                    action_box=box["action"],
                    action_key_prefix="bulk",
                )
                if result and result.get("type") == "file":
                    download_results.append(result)
            except Exception as exc:
                box["status"].error(f"No se pudo completar: {exc}")
                box["progress"].progress(1.0)
            overall_progress.progress(idx / total)

        overall_info.success("Proceso masivo terminado")
        if download_results:
            auto_download_many(download_results, f"{selected_date.isoformat()}_{len(download_results)}")


if __name__ == "__main__":
    main()
