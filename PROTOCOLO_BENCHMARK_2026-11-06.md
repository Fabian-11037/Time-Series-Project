# Protocolo del benchmark numérico

Versión 1.0 · 6 de noviembre de 2026 · Hora de Colombia.

Autores: Fabian José Manrique Morelos y Gloria Bastida.

## 1. Protocolo del benchmark

### Pregunta y alcance

¿Qué familia, entre MLP, LSTM y CNN1D, presenta menor MAE al pronosticar los próximos 24 precios horarios nacionales de bolsa con las mismas fuentes numéricas y orígenes de evaluación? El benchmark distingue magnitud del error, evidencia estadística y relevancia práctica.

### Métricas y margen de relevancia

La métrica primaria es **MAE en COP/kWh**; RMSE y R² son secundarias. Se mantienen las mismas 24 horas y orígenes para todas las familias. La formulación y el fundamento del MAE se presentan en la sección 8.2 del libro, basados en [Ugurlu et al. (2018, §4.1)](https://doi.org/10.3390/en11051255) y [Lago et al. (2021, §5.4)](https://doi.org/10.1016/j.apenergy.2021.116983).

Se adopta **δ = 2 % de reducción relativa del MAE**. Para una referencia A y un candidato B, evaluados sobre el mismo periodo,

$$
g_{A\to B}=1-\frac{\operatorname{MAE}_B}{\operatorname{MAE}_A},\qquad \delta_{\mathrm{rel}}=0{,}02.
$$

Una reducción del 2 % corresponde a un MAE del candidato igual al 98 % del MAE de referencia. El margen se establece como umbral operativo del estudio. Su formulación relativa mantiene una exigencia proporcional al error de referencia y facilita interpretar mejoras entre periodos de distinta escala. La reducción relativa queda indefinida cuando el MAE de referencia es cero.

### Hipótesis, comparaciones y error estadístico

Para cada par se define $D_{A,B}=\operatorname{MAE}_A-\operatorname{MAE}_B$. La hipótesis de igualdad de precisión es $H_0:D_{A,B}=0$, frente a $H_1:D_{A,B}\ne0$. El signo positivo indica menor MAE de B. Se prevén tres comparaciones: **MLP–LSTM, MLP–CNN1D y LSTM–CNN1D**. El primer modelo de cada par fija el denominador de su reducción relativa; para modelos avanzados posteriores, la referencia será el baseline congelado.

El nivel familiar es **α = 0,05**, con ajuste de Holm sobre las tres comparaciones principales. La potencia objetivo es **1−β ≥ 0,80** para detectar el efecto de interés. El número de semillas se determinará mediante el análisis de potencia, utilizando conservadoramente α/3 y considerando la variabilidad de las diferencias emparejadas.

Se reportarán diferencias, reducciones relativas e intervalos del 95 % marginales; para afirmaciones conjuntas sobre los tres pares se utilizarán intervalos con cobertura familiar de al menos el 95 %, mediante Bonferroni (98,333 % por par), distinguiéndolos de los marginales. Una estimación $g\ge0{,}02$ alcanza el umbral práctico puntual. Para afirmar con incertidumbre controlada una mejora superior al margen se exigirá que el límite inferior del intervalo simultáneo supere 0,02.

### Selección y evaluación final

La referencia descriptiva es la configuración con menor MAE medio entre semillas sobre los mismos orígenes. Si la inferencia no permite distinguirla de otra familia, se conservará esa designación descriptiva y se informará la falta de una superioridad concluyente. La referencia semanal permanece como control de contexto y no sustituye a las tres familias del benchmark.

La evaluación final requiere registrar periodo, archivos y huellas, disponibilidad de covariables, configuraciones y escaladores, semillas, presupuesto y reglas de análisis antes de calcular sus errores. No se reajustan decisiones a partir de ese bloque. La configuración se registra en `configs/benchmark_protocol.json`.

## 2. Unidad de evaluación e inferencia temporal

### Origen diario y pérdida evaluada

La **unidad de evaluación es cada origen diario de pronóstico**, a las 00:00 de Colombia, con una salida conjunta de 24 precios horarios.

Para la familia A, semilla r y origen o,

$$
\ell_{A,r,o}=\frac1{24}\sum_{h=0}^{23}|y_{o+h}-\widehat y_{A,r,o,h}|,\qquad
\bar\ell_{A,o}=\frac1R\sum_{r=1}^{R}\ell_{A,r,o}.
$$

El contraste diario emparejado es $d_o=\bar\ell_{A,o}-\bar\ell_{B,o}$. Se promedian las pérdidas entre semillas para estimar el desempeño medio de las inicializaciones. Con 24 etiquetas completas por origen, promediar las pérdidas diarias reproduce el MAE agrupado por horas. Si falta una predicción o etiqueta, no se elimina silenciosamente para un solo modelo: se resuelve la incidencia o se declara un conjunto común y su exclusión.

### Bloques y dependencia

Los orígenes diarios consecutivos pueden presentar dependencia por autocorrelación, estacionalidad, regímenes y entrenamiento compartido. Los bloques constituyen la unidad de remuestreo temporal de la serie nacional.

La inferencia temporal se planifica mediante **bootstrap emparejado de bloques móviles de 14 días consecutivos**, con **5000 réplicas** y semilla **20261106**. Se mantendrán juntos todos los modelos y semillas correspondientes a cada origen seleccionado. Los bloques conservarán el orden interno y se extraerán sin unión circular del final al inicio. El mecanismo se documenta en la [referencia de MovingBlockBootstrap](https://arch.readthedocs.io/en/latest/bootstrap/generated/arch.bootstrap.MovingBlockBootstrap.html).

La longitud de 14 días conserva tramos de dos ciclos semanales. Se evaluará sensibilidad con **7 y 28 días**, manteniendo 14 días como especificación principal.

En validación, cada fold constituye un estrato temporal: se remuestrea dentro de él hasta recuperar su cantidad original de orígenes, recortando el último bloque cuando sea necesario. Se mantienen sus pesos según el número de días. Los bloques no cruzan folds ni discontinuidades del calendario; si no hay suficientes tramos consecutivos para una longitud prevista, se informa la limitación en lugar de concatenar segmentos. En un periodo final único se conserva su estructura temporal, sin imponer artificialmente los folds de desarrollo.

### Variabilidad de las ejecuciones

La incertidumbre temporal se estimará sobre las pérdidas diarias promediadas entre semillas. La variabilidad de inicialización se describirá mediante media, desviación estándar y coeficiente de variación del MAE, con diferencias emparejadas por semilla y bloque. Los folds se tratarán como estratos temporales que comparten historia de entrenamiento. La interpretación de los intervalos quedará referida al periodo y régimen evaluados y a las condiciones de estabilidad local del remuestreo.
