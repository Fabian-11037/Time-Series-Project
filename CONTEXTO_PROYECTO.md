# Contexto para continuar el proyecto

Actualización: 6 de noviembre de 2026. Idioma de trabajo: español.

Autores: Fabian José Manrique Morelos y Gloria Bastida. Maestría en Estadística Aplicada, Universidad del Norte.

## 1. Proyecto y estado

Repositorio: https://github.com/Fabian-11037/Time-Series-Project, rama `main`.
Libro público: https://fabian-11037.github.io/Time-Series-Project/.

El objetivo general es desarrollar un modelo de pronóstico que integre series temporales y texto. La etapa actual prepara los modelos numéricos de referencia para el precio nacional horario de bolsa de XM, en COP/kWh (`precio_bolsa_cop_kwh`). El E1 utiliza exclusivamente variables numéricas y calendario; los modelos multimodales corresponden a etapas posteriores.

Estado al actualizar este archivo:

- Dataset consolidado, versionado y auditado; EDA y revisión bibliográfica publicados.
- **Prueba 2022–2025 evaluada el 5 de noviembre de 2026 por solicitud explícita del usuario para las tres familias.** Ya no es un periodo sin consultar; véase sección 9. Los bloqueos de EDA y piloto continúan activos.
- Pipeline de validación **`split_train_val_forwardChaining`** implementado y configurado con cinco folds.
- Preparación de ventanas y escaladores independiente por fold; interfaz disponible para incorporar modelos.
- **Se completó un piloto colombiano de MLP, LSTM y CNN1D en PyTorch/ROCm:** 75 ajustes (cinco folds × cinco semillas × tres familias), 30 épocas fijas. El benchmark confirmatorio final sigue pendiente. `project_scope.json` distingue ambos estados.
- Las implementaciones y resultados previos de Time-MMD pertenecen a otro proyecto; sus métricas, ventana semanal y margen de mejora no deben trasladarse a este dataset.

La solicitud vigente sustituye la propuesta de `split_train_val_kFold` por **forward chaining**. El antiguo corte 2000–2017 / 2018–2021 se conserva únicamente para interpretar los diagnósticos del EDA; no constituye una única partición fija de entrenamiento/validación del nuevo pipeline.

## 2. Datos y protección de prueba

Los datos necesarios están en el repositorio; no hace falta descargar nuevamente las APIs.

| Bloque | Ruta | Contenido |
|---|---|---|
| Numérico horario | `data/numeric/hourly/{año}.csv.gz` | 227.928 horas, 2000–2025; precio, demanda real y comercial, y 24 variables meteorológicas de ocho ciudades |
| Hidrología diaria | `data/numeric/hydrology/{año}.csv.gz` | 9.497 días; llenado, reserva útil, capacidad útil y aportes |
| Texto | `data/text/` | Titulares de siete medios y entradas de informes IDEAM/XM; cobertura parcial |
| Metadatos | `data/metadata/` | Diccionario, unidades, procedencia, cobertura y reglas de disponibilidad |
| Integridad | `data/manifest.json` | Conteos y SHA-256 de los archivos |
| Prueba congelada | `data/test_freeze.json` | Archivos y huellas de 2022–2025 |

Las ubicaciones meteorológicas son Bogotá, Medellín, Cali, Barranquilla, Cartagena, Bucaramanga, Pereira y Cúcuta. Corresponden a puntos de rejilla ERA5. La lluvia urbana no representa directamente las cuencas de los embalses. Se preservan las incidencias de llenado fuera de [0,1] identificadas en la auditoría; no corregirlas automáticamente.

**Prueba: 2022-01-01 inclusive a 2026-01-01 exclusivo, hora de Colombia.** No utilizar sus valores, distribuciones, correlaciones o errores para seleccionar modelos, transformaciones o hiperparámetros. El pipeline actual no carga esos valores. `load_numeric('test')` está bloqueado por defecto. Las comprobaciones de hashes/calendario no equivalen a una evaluación predictiva.

## 3. Diseño activo de validación

La configuración está en `configs/training_pipeline.json`; los cortes efectivos y conteos están en `results/pipeline/folds.csv`.

- Desarrollo: 2000–2021.
- Cinco validaciones consecutivas que, en conjunto, cubren 2018–2021. Los bloques contienen cantidades aproximadamente iguales de orígenes diarios; no son cinco años de validación.
- Entrenamiento expansivo: el primer fold utiliza etiquetas anteriores a 2018; los siguientes incorporan los periodos anteriores a su respectiva validación.
- Contexto: 168 horas. Horizonte: 24 horas. Paso: 24 horas. Orígenes: 00:00 de Colombia.
- Las etiquetas de entrenamiento terminan antes o exactamente al inicio de validación. Los horizontes que cruzan el final de un bloque se purgan.
- Las entradas de validación pueden usar observaciones pasadas de periodos anteriores: la separación corresponde a sus etiquetas futuras.
- Cada fold estima un `StandardScaler` nuevo exclusivamente con las filas usadas en las entradas de entrenamiento. Las etiquetas permanecen en COP/kWh.

La función original de timeseries-cv 0.1.5 está en `src/colombia_energy/forward_chaining.py`. Se aplica a identificadores de bloques para planificar los folds; el pipeline construye después las ventanas numéricas. Así se evita la materialización cuadrática de ventanas de la implementación original sobre toda la serie horaria.

La distribución completa exige NumPy <2, mientras el entorno reproducido utiliza NumPy 2.5.4. Se conserva únicamente la función auditada, con licencia y atribución en `third_party/timeseries-cv/`. **No instalar timeseries-cv con sus dependencias sobre el entorno bloqueado ni sustituir silenciosamente esta implementación.**

### Disponibilidad de covariables

El pipeline desplaza las variables horarias 24 horas y asigna a la hidrología una disponibilidad supuesta dos días después del inicio del día de referencia. La hidrología se alinea mediante el último registro ya disponible. Se descartan las ventanas con entradas iniciales incompletas.

Estos rezagos son supuestos retrospectivos configurables, no horarios de publicación certificados. Las series actuales de XM y ERA5 pueden contener revisiones. La evaluación operativa necesita analizar estos supuestos. No usar demanda, clima o hidrología futuros realizados como si fueran pronósticos conocidos al origen.

## 4. Preparación en otro equipo

Usar un clon nuevo y un entorno virtual nuevo con Python 3.12. No copiar `.venv`, cachés ni rutas absolutas de otro PC.

```bash
git clone https://github.com/Fabian-11037/Time-Series-Project.git
cd Time-Series-Project
python -m venv .venv
```

Activar el entorno (`.venv\Scripts\Activate.ps1` en PowerShell o `source .venv/bin/activate` en Linux/macOS) y ejecutar:

```bash
python -m pip install -r requirements.lock.txt
python scripts/verify_dataset.py
python -m unittest discover -s tests
python scripts/prepare_pipeline.py
python scripts/create_notebooks.py
python scripts/create_literature_notebooks.py
python scripts/run_eda.py
python scripts/verify_book.py
```

En Windows también puede utilizarse `.venv\Scripts\python.exe` sin activar el entorno. Jupyter Book debe permanecer en la versión 1.0.4. El bloqueo original cubre EDA y pipeline. El piloto utilizó PyTorch 2.9.1+rocm6.4; sus versiones efectivas se registran en `results/pilot_pytorch_gfx1030/environment_freeze.txt`, sin modificar el entorno ni el bloqueo del EDA.

`scripts/prepare_pipeline.py --plan-only` calcula sólo el plan temporal. Sin esa opción prepara y audita los escaladores de los cinco folds, sin entrenar modelos. Sus artefactos están en `results/pipeline/`: `folds.csv`, `fold_indices.npz`, `preprocessors.json` y `manifest.json`.

Los scripts de adquisición y `import_local_downloads.py` documentan la procedencia del dataset; no son necesarios para reproducir la instantánea versionada en otro equipo.

## 5. Incorporación del entrenamiento

Leer `PIPELINE.md`, `MODELOS_E1.md`, `PROTOCOLO_EDA.md` y `PROTOCOLO_PIPELINE_CV.md`.

Los candidatos propuestos son:

1. MLP/DNN sobre ventanas de rezagos.
2. LSTM de una capa recurrente con salida densa.
3. CNN1D poco profunda con salida densa.

Las tres familias ya se entrenaron en el piloto y la búsqueda exploratoria descritos en las secciones 8–16; su selección sistemática desde la literatura sigue pendiente. Para cerrar el benchmark del E1:

1. Completar la extracción de modelos usados como baseline en los textos completos: arquitectura, profundidad, ancho, regularización, entrenamiento y resultados. Elaborar la tabla de frecuencia y justificar simplicidad y sesgos inductivos distintos.
2. Escribir un preregistro específico del E1 colombiano antes de búsqueda/piloto: arquitectura, espacios, esfuerzo comparable, pérdida, métricas, margen práctico δ, semillas, inferencia y política temporal. MAE en COP/kWh es la propuesta previa; RMSE y una medida relativa/estacional son complementarias. El margen δ no está fijado. No importar el 3 % ni la MASE semanal del proyecto anterior.
3. Implementar construcción, ajuste y evaluación mediante los callbacks de `run_forward_chaining`. Crear un modelo nuevo por fold y semilla; mantener los mismos datos y esfuerzo de ajuste para las tres familias. El pipeline entrega entradas `(n,168,p)` y etiquetas `(n,24)`; el MLP puede aplanar la entrada.
4. Realizar piloto de al menos cinco semillas en desarrollo. Dimensionar las ejecuciones finales para potencia al menos 0,80 y α=0,05, con las comparaciones y su corrección declaradas. E1 exige al menos cinco ejecuciones finales, o seis si se utilizan pruebas por rangos, y más si la potencia lo requiere.
5. Tratar por separado variabilidad de inicialización y dependencia entre orígenes. Las semillas no convierten los errores horarios en observaciones independientes. Fijar la inferencia temporal antes de consultar prueba.
6. Seleccionar y congelar el diseño con desarrollo. Implementar una entrada explícita y separada para evaluación final de prueba. No habilitar `allow_test=True` en búsqueda, piloto, EDA o preparación ordinaria.
7. Registrar configuraciones, curvas, semillas, parámetros, tiempos, predicciones por origen y métricas. Actualizar `models_trained` sólo cuando existan entrenamientos reales y artefactos verificables.

Los PDF originales de las pautas del curso no están versionados aquí. El resumen de requisitos no sustituye su consulta al cerrar la entrega. Las condiciones de arquitectura insuficientemente descrita deben verificarse en la sección 3.2 del E1.

## 6. Bibliografía y texto

`literature/fulltext_manifest.json` y `verified_extracts.csv` identifican textos completos y resultados comprobados. `inherited_selected_83.csv` contiene una preselección; las menciones de arquitecturas en resúmenes no son frecuencias verificadas de uso como baseline. La conciliación de exportaciones y la revisión sistemática están incompletas.

Referencias metodológicas centrales: Lago et al. (2021), DOI `10.1016/j.apenergy.2021.116983`; para la recomendación de familias se consultó también Lago et al. (2018), DOI `10.1016/j.apenergy.2018.02.069`. Este último utiliza LSTM-DNN y una CNN con ramas: una simplificación para Colombia debe justificarse como adaptación.

El corpus se conserva para E2/E3. El escenario `declared_dates` incluye versiones retrospectivas no verificadas; `verified` utiliza capturas de versiones exactas y tiene menor cobertura. Los informes sin fecha no se asignan temporalmente. El análisis NMF del capítulo 7 se ajustó con prensa del tramo diagnóstico 2000–2017 y se proyectó a 2018–2021. No reutilizar sus pesos como atributos de E1. Cualquier futura representación textual debe ajustarse dentro del fold correspondiente.

## 7. Libro, publicación y mantenimiento

- Los cuadernos se generan con `scripts/create_notebooks.py` y `create_literature_notebooks.py`. Editar sus fuentes y regenerar, no mantener modificaciones aisladas de un `.ipynb`.
- `inline_notebook_code.py` incorpora las implementaciones en celdas ejecutables. El código analítico debe estar en el libro, no sólo importado desde un módulo privado.
- El código de Markdown, texto y formato se elimina de la edición HTML mediante `remove-input`; el texto/resultados permanecen. No usar botones `hide-input` para esas celdas.
- Mantener redacción académica, autores Fabian José Manrique Morelos y Gloria Bastida, referencias verificables y cifras generadas por ejecución.
- `python scripts/run_eda.py --build-only` reconstruye HTML desde salidas existentes. Tras cambiar cálculos, ejecutar los capítulos afectados y verificar el libro.
- GitHub Pages publica `main:/docs`. Al subir código y HTML actualizado se despliega el sitio. El workflow valida dataset, pruebas, pipeline y libro.
- No sobrescribir los protocolos fechados ni las huellas de prueba. Documentar las nuevas decisiones en registros posteriores.

Al cerrar una sesión, actualizar este archivo con el estado real de implementaciones, experimentos, comprobaciones y pendientes, sin incorporar credenciales ni rutas propias del equipo.

## 8. Piloto ejecutado el 5 de noviembre de 2026

Se descargó el repositorio en un clon nuevo y se leyó este contexto antes de modificar entrenamientos. El usuario confirmó el entorno existente `mlenv`. Hardware: AMD Radeon RX 6700 XT de 12 GB (gfx1031), PyTorch 2.9.1+rocm6.4, Python 3.12.3. El primer intento sin override falló por `HIP invalid device function`; no produjo ajustes completos. El proceso con `HSA_OVERRIDE_GFX_VERSION=10.3.0` superó operaciones GPU y completó los entrenamientos. No se modificaron controladores, paquetes ni variables globales.

Prerregistro exploratorio: `PROTOCOLO_PILOTO_2026-11-05.md`, congelado antes del primer ajuste. Scripts: `scripts/train_pytorch.py` (callbacks de `run_forward_chaining`) y `scripts/summarize_pytorch.py`. Arquitecturas simples adaptadas de las familias propuestas; no se afirma haber completado la extracción bibliográfica previa al benchmark final. Cinco semillas 11037–11041; mismos folds, 30 épocas y Adam para las tres familias, sin búsqueda ni selección por validación. Se añadió una normalización auxiliar del objetivo con estadísticas exclusivas de entrenamiento, invertida para calcular errores en COP/kWh.

Resultados agrupados sobre todas las horas de validación de los cinco folds y luego promediados entre semillas:

| Familia | MAE medio ± DE entre semillas (COP/kWh) | RMSE medio (COP/kWh) |
|---|---:|---:|
| CNN1D | 25.307 ± 0.189 | 38.529 |
| LSTM | 26.382 ± 0.453 | 40.155 |
| MLP | 32.024 ± 0.991 | 46.789 |

Referencia de repetición semanal: MAE 40.157 COP/kWh. CNN1D obtuvo aproximadamente 37.0 % menos MAE que esa referencia en este piloto. Este porcentaje es un resultado descriptivo, no un margen δ preregistrado ni una prueba de significancia. La variación entre semillas no mide incertidumbre temporal. Duración del bucle experimental: 330.84 s, excluyendo inicialización y carga previa.

Artefactos en `results/pilot_pytorch_gfx1030/`: informe `RESUMEN_RESULTADOS.md`, `summary.csv`, métricas por fold y semilla, curva de cada ajuste, checkpoints con pesos y escaladores, predicciones por origen, configuración, versiones y huellas de fuentes/artefactos. Se verificaron 75 ajustes y 300 artefactos; MAE/RMSE se recalcularon desde predicciones. Figura: `comparacion_modelos.png`. El intento fallido conserva sólo su configuración en `results/pilot_pytorch/`.

Verificaciones: 17 pruebas existentes superadas; 142 archivos del dataset comprobados, calendarios completos y huellas de prueba intactas. No se cargaron valores de prueba para el entrenamiento ni se evaluó 2022–2025. El libro y `docs/` no se regeneraron; sus textos anteriores describen la etapa previa. No se publicó ni se subió a GitHub.

Pendientes para el benchmark confirmatorio E1: completar extracción/frecuencias de baselines de textos completos, justificar arquitecturas, fijar δ e inferencia temporal/multiplicidad, dimensionar las repeticiones finales con potencia >=0.80 y alfa=0.05, congelar el diseño y disponer una evaluación final explícita de prueba. El piloto no sustituye esos requisitos.

## 9. Prueba evaluada por autorización explícita

El 5 de noviembre de 2026, después de conocer la validación, el usuario solicitó evaluar prueba con los tres modelos. Registro previo a consultar sus valores: `PROTOCOLO_PRUEBA_2026-11-05.md`. Se mantuvieron las arquitecturas del piloto y sus hiperparámetros, cinco semillas 11037–11041 y 30 épocas fijas. Se reentrenaron desde cero 15 modelos con todos los ejemplos admisibles de desarrollo 2000–2021. Se guardaron los 15 checkpoints antes de abrir prueba; escaladores de entradas y objetivo se estimaron sólo con desarrollo. No se optimizó ni seleccionó época o semilla por prueba.

Entrada explícita y separada: `scripts/evaluate_test_pytorch.py --evaluate-test`, que usa `allow_test=True` únicamente después del ajuste. La extensión de calendario para construir covariables de prueba es local; no altera los límites ni bloqueos del pipeline de desarrollo. El script impide una segunda apertura automática de prueba. `scripts/summarize_test_pytorch.py` audita y resume predicciones existentes sin reentrenar ni volver a inferir.

Prueba cubre 1461 orígenes diarios y 35064 horas, del 1 de enero de 2022 al 31 de diciembre de 2025. Pronóstico secuencial diario con pesos fijos, contexto 168 horas y horizonte 24 horas. Orígenes posteriores pueden usar observaciones pasadas de prueba ya disponibles con los rezagos declarados (24 horas y dos días); no equivale a un único pronóstico a cuatro años ni a reentrenar con prueba.

| Familia | R² medio ± DE | MAE medio (COP/kWh) | RMSE medio (COP/kWh) |
|---|---:|---:|---:|
| CNN1D | 0.8151 ± 0.0033 | 81.618 | 155.206 |
| MLP | 0.7925 ± 0.0167 | 96.453 | 164.332 |
| LSTM | 0.6726 ± 0.0066 | 101.644 | 206.538 |

Media y DE entre cinco semillas; R² global calculado sobre todas las horas de prueba. Referencia semanal: MAE 133.636 COP/kWh, RMSE 235.198 COP/kWh y R² 0.5754. CNN1D obtuvo el menor error descriptivo entre las redes; no se afirma significancia estadística. No se efectuaron cambios de hiperparámetros ni nuevas evaluaciones a partir de estos resultados.

Artefactos: `results/test_pytorch/RESUMEN_PRUEBA.md`, configuración congelada, estadísticas de desarrollo, métricas por semilla, resumen, curvas, pesos, predicciones, referencia semanal y huellas. Se verificaron 15 ejecuciones y 60 artefactos, recalculando MAE, RMSE y R² desde predicciones. Se superaron las 17 pruebas existentes. Las huellas del dataset se preservan; sus valores de prueba sí fueron consultados en esta evaluación. Libro y HTML sin regenerar; no se publicó en GitHub.

La descripción de prueba sin consultar en apartados anteriores corresponde al estado previo a esta autorización. Para trabajos futuros no tratar 2022–2025 como prueba intacta si se ajustan decisiones con sus resultados. Los requisitos confirmatorios bibliográficos, δ, potencia y dependencia temporal siguen pendientes; esta evaluación autorizada no equivale a completarlos.

## 10. Interpretación de variables, 5 de noviembre de 2026

Se calculó importancia por permutación de los checkpoints del piloto en el último fold de validación (2021-03-15 a 2021-12-31, 292 orígenes), cinco semillas y tres permutaciones por variable/semilla. Se intercambian trayectorias de 168 horas entre orígenes, preservando su orden interno; los pares seno/coseno se permutan conjuntamente. No se reentrenó ni se consultó prueba para este diagnóstico. Se comprobó que las predicciones originales reproducen las guardadas.

Las 37 entradas son: precio, dos demandas, 24 variables meteorológicas (tres por ocho ciudades), cuatro hidrológicas y seis columnas de calendario. El precio histórico fue la principal variable: incremento medio del MAE al permutar de 35.328 (MLP), 38.494 (LSTM) y 41.691 (CNN1D) COP/kWh. Le siguen aportes, reserva útil y calendario anual/semanal. Son dependencias predictivas descriptivas del último fold, no causalidad ni importancias de los modelos finales de prueba. La correlación entre variables limita la interpretación y el calendario horario, idéntico entre ventanas diarias, no puede evaluarse mediante esta permutación.

Script: `scripts/feature_importance_pytorch.py`. Resultados: `results/feature_importance_pytorch/IMPORTANCIA.md`, tablas completas y método. Las variantes de arquitectura y contextos de 24/72/168/336 horas discutidas después del piloto todavía no se han entrenado; los modelos existentes usan 168 horas.

## 11. Búsqueda de variantes iniciada, 5 de noviembre de 2026

El usuario autorizó iniciar el entrenamiento de variantes con Dropout fijo. Se fijó p=0.1 para todas las familias. Registro previo: `PROTOCOLO_VARIANTES_2026-11-05.md`. Doce arquitecturas (cuatro por familia), contextos24/72/168/336horas y Ridge0/1e-5/1e-4/1e-3:192configuraciones, cinco folds y cinco semillas11037–11041, total4800ajustes. Se inició en GPU con el entorno confirmado `mlenv` y el mismo override ROCm10.3.0. No se consulta ni reevalúa prueba.

Todas las variantes nuevas usan salida Softplus positiva y objetivo dividido por la DE de etiquetas de entrenamiento, sin centrar, de acuerdo con la restricción de precios no negativos discutida. Por tanto las variantes de ancho equivalente al piloto ya no son réplicas exactas del piloto con salida lineal. Ridge es una suma L2 explícita sobre matrices de pesos, excluye sesgos, y Adam usa weight_decay=0. Presupuesto máximo200épocas; mínimo20; parada tras15épocas sin reducción relativa de0.2% en MAE de validación respecto a la referencia de mejora acumulada. Se restauran los pesos de menor MAE absoluto y se registran época óptima y de parada. No es significancia estadística; el mismo bloque usado para parada también sirve para selección y puede producir métricas optimistas.

Los orígenes se fijan con contexto336 para las cuatro longitudes y se comparten entre candidatos. Escaladores nuevos por contexto/fold, exclusivamente con entrenamiento. Comprobaciones previas superadas:48combinaciones de arquitectura/longitud, salidas positivas, gradientes finitos, exclusión de sesgos en Ridge y comportamiento de parada; además17pruebas existentes. Los primeros ajustes reales finalizaron y la recuperación del mejor checkpoint reprodujo su MAE.

Script: `scripts/train_variants.py`; se ejecuta en segundo plano y continúa al finalizar la respuesta, mientras el equipo siga encendido. No se registra arranque automático. Resultados y estado vivo en `results/variant_search/`: `status.json`, `progress.html`, `metrics.csv`, `runs/`, configuraciones, entorno y auditoría de folds. La ejecución completa aún NO se ha verificado: consultar `status.json` y sólo considerar terminada si existe `completed.json` con4800ajustes. Los PID y URL local del panel están en `processes.json`; el panel local se refresca cada5segundos. Barra en consola: `python scripts/show_training_progress.py --watch`.

Para reanudar, con GPU accesible y mlenv activo: `HSA_OVERRIDE_GFX_VERSION=10.3.0 python scripts/train_variants.py`. El proceso rechaza configuraciones/fuentes distintas y usa bloqueo para impedir duplicados. Reanuda ajustes completos; uno interrumpido se repite desde cero. No ejecutar una segunda copia mientras el PID siga activo. La búsqueda no constituye aún benchmark confirmatorio ni repone prueba independiente.

## 12. Apagado al finalizar, autorizado por el usuario

El usuario solicitó apagar el PC al finalizar el entrenamiento. Se activó un proceso separado `scripts/shutdown_after_training.py`, sin modificar las fuentes congeladas de entrenamiento. Estado en `results/variant_search/shutdown_status.json`; registro en `shutdown_watcher.log`. Sólo solicita `systemctl poweroff --no-ask-password` después de existir `completed.json`, estado Completado,4800métricas únicas,192filas de resumen,960resultados por semilla y los checkpoints/predicciones/curvas/métricas de los4800ajustes. Espera60segundos adicionales y sincroniza escrituras antes del apagado. Si falla o se interrumpe el entrenamiento, no apaga. Se verificó permiso de logind CanPowerOff=yes.

Para cancelar el apagado pendiente, crear el archivo `results/variant_search/cancel_shutdown` (por ejemplo `touch results/variant_search/cancel_shutdown`). El vigilante comprueba la cancelación también durante la espera final. No es un apagado a hora fija ni persiste tras reiniciar el equipo.

## 13. Búsqueda de variantes finalizada, 6 de noviembre de 2026

Se completaron4800ajustes y192configuraciones a las00:10(hora de Colombia), en40774.75segundos (11h20min). Estado Completado y completed.json verificados;4800claves únicas y192filas de resumen. Resultados: `results/variant_search/summary.csv`, `best_by_family.csv` y `RESUMEN_VARIANTES.md`.

- CNN1D: `C3_h24_l2_0.0001`, MAE=24.155 ± 0.144, RMSE=37.604 COP/kWh; R²=0.8766; mejor época mediana=23.
- LSTM: `L2_h72_l2_0.001`, MAE=24.624 ± 0.101, RMSE=37.773 COP/kWh; R²=0.8755; mejor época mediana=22.
- MLP: `M3_h24_l2_0.001`, MAE=24.992 ± 0.095, RMSE=37.953 COP/kWh; R²=0.8743; mejor época mediana=18.

Métricas de selección en validación, potencialmente optimistas por parada y búsqueda sobre el mismo bloque; no son evaluación externa ni prueba. Se recalcularon R² y MAE de los75checkpoints ganadores desde sus predicciones. Prueba NO reevaluada. La orden de apagado registró poweroff_requested tras finalizar; no inferir apagado físico exclusivamente de ese registro. La barra anterior puede requerir reiniciar su servidor local si el equipo fue reiniciado.

## 14. Integración de modelos en el Jupyter Book, 6 de noviembre de 2026

Se añadió `book/10_modelos.ipynb`, generado por `scripts/create_model_notebook.py`. Incluye estructura de las37entradas, alineación temporal, escalado, salida Softplus, diagramas SVG de la entrada y de las mejores arquitecturas M3/L2/C3, fundamentos matemáticos, búsqueda192/4800, regularización y parada, tablas generadas desde artefactos, comparación semanal, curvas y limitaciones de selección. Las celdas incorporan las funciones de preparación y las definiciones del pipeline de entrenamiento; no importan módulos privados del proyecto ni reinician la búsqueda al ejecutar la documentación. Las fuentes matemáticas y de API se enlazan en el capítulo y referencias.

Se ejecutó el capítulo sin errores con mlenv y se reconstruyó HTML con Jupyter Book1.0.4, instalado en `.bookenv` dentro del proyecto para no modificar el entorno experimental. La ejecución documental recalculó la referencia semanal y verificó R² de los75checkpoints seleccionados desde predicciones de validación, sin consultar prueba. `verify_book.py` comprobó11cuadernos ejecutados,17páginas HTML, cero errores y cero enlaces locales rotos. Fuentes y HTML en `book/` y `docs/`; no se publicó en GitHub.

Se actualizaron título/introducción, índice, reproducibilidad y fuentes de conclusiones; la síntesis pasa al capítulo11. Las etiquetas de diagramas se ampliaron y los encabezados se adaptaron a modo oscuro. El libro se abrió en navegador local; PID/URL del servidor actual en `results/jbook_local_server.json`. Para regenerar el capítulo: `python scripts/create_model_notebook.py`; para ejecutar sólo sus cálculos: `python scripts/run_eda.py --chapters 10_modelos --no-build`; construir con Jupyter Book1.0.4 y verificar con `python scripts/verify_book.py`. Las definiciones de entrenamiento quedan visibles pero no se invocan automáticamente.

## 15. Preparación de publicación, 6 de noviembre de 2026

Se prepara la actualización de main y GitHub Pages a partir del HTML verificado en docs. El paquete versionado contiene fuentes del libro y scripts, resúmenes del piloto/prueba, métricas agregadas de4800ajustes y predicciones/curvas/métricas de los75ajustes de las configuraciones ganadoras. Los checkpoints y el resto de resultados completos permanecen en local, excluidos por `.gitignore`, sin borrarlos. El capítulo puede regenerar sus tablas/figuras con este subconjunto sin pesos. El workflow incorpora PyTorch CPU2.9.1 para ejecutar definiciones del capítulo y el generador `create_model_notebook.py`; no entrena redes en CI. El estado final de publicación debe verificarse en la URL pública del capítulo.

Para distribución, las75predicciones seleccionadas se agrupan en `results/variant_search/selected_predictions.zip` con huellas en `selected_predictions_manifest.json`. El capítulo lee ese archivo directamente; las curvas y métricas seleccionadas conservan su estructura de carpetas. Las predicciones originales permanecen en local.

## 16. Publicación verificada, 6 de noviembre de 2026

La actualización se publicó en main mediante el commit `312d11865459e81e35d13cd7eed37b444eb704b8`. GitHub Actions completó con éxito la validación del dataset,17pruebas,preparación de folds,generación/ejecución del libro y verificación de enlaces. El despliegue Pages finalizó correctamente; el capítulo público `https://fabian-11037.github.io/Time-Series-Project/10_modelos.html` respondióHTTP200 y se comprobaron las métricas24.155/40.157,los4800ajustes,losdiagramas y el archivo de predicciones.

Se versionaron281archivos modificados/nuevos (aproximadamente6MB), incluyendo la distribución compacta de75predicciones seleccionadas con huellas. No se incluyeron checkpoints,los5.4GBdelarchivo completo,entornos virtuales,PID ni estados de procesos. El código y los resultados completos permanecen en el equipo. El libro público diferencia selección en validación y prueba previamente consultada.

## 17. Revisión frente al Entregable 1, 6 de noviembre de 2026

Se actualizó este clon desde main hasta `f67a377e225087437829ee0826be971886acdf29` y se contrastó el JBook con las 34 páginas del PDF original del E1. Informe completo: `REVISION_ENTREGABLE_1.md`; evidencia: `results/e1_audit_2026-11-06.json`.

Estado vigente: EDA, datos y pipeline disponibles; piloto, evaluación inicial de prueba y búsqueda de variantes realizados. **El E1 no está completo:** faltan extracción/frecuencias de baselines, margen práctico, potencia, inferencia temporal con IC/tamaños de efecto/multiplicidad y evaluación independiente del proceso posterior de selección. Las 192 configuraciones no acreditan el protocolo condicional de arquitectura al que remite E1 §3.2; primero debe resolverse qué arquitecturas publicadas están suficientemente especificadas. No se ordenó repetir entrenamientos en esta revisión.

Verificaciones nuevas: 17 pruebas correctas; 142 archivos de datos íntegros; 11 cuadernos ejecutados según sus salidas almacenadas, 216 celdas, 17 páginas y cero errores/enlaces locales rotos. Se comprobaron 4800 registros únicos, código/protocolo congelados y 75 predicciones de validación con SHA-256, recalculando MAE/RMSE/R². Las 14 páginas públicas coinciden con docs; CI y Pages de la versión auditada finalizaron correctamente. No se reentrenó, no se ejecutaron nuevamente todos los cuadernos y no se volvió a evaluar prueba.

Las configuraciones seleccionadas son C3 con 24 h, L2 con 72 h y M3 con 24 h; sus errores son de selección en validación. La prueba previa corresponde a las configuraciones iniciales de 168 h. Para el estado actual prevalecen estas precisiones sobre las descripciones históricas de preparación anterior al entrenamiento. No presentar 2022–2025 como una prueba intacta del diseño posterior.

Pendientes documentados adicionales: expresiones desactualizadas en el capítulo 8, uso de «ajustes independientes» en el capítulo 10 y portabilidad a Windows (`fcntl` en script/cuaderno; búsqueda con GPU). Este clon distribuye predicciones seleccionadas, curvas y métricas, pero no todos los checkpoints ni predicciones de la prueba inicial. La revisión registra estas brechas sin modificar los experimentos ni el HTML.