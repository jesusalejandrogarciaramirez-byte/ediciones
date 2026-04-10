# Descargador y visor de periódicos

Aplicación en **Streamlit** que combina dos comportamientos:

- para periódicos con **PDF directo**, la app genera un **enlace** y lo muestra inmediatamente en el mismo bloque del procesamiento para abrirlo en una **nueva pestaña**;
- para periódicos que se obtienen por **imágenes**, la app sigue descargando y armando el PDF como antes, pero con un log compacto.

## Cambios de esta versión

- La fecha por defecto usa la zona horaria local del usuario configurada como **America/Guadalajara (UTC-6)**.
- Los enlaces de PDFs directos aparecen **en el mismo div del proceso**, no en un bloque separado de resultados.
- En procesos por imágenes, el log visible se limita a las **últimas 5 líneas**.
- Se eliminó el mensaje que prometía intentos automáticos de descarga individual.

## Diferenciación de nombres

- periódicos **(escaneado)**
- periódicos **(digital)**

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```

## Estructura

```text
.
├── app.py
├── requirements.txt
└── README.md
```
