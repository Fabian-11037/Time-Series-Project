# Abstracts IEEE aportados el 6 de noviembre de 2026

Cinco exportaciones, 438 registros únicos: 12 prioritarios, ocho de contexto, cuatro registros retractados/avisos y 414 no seleccionados. Se identifican 28 coincidencias de título normalizado con el inventario heredado de 83 registros; no se suman como un nuevo flujo PRISMA deduplicado sin conciliación de identificadores.

La prioridad considera cercanía al sistema eléctrico, mecanismos transferibles de fusión numérica/documental, horizonte diario, eficiencia y disponibilidad causal. El cribado combina reglas orientativas con lectura detallada de candidatos. No se declara doble revisión independiente, búsqueda exhaustiva ni conocimiento de las cadenas de búsqueda originales.

- `source_manifest.json`: archivos originales, tamaños, SHA-256 y conteos. Los cinco TXT permanecen en la carpeta de descargas del usuario y no se redistribuyen.
- `records.csv`: metadatos completos, referencia por archivo/posición y huella de cada abstract; DOI o título normalizado para deduplicación.
- `screening.csv`: decisión y motivo por registro, coincidencias con H001–H083.
- `selected_abstracts.csv`: arquitectura, objetivo, entradas, utilidad, resultados declarados y limitaciones de 20 estudios.
- `review_summary.json`: conteos de la selección.

Las arquitecturas y mejoras se identifican desde abstracts. Profundidad, ancho, regularización, comparadores y protocolo que el resumen no especifica quedan pendientes de texto completo. Ningún registro se añade a la frecuencia verificada de baselines; los modelos originales y sus resultados permanecen sin cambios. No se confunde inspiración en NLP con uso de texto externo, predicción de demanda/pérdidas con precio, o clasificación de dirección con regresión horaria. Los agrupamientos y la relevancia futura se aprenden dentro del entrenamiento; no se añaden categorías temáticas manuales al dataset.

Para reproducir el inventario: `python scripts/parse_ieee_exports.py <cinco rutas TXT>`. El capítulo 9 calcula los conteos desde los CSV mediante código visible. La priorización es una extracción documental, no una clasificación automática de titulares ni una elección basada en prueba.
