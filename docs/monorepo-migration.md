# Consolidación para portafolio

Estado: **monorepo público y verificado en Docker local**. Este documento registra la validación del monorepo; los resultados de la copia modernizada son históricos y no sustituyen estas comprobaciones.

## Checklist de publicación

- [x] Crear una tercera carpeta independiente; preservar original y modernización.
- [x] Importar ocho componentes y orquestación como archivos normales, sin submódulos.
- [x] Registrar commits de procedencia, colaboradores y hashes de importación.
- [x] Excluir objetos Git antiguos, dependencias, datos y credenciales.
- [x] Sustituir identificadores Firebase por una configuración ficticia.
- [x] Unificar Compose y aislar proyecto, imágenes y puertos.
- [x] Eliminar dependencia de rutas privadas y fixtures de benchmark externos.
- [x] Documentar demo, arquitectura, calidad y alcance de licencias.
- [x] Verificar archivos versionados, secretos e historial nuevo.
- [x] Ejecutar la pipeline completa sobre este monorepo y la reconstrucción limpia.
- [x] Publicar `dieramirezma/fullstyle`, público, y comprobar remoto y GitHub Actions.

## Decisiones

Se conservan los nombres de carpetas de los componentes para reducir cambios de rutas durante la consolidación. No se fusionan procesos ni se eliminan servicios. Las migraciones y la política SQL se mantienen.

Los archivos de texto se normalizan a LF mediante `.gitattributes`. Los hashes de importación registran los bytes anteriores a esa normalización; los checksums de migraciones se calculan con los archivos del monorepo. La demo inicializa sus propios volúmenes vacíos. No reutilizar los volúmenes ni importar automáticamente el estado de migraciones de la copia anterior: cualquier transferencia de datos requiere revisar esa correspondencia explícitamente.

La importación es un snapshot del estado modernizado, incluidas modificaciones locales. No conserva el grafo de commits de los nueve repositorios dentro del nuevo repositorio, ni modifica sus historiales originales. [provenance.json](provenance.json) registra la relación con esos historiales y los autores; los hashes de importación describen el estado previo a adaptaciones de portabilidad y saneamiento.

Las evidencias operativas voluminosas, respaldos y llaves permanecen fuera de Git. Los resultados nuevos se generan en `.quality/reports`. El repositorio incluye código, locks, tests, documentación y herramientas para reproducirlos.


## Resultado sobre el monorepo

Pipeline local de **27 pasos con salida 0**, 30 controles de calidad, siete auditorías de locks, 47 casos pytest, 19 regresiones de seguridad, 17 contratos HTTP y 17 escenarios de consistencia aprobados. Se verificaron seis recorridos de identidad y cinco etapas de navegador, mutaciones, fallos reales y restauración cifrada SQL/Firebase/claves. La reconstrucción desde archivos Git usó `fullstyle-portfolio-clean-70799902`, repitió los contratos y eliminó sus propios volúmenes y redes.

[Resumen de validación](local-validation.json). El fingerprint pertenece a este monorepo, no a la copia modernizada. El original conserva 720 hashes y nueve estados Git; la copia modernizada conserva su fingerprint previo. Los logs completos y los respaldos permanecen en `.quality/` fuera de Git.

GitHub Actions ejecuta la pipeline sobre un checkout nuevo. Consultar sus resultados actuales en [Actions](https://github.com/dieramirezma/fullstyle/actions); la evidencia local anterior no afirma por sí sola el resultado de ese runner.

Durante la preparación, el primer intento falló en el navegador por selectores con tildes leídos con una codificación incorrecta. Se restauró ese archivo desde UTF-8, se comprobó el botón real y se repitió la pipeline completa con éxito. El intento fallido permanece separado en `.quality/attempt-browser-encoding/`; no se computa como una ejecución aprobada.

Repositorio público: [dieramirezma/fullstyle](https://github.com/dieramirezma/fullstyle). Se comprobó la correspondencia del commit remoto con la copia local y la creación de la ejecución de GitHub Actions; su resultado hospedado se consulta en Actions, separado de la evidencia Docker local.

## QA funcional posterior a la publicación

La validación técnica local y GitHub Actions están aprobadas. El QA exploratorio web arroja **36 comprobaciones aprobadas, tres fallidas y una bloqueada**, con 41 capturas. El ciclo de reserva/pago/reembolso sintético funciona con oferta precargada; el onboarding de negocio está bloqueado por geocodificación local. [Estado funcional y evidencia](qa/2026-11-04/README.md). Este resultado amplía el alcance de la aceptación técnica y no convierte los hallazgos pendientes en tareas ya resueltas.
