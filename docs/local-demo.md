# Operación local

La configuración única es `compose.yaml`. Su nombre de proyecto es `fullstyle-portfolio`; no comparte imágenes, volúmenes, redes ni puertos publicados con `fullstyle-modernization`.

| Uso | Dirección de acceso |
| --- | --- |
| Web / API / GraphQL | http://localhost:38080 |
| PostgreSQL sintético | `postgres:5432` dentro de la red Docker |
| Redis sintético | `redis:6379` dentro de la red Docker |
| RabbitMQ AMQP / administración | `rabbitmq:5672` / `rabbitmq:15672` dentro de la red Docker |
| Reconstrucción desechable de tests | http://localhost:38081 |

Las credenciales sintéticas de las dependencias están declaradas en Compose. No existe conexión a datos originales o productivos. `db-init` aplica las migraciones versionadas antes de admitir tráfico y finaliza con código 0; los otros doce contenedores permanecen en ejecución. La demo inicia un contenedor de chatbot; las pruebas de fiabilidad despliegan dos réplicas adicionales en un proyecto desechable para verificar su estado SQL compartido. El worker de correo se supervisa mediante persistencia y pruebas de entrega; no declara un healthcheck HTTP.

Compose conserva declaraciones de puertos `35432`, `36379`, `35672` y `35673` en el contrato de aislamiento de las dependencias. En el motor verificado, la red interna no publica esos endpoints al host (`NetworkSettings.Ports` vacío). La entrada de la aplicación es el proxy en `38080`. Para administrar SQL desde el host usar `docker compose exec postgres psql -U synthetic -d fullstyle_synthetic`; para Redis, `docker compose exec redis redis-cli`. No depender de conectividad directa a los puertos declarados de las bases.

## Arranque y parada

```bash
docker compose up --build -d --wait --wait-timeout 240
docker compose ps -a
docker compose down
```

También puede usarse `python scripts/start_local.py`, que comprueba aislamiento y pertenencia del proyecto antes del arranque. El nombre de proyecto fijo impide confundir datos de otras copias; si ya existe desde otra carpeta, el script rechaza su uso. No cambiar `-p` sin adaptar los validadores.

Para eliminar **solo los datos de esta demo**, ejecutar desde este monorepo `docker compose down --volumes`. Esta operación es opcional y borra las reservas y cuentas sintéticas creadas en sus volúmenes.

## Uso

Crear una cuenta desde la web. La administración de sedes y recursos respeta el rol del usuario; el registro no concede permisos sobre datos ajenos. `/operations` permite consultar operaciones propias y flujos financieros sintéticos según permisos. `/chatbot` permite recuperar una conversación y revisar una operación incierta sin reenviarla. Activar MFA muestra códigos de recuperación una sola vez: guardarlos antes de cerrar la pantalla.

El emulador y los proveedores ficticios permiten ejecutar la demostración sin claves externas. La variante Flutter usa `--dart-define=FS_LOCAL_ONLY=true`; puede compilarse para web con `flutter build web --no-web-resources-cdn --dart-define=FS_LOCAL_ONLY=true` desde `FullStyle-App/fullstyle_aplication`. El build Flutter se valida por separado y no se sirve como parte de la web Next.js.

## Respaldos y recuperación

Con el stack iniciado y las herramientas de [testing](testing.md) instaladas:

```bash
python scripts/backup_local.py
python scripts/backup_firebase_local.py
```

El segundo comando detiene temporalmente los escritores locales, verifica SQL y Firebase en contenedores independientes, cifra un archivo con datos y claves y vuelve a iniciar los servicios que estaban activos. Los archivos y la llave separada quedan en `.quality/`, excluidos de Git. No publicar esa carpeta. Un respaldo y su llave en el mismo disco no constituyen recuperación ante pérdida física del disco.

Para rollback de código se requieren imágenes compatibles con las familias de sesión, epoch, MFA y el esquema `0005_local_completion`. No regresar a validadores anteriores que omitan estas políticas. Las migraciones de datos productivos quedan fuera de esta demo.
