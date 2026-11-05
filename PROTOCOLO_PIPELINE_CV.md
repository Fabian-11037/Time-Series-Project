# Diseño del pipeline de validación temporal

Registrado el 4 de noviembre de 2026 durante la preparación del pipeline, antes de búsqueda, piloto o entrenamiento supervisado de los modelos colombianos.

Se sustituye la partición fija de desarrollo por cinco folds forward chaining. La secuencia de validación comienza el 1 de enero de 2018 y cubre el periodo restante de desarrollo hasta el 1 de enero de 2022, exclusivo. El entrenamiento se amplía en cada fold con las etiquetas anteriores al inicio de su validación. El periodo de prueba 2022–2025 y sus huellas se conservan.

El contexto es de 168 horas, el horizonte de 24 horas y el paso entre orígenes de 24 horas, a las 00:00 de Colombia. Se purgan los horizontes que atraviesan el límite del bloque de etiquetas. El escalado se ajusta sólo con las filas de entrada de entrenamiento de cada fold. Los rezagos supuestos son 24 horas para las variables horarias y dos días para hidrología; se documentan como un escenario retrospectivo, sujeto a sensibilidad.

La planificación utiliza `split_train_val_forwardChaining` de timeseries-cv 0.1.5 sobre identificadores de bloques de calendario. El pipeline traduce estos bloques a ventanas supervisadas. Fuente y licencias: `third_party/timeseries-cv/`.

Las métricas, pérdida, arquitectura, búsqueda, margen δ, semillas y dimensionamiento final requieren un preregistro experimental específico. Este registro documenta la preparación y partición; no contiene resultados de modelos ni constituye un benchmark terminado.
