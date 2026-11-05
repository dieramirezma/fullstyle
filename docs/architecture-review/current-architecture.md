# Arquitectura actual

Nginx es la entrada local. Next.js sirve la web y NextAuth mantiene la sesión; Apollo adapta GraphQL hacia negocio. Flask administra usuarios, sedes, recursos y reservas. Go conserva el acceso de identidad compatible con la política SQL. Firebase sigue disponible mediante un adaptador y un emulador local.

PostgreSQL es la autoridad de identidad, reservas y efectos financieros sintéticos. Redis es caché prescindible. Las escrituras de reservas bloquean al trabajador dentro de la misma transacción que comprueba disponibilidad y guarda el resultado. La duración y el importe se conservan como términos de la reserva.

El chatbot FastAPI autoriza mediante una identidad delegada verificada por negocio. La demo inicia un contenedor; las pruebas despliegan dos réplicas que comparten conversaciones y recibos SQL, y comprueban su reinicio. Una operación incierta requiere revisar el estado de negocio antes de marcar su revisión; la revisión no vuelve a ejecutar la escritura. La retención redacta contenido vencido conservando identificadores y hashes de deduplicación.

El correo utiliza outbox SQL y RabbitMQ. El worker registra la entrega y su deduplicación de manera transaccional. La revisión permite reprogramar eventos válidos propios y no repite una entrega registrada. La demo usa entrega local, sin proveedor comercial.

La política de sesión combina identidad SQL activa, epoch de cuenta, familia, revocación, MFA y vencimiento. Un cambio de política invalida el vínculo Firebase; volver a vincular exige credenciales actuales. Los códigos de recuperación MFA solo persisten como hashes.

La [matriz base](route-matrix.json) conserva las rutas de transición auditadas durante la modernización. Los endpoints agregados posteriormente están en [additional-contracts.md](additional-contracts.md). Los prefijos del proxy distinguen `/chatbot` web, `/chatbot/` API, `/graphql` y las rutas REST.

Los servicios se construyen con Dockerfiles del directorio `docker`. `db-init` aplica SQL versionado y readiness exige `0005_local_completion`. Las bases tienen volúmenes nombrados del proyecto; los servicios internos carecen de salida a Internet y la entrada pública se limita a localhost.
