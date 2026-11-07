"""Genera el capítulo de modelos a partir de fuentes y artefactos reproducibles."""
import ast
import hashlib
from pathlib import Path
import nbformat as nbf
from inline_notebook_code import SourceCatalog,apply_presentation_visibility

ROOT=Path(__file__).resolve().parents[1]
BOOK=ROOT/'book'

def diagram(name,labels):
    from html import escape
    width=1100;height=220;gap=16;box=(width-32-gap*(len(labels)-1))/len(labels)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img"><title>{escape(name)}</title><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#526575"/></marker></defs>']
    for i,label in enumerate(labels):
        x=16+i*(box+gap)
        parts.append(f'<rect x="{x}" y="35" width="{box}" height="140" rx="9" fill="{["#eaf2f8","#eaf5ef"][i%2]}" stroke="#718697"/>')
        lines=label.split('|')
        for j,line in enumerate(lines):
            parts.append(f'<text x="{x+box/2}" y="{105+(j-(len(lines)-1)/2)*25}" text-anchor="middle" fill="#163247" font-family="sans-serif" font-size="20">{escape(line)}</text>')
        if i<len(labels)-1:parts.append(f'<path d="M{x+box+2},105 H{x+box+gap-3}" stroke="#526575" marker-end="url(#arrow)"/>')
    parts.append('</svg>')
    (BOOK/'_static'/f'{name}.svg').write_text(''.join(parts),encoding='utf-8')

INTRO=r'''# 10. Modelos numéricos y búsqueda de configuraciones

Se comparan redes densas (MLP), recurrentes (LSTM) y convolucionales temporales (CNN1D) para pronosticar el precio nacional horario de bolsa. La búsqueda comprende 192 configuraciones y 4800 ajustes, exclusivamente con desarrollo 2000–2021. El MAE en COP/kWh es la métrica principal del benchmark y el criterio de selección; RMSE y R² son métricas secundarias. Se utilizan cinco bloques de validación consecutivos en 2018–2021 y cinco inicializaciones por configuración. La justificación bibliográfica y la agregación se desarrollan en la [sección 8.2](08_validacion.ipynb).

El experimento utiliza únicamente variables numéricas y calendario. Los resultados presentados son de **selección en validación**: el mismo bloque interviene en la parada anticipada y en la comparación de configuraciones. La prueba 2022–2025 no se reevalúa en esta búsqueda. Ese periodo se evaluó el 5 de noviembre de 2026 con las configuraciones iniciales de 168 horas; por tanto, estos resultados no constituyen una nueva evaluación externa ni un benchmark confirmatorio.

## 10.1 Estructura de la entrada y disponibilidad temporal

Para un origen diario $o$ a las 00:00 de Colombia y una longitud de historia $L$, una observación supervisada está formada por

$$
X_o=[\mathbf x_{o-L},\ldots,\mathbf x_{o-1}]\in\mathbb R^{L\times37},\qquad
\mathbf y_o=(y_o,\ldots,y_{o+23})\in\mathbb R^{24}.
$$

El eje temporal conserva frecuencia horaria; la salida predice directamente las 24 horas siguientes. No se realimentan predicciones entre horizontes.

| Bloque predictor | Variables | Columnas | Disponibilidad implementada |
|---|---|---:|---|
| Precio | Precio nacional de bolsa, COP/kWh | 1 | Desplazamiento de 24 horas |
| Demanda | Demanda real y comercial, kWh | 2 | Desplazamiento de 24 horas |
| Meteorología | Temperatura, humedad relativa y precipitación en ocho ciudades | 24 | Desplazamiento de 24 horas |
| Hidrología | Llenado, reserva útil, capacidad útil y aportes diarios | 4 | Dos días desde el inicio del día de referencia; último registro disponible |
| Calendario | Seno y coseno de los ciclos horario, semanal y anual | 6 | Calculados para la fecha de cada fila de entrada |
| **Total** | | **37** | |

Las ciudades son Bogotá, Medellín, Cali, Barranquilla, Cartagena, Bucaramanga, Pereira y Cúcuta. Para una variable horaria $v$, la fila alineada en $s$ contiene $v_{s-24}$. El dato horario más reciente de $X_o$ corresponde a $o-25$ horas; la hidrología se incorpora mediante una unión temporal hacia atrás según su fecha de disponibilidad. Estos rezagos son supuestos retrospectivos, no horarios de publicación certificados. Las variables climáticas proceden de reanálisis y las series pueden incorporar revisiones.

```{figure} _static/modelos-entrada.svg
:alt: Datos numéricos y calendario alineados, ventanas temporales, escalado y salida de 24 precios.
:width: 100%

Construcción de cada ejemplo supervisado. La historia varía entre 24 y 336 horas; las columnas predictoras y el horizonte permanecen constantes.
```

Las entradas se estandarizan por columna con media y desviación estimadas exclusivamente sobre las filas utilizadas por el entrenamiento del fold. El objetivo se divide por su desviación de entrenamiento $s_y>0$, sin centrarlo. Esta transformación permite imponer positividad en unidades originales:

$$
\widetilde y=y/s_y,\qquad
\widehat y=s_y\,\operatorname{Softplus}(z),\qquad
\operatorname{Softplus}(z)=\log(1+e^z).
$$

La restricción supone precios no negativos. Softplus produce valores estrictamente positivos y una derivada sigmoide; no representa exactamente cero. No se aplica sobre un objetivo centrado. La salida tiene 24 componentes porque el horizonte comprende 24 horas, no por una restricción de la arquitectura.

## 10.2 Configuración MLP seleccionada

La variante **M3**, con historia de **24 horas**, transforma $X_o\in\mathbb R^{24\times37}$ en un vector de 888 entradas. Utiliza dos capas ocultas de 256 y 128 unidades, activación ReLU, Dropout de 0,1 después de cada activación, y una proyección a 24 salidas con Softplus. La penalización seleccionada es $\lambda=10^{-3}$.

```{figure} _static/modelos-mlp.svg
:alt: Entrada 24 por 37, aplanamiento a 888, capas densas de 256 y 128, proyección a 24 y Softplus.
:width: 100%

MLP seleccionada. Las dimensiones representan una observación, sin el eje de lote.
```

Con $\mathbf h^{(0)}=\operatorname{vec}(X_o)$, las capas ocultas calculan

$$
\mathbf h^{(\ell)}=D_{0.1}\!\left[\max(0,W_\ell\mathbf h^{(\ell-1)}+\mathbf b_\ell)\right],\qquad \ell\in\{1,2\}.
$$

La salida es $\widehat{\mathbf y}_o=s_y\operatorname{Softplus}(W_3\mathbf h^{(2)}+\mathbf b_3)$. Durante entrenamiento, $D_p(\mathbf h)=\mathbf m\odot\mathbf h/(1-p)$, con máscaras Bernoulli de probabilidad $1-p$; en evaluación actúa como identidad. Las matrices densas permiten interacciones no lineales entre variables y posiciones temporales. El aplanamiento conserva la posición mediante pesos específicos, pero no impone compartición temporal; su número de parámetros crece con $L$.

Esta estructura sigue los fundamentos de las [redes de propagación hacia delante de Goodfellow, Bengio y Courville](https://www.deeplearningbook.org/contents/mlp.html). Los tamaños concretos se seleccionaron dentro del espacio experimental declarado; no corresponden a una reproducción exacta de una arquitectura publicada.

## 10.3 Configuración LSTM seleccionada

La variante **L2** utiliza **72 horas**, una capa LSTM unidireccional de **64 unidades**, el último estado oculto, Dropout de 0,1 y una proyección de 64 a 24 con Softplus. La penalización seleccionada es $\lambda=10^{-3}$. Cada ventana inicia sus estados oculto y de celda en cero; no se transfiere estado entre ejemplos.

```{figure} _static/modelos-lstm.svg
:alt: Secuencia 72 por 37, LSTM de 64 unidades, último estado, Dropout, proyección a 24 y Softplus.
:width: 100%

LSTM seleccionada. La secuencia completa se procesa antes de emitir el horizonte diario.
```

Para el paso temporal $s$, la implementación combina la entrada $\mathbf x_s$, el estado oculto $\mathbf h_{s-1}$ y la memoria $\mathbf c_{s-1}$:

$$
\begin{aligned}
\mathbf i_s&=\sigma(W_{xi}\mathbf x_s+W_{hi}\mathbf h_{s-1}+\mathbf b_i),\\
\mathbf f_s&=\sigma(W_{xf}\mathbf x_s+W_{hf}\mathbf h_{s-1}+\mathbf b_f),\\
\mathbf g_s&=\tanh(W_{xg}\mathbf x_s+W_{hg}\mathbf h_{s-1}+\mathbf b_g),\\
\mathbf o_s&=\sigma(W_{xo}\mathbf x_s+W_{ho}\mathbf h_{s-1}+\mathbf b_o),\\
\mathbf c_s&=\mathbf f_s\odot\mathbf c_{s-1}+\mathbf i_s\odot\mathbf g_s,\\
\mathbf h_s&=\mathbf o_s\odot\tanh(\mathbf c_s).
\end{aligned}
$$

Las compuertas regulan conservación, incorporación y exposición de información. La actualización aditiva de la memoria favorece la propagación de gradientes respecto de una recurrencia puramente multiplicativa, sin garantizar que cualquier dependencia larga pueda aprenderse. La salida usa $\mathbf h_{o-1}$ para los 24 horizontes. Los fundamentos se remontan a [Hochreiter y Schmidhuber (1997)](https://www.bioinf.jku.at/publications/older/2604.pdf); las ecuaciones con compuerta de olvido y las convenciones implementadas corresponden a la [LSTM de PyTorch](https://docs.pytorch.org/docs/stable/generated/torch.nn.LSTM.html).

## 10.4 Configuración CNN1D seleccionada

La variante **C3** emplea **24 horas**, dos convoluciones temporales de **64 filtros**, kernel de longitud **5**, paso 1 y padding 2. Cada convolución se sigue de ReLU y Dropout1d de 0,1. Un promedio adaptativo reduce el eje temporal a siete posiciones; el tensor $64\times7$ se aplana a 448 componentes y se proyecta a 24 salidas con Softplus. La penalización seleccionada es $\lambda=10^{-4}$.

```{figure} _static/modelos-cnn.svg
:alt: Entrada 37 por 24, dos convoluciones de 64 filtros, pooling a siete posiciones, aplanamiento y salida positiva de 24 precios.
:width: 100%

CNN1D seleccionada. Se transpone la entrada para que los predictores formen el eje de canales.
```

Cada filtro combina los canales de entrada en un entorno temporal compartiendo parámetros entre posiciones. Con padding cero y kernel 5, una capa calcula la correlación cruzada

$$
z_{c,s}=b_c+\sum_{j=1}^{C_{\mathrm{in}}}\sum_{q=0}^{4}K_{c,j,q}\,h_{j,s+q-2},\qquad h'_{c,s}=\max(0,z_{c,s}).
$$

Las dos capas generan un campo receptivo local de nueve horas antes del pooling. El promedio adaptativo calcula siete promedios sobre intervalos del eje temporal; para 24 posiciones, los intervalos pueden solaparse por el redondeo de sus límites. La capa densa integra después esas representaciones a lo largo de toda la ventana. Dropout1d elimina canales completos durante entrenamiento. El padding simétrico utiliza posiciones de la ventana histórica; no incorpora datos posteriores al origen de pronóstico.

La compartición de filtros reduce la dependencia del número de parámetros respecto de la longitud de entrada y favorece la detección de patrones locales repetidos. El pooling reduce resolución temporal, por lo que puede perder detalle de la hora exacta. Véanse los fundamentos de [redes convolucionales](https://www.deeplearningbook.org/contents/convnets.html) y la [documentación de Conv1d](https://docs.pytorch.org/docs/stable/generated/torch.nn.Conv1d.html).

## 10.5 Espacio de búsqueda y protocolo de entrenamiento

La búsqueda exhaustiva cruza las siguientes doce arquitecturas con cuatro contextos y cuatro penalizaciones. El Dropout se mantiene en 0,1 en todos los candidatos.

| Familia | Código | Configuración estructural |
|---|---|---|
| MLP | M1 | Densas 64 → 32 |
| MLP | M2 | Densas 128 → 64 |
| MLP | M3 | Densas 256 → 128 |
| MLP | M4 | Densas 128 → 64 → 32 |
| LSTM | L1 | Una capa, 32 unidades |
| LSTM | L2 | Una capa, 64 unidades |
| LSTM | L3 | Dos capas, 32 unidades por capa |
| LSTM | L4 | Una capa de 64 unidades y densa intermedia de 32 |
| CNN1D | C1 | Dos convoluciones, 32 filtros, kernel 5 |
| CNN1D | C2 | Dos convoluciones, 32 filtros, kernel 3 |
| CNN1D | C3 | Dos convoluciones, 64 filtros, kernel 5 |
| CNN1D | C4 | Tres convoluciones, 32 filtros, kernel 3, dilataciones 1, 2 y 4 |

Los contextos son $L\in\{24,72,168,336\}$ horas y Ridge usa $\lambda\in\{0,10^{-5},10^{-4},10^{-3}\}$. El total es $12\times4\times4=192$ configuraciones, con cinco folds y cinco semillas (11037–11041), para **4800 ajustes desde cero**. No se descartan configuraciones según resultados intermedios. Los orígenes admisibles se fijan con la ventana máxima de 336 horas y se comparten entre todas las longitudes. Los cinco bloques consecutivos de validación cubren 2018–2021 y el entrenamiento se amplía antes de cada bloque.

La función objetivo es

$$
\mathcal L(\theta)=\frac{1}{24N}\sum_{i=1}^{N}\sum_{h=0}^{23}\left|\frac{y_{i,h}}{s_y}-\operatorname{Softplus}(z_{i,h})\right|
+\lambda\sum_{W\in\mathcal W}\lVert W\rVert_F^2.
$$

$\mathcal W$ comprende las matrices y tensores de pesos con más de una dimensión; se excluyen sesgos. La suma L2 no se normaliza por la cantidad de parámetros: un mismo $\lambda$ no supone igual regularización efectiva entre arquitecturas. Se utiliza Adam con tasa $10^{-3}$, `weight_decay=0`, lotes de 256 y recorte de la norma del gradiente a 1. Los gradientes se obtienen por retropropagación; en LSTM, a través de la secuencia temporal.

La parada anticipada monitoriza **MAE de validación en COP/kWh, sin penalización**. Una reducción relativa de al menos 0,2 % respecto de la referencia acumulada reinicia la paciencia. Se detiene después de 15 épocas sin esa mejora, con mínimo de 20 y máximo de 200 épocas. Se conservan los pesos de menor MAE absoluto, aunque esa época sea anterior a la 20. El umbral define una meseta práctica; no representa significancia estadística ni el margen de relevancia confirmatorio $\delta$.

Las familias representan hipótesis inductivas diferentes: interacciones densas por posición, memoria recurrente y patrones locales con pesos compartidos. La revisión de textos completos del [capítulo 9](09_literatura.ipynb) verifica LSTM en 7/16 estudios puntuales, MLP/DNN en 6/16 y CNN en 2/16. La selección combina recurrencia y simplicidad con memoria, interacciones por posición y patrones locales. CNN empata en frecuencia con CNN-LSTM y Transformer; su estructura convolucional independiente permite mantener tres referencias diferenciadas. Una referencia describe explícitamente CNN1D y otra no permite confirmar la dimensión. Los tamaños concretos se seleccionaron en desarrollo y constituyen adaptaciones, no réplicas exactas de esos artículos. El capítulo 9 presenta fuentes, configuraciones reportadas, análisis crítico y fórmulas de parámetros y costo. El mismo máximo de épocas no iguala costo computacional ni capacidad. La inferencia confirmatoria con dependencia temporal y el dimensionamiento por potencia permanecen pendientes.
'''

RESULTS=r'''## 10.6 Resultados y referencia estacional

Para cada semilla se concatenan los errores de todos los orígenes y las 24 horas de los cinco folds. Se calcula MAE, RMSE y R² sobre esa concatenación; después se promedian las cinco métricas. La desviación estándar refleja variación entre inicializaciones, no incertidumbre temporal. El RMSE se obtiene de errores cuadrados agrupados, no promediando directamente los RMSE de folds.

La referencia estacional repite el precio observado 168 horas antes de cada hora objetivo: $\widehat y^{\mathrm{sem}}_{o+h}=y_{o+h-168}$. Se evalúa sobre los mismos orígenes. La mejora porcentual es $100(1-\operatorname{MAE}_{\mathrm{modelo}}/\operatorname{MAE}_{\mathrm{sem}})$; esta razón no se denomina MASE.
'''

END=r'''La configuración C3 con 24 horas de historia y $\lambda=10^{-4}$ presenta el menor MAE medio de selección. La reducción respecto de la referencia semanal es cercana al 40 %. Las diferencias entre los mejores candidatos de las tres familias son menores que la diferencia frente a la referencia, pero no se ha contrastado su significancia con un procedimiento que considere dependencia temporal y selección múltiple.

Los contextos de 24 y 72 horas concentran las mejores configuraciones por familia. Esto no demuestra ausencia de información útil en historias más largas: capacidad, regularización, optimización y representación temporal se modifican conjuntamente. La positividad de salida y el procedimiento de parada también difieren del piloto inicial de 30 épocas, por lo que el cambio de error no puede atribuirse a un único factor.

Los 4800 ajustes terminaron por paciencia y ninguno alcanzó el máximo de 200 épocas. Las curvas ilustrativas permiten examinar mejoras iniciales y estabilización, pero el umbral del 0,2 % no es un contraste de hipótesis. El uso de validación tanto para elegir la época como para seleccionar entre 192 candidatos introduce optimismo. Estos valores no deben presentarse como errores de prueba de los nuevos modelos.

## 10.7 Alcance de la evaluación

La búsqueda utiliza datos retrospectivos y rezagos de disponibilidad supuestos. Las variables meteorológicas urbanas no representan directamente las cuencas aportantes; la correlación entre predictores dificulta atribuir su contribución individual. El análisis de importancia de los modelos iniciales no se transfiere automáticamente a estas nuevas configuraciones.

El periodo 2022–2025 fue evaluado previamente con configuraciones iniciales distintas. No se consultó de nuevo durante esta búsqueda y no se asignan sus métricas a los modelos aquí seleccionados. La validación utilizada para selección no constituye una estimación externa imparcial. Una conclusión confirmatoria requiere un diseño de evaluación independiente, control de comparaciones, margen práctico y potencia definidos antes de observar sus resultados.

## 10.8 Código del pipeline de entrenamiento

Las celdas siguientes contienen las definiciones ejecutables de las arquitecturas, penalización, parada y búsqueda utilizadas. Las funciones de preparación temporal y escalado aparecen al inicio del cuaderno. La ejecución documental define las funciones y verifica los artefactos, sin repetir los 4800 ajustes. El entrenamiento completo se invoca desde la raíz del repositorio mediante `python scripts/train_variants.py --device auto`. La ejecución admite CPU o una GPU CUDA/ROCm compatible con la instalación de PyTorch; `--device cpu` fuerza CPU y `--device gpu` exige GPU. El registro identifica el dispositivo utilizado.
'''

def source_nodes(path):
    nodes=[]
    for node in ast.parse(path.read_text(encoding='utf-8')).body:
        if isinstance(node,ast.ImportFrom) and (node.module or '').startswith('colombia_energy'):continue
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ROOT' for t in node.targets):continue
        if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and ast.unparse(node.value.func)=='sys.path.insert':continue
        if isinstance(node,ast.If) and '__name__' in ast.unparse(node.test):continue
        nodes.append(node)
    return nodes

def main():
    BOOK.mkdir(exist_ok=True)
    diagram('modelos-entrada',['Precio, demanda|clima|e hidrología','Rezagos de|disponibilidad','37 predictores|con calendario','Ventana|L × 37','Escalado sólo|con entrenamiento','Modelo|24 precios|futuros'])
    diagram('modelos-mlp',['Entrada|24 × 37','Aplanamiento|888','Densa 256|ReLU · Dropout','Densa 128|ReLU · Dropout','Proyección|24','Softplus|× escala|del precio'])
    diagram('modelos-lstm',['Entrada|72 × 37','LSTM|64 unidades','Último estado|64','Dropout|p = 0,1','Proyección|24','Softplus|× escala|del precio'])
    diagram('modelos-cnn',['Entrada|37 × 24','Conv1d|64 × 24|ReLU|Dropout1d','Conv1d|64 × 24|ReLU|Dropout1d','Promedio|64 × 7','Aplanamiento|448','Densa 24|Softplus|× escala'])
    cells=[nbf.v4.new_markdown_cell(INTRO)]
    catalog=SourceCatalog()
    support=ast.parse("pipeline = build_training_pipeline(dict(load_pipeline_config(), lookback_hours=336))\nbatch = prepare_fold_arrays(pipeline,pipeline['folds'][0])").body
    cells += [nbf.v4.new_markdown_cell('### Preparación temporal y escalado: implementación\n\nLas siguientes funciones construyen las entradas exclusivamente con desarrollo y conservan los controles de disponibilidad y separación temporal.')]
    cells += catalog.support_cells(support)
    cells += [nbf.v4.new_markdown_cell(RESULTS)]
    analysis='''import json
import numpy as np
import pandas as pd
from IPython.display import display
from io import BytesIO
from zipfile import ZipFile
RESULTS = ROOT / 'results/variant_search'
metrics = pd.read_csv(RESULTS / 'metrics.csv')
summary = pd.read_csv(RESULTS / 'summary.csv')
winners = pd.read_csv(RESULTS / 'best_by_family.csv')
assert len(metrics) == 4800 and len(summary) == 192
assert not metrics.duplicated(['candidate', 'fold', 'seed']).any()
assert json.loads((RESULTS / 'completed.json').read_text())['test_evaluated'] is False
pipeline = build_training_pipeline(dict(load_pipeline_config(), lookback_hours=336))
y_all, weekly_all = [], []
for fold in pipeline['folds']:
    positions = fold['validation_origins'][:, None] + np.arange(24)
    y_all.append(pipeline['target'].to_numpy()[positions])
    weekly_all.append(pipeline['target'].to_numpy()[positions - 168])
y_all, weekly_all = np.concatenate(y_all), np.concatenate(weekly_all)
error = weekly_all - y_all
baseline = {'mae': float(np.abs(error).mean()),
            'rmse': float(np.sqrt(np.square(error).mean())),
            'r2': float(1 - np.square(error).sum() / np.square(y_all - y_all.mean()).sum())}
records = [{'Modelo': 'Referencia semanal', 'Configuración': 'Repetición a 168 h',
            'MAE': baseline['mae'], 'DE MAE': np.nan, 'RMSE': baseline['rmse'],
            'R²': baseline['r2'], 'Reducción MAE (%)': 0.0}]
prediction_archive = ZipFile(RESULTS / 'selected_predictions.zip')
for row in winners.itertuples():
    # R² se verifica desde las predicciones de cada semilla, sin abrir prueba.
    r2_values = []
    for seed in range(11037, 11042):
        actual, predicted = [], []
        for fold in range(1, 6):
            folder = RESULTS / 'runs' / row.candidate / f'fold_{fold}_seed_{seed}'
            archive_path = f'{row.candidate}/fold_{fold}_seed_{seed}/predictions.npz'
            with np.load(BytesIO(prediction_archive.read(archive_path))) as saved:
                yy = saved['actual'].astype(np.float64).ravel()
                pp = saved['predictions'].astype(np.float64).ravel()
                actual.append(yy); predicted.append(pp)
        yy, pp = np.concatenate(actual), np.concatenate(predicted)
        r2_values.append(1 - np.square(yy-pp).sum() / np.square(yy-yy.mean()).sum())
    assert np.isclose(np.mean(r2_values), row.r2)
    records.append({'Modelo': row.family, 'Configuración': row.candidate,
                    'MAE': row.mae, 'DE MAE': row.mae_sd, 'RMSE': row.rmse,
                    'R²': row.r2, 'Reducción MAE (%)': 100*(1-row.mae/baseline['mae'])})
prediction_archive.close()
comparison = pd.DataFrame(records)
display(comparison.style.format({'MAE':'{:.3f}', 'DE MAE':'{:.3f}', 'RMSE':'{:.3f}',
                                 'R²':'{:.4f}', 'Reducción MAE (%)':'{:.2f}'}, na_rep='—').hide(axis='index'))
'''
    cells += [nbf.v4.new_code_cell(analysis)]
    cells += [nbf.v4.new_markdown_cell('### Capacidad y comportamiento de la parada\n\nLas épocas óptimas pueden preceder al mínimo de 20: ese mínimo restringe cuándo se detiene el ajuste, no qué checkpoint se conserva. Los conteos incluyen pesos y sesgos entrenables.')]
    cells += [nbf.v4.new_code_cell('''rows = []
for w in winners.itertuples():
    g = metrics[metrics.candidate == w.candidate]
    rows.append({'Modelo':w.family, 'Parámetros':int(g.parameters.iloc[0]),
                 'Mejor época (mediana)':g.best_epoch.median(),
                 'Época de parada (mediana)':g.epochs.median(),
                 'Ajustes':len(g)})
display(pd.DataFrame(rows).style.format(precision=0).hide(axis='index'))
assert (metrics.stop_reason == 'patience').all()
display(pd.DataFrame([{'Ajustes completos':len(metrics), 'Configuraciones':len(summary),
                       'Épocas promedio':metrics.epochs.mean(), 'Máximo observado':metrics.epochs.max(),
                       'Duración (horas)':json.loads((RESULTS/'completed.json').read_text())['total_seconds']/3600}]).style.format(precision=2).hide(axis='index'))''')]
    cells += [nbf.v4.new_markdown_cell('### Comparación con la referencia semanal\n\nLas barras muestran el MAE agrupado y las líneas de error, la desviación estándar entre semillas; no representan intervalos de confianza temporal.')]
    cells += [nbf.v4.new_code_cell('''import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(8, 4))
positions = np.arange(len(winners))
ax.bar(positions, winners.mae, yerr=winners.mae_sd, capsize=5,
       color=['#247ba0','#2a9d8f','#d18a2d'])
ax.axhline(baseline['mae'], color='#555555', linestyle='--', label='Referencia semanal')
ax.set_xticks(positions, winners.family)
ax.set_ylabel('MAE (COP/kWh)'); ax.set_ylim(0, 45)
ax.legend(frameon=False); ax.spines[['top','right']].set_visible(False)
ax.grid(axis='y', alpha=.15); fig.tight_layout(); plt.show()''')]
    cells += [nbf.v4.new_markdown_cell('### Curvas de aprendizaje de los candidatos seleccionados\n\nSe presentan las ejecuciones del quinto fold y semilla 11037, con MAE de entrenamiento y validación. La línea vertical identifica el checkpoint óptimo; la última época corresponde a la parada. Las curvas de entrenamiento agregan lotes con pesos y máscaras Dropout cambiantes; no son una evaluación final del conjunto de entrenamiento.')]
    cells += [nbf.v4.new_code_cell('''fig, axes = plt.subplots(1, 3, figsize=(13, 3.6))
for ax, w in zip(axes, winners.itertuples()):
    curve = pd.read_csv(RESULTS/'runs'/w.candidate/'fold_5_seed_11037'/'curves.csv')
    row = metrics[(metrics.candidate==w.candidate)&(metrics.fold==5)&(metrics.seed==11037)].iloc[0]
    ax.plot(curve.epoch,curve.train_mae_cop_kwh,label='Entrenamiento')
    ax.plot(curve.epoch,curve.validation_mae_cop_kwh,label='Validación')
    ax.axvline(row.best_epoch,color='#666666',linestyle=':',label='Mejor época')
    ax.set_title(w.family); ax.set_xlabel('Época'); ax.set_ylabel('MAE (COP/kWh)')
    ax.spines[['top','right']].set_visible(False)
axes[0].legend(frameon=False,fontsize=8)
fig.tight_layout(); plt.show()''')]
    cells += [nbf.v4.new_markdown_cell(END)]
    cells += [nbf.v4.new_code_cell("SOURCE_PATH = ROOT / 'scripts/train_variants.py'")]
    runtime_names=ast.parse('select_device; synchronize_device; seed_training; runtime_environment; exclusive_run').body
    cells += catalog.support_cells(runtime_names)
    for node in source_nodes(ROOT/'scripts/train_variants.py'):
        code=ast.unparse(node).replace('Path(__file__).read_bytes()', 'SOURCE_PATH.read_bytes()')
        if not isinstance(node,ast.Expr) or not isinstance(node.value,ast.Constant):
            cells.append(nbf.v4.new_code_cell(code))
    cells += [nbf.v4.new_markdown_cell('### Reproducción y trazabilidad\n\nLas fuentes originales del experimento se conservan con sus huellas en `resources/experiment_sources/`; el registro es `PROTOCOLO_VARIANTES_2026-11-05.md`. La versión portable de ejecución está en `scripts/train_variants.py`; los resultados están en `results/variant_search/`. La configuración histórica registra huellas del código original archivado y del protocolo; cada checkpoint incluye arquitectura, contexto, penalización, semilla, escaladores y época óptima. La ejecución documental verifica resultados existentes y no inicia entrenamiento.\n\nPyTorch 2.9.1+rocm6.4, Python 3.12.3 y AMD Radeon RX 6700 XT de 12 GB constituyen el entorno experimental. La ejecución empleó el ajuste de compatibilidad local `HSA_OVERRIDE_GFX_VERSION=10.3.0`; no se presupone necesario para otros dispositivos. La reconstrucción documental se realiza por CPU en Windows y Linux; no requiere los controladores de ese equipo ni repite los ajustes. Las nuevas ejecuciones usan una carpeta distinta y registran su entorno; los resultados entre dispositivos pueden diferir por aritmética y algoritmos de cálculo. Los datos y supuestos retrospectivos se describen en los capítulos de fuentes y validación.')]
    nb=nbf.v4.new_notebook(cells=cells)
    nb.metadata.kernelspec=dict(name='python3',display_name='Python 3',language='python')
    nb.metadata.language_info=dict(name='python',version='3.12')
    nb.metadata.inline_analysis_sources={**catalog.hashes,'train_variants':hashlib.sha256((ROOT/'scripts/train_variants.py').read_bytes()).hexdigest()}
    apply_presentation_visibility(nb)
    path=BOOK/'10_modelos.ipynb'
    if path.exists():
        old=nbf.read(path,as_version=4)
        for previous,current in zip(old.cells,nb.cells):
            if previous.cell_type==current.cell_type:current.id=previous.id
            if previous.cell_type==current.cell_type=='code' and previous.source==current.source:
                current.outputs=previous.get('outputs',[]);current.execution_count=previous.get('execution_count')
    with path.open('w',encoding='utf-8',newline='\n') as stream:
        nbf.write(nb,stream)

if __name__=='__main__':main()
