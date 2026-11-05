# Calidad y tests

## Preparación

Instalar Python 3.13, Node 22.23.4, pnpm 10.8.1, Flutter 3.32.2 y Docker Compose v2. Ejecutar `python scripts/bootstrap.py`: crea un entorno virtual, instala herramientas, usa `npm ci` y `pnpm --frozen-lockfile` y exige el lock Flutter. No requiere otra copia del proyecto.

La pipeline completa se ejecuta con el Python de `.venv`: `python scripts/ci.py`. Guarda resultados y logs en `.quality/reports/`, nunca en archivos versionados. En Windows utiliza Edge instalado; Linux/macOS descargan Chromium mediante la versión fijada de Playwright. Puede indicarse otra instalación con `PLAYWRIGHT_EXECUTABLE_PATH`.

## Riesgos comprobados

| Riesgo | Evidencia exigida |
| --- | --- |
| Recursos ajenos | Dos identidades, peticiones directas y delegadas; rechazo y datos intactos |
| Doble reserva | Conexiones SQL independientes; una confirmación y conflicto controlado |
| Estado obsoleto | Mismo cuerpo y estado HTTP con hit/miss; invalidación después de modificar |
| Sesiones inseguras | MFA, recuperación de uso único, epoch, familias, logout y renovación concurrente |
| Eventos repetidos | Un efecto financiero o entrega persistente; recuperación tras caída |
| Chat entre réplicas | Historial autorizado, reinicio, revisión sin reejecución y retención programada |
| Pérdida de datos | Restore SQL y Firebase, igualdad de manifiestos y descifrado del archivo |
| Contratos rotos | REST, GraphQL, NextAuth y navegador reales |

Los tests usan PostgreSQL real con esquemas propios, Redis y RabbitMQ sintéticos. Las fronteras comerciales se sustituyen por adaptadores locales. Las mutaciones de bloqueo, caché, atomicidad, epoch y recuperación deben provocar el fallo de las aserciones correspondientes. El benchmark incluye funciones históricas extraídas y verificadas en `tests/fixtures/schedule`, sin requerir repositorios o imágenes antiguas.

## Comandos parciales

Tras preparar las herramientas y levantar el stack:

```bash
python scripts/quality.py
python scripts/run_security_tests.py
python scripts/run_phase3.py
python scripts/run_phase4.py
python scripts/run_phase5.py
python scripts/run_phase6.py
python scripts/run_phase6.py --suite contracts
python scripts/run_browser_smoke.py
python scripts/scan_secrets.py
python scripts/scan_secrets.py --history
python scripts/publication_check.py
```

Usar el Python del entorno virtual para los comandos que necesitan paquetes. `run_phase3`, `run_phase4`, etc. conservan sus nombres históricos, pero prueban el código actual. El gate final exige evidencia correspondiente a los hashes actuales e imágenes comprobadas; un informe antiguo no demuestra que un cambio posterior funcione.

## Alcance estático

Python: Ruff de corrección global, sintaxis, formato y reglas adicionales en módulos críticos; mypy estricto sobre el keyring. No se afirma tipado integral del ORM. Web/gateway: ESLint, Prettier, TypeScript y build. Go: gofmt, vet, tests, compilación y govulncheck. Flutter: formato, analyze, tests y build web. Auditorías de locks incluyen dependencias de desarrollo.

GitHub Actions ejecuta la preparación y pipeline sobre un checkout nuevo en un runner hospedado, sin rutas privadas ni runners de tu equipo. La publicación distingue los resultados históricos de modernización de los resultados obtenidos sobre este monorepo.
