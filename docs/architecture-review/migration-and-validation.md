# Migración, validación y rollback

El esquema evoluciona mediante SQL aditivo con checksums. El proceso web no ejecuta `create_all` sobre la base de la demo. `db-init` termina antes de los servicios que exigen `0005_local_completion`; una deriva o versión ausente impide readiness.

Antes de cambiar datos, ejecutar y comprobar los respaldos de [local-demo.md](../local-demo.md). SQL se restaura en un contenedor desechable sin red; Firebase Auth y Firestore se exportan y restauran en otra red interna. El archivo cifrado incluye claves de runtime, con su llave en una carpeta separada fuera de Git. Este procedimiento demuestra restauración local y no sustituye almacenamiento externo.

Los contratos evolucionan de forma aditiva: conservar rutas y campos de transición, desplegar primero consumidores compatibles y después productores. No cambiar hashes de contraseñas ni tokens de cuentas heredadas sin probar login, renovación y revocación. Recuperación MFA requiere contraseña actual y un código de uso único; no existe recuperación administrativa sin ambos requisitos.

El rollback requiere un binario compatible con epoch, familia de sesión, MFA y los datos ya migrados. Conservar el esquema aditivo, las claves necesarias para descifrar y las imágenes verificadas. Una versión anterior que omita autorización o revocación no es un destino aceptable de rollback.

La aceptación combina acceso ajeno rechazado, una única reserva compatible bajo concurrencia, igualdad hit/miss, efectos deduplicados, recuperación de dependencias, navegador y reconstrucción desde archivos versionados. El gate compara hashes de fuente e imágenes con las evidencias actuales.

Los indicadores locales incluyen latencia, errores inesperados, conflictos, antigüedad del outbox y entregas. Sus límites son presupuestos de pruebas locales; los SLO productivos requieren una línea base operativa real.
