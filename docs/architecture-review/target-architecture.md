# Responsabilidades y decisiones

Se conservan los servicios existentes. El monorepo facilita coordinar contratos y pruebas; no cambia las fronteras de ejecución ni convierte las bases o procesos en un único servicio.

1. **Autoridad en negocio y SQL.** La identidad recibida por REST, GraphQL o chatbot no sustituye la autorización del recurso. Las reservas y pagos se deciden con estado persistente dentro de transacciones.
2. **Adaptadores compatibles.** Go, Flask y Firebase permanecen. La política SQL de cuenta y sesión evita que un adaptador omita revocación o MFA. La consolidación de emisores puede evaluarse después con evidencia de compatibilidad.
3. **Caché descartable.** Redis acelera lecturas; su caída no puede autorizar reservas incompatibles ni cambiar el contrato HTTP.
4. **Efectos durables.** RabbitMQ transporta correo; PostgreSQL conserva intención, estado y deduplicación. Eventos e identificadores de operación permiten repetir transporte sin repetir efectos.
5. **Incertidumbre explícita.** Una respuesta perdida no prueba el fracaso de una escritura. El chatbot conserva recibos y permite revisión manual sin reenviar la operación.
6. **Migraciones separadas del proceso web.** El servicio de inicialización aplica migraciones y los healthchecks verifican el esquema. El rollback conserva los contratos de autorización y el esquema compatible.
7. **Demo autónoma.** Proveedores ficticios y emuladores permiten probar sin credenciales externas. Las integraciones comerciales requieren otra configuración y validación operativa.

No se añaden servicios para resolver problemas que pueden abordarse con responsabilidades y contratos claros en los actuales. Los cambios futuros deben justificar su coste mediante medición y necesidades concretas.
