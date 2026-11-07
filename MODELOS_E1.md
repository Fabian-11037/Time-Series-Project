# Modelos numéricos del Entregable 1

La comparación utiliza MLP, LSTM y CNN1D para el precio nacional horario de bolsa de XM, con entradas numéricas y calendario. Las variables y su disponibilidad se documentan en `PIPELINE.md`; el horizonte es de 24 horas. El desarrollo 2000–2021 utiliza cinco folds expansivos `split_train_val_forwardChaining`. La prueba 2022–2025 fue consultada para configuraciones iniciales el 5 de noviembre; no constituye una prueba intacta para decisiones posteriores.

## Justificación bibliográfica

La revisión focalizada de 20 textos completos recuperó 16 estudios puntuales, tres empíricos complementarios y una revisión secundaria. LSTM aparece como comparador en 7/16, MLP/DNN en 6/16 y CNN en 2/16; sólo una de las dos referencias CNN especifica 1D. CNN empata con CNN-LSTM y Transformer. La elección combina frecuencia, estructura y contraste inductivo: interacciones densas, memoria recurrente y patrones locales compartidos. Las fuentes, roles, configuraciones, resultados, calidad y sensibilidad están en `literature/baseline_review/` y capítulo 9 del JBook. Las frecuencias describen el corpus recuperado; cinco candidatos siguen sin texto íntegro verificado y la búsqueda sistemática no es exhaustiva.

| Modelo seleccionado | Historia | Arquitectura | Parámetros |
|---|---:|---|---:|
| MLP M3 | 24 h | Capas densas 256–128 y 24 salidas | 263576 |
| LSTM L2 | 72 h | Una capa de 64 unidades y 24 salidas | 27928 |
| CNN1D C3 | 24 h | Dos convoluciones de 64 filtros, kernel 5; pooling a 7 y 24 salidas | 43224 |

Los tamaños proceden de la búsqueda exploratoria colombiana; no son reproducciones exactas de las publicaciones. El capítulo 9 contiene fórmulas de parámetros/costo y el capítulo 10 contiene ecuaciones, diagramas, implementación y resultados. La revisión documental es posterior a esa búsqueda y no se presenta como selección a priori.

## Métrica principal del benchmark

El MAE en COP/kWh es el criterio principal para comparar configuraciones y seleccionar la referencia numérica. Se calcula sobre todas las horas objetivo de los mismos orígenes de validación y después se resume entre cinco semillas, sin promediar predicciones. RMSE y R² son métricas secundarias. El MAE conserva la unidad del precio y penaliza linealmente el error, conforme al uso de Ugurlu et al. (2018, §4.1; DOI 10.3390/en11051255) y a la discusión de Lago et al. (2021, §5.4; DOI 10.1016/j.apenergy.2021.116983). La referencia semanal aporta una comparación relativa sobre el mismo periodo. Véase la sección 8.2 del libro para la fórmula y sus límites.

CNN1D C3 tiene el menor MAE descriptivo de selección (24,155 COP/kWh). Su designación es exploratoria: siguen pendientes δ, potencia, incertidumbre temporal y evaluación independiente. Esta declaración documental no se presenta como preregistro de las ejecuciones existentes.

## Estado experimental

Se completaron el piloto de 75 ajustes y la búsqueda de 192 configuraciones/4800 ajustes sobre desarrollo. Sus protocolos y fuentes históricas se conservan. Las métricas de selección comparten bloques con parada anticipada y HPO; no son una evaluación externa. Las entradas de entrenamiento excluyen texto y atributos derivados de noticias; sus representaciones permanecen en el EDA del corpus para la investigación posterior.

La adaptación Windows/Linux permite CPU o GPU CUDA/ROCm según `EJECUCION.md`. La revisión bibliográfica no modifica datos, arquitecturas, métricas ni prueba. Los siguientes experimentos deben definir δ, potencia, inferencia temporal, presupuesto comparable y evaluación independiente antes de obtener nuevos resultados. La especificación insuficiente de algunos comparadores mantiene vigente la condición E1 §3.2 que remite a la búsqueda de arquitectura E2 §14; las 192 configuraciones ya ejecutadas no acreditan por sí solas su cumplimiento.

Estado detallado e instrucciones de continuidad: `CONTEXTO_PROYECTO.md`, secciones 19, 22 y 23. El proyecto histórico Time-MMD conserva sus protocolos y resultados propios.
