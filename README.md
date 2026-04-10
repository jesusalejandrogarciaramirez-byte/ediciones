# Descargador y visor de periódicos

Aplicación en **Streamlit** que combina dos comportamientos:

- para periódicos con **PDF directo**, la app genera un **enlace** y lo abre en una **nueva pestaña**;
- para periódicos que se obtienen por **imágenes**, la app sigue descargando y armando el PDF como antes.

## Diferenciación de nombres

Para distinguir fácilmente los tipos de fuente:

- los periódicos de papel aparecen como **(escaneado)**;
- los periódicos originales aparecen como **(digital)**.

Ejemplos:
- `Reforma (escaneado)`
- `El Universal (digital)`

## Cómo funciona

### 1. PDF directo
Estos periódicos no se descargan desde la app.  
La app construye el enlace y muestra un botón para abrirlo en otra pestaña.

Aplica a:
- todos los `(escaneado)`;
- `El Financiero (digital)`;
- `Excelsior (digital)`;
- `La Jornada (digital)`;
- `Adrenalina (digital)`;
- `La Jornada EdoMex (digital)`.

### 2. Por imágenes
Estos siguen igual que antes:
- descargan páginas como imágenes;
- generan un PDF;
- permiten descarga automática o manual.

Aplica a:
- `El Universal (digital)`;
- todas las ediciones regionales de Milenio `(digital)`;
- `La Afición (digital)`.

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

## Notas

- Los enlaces o disponibilidades pueden cambiar sin previo aviso.
- Los PDF directos se delegan al navegador y al sitio destino.
- Los diarios por imágenes siguen usando `requests` y `Pillow` para reconstruir el PDF.
