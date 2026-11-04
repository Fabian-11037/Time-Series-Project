# Fuentes, atribución y alcance de los datos

## Núcleo numérico

- **XM, Sistema Interconectado Nacional.** Precio nacional de bolsa (`PrecBolsNaci`), demanda real/comercial y cuatro series diarias de hidrología. Datos obtenidos mediante la [API de XM](https://github.com/EquipoAnaliticaXM/API_XM). COP/kWh para precio; kWh para energía; llenado como fracción original. No son tarifas de factura por región. La licencia de una biblioteca de acceso no se interpreta automáticamente como licencia general de las series.
- **Open-Meteo y ECMWF/Copernicus Climate Change Service.** Weather data by [Open-Meteo.com](https://open-meteo.com/), Historical Weather API, modelo ERA5 explícito para todo el periodo. Contiene información modificada de Copernicus Climate Change Service. Se requiere atribución conforme a [la especificación de datos CC BY 4.0 publicada por Open-Meteo](https://github.com/open-meteo/open-meteo/blob/main/openapi/historical-weather.yml). Los puntos de rejilla y unidades están en el diccionario y el catálogo.

Las series cubren 2000–2025 y se recuperaron como versiones actuales retrospectivas. El manifiesto identifica la instantánea; no acredita que esos valores finales estuvieran disponibles en cada origen histórico.

## Texto

Prensa seleccionada: El Tiempo, El Espectador, Semana, Portafolio, La República, El Colombiano y Dinero. Se conservan título, enlace, fechas declaradas y evidencia de recuperación. Se excluyen los otros medios indicados por el autor. No se publican cuerpos de artículos ni etiquetas temáticas.

El archivo antiguo de El Colombiano incluye entradas editoriales y caricaturas, especialmente en sus primeros años. No es un censo exclusivo de noticias informativas; se preserva el título explícito de la fuente sin seleccionar temas o géneros por su relación aparente con el precio.

Se combinaron índices editoriales, capturas públicas de Internet Archive y títulos de corpus abiertos: [Babel Briefings](https://huggingface.co/datasets/felixludos/babel-briefings), [colmbian_spanish_news](https://huggingface.co/datasets/hacktoberfest-corpus-es/colmbian_spanish_news) y [Villaitech/colombia-news](https://huggingface.co/datasets/Villaitech/colombia-news). Se conservaron sus revisiones y huellas, pero no sus categorías, resúmenes o cuerpos como entradas. Las divisiones originales train/test de esos corpus no definen las particiones del pronóstico.

Texto oficial: [boletines IDEAM](https://www.ideam.gov.co/sala-de-prensa/boletines), [informes XM](https://www.xm.com.co/nuestra-empresa/informes/informes-de-la-operacion-y-el-mercado) y [Sinergox](https://sinergox.xm.com.co/). `title_kind` distingue un título institucional de una etiqueta de archivo. Un contenedor ZIP no representa todos sus boletines como registros individuales. Los anexos numéricos se separaron del inventario de títulos.

No se impone una licencia única que atribuya derechos sobre contenido de terceros. El acceso público o la descarga técnica no certifican permisos generales de entrenamiento/redistribución: se conservan procedencia y condiciones por fuente, y no se publican los corpus originales completos. Los documentos privados del curso y los archivos de resúmenes institucionales no se redistribuyen.

## Evidencia temporal

`data/provenance/verified_archive_entries.jsonl.gz` vincula el identificador del título, entrada XML, fecha real de captura y SHA-256. `archive_capture_metadata.json` conserva las URIs y huellas del índice, sin cabeceras o cookies de sesión. Las respuestas brutas se preservan localmente en el flujo original, fuera de GitHub. Un título verificado no acredita la versión actual del cuerpo de una noticia.

El escenario ampliado fue autorizado por el autor para las fases con texto, con disponibilidad supuesta y advertencia explícita de posible fuga. **E1 usa sólo números.** El escenario estricto exige disponibilidad de la versión anterior o igual al origen. No se asigna publicación a partir de nombres de archivos o periodos de referencia.

## Integridad y reproducción

Los CSV comprimidos se particionan por año y fuente, sin alterar sus valores. Las diferencias frente al CSV original son sólo serialización y organización; `data/manifest.json` conserva huellas de los archivos originales numéricos y de cada fragmento entregado. `verify_dataset.py` comprueba calendario y claves sin hacer análisis del objetivo de prueba. Las huellas de prueba están separadas y no se regeneran al ejecutar el EDA.

