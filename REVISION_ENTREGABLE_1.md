# Revisión del Jupyter Book frente al Entregable 1

Actualización documental: 6 de noviembre de 2026. Autores: Fabian José Manrique Morelos y Gloria Bastida.

Pauta: Entregable1DeepLearningProject.pdf, 34 páginas, SHA-256 `56cffb2e0e23bbdfd28815b7c7515d2663bf501ed5d6e0656a37a76fc45e43eb`.

El E1 dispone de dataset auditado, EDA de desarrollo 2000–2021, pipeline forward chaining y tres familias entrenadas. El benchmark confirmatorio permanece incompleto.

| Componente | Estado vigente |
|---|---|
| Formulación | Series de tiempo multivariadas, 37 entradas, salida diaria de 24 precios |
| Datos | Snapshot 2026-11-03, manifiesto SHA-256 y calendarios numéricos completos |
| EDA | Desarrollo completo; diagnóstico temporal, meteorológico, hidrológico y documental |
| Validación | Cinco folds expansivos; preparación y escalado por fold |
| Métricas | MAE principal en COP/kWh; RMSE y R² secundarios; fundamento en Ugurlu 2018 y Lago 2021 |
| Implementación | MLP, LSTM y CNN1D; Windows/Linux y CPU/GPU compatibles según entorno |
| Experimentos | Piloto de 75 ajustes y búsqueda de 192 configuraciones/4800 ajustes |
| Literatura | 20 textos completos y 438 registros IEEE; 23 estudios destacados |
| Protocolo e inferencia | MAE, δ = 2 %, α = 0,05, potencia objetivo ≥ 0,80, tres comparaciones/Holm y unidades definidos; pendientes dimensionamiento, IC y contrastes |
| Evaluación independiente | Protocolo general definido; faltan periodo independiente, dimensionamiento y ejecución |

CNN1D C3 de 24 h presenta MAE de selección 24,155; LSTM L2 de 72 h, 24,624; MLP M3 de 24 h, 24,992 COP/kWh. La validación interviene en la parada y selección: no son métricas externas ni demuestran superioridad estadística.

La revisión bibliográfica sigue siendo focalizada: faltan conciliación de Scopus 615/562, cadenas/fechas originales, flujo completo de búsqueda y resolución de especificaciones insuficientes conforme a E1 §3.2. Las 192 configuraciones no acreditan automáticamente la búsqueda condicional remitida al E2.

Faltan métricas por horizonte, MASE con escala de entrenamiento, referencias causales adicionales, errores por segmentos, residuos de las redes, robustez y costos completos. Cinco semillas no garantizan potencia y los 25 ajustes por configuración no constituyen 25 réplicas independientes. El corpus textual permanece como EDA, sin atributos textuales en los modelos numéricos.

Continuidad: CONTEXTO_PROYECTO.md. Verificación documental: results/book_verification.json. Los datos 2022–2025 y sus huellas se conservan; los accesos del EDA y búsqueda a sus valores permanecen bloqueados. La independencia de una evaluación debe justificarse mediante su protocolo, sin inferirla de la integridad de archivos.

Protocolo vigente: PROTOCOLO_BENCHMARK_2026-11-06.md, secciones 8.3–8.4 del libro. Unidad de evaluación: origen diario de 24 precios. Remuestreo temporal por bloques móviles de 14 días, sensibilidad 7/28 días y variabilidad entre semillas separada. Las reglas están definidas; sus análisis aún no se han ejecutado.
