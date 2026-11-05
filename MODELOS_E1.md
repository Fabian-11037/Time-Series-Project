# Alcance de los modelos del Entregable 1

Decisión expresa del autor: **sin NLP; únicamente variables numéricas**.

Las entradas candidatas son rezagos del precio nacional de bolsa y observaciones históricas de demanda, temperatura, humedad, precipitación y las cuatro series hidrológicas. Se pueden representar ciclos conocidos del calendario. La disponibilidad temporal y la versión de cada entrada deben declararse: que una medida corresponda al pasado no acredita que su versión actual estuviera publicada entonces.

No se incorporan titulares, cuerpos, embeddings, sentimiento, tópicos, agrupamientos, relevancia ni conteos derivados de noticias. El texto y sus auditorías se conservan como material del dataset para E2/E3, sin alimentar los modelos del E1. La autorización de usar versiones de texto no verificadas se refiere a ese escenario contextual posterior y mantiene su advertencia de posible fuga.

Escalado, imputación y cualquier selección se ajustan sólo con entrenamiento. No se usan demanda o clima realizados del horizonte futuro. La hidrología diaria no se propaga desde las 00:00 de su propio día sin una regla de publicación explícita. Los datos numéricos actuales son retrospectivos; no se certifican todas sus versiones históricas.

El EDA propuesto estudia una tarea numérica de salida directa de las siguientes 24 horas con contexto semanal. El benchmark requiere cerrar antes de entrenar su preregistro, tres baselines extraídos de la literatura, espacios/presupuestos, métricas, δ, piloto y repeticiones. Este trabajo no ejecuta ni inventa resultados de esos modelos.

Esta decisión pertenece al candidato colombiano y no modifica el E1 ya existente de Time-MMD ni sus resultados congelados.

Actualización del diseño de evaluación: se utiliza `split_train_val_forwardChaining` para planificar cinco folds expansivos sobre desarrollo 2000–2021. El periodo 2022–2025 continúa reservado para prueba. La configuración activa está en `configs/training_pipeline.json` y el contrato de entrenamiento en `PIPELINE.md`.
