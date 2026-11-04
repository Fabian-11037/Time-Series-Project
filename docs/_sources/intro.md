# Precio eléctrico colombiano: datos y análisis exploratorio

**Fabian José Manrique Morelos**  
Maestría en Estadística Aplicada · Universidad del Norte

**E1: modelos exclusivamente numéricos, sin NLP ni atributos derivados de noticias.** El texto se conserva y audita para E2/E3.

Este libro documenta un dataset candidato para pronosticar el precio nacional horario de bolsa de XM mediante historia numérica y texto. Reúne series de precio, demanda, hidrología, clima de ocho ciudades y titulares de los medios seleccionados, además de títulos de informes de IDEAM y XM.

El EDA sigue las secciones general y de series de tiempo del Entregable 1. Cada análisis termina en implicaciones para preprocesamiento, arquitectura, validación y riesgos. Las tablas y figuras numéricas provienen de celdas ejecutadas; las extracciones de resultados bibliográficos identifican el texto completo y la tabla original.

```{admonition} Alcance y decisiones del autor
:class: important
Para las fases posteriores con NLP se incluyen versiones de texto sin disponibilidad histórica verificada, por solicitud expresa del autor. Es un escenario retrospectivo con fechas declaradas y disponibilidad **supuesta**, con posible fuga por revisiones. El subconjunto de versiones con captura comprobada se mantiene separado. Una fecha impresa o el mes de referencia de un informe no acredita la versión histórica.
```

El libro muestra análisis de entrenamiento y diagnósticos de validación. El conjunto de prueba permanece congelado para decisiones de modelado: no se presentan sus distribuciones, correlaciones ni desempeño. Las auditorías de calendario, cobertura y procedencia no se interpretan como evaluación predictiva.

Este repositorio es el candidato colombiano; no modifica el E1 existente de Time-MMD. El trabajo entregado es **EDA con soporte bibliográfico**, no el Entregable 1 completo: todavía no se ejecuta el piloto, el entrenamiento de tres redes, su búsqueda ni la inferencia del benchmark. No se afirma que NLP mejore el pronóstico antes de contrastarlo.

```{tableofcontents}
```

