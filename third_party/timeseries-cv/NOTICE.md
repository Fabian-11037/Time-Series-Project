# timeseries-cv

Se incorpora únicamente `split_train_val_forwardChaining` de la distribución 0.1.5 (MIT).
Fuente: https://pypi.org/project/timeseries-cv/ y https://github.com/DidierRLopes/timeseries-cv.
La implementación ejecutable conserva el algoritmo; su formato y docstring incluyen la atribución y las licencias originales.

La distribución completa declara NumPy >=1.21,<2.0; el entorno del proyecto utiliza NumPy 2.5.4. Para conservar el entorno reproducible se incluye la función auditada, cuyas operaciones NumPy se verifican con pruebas de partición. No se instala la distribución completa ni se omiten controles de dependencias.

El backend recibe identificadores de bloques de calendario. Sus índices se traducen a ventanas de 168 horas y etiquetas de 24 horas mediante el pipeline. Esta planificación evita materializar un número cuadrático de ventanas en la función original.
