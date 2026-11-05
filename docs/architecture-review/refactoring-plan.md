# Plan de modernización y consolidación

El proyecto se modernizó primero en una copia independiente de nueve repositorios y después se consolidó para publicación. Las casillas de las fases 1–6 y el cierre complementario corresponden a evidencia histórica de esa copia, identificada por el fingerprint de [provenance.json](../provenance.json). La portabilidad y publicación del monorepo se verifican por separado en [monorepo-migration.md](../monorepo-migration.md).

## Fase 1 — Preparación

- [x] Copias Git independientes, ramas de trabajo y baseline sin modificar el original.
- [x] Inventario de secretos sin divulgar valores.
- [x] Docker y bases sintéticas con redes, volúmenes y puertos aislados.
- [x] Verificar 720 hashes y nueve estados Git del original.

## Fase 2 — Contención

- [x] Autorización de recursos en negocio y peticiones del chatbot.
- [x] Sesiones/delegación sin cuenta compartida.
- [x] Preparar rotación por proveedor; mantener efectos reales desactivados.
- [x] Regresiones de acceso ajeno y persistencia con PostgreSQL real.

## Fase 3 — Funcionamiento reproducible

- [x] Arranque, rutas, variables, webhook y healthchecks.
- [x] Builds, linters, formato, tipos y contratos antes de publicar.
- [x] Stack completo con datos sintéticos y emulador Firebase.
- [x] Reconstrucción con volúmenes nuevos y limpieza del proyecto desechable.

## Fase 4 — Consistencia

- [x] Reservas y modificaciones transaccionales con bloqueo por trabajador.
- [x] Duración y precio inmutables por reserva.
- [x] Caché prescindible y equivalencia de cuerpo/estado HTTP.
- [x] Deduplicación de pagos y pruebas de concurrencia/rollback.

## Fase 5 — Fiabilidad

- [x] Timeouts y reintentos acotados de operaciones seguras.
- [x] Outbox SQL, RabbitMQ y deduplicación durable de correo.
- [x] Historial SQL compartido entre réplicas del chatbot.
- [x] Caída/reinicio de dependencias y mutaciones que detectan regresiones.

## Fase 6 — Mantenibilidad y rendimiento

- [x] Migraciones explícitas versionadas y readiness de esquema.
- [x] Política SQL compatible entre Flask, Go y Firebase.
- [x] MFA, renovación/revocación y cuentas heredadas comprobadas.
- [x] Consultas optimizadas mediante medición y benchmark reproducible.

## Cierre complementario local

- [x] Recuperación MFA de uso único y revocación de sesiones.
- [x] Interfaz para guardar códigos y recuperar autenticador.
- [x] Renovación concurrente idempotente y familias revocables.
- [x] Rotación local del cifrado con rollback probado.
- [x] Cancelación/vencimiento de intenciones y conciliación tardía.
- [x] Reembolsos sintéticos idempotentes y auditados.
- [x] Suscripciones ficticias con precios del servidor.
- [x] Concurrencia, duplicados y ausencia de efectos no autorizados.
- [x] Revisión explícita de operaciones inciertas del chatbot.
- [x] Interfaz y retención de contenido con deduplicación.
- [x] Revisión y reprogramación autorizada de correo fallido.
- [x] Restore de PostgreSQL, Firebase Auth/Firestore y claves cifradas.
- [x] Auditorías de dependencias y análisis estático útil.
- [x] Pipeline completa y reproducción limpia sobre las mismas fuentes.
- [x] Comparación, contratos, operación y límites documentados.

## Reglas transversales

Los tests verifican efectos persistentes y riesgos concretos, no una cuota de cobertura. Bloqueos y atomicidad se prueban con bases reales aisladas. Mantener APIs compatibles durante transiciones, migraciones aditivas, rollback que conserve la autorización y datos sintéticos. Ninguna casilla local certifica rotación de credenciales reales, cobros, envío comercial o despliegue productivo.
