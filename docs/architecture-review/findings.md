# Hallazgos y tratamiento

Los hallazgos siguientes motivaron la modernización. Su estado describe la implementación importada; el resultado de ejecución del monorepo se registra en [la validación de publicación](../monorepo-migration.md).

| Hallazgo | Impacto / riesgo | Complejidad | Tratamiento y verificación |
| --- | --- | --- | --- |
| Autorización insuficiente de recursos | Lectura o escritura ajena; crítico | Media | Propiedad comprobada en negocio; pruebas con dos usuarios y vía chatbot |
| Emisores de sesión sin una política común | Renovación tras revocación o bypass MFA; crítico | Alta | Política SQL compartida, epoch/familias/MFA y contratos entre adaptadores |
| Comprobación y escritura separadas en reservas | Horarios incompatibles confirmados; alto | Alta | Transacción y bloqueo por trabajador; carreras reales al crear/modificar |
| Caché con diferencias de estado o invalidación incompleta | Respuestas inconsistentes; alto | Media | Generación SQL, equivalencia hit/miss y fallo real de Redis |
| Repetición de eventos financieros o de correo | Efectos duplicados; alto | Alta | Ledger/outbox/recibos durables e idempotencia transaccional |
| Historial local por réplica | Pérdida o repetición al reiniciar; alto | Media | SQL compartido, pruebas alternando y reiniciando réplicas |
| Migraciones implícitas al arrancar aplicaciones | Deriva de esquema; alto | Media | SQL versionado con checksum y arranque bloqueado hasta readiness |
| Clones manuales y rutas privadas | Demo irreproducible; medio | Media | Monorepo, Compose único y fixtures históricos portables |
| Historial con material sensible | Riesgo de publicación; alto | Media | Importación sin objetos Git antiguos, exclusiones, saneamiento y escaneo |

Las credenciales reales antiguas no se rotan mediante esta publicación. Su revocación corresponde a los titulares de las cuentas. No se declara validada una integración comercial por haber pasado una simulación local.
