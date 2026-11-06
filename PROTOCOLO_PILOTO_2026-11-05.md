# Prerregistro del piloto numérico E1

Registrado el 5 de noviembre de 2026, antes del primer ajuste colombiano.

Este experimento es un piloto exploratorio reproducible, no el benchmark confirmatorio final. La revisión de frecuencias y extracción completa de arquitecturas de la literatura sigue pendiente. Se implementan las tres familias propuestas por el contexto como adaptaciones simples; no se atribuyen estas arquitecturas exactas a los artículos citados.

Se conserva sin cambios `configs/training_pipeline.json`: cinco folds expansivos de desarrollo, contexto 168 horas, salida directa de 24 horas y rezagos de disponibilidad. No se cargan valores de prueba 2022–2025.

Arquitecturas: MLP Flatten–Dense(128)–ReLU–Dropout(0.1)–Dense(64)–ReLU–Dense(24); LSTM de una capa con 32 unidades y Dense(24) desde el último estado; CNN1D Conv(p,32,k=5,padding=2)–ReLU–Conv(32,32,k=5,padding=2)–ReLU–AdaptiveAvgPool(7)–Flatten–Dense(24). Misma entrada multivariante para todas las familias.

Presupuesto fijo: 30 épocas, sin búsqueda ni parada anticipada; Adam con lr=0.001 y weight_decay=0.0001; batch 256; recorte de norma de gradiente a 1. Cinco semillas: 11037, 11038, 11039, 11040 y 11041, para 75 ajustes. Cada ajuste comienza con un modelo nuevo y orden aleatorio controlado. Igual número de épocas no implica igual costo ni igual capacidad entre familias. Precisión float32; se registran versiones, hardware, parámetros y tiempos. No se garantiza reproducibilidad bit a bit de kernels GPU.

Entradas estandarizadas por el pipeline sólo con entrenamiento del fold. Para estabilidad numérica, la salida se centra y escala con media y desviación de etiquetas de entrenamiento; pérdida MAE en esa escala (equivalente a minimizar MAE original por una constante positiva). Métricas y predicciones se restituyen a COP/kWh. Se informa MAE principal y RMSE complementaria. El checkpoint es el de la época 30; no se elige por validación.

Referencia descriptiva adicional: repetición semanal (precio observado 168 horas antes de cada hora objetivo), disponible al origen incluso con el rezago horario de 24 horas. Se informa su MAE y la razón MAE_modelo / MAE_referencia sobre los mismos orígenes. Esta razón no se denomina MASE.

Se guardan curvas de entrenamiento/validación, pesos, escaladores de entradas y salida, orígenes y predicciones, métricas por fold/semilla y configuración. Las curvas de validación se registran sin intervenir en el ajuste. Se agregan errores ponderando todas las horas de validación; se informa variación entre semillas sin interpretar folds/horas como réplicas independientes. No se ejecutan contrastes ni se declara superioridad estadística. Margen práctico δ y dimensionamiento por potencia quedan pendientes para un registro confirmatorio posterior; no se importa el 3 % de Time-MMD.

El piloto no completa los requisitos finales de E1 (extracción bibliográfica, potencia >=0.80 con alfa=0.05, repeticiones finales, corrección por comparaciones e inferencia con dependencia temporal). No se seleccionará ni evaluará un modelo final en prueba durante esta ejecución.
