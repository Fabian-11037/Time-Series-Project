# Contexto para continuar el proyecto

Actualización: 4 de noviembre de 2026. Idioma de trabajo: español.

Autores: Fabian José Manrique Morelos y Gloria Bastida. Maestría en Estadística Aplicada, Universidad del Norte.

## 1. Proyecto y estado

Repositorio: https://github.com/Fabian-11037/Time-Series-Project, rama `main`.
Libro público: https://fabian-11037.github.io/Time-Series-Project/.

El objetivo general es desarrollar un modelo de pronóstico que integre series temporales y texto. La etapa actual prepara los modelos numéricos de referencia para el precio nacional horario de bolsa de XM, en COP/kWh (`precio_bolsa_cop_kwh`). El E1 utiliza exclusivamente variables numéricas y calendario; los modelos multimodales corresponden a etapas posteriores.

Estado al actualizar este archivo:

- Dataset consolidado, versionado y auditado; EDA y revisión bibliográfica publicados.
- Pipeline de validación **`split_train_val_forwardChaining`** implementado y configurado con cinco folds.
- Preparación de ventanas y escaladores independiente por fold; interfaz disponible para incorporar modelos.
- **No se han entrenado MLP, LSTM ni CNN1D ni se ha ejecutado su benchmark colombiano.** `project_scope.json` registra este estado.
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

En Windows también puede utilizarse `.venv\Scripts\python.exe` sin activar el entorno. Jupyter Book debe permanecer en la versión 1.0.4. El archivo de dependencias actual cubre EDA y pipeline; el framework de Deep Learning y sus versiones deberán incorporarse antes del entrenamiento.

`scripts/prepare_pipeline.py --plan-only` calcula sólo el plan temporal. Sin esa opción prepara y audita los escaladores de los cinco folds, sin entrenar modelos. Sus artefactos están en `results/pipeline/`: `folds.csv`, `fold_indices.npz`, `preprocessors.json` y `manifest.json`.

Los scripts de adquisición y `import_local_downloads.py` documentan la procedencia del dataset; no son necesarios para reproducir la instantánea versionada en otro equipo.

## 5. Incorporación del entrenamiento

Leer `PIPELINE.md`, `MODELOS_E1.md`, `PROTOCOLO_EDA.md` y `PROTOCOLO_PIPELINE_CV.md`.

Los candidatos propuestos son:

1. MLP/DNN sobre ventanas de rezagos.
2. LSTM de una capa recurrente con salida densa.
3. CNN1D poco profunda con salida densa.

Son una recomendación de familias, no una selección sistemática cerrada ni configuraciones ya entrenadas. Antes del benchmark:

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
