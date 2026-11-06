# Registro de ejecución local

Fecha: 5 de noviembre de 2026.

- Repositorio clonado desde `Fabian-11037/Time-Series-Project`; commit de partida `8c10f0db1a24ea5ca2017d6e160d41f89cc5f1c8`.
- Entorno confirmado por el usuario: `mlenv`, Python 3.12.3. No se modificaron sus paquetes.
- Hardware identificado con rocminfo: AMD Ryzen 7 5700X; AMD Radeon RX 6700 XT, gfx1031, aproximadamente 12 GB VRAM.
- Intento sin override: detectó GPU pero falló en el primer ajuste con `HIP error: invalid device function`. Su configuración se conserva en `results/pilot_pytorch/configuration.json`; no produjo métricas ni modelos ajustados completos.
- El proceso de entrenamiento se relanzó con `HSA_OVERRIDE_GFX_VERSION=10.3.0`, tras comprobar multiplicación de matrices y generación aleatoria en GPU. No se cambiaron los controladores ni variables globales del usuario.
- La API `torch.cuda` también es la API de PyTorch para HIP/ROCm: [documentación oficial](https://docs.pytorch.org/docs/stable/notes/hip.html).
- Antes del entrenamiento pasaron las 17 pruebas de `python -m unittest discover -s tests`.
- `python scripts/verify_dataset.py`: 142 archivos verificados, 227928 horas, 9497 días, calendario completo y `test_hashes_unchanged=true`; `test_target_distribution_read=false`.
- Protocolo del piloto congelado antes del ajuste: `PROTOCOLO_PILOTO_2026-11-05.md`. Arquitecturas sencillas exploratorias, sin búsqueda de hiperparámetros, sin contrastes confirmatorios ni evaluación de prueba.
- Las métricas parciales/finales están en la carpeta de esta nota y el registro de consola en `results/pilot_training_gfx1030.log` (ignorado por Git por extensión).
