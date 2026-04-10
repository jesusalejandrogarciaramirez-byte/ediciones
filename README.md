# Descargador y visor de periódicos

Esta versión deja el resultado exactamente en el mismo bloque donde se procesa cada periódico.

## Comportamiento

- **PDF directo**: muestra ahí mismo el botón/enlace para abrir el PDF en una nueva pestaña.
- **Por imágenes**: muestra ahí mismo el botón de descarga al terminar.
- Ya no se crea un bloque adicional de resultado individual.
- En masivo, cada periódico deja su enlace o botón dentro de su propio bloque.
- El log visible de procesos por imágenes se limita a las últimas 5 líneas.

## Zona horaria

La fecha por defecto usa la referencia de **America/Guadalajara (UTC-6)** para tomar el día actual.

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```
