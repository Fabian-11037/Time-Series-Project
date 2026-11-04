# Time-Series-Project

Dataset y análisis exploratorio del precio eléctrico colombiano. Autor: **Fabian José Manrique Morelos**, Maestría en Estadística Aplicada, Universidad del Norte.

**Los modelos del Entregable 1 usarán exclusivamente variables numéricas, sin NLP ni atributos derivados de noticias.** El corpus textual queda documentado para E2/E3. Véase [alcance de los modelos](MODELOS_E1.md).

## Datos disponibles

Periodo numérico: 2000–2025, hora de Colombia.

| Bloque | Filas | Contenido |
|---|---:|---|
| Horario | 227.928 | Precio nacional de bolsa y dos demandas de XM; temperatura, humedad y precipitación de ocho ciudades. 27 variables numéricas. |
| Hidrología diaria | 9.497 | Llenado, reserva útil, capacidad útil y aportes del SIN. |
| Titulares de prensa | 561.072 | Siete medios seleccionados; 115.480 con fecha declarada en 2020–2025. |
| Informes oficiales | 7.629 | 7.223 entradas del IDEAM y 406 títulos/nombres de archivos de XM. |

Los datos están **incluidos en este repositorio**, comprimidos por año/fuente para facilitar su descarga: [numéricos](data/numeric/), [texto](data/text/), [diccionario](data/metadata/data_dictionary.csv), [manifiesto de huellas](data/manifest.json). No requieren consultar las APIs para reproducir este EDA.

Medios: El Tiempo, El Espectador, Semana, Portafolio, La República, El Colombiano y Dinero. No se incluyen El Heraldo, La Silla Vacía, Las2Orillas o Razón Pública en las tablas seleccionadas. No se asignan etiquetas temáticas manuales, sentimiento ni relevancia al corpus original.

El capítulo de texto incorpora **frecuencias, bigramas, diversidad léxica, tópicos NMF, evolución temporal y cambio del vocabulario**. El vocabulario y los tópicos se ajustan sólo con prensa de entrenamiento y se congelan para proyectar validación. No se abre contenido de prueba. Son resultados del EDA, separados de las entradas numéricas del E1; no se presenta su agrupamiento como capacidad predictiva. [Protocolo](PROTOCOLO_EDA_TITULARES.md).

El histórico editorial es **parcial**. La [cobertura mensual](data/metadata/coverage_2000_2025_by_month_source.csv) distingue publicación declarada, captura comprobada y periodo de referencia. Un cero no demuestra que el medio no publicara noticias.

## Jupyter Book

El libro contiene diez cuadernos ejecutados, referencias y reproducción. Incluye calidad, distribución y anomalías, cambios de régimen, STL/MSTL, ADF/KPSS conjuntos, ACF/PACF, espectro, ARCH/BDS, covariables, cobertura textual y controles temporales. Cada análisis termina en decisiones de preprocesamiento, arquitectura, validación y riesgos.

- [Cuadernos y fuentes del libro](book/).
- [HTML construido](docs/): abrir `docs/index.html` tras descargar/clonar el repositorio.
- [Tablas y figuras generadas](results/).
- [Protocolo del EDA](PROTOCOLO_EDA.md).
- [Síntesis bibliográfica y extracciones verificadas](literature/).

El alcance entregado es **EDA con soporte bibliográfico**. No se han ejecutado los tres modelos, el piloto ni el benchmark completo del E1 colombiano. El E1 previo de Time-MMD no se modificó ni se reutilizaron sus resultados como si pertenecieran a este dataset.

## Disponibilidad y fuga temporal

Por decisión del autor, el conjunto ampliado incluye versiones de texto sin disponibilidad histórica acreditada. Hay 568.294 registros fechados utilizables bajo **supuestos declarados**; el escenario estricto conserva 62.572 versiones con captura comprobada. Los 406 títulos de XM sin publicación fechada se preservan sin asignar una fecha inventada. Un registro contradictorio permanece en cuarentena.

El escenario ampliado usa la hora declarada con zona, o las 00:00 del día siguiente cuando sólo existe el día. Estos supuestos no certifican la versión histórica y pueden introducir fuga por revisiones. El escenario estricto usa la captura de la versión exacta y nunca la retrofecha al mes del informe.

Las series actuales de XM y ERA5 son retrospectivas: no se han acreditado todos los horarios de publicación ni las ediciones numéricas originales. No se permite usar realizaciones futuras de demanda, clima o hidrología. La reproducibilidad de una instantánea no equivale a ausencia de fuga operativa.

Entrenamiento 2000–2017, validación 2018–2021 y prueba 2022–2025 constituyen la propuesta usada para este EDA. El libro explora entrenamiento y diagnostica validación. Prueba conserva sus [huellas congeladas](data/test_freeze.json); sólo se audita integridad, calendario y procedencia. El benchmark debe preregistrarse antes de entrenar.

## Reproducir

Requiere Python 3.12. Crear/activar un entorno virtual y ejecutar:

```bash
python -m pip install -r requirements.lock.txt
python scripts/verify_dataset.py
python -m unittest discover -s tests
python scripts/create_notebooks.py
python scripts/create_literature_notebooks.py
python scripts/run_eda.py
```

El análisis usa únicamente los archivos versionados. Para construir el HTML sin recalcular cuadernos ya ejecutados: `python scripts/run_eda.py --build-only`. En Windows conviene ejecutar fuera de una carpeta sincronizada si el inicio de procesos de Jupyter está restringido.

Los scripts originales de adquisición se conservan como procedencia en `scripts/acquisition/`; sus archivos brutos completos permanecen fuera del repositorio. La conversión de esa instantánea se documenta en `scripts/import_local_downloads.py`. No se publican cuerpos de noticias, corpus completos de terceros ni PDF privados del curso.

## Fuentes y bibliografía

Se verificaron en texto completo Time-MMD, Tan et al., NSW-EPNews, Lago et al., REST-TS, TeR-TSF y TimesX. El inventario previo de Scopus/WoS y la lista aportada se distinguen de esos resultados verificados. Hay una diferencia pendiente de conciliación entre el inventario anterior y la exportación actual de Scopus; no se presenta el PRISMA como definitivo.

[Referencias del libro](book/referencias.md) · [Fuentes, atribuciones y condiciones](DATA_SOURCES.md).

La preparación fue asistida por IA. El autor debe revisar las interpretaciones y cerrar el protocolo experimental antes del benchmark.

