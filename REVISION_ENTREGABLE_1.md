# Revisión del Jupyter Book frente al Entregable 1

Fecha de revisión: **6 de noviembre de 2026**, hora de Colombia. Autores del proyecto: Fabian José Manrique Morelos y Gloria Bastida.

Versión examinada: `f67a377e225087437829ee0826be971886acdf29`, rama `main`. Libro: https://fabian-11037.github.io/Time-Series-Project/.

Documento normativo consultado: *Entregable1DeepLearningProject.pdf*, 34 páginas, SHA-256 `56cffb2e0e23bbdfd28815b7c7515d2663bf501ed5d6e0656a37a76fc45e43eb`. Las páginas citadas corresponden al PDF original. Se consultó también la sección 14 del E2 por remisión expresa de la sección 3.2 del E1; los demás requisitos propios del E2 no se exigen aquí.

## Dictamen

**El Jupyter Book todavía no satisface íntegramente el Entregable 1.** Dispone de un EDA amplio, un conjunto de datos auditado, un pipeline temporal y tres familias implementadas y entrenadas. La actualización bibliográfica de cierre incorpora una selección focalizada trazable de baselines (véase apartado final). Permanecen la búsqueda sistemática exhaustiva y el benchmark con sustento inferencial: margen práctico, dimensionamiento, incertidumbre, contrastes y evaluación independiente del proceso de selección.

La rúbrica asigna 30 % al EDA, 30 % a literatura y extracción, 20 % a implementación y 20 % a benchmark e inferencia (p. 34). Estos pesos permiten priorizar el trabajo; no constituyen una estimación de nota ni un porcentaje de cumplimiento.

## Verificación técnica realizada

- Actualización de la copia local mediante avance directo de `8c10f0d` a `f67a377`, sin conflictos ni sobrescritura de trabajo local.
- Las **17 pruebas existentes** finalizaron correctamente.
- Integridad de **142 archivos**: 227.928 registros horarios, 9.497 días hidrológicos y 568.701 títulos; calendarios numéricos completos y claves únicas. Las huellas de prueba coinciden con el manifiesto.
- **11 cuadernos, 216 celdas de código y 17 páginas HTML**, sin errores de celda ni enlaces locales rotos. La comprobación inspeccionó las salidas almacenadas; esta revisión no volvió a ejecutar todos los cuadernos. La ejecución completa de la versión examinada consta además en el workflow de GitHub finalizado correctamente.
- Código analítico incorporado en los cuadernos; 52 entradas de presentación eliminadas del HTML. Los modelos utilizan únicamente variables numéricas y calendario.
- **4800 claves únicas** de configuración/fold/semilla, correspondientes a **192 configuraciones**, 25 ajustes por configuración y 1600 por familia. Se verificaron las huellas del código y del protocolo de búsqueda contra su configuración congelada.
- Verificación SHA-256 de las **75 predicciones de validación** distribuidas en `selected_predictions.zip`. Se recalcularon MAE/RMSE por fold y semilla y MAE/RMSE/R² agrupados; coinciden con los resultados seleccionados.
- **14 páginas públicas** consultadas respondieron HTTP 200 y coincidieron exactamente con los HTML descargados. Tanto la validación de GitHub como el despliegue Pages de `f67a377` finalizaron correctamente.

Evidencia estructurada: [results/e1_audit_2026-11-06.json](results/e1_audit_2026-11-06.json). Esta revisión no entrenó redes ni volvió a evaluar prueba. La verificación de integridad no convierte un periodo previamente consultado en una prueba sin consultar.

## Matriz de requisitos

| Requisito del E1 | Estado | Evidencia y trabajo restante |
|---|---|---|
| Problema, espacios de entrada/salida y pérdida; pregunta e hipótesis operativa; métrica, δ y unidad de independencia a priori (pp. 2–3) | Parcial | Los capítulos 1 y 10 describen pronóstico horario, 37 entradas, horizonte de 24 horas y pérdida MAE. Falta reunir la formulación numérica del E1, pregunta e hipótesis contrastable, unidad de inferencia y declaración conjunta de métricas y δ. Los registros exploratorios no fijan δ. |
| Dataset: procedencia, licencia, medición, dependencia, versión y huellas (p. 3) | Parcial | Fuentes, unidades, estructura, limitaciones de medición, manifiesto y hashes están documentados. Falta cerrar las condiciones de uso/redistribución por fuente cuando no están acreditadas y vincular el uso previo de un conjunto comparable con la literatura seleccionada. Una licencia del cliente de API no acredita la licencia de las series. |
| Calidad, distribución, sesgos, desplazamiento y decisiones derivadas (pp. 3–5 y 12) | Ampliamente cubierto | Capítulos 2, 3, 6 y 8: continuidad, duplicados, rangos, colas, multicolinealidad, sesgos de medición/editoriales y desplazamiento; implicaciones explícitas. No corresponde inventar un mecanismo MCAR/MAR/MNAR para una matriz numérica sin nulos. |
| EDA específico de series temporales (pp. 5–6) | Cubierto en desarrollo | Capítulos 3–6: serie, rupturas, STL/MSTL, espectro, ACF/PACF, lectura conjunta ADF/KPSS, ARCH, Ljung–Box y BDS. Estas últimas pruebas usan un AR(7) auxiliar; no sustituyen el diagnóstico de las redes entrenadas. |
| Partición temporal y preprocesamiento con pasado (pp. 4–6, 17 y 28) | Implementado, con limitaciones declaradas | Cinco folds expansivos, escaladores por fold y etiquetas completas por bloque. Rezagos horarios de 24 h e hidrología de dos días; son supuestos retrospectivos, no evidencia de versiones históricas disponibles. Falta sensibilidad a esos supuestos para sostener una interpretación operativa. |
| Búsqueda bibliográfica reproducible y selección de estudios (pp. 12–13) | Incompleto | Capítulo 9 e inventario: falta conciliar 615 frente a 562 registros Scopus, cadenas booleanas/fechas/conteos originales, consulta IEEE Xplore, exclusiones por registro, responsables y resolución de desacuerdos, evaluación de calidad y flujo PRISMA conciliado. |
| Extracción de exactamente tres baselines desde textos completos (pp. 13–14) | Incompleto | Hay siete extracciones de resultados verificadas. Los conteos de menciones en resúmenes no indican frecuencia de uso como baseline. Falta extraer arquitectura/profundidad/ancho/regularización/entrenamiento, contar usos como referencia y justificar frecuencia, simplicidad y sesgos inductivos de MLP/LSTM/CNN1D. |
| Arquitectura insuficientemente especificada en la literatura (p. 14; remisión al E2 §14) | Por resolver | La cuadrícula actual usa cuatro arquitecturas por familia, cuatro contextos y cuatro penalizaciones. No equivale al protocolo condicional de 1000 arquitecturas por modelo en dos fases de la sección remitida. Primero debe identificarse qué estudios definen arquitecturas y cuáles no. No corresponde aplicar automáticamente ese requisito a toda arquitectura ni presentar los 4800 ajustes actuales como su cumplimiento. |
| Análisis por modelo: referencias, ecuaciones, diagramas, supuestos, complejidad y crítica (pp. 15–16) | Parcial | Capítulo 10: diagramas, ecuaciones, flujo, sesgos inductivos, hiperparámetros y parámetros de los seleccionados. Falta completar la trazabilidad a baselines publicados, expresión analítica del número de parámetros y costo asintótico de entrenamiento/inferencia; comparación crítica por modelo, robustez y brecha verificable en la literatura. |
| Piloto y dimensionamiento antes de ejecución definitiva (pp. 17–18) | Piloto realizado; dimensionamiento pendiente | Piloto de 75 ajustes, cinco semillas por familia y cinco folds. Hay media/DE, pero falta reporte completo con coeficiente de variación, DE de diferencias pareadas, δ/σd, cálculo de R para potencia ≥0,80 y α=0,05 y diferencia mínima detectable. Cinco semillas cumplen el mínimo numérico; no acreditan potencia suficiente. |
| Implementación y equidad experimental (pp. 18–19) | Sustancialmente implementado | Tres familias, mismas semillas/folds/orígenes y 64 configuraciones por familia; curvas, regularización, parada, parámetros y tiempos guardados. Igual número de intentos no demuestra por sí solo igualdad de costo o amplitud efectiva del espacio. La validación utilizada para parar y seleccionar produce métricas de selección. |
| Dependencias, determinismo y ejecución reproducible (pp. 18–19 y 33) | Parcial | Entorno documental y entorno ROCm registrados, fuentes versionadas y workflow Linux correcto. El script de búsqueda y sus definiciones incorporadas en el capítulo importan `fcntl`, ausente en Windows; la búsqueda exige GPU. Falta explicitar Linux/WSL como requisito actual o adaptar el bloqueo y verificar Windows. Los checkpoints completos y las predicciones de la prueba inicial no están en este clon. |
| Métricas por horizonte, ingenuos y errores segmentados (pp. 20–21 y 28) | Parcial | MAE/RMSE/R² globales y comparación semanal disponibles. Faltan MAE/RMSE/MASE por horizonte con escala definida sólo con entrenamiento, persistencia causal con información disponible al origen, errores por régimen/rango y visualizaciones de observado frente a pronosticado. |
| Robustez, residuos y costo (pp. 21–23 y 25) | Parcial | Curvas seleccionadas e importancia por permutación del piloto documentadas. Faltan robustez de los seleccionados, residuos con sesgo/autocorrelación/heterocedasticidad, Ljung–Box/BDS de las redes, tabla de costos por familia y latencia de inferencia. La importancia del piloto no es evidencia de robustez de las nuevas variantes. |
| IC95 %, tamaños de efecto, contrastes, multiplicidad y potencia (pp. 21–25 y 32–33) | Pendiente | Las tablas muestran medias y DE entre semillas. Faltan IC de métricas/diferencias, pruebas pareadas/globales con supuestos, p exactos y ajustados, tamaños de efecto, potencia o diferencia detectable, y Diebold–Mariano-HLN por horizonte. El bootstrap del capítulo 8 compara distribuciones del EDA, no errores de los modelos. |
| Baseline y umbral de mejora para modelos avanzados (pp. 22–23 y 27) | Pendiente de sustento inferencial | CNN1D tiene menor MAE descriptivo de selección. Falta fijar el baseline con incertidumbre e inferencia y distinguir margen práctico δ de diferencia mínima detectable. No se puede afirmar superioridad estadística con esos promedios. |
| Evaluación final independiente y prueba (pp. 5 y 19) | Limitación material | Los 15 modelos iniciales se evaluaron en 2022–2025 antes de la búsqueda de variantes. Sus resultados corresponden a esas configuraciones congeladas. El periodo no debe presentarse como una nueva prueba intacta del diseño posterior. Hace falta una evaluación independiente prospectiva o un diseño temporal anidado, establecido antes de observar sus resultados y con historia de decisiones transparente. |

## Interpretación correcta de los resultados existentes

| Familia | MAE de selección (COP/kWh) | Contexto seleccionado |
|---|---:|---:|
| CNN1D | 24,155 ± 0,144 | 24 h |
| LSTM | 24,624 ± 0,101 | 72 h |
| MLP | 24,992 ± 0,095 | 24 h |

Son medias y desviaciones estándar entre cinco semillas, tras agrupar errores de los cinco bloques de validación. Los bloques también intervienen en parada anticipada y elección entre candidatos. Los valores no son errores externos ni intervalos de confianza. La cifra de 4800 ajustes cuenta ejecuciones; no implica 4800 observaciones estadísticamente independientes, pues comparten datos y decisiones de selección.

La evaluación anterior de prueba utiliza contexto de 168 horas, salidas y entrenamiento distintos. Su MAE de CNN1D es 81,618 COP/kWh. Ese valor no corresponde al candidato C3 seleccionado después. Las diferencias de error entre periodos no permiten atribuir por sí solas una mejora a la nueva arquitectura.

## Coherencia editorial pendiente

1. **Capítulo 8:** actualizar las expresiones «antes de entrenar modelos» y «prueba congelada; sólo integridad/calendario/cobertura» para situarlas como descripción del diagnóstico o del acceso del pipeline. La búsqueda y la evaluación inicial ya ocurrieron. No se modifica su fecha histórica ni se afirma que esta revisión haya abierto prueba.
2. **Capítulo 10:** sustituir «4800 ajustes independientes» por «4800 ajustes»; distinguir independencia de inicialización de dependencia estadística por datos compartidos.
3. **Síntesis:** diferenciar explícitamente piloto, prueba inicial y selección posterior. La presentación detallada de la prueba inicial está en el repositorio; el libro sólo menciona que se realizó.
4. **Documentos de continuidad:** varios apartados iniciales de contexto y `MODELOS_E1.md` conservan estados previos —arquitecturas no entrenadas o prueba reservada— junto a actualizaciones posteriores. Mantener una cronología inequívoca y un estado vigente único para decisiones futuras.

## Secuencia propuesta para cerrar el E1

1. **Cerrar literatura y baselines.** Conciliar el inventario y el flujo, completar extracción de referencias y resolver el requisito condicional de arquitectura. Conservar la búsqueda ya realizada como evidencia exploratoria.
2. **Definir el siguiente protocolo antes de nuevos resultados.** Fijar pregunta/hipótesis, δ justificado por la aplicación, métricas, unidad de inferencia, comparaciones y evaluación independiente. Un registro nuevo no convierte decisiones previas en decisiones a priori.
3. **Dimensionar ejecuciones e inferencia.** Usar el piloto para estimar variabilidad, justificar R y separar inicialización de dependencia temporal. No tratar cinco folds por cinco semillas como 25 réplicas independientes; para Wilcoxon exacto bilateral con cinco pares el p mínimo es 0,0625 antes de Holm.
4. **Completar evaluación y diagnóstico.** Incorporar horizontes, ingenuos causales, residuos de las redes, robustez, costos, IC y tamaños de efecto. Los análisis de artefactos de selección existentes deben identificarse como exploratorios.
5. **Cerrar reproducción y redacción.** Documentar el sistema operativo soportado, conservar el material necesario para reproducir resultados y armonizar capítulos/contexto. Verificar nuevamente cuadernos y publicación después de cambios.

Esta revisión registra el estado y las brechas; no altera modelos, hiperparámetros, cortes, datos, protocolos históricos ni resultados del libro.


## Actualización posterior de ejecución

La adaptación posterior a la versión examinada incorpora ejecución documental Windows/Linux, selección CPU/GPU y fuentes experimentales históricas preservadas. La guía vigente es `EJECUCION.md` y su evidencia está en `results/portability_verification.json`. La tabla anterior describe la versión auditada; sus limitaciones de portabilidad se sustituyen por el estado de esta actualización. Las brechas bibliográficas e inferenciales continúan sujetas al cierre descrito.


## Actualización posterior: extracción bibliográfica y selección de tres familias

El 6 de noviembre se revisaron 20 textos completos y se publicaron extracción de 90 registros de modelos, cribado individual de 83 títulos/resúmenes y tabla reproducible de frecuencia de comparadores. La comparación principal comprende 16 estudios puntuales: LSTM 7/16, MLP/DNN 6/16 y CNN 2/16. Se documentan sensibilidad a preprints, mercados y objetivos, taxonomía, roles y calidad. CNN tiene frecuencia empatada y se selecciona por su estructura independiente y contraste inductivo; únicamente una fuente confirma explícitamente CNN1D. El capítulo 9 justifica las tres familias, sus adaptaciones, número de parámetros, costo asintótico y una brecha delimitada al corpus. Capítulo 10 y contexto remiten a esta evidencia.

La fila de extracción de la tabla auditada queda **atendida para el corpus focalizado recuperado, con limitaciones explícitas de especificación y acceso**. No se declara búsqueda sistemática exhaustiva, conciliación PRISMA ni doble revisión. Cinco candidatos carecen de texto íntegro verificado. Las configuraciones insuficientes mantienen la condición E1 §3.2/E2 §14; no se valida retrospectivamente la búsqueda de 192 configuraciones como cumplimiento de ese procedimiento. δ, dimensionamiento, inferencia y evaluación independiente permanecen pendientes. Esta actualización es documental y no reabre prueba ni modifica resultados experimentales.
