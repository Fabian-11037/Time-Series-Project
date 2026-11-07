# Ejecución en Windows y Linux

Se utiliza Python 3.12 y un entorno virtual nuevo. El libro puede ejecutarse por CPU en ambos sistemas. Los scripts de entrenamiento admiten CPU y las GPU CUDA/ROCm que detecte la distribución instalada de PyTorch.

## Instalación por CPU

```bash
python -m venv .venv
```

Activación en Windows PowerShell: `.venv\Scripts\Activate.ps1`. En Linux: `source .venv/bin/activate`. También se puede invocar directamente `.venv\Scripts\python.exe` o `.venv/bin/python`.

```bash
python -m pip install -r requirements.lock.txt
python -m pip install -r requirements-pytorch-cpu.txt
python scripts/verify_dataset.py
python -m unittest discover -s tests
python scripts/prepare_pipeline.py
python scripts/create_notebooks.py
python scripts/create_literature_notebooks.py
python scripts/create_model_notebook.py
python scripts/run_eda.py
python scripts/verify_book.py
```

La construcción usa Jupyter Book 1.0.4. Las definiciones del entrenamiento se incluyen en el capítulo de modelos; su ejecución documental utiliza resultados guardados y no inicia la búsqueda. Los análisis y funciones permanecen en las celdas. El código de presentación se elimina del HTML.

## Entrenamiento

```bash
python scripts/train_pytorch.py --device cpu --output results/pilot_pytorch_portable
python scripts/train_variants.py --device auto --output results/variant_search_portable
```

Opciones compartidas: `--device cpu`, `--device auto`, `--device gpu` y `--device cuda:N`; `--threads 4` limita los hilos de CPU de PyTorch. `auto` elige la primera GPU CUDA/ROCm detectada o CPU. `gpu` exige una GPU; un error de hardware o memoria durante el ajuste se comunica y no activa una sustitución silenciosa de dispositivo. Los identificadores CUDA también se utilizan en PyTorch/ROCm para AMD.

Para GPU se instala PyTorch 2.9.1 con la distribución apropiada al sistema, controlador y dispositivo, en lugar del archivo de dependencias CPU. Consultar el [selector oficial](https://pytorch.org/get-started/previous-versions/) y las [convenciones de ROCm](https://docs.pytorch.org/docs/2.9/notes/hip.html). La adaptación no instala controladores ni convierte cualquier GPU en un dispositivo compatible; el equipo puede usar CPU cuando su GPU no esté soportada. No se configura automáticamente el override utilizado por el equipo AMD original.

Cada ejecución registra sistema, versiones, dispositivo, backend, hilos y configuración de determinismo. Las semillas no garantizan identidad bit a bit entre CPU, GPU, versiones o sistemas; véase la [documentación de reproducibilidad](https://docs.pytorch.org/docs/2.9/notes/randomness.html). Reanudar exige que coincidan fuentes, configuración y entorno registrados. Para cambiar de dispositivo debe utilizarse otra carpeta y comparar ejecuciones identificadas.

La búsqueda completa conserva 192 configuraciones, cinco folds, cinco semillas y sus reglas de entrenamiento. Por CPU su duración dependerá del equipo; los tests sólo realizan pasos pequeños con datos sintéticos y no repiten los 4800 ajustes.

## Integridad y fuentes históricas

Los resultados de `results/variant_search/`, piloto original se conservan. Las nuevas carpetas predeterminadas terminan en `_portable`; intentar usar una configuración congelada incompatible produce un error antes de escribir sus resultados. Los checkpoints deben acompañarse de sus escaladores y configuración; se cargan con `map_location` en el dispositivo elegido.

`resources/experiment_sources/manifest.json` conserva las fuentes originales exactas, referidas por los hashes de los experimentos de noviembre de 2026. Estos archivos constituyen evidencia histórica y no son puntos de entrada de ejecución. Los scripts actuales y `src/colombia_energy/runtime.py` contienen la implementación portable; las nuevas configuraciones registran ambas huellas.

El bloqueo de ejecución utiliza `msvcrt` en Windows y `fcntl` en Linux, importados únicamente dentro de su rama correspondiente. La liberación se realiza también ante excepciones. No deben ejecutarse dos procesos sobre una misma carpeta.

La ejecución documental y la búsqueda se limitan a desarrollo 2000–2021. El acceso a valores de 2022–2025 permanece bloqueado por defecto; cualquier evaluación final requiere un protocolo específico. El manifiesto y los cortes temporales se conservan.


## Ejecución del kernel documental

`run_eda.py` utiliza por defecto `--kernel-mode local`: nbclient e IPython ejecutan cada cuaderno en un proceso separado, sin conexiones TCP entre cliente y kernel. Se conservan mensajes de salida, tablas, figuras, contadores de ejecución y propagación de errores. La alternativa `--kernel-mode tcp` mantiene el kernel convencional cuando el entorno permite esa comunicación. El proceso de cada cuaderno tiene un límite de 2000 segundos. Las dependencias documentales fijan ipykernel 6.30.1 y jupyter_client 8.6.3; este cambio no modifica el entorno histórico de entrenamiento ROCm.

El ejecutor local está destinado a las celdas síncronas del libro. Para celdas con `await` de nivel superior o extensiones interactivas del kernel debe utilizarse `--kernel-mode tcp` y comprobar su funcionamiento en el entorno correspondiente.
