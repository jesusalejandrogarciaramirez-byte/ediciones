# Descargador de periódicos — corrección de estabilidad

Aplicación Streamlit para descargar periódicos individualmente o en lote. Conserva el catálogo de 35 ediciones, sus URL y los días de publicación del archivo recibido.

## Qué mostró el log

Las dependencias se instalaron y el servidor arrancó. Después se registró `connection reset by peer` al comprobar `/healthz`. El log no contiene traceback ni un diagnóstico explícito de falta de memoria: confirma la interrupción, pero no permite asegurar su causa.

El código original sí tenía un problema de consumo de memoria reproducible: acumulaba todas las páginas como imágenes PIL, conservaba todos los PDF en `session_state` y creaba copias base64 sin límite para las descargas automáticas. La corrección elimina esa acumulación y limita las copias que todavía requiere la descarga automática.

Las advertencias de `st.components.v1.html` correspondían a una función obsoleta; se sustituyó por `st.iframe`. Esa advertencia, por sí sola, no demuestra la causa de la caída.

## Cambios aplicados

- Las ediciones por imágenes se convierten a PDF página por página, usando `append=True` de Pillow. Cada imagen se cierra al terminar y sus bytes se liberan antes de descargar la siguiente.
- Los PDF directos se transfieren por bloques a archivos temporales. No se descarga la respuesta HTTP completa a la memoria de la aplicación.
- La sesión conserva las rutas y los metadatos de los resultados. Los botones leen cada archivo cuando se hace clic, mediante el parámetro `data` diferido de Streamlit.
- Las descargas automáticas se intentan una sola vez por resultado y se limitan a archivos pequeños. El navegador puede bloquearlas; los botones de descarga permanecen disponibles.
- Se agregaron límites de tamaño, validación de imágenes y limpieza de archivos parciales. Los fallos al escribir un PDF abortan la edición y no se tratan como una página ausente.
- El botón **Limpiar resultados**, el inicio de un lote y los cambios de fecha eliminan los resultados anteriores. Regenerar una edición reemplaza su resultado anterior. Descarga lo que quieras conservar antes de esas acciones.
- Los errores recuperables se registran con traceback en el log del servidor. En un lote, una edición con error no impide continuar con las demás.
- El progreso por imágenes muestra las últimas cinco líneas; el resultado conserva el registro completo.

## Límites configurados

Se muestran como MB en la aplicación; las constantes usan múltiplos de 1,024 bytes (MiB).

| Recurso | Límite |
| --- | ---: |
| Imagen descargada | 12 MiB |
| Resolución de una imagen | 20 megapíxeles |
| PDF individual, directo o generado | 100 MiB |
| PDF guardados por sesión | 500 MiB |
| Archivo para descarga automática | 8 MiB |
| Total de descarga automática por lote | 16 MiB |

Un archivo que excede el límite automático sigue disponible mediante su botón, siempre que cumpla el límite de PDF individual. Si una edición supera un límite de procesamiento, se informa el error y se elimina su archivo parcial.

Los PDF temporales no son un archivo permanente: se eliminan al limpiar los resultados o cuando Streamlit libera la sesión. Al descargar un PDF, Streamlit todavía necesita memoria para servir ese archivo; por eso también existe un límite individual.

## Instalar o actualizar

1. Reemplaza `app.py` en la raíz del repositorio `ediciones`, rama `main`.
2. Conserva `requirements.txt`; el incluido en este paquete es idéntico al que se recibió. No se agregaron dependencias.
3. Guarda el cambio en GitHub y permite que Streamlit Community Cloud actualice la aplicación. Si sigue mostrando el proceso anterior, reiníciala desde su panel de administración.
4. Comprueba primero una edición por imágenes y luego un lote pequeño. La confirmación del incidente original requiere ejecutar esta versión en el despliegue real.

Instalación local:

```bash
pip install -r requirements.txt
streamlit run app.py
```

La fecha inicial utiliza `date.today()`, como el código recibido; corresponde a la fecha del servidor. Puede modificarse con el selector. Los PDF directos se descargan al servidor y se ofrecen mediante botones: el README anterior describía otro comportamiento que no coincidía con `app.py`.

## Validación realizada

- Compilación de Python y 22 pruebas funcionales automatizadas sobre descargas, límites, orden y dimensiones de páginas, imágenes corruptas, limpieza, estado de sesión y descarga diferida.
- Interfaz ejecutada con `streamlit.testing.v1.AppTest` y respuestas HTTP simuladas: descarga individual, lote, nueva ejecución sin repetir descargas, limpieza, cambio de fecha y fallo de una edición dentro de un lote.
- Arranque del servidor local con Streamlit 1.60.0 y Starlette 0.50.0. El endpoint interno `/_stcore/health` respondió HTTP 200 con `ok`.
- Comparación del algoritmo de conversión con 12 JPEG sintéticos RGB de 1600 × 2400 píxeles, en procesos equivalentes: pico RSS de 223.24 MiB con el método original frente a 43.96 MiB con escritura página por página. Una prueba adicional de 80 páginas con el nuevo método alcanzó 50.15 MiB. Se verificó la lectura de los PDF, sus páginas y dimensiones con `pypdf`.

Las cifras de memoria corresponden a pruebas aisladas del algoritmo, no al consumo de toda la aplicación ni a periódicos reales. El entorno local de validación usa Python 3.12 y Pillow 12.3.0; el log recibido corresponde a Python 3.14.10. No se ha modificado ni validado el despliegue de Community Cloud y no se comprobó la disponibilidad actual de los sitios de los periódicos. Las pruebas de interfaz no ejecutan el JavaScript del navegador.

## Referencias técnicas

- [Streamlit: función obsoleta `st.components.v1.html`](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v1.html)
- [Streamlit: `st.iframe`](https://docs.streamlit.io/develop/api-reference/text/st.iframe)
- [Streamlit: descarga diferida con `st.download_button`](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button)
- [Pillow: PDF y opción `append`](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#pdf)
