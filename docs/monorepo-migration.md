# Consolidación para portafolio

Estado: preparación y verificación en curso. Este documento registra la validación del monorepo; los resultados de la copia modernizada son históricos y no sustituyen estas comprobaciones.

## Checklist de publicación

- [x] Crear una tercera carpeta independiente; preservar original y modernización.
- [x] Importar ocho componentes y orquestación como archivos normales, sin submódulos.
- [x] Registrar commits de procedencia, colaboradores y hashes de importación.
- [x] Excluir objetos Git antiguos, dependencias, datos y credenciales.
- [x] Sustituir identificadores Firebase por una configuración ficticia.
- [x] Unificar Compose y aislar proyecto, imágenes y puertos.
- [x] Eliminar dependencia de rutas privadas y fixtures de benchmark externos.
- [x] Documentar demo, arquitectura, calidad y alcance de licencias.
- [ ] Verificar archivos versionados, secretos e historial nuevo.
- [ ] Ejecutar la pipeline completa sobre este monorepo y la reconstrucción limpia.
- [ ] Publicar `dieramirezma/fullstyle`, público, y comprobar remoto y GitHub Actions.

## Decisiones

Se conservan los nombres de carpetas de los componentes para reducir cambios de rutas durante la consolidación. No se fusionan procesos ni se eliminan servicios. Las migraciones y la política SQL se mantienen.

Los archivos de texto se normalizan a LF mediante `.gitattributes`. Los hashes de importación registran los bytes anteriores a esa normalización; los checksums de migraciones se calculan con los archivos del monorepo. La demo inicializa sus propios volúmenes vacíos. No reutilizar los volúmenes ni importar automáticamente el estado de migraciones de la copia anterior: cualquier transferencia de datos requiere revisar esa correspondencia explícitamente.

La importación es un snapshot del estado modernizado, incluidas modificaciones locales. No conserva el grafo de commits de los nueve repositorios dentro del nuevo repositorio, ni modifica sus historiales originales. [provenance.json](provenance.json) registra la relación con esos historiales y los autores; los hashes de importación describen el estado previo a adaptaciones de portabilidad y saneamiento.

Las evidencias operativas voluminosas, respaldos y llaves permanecen fuera de Git. Los resultados nuevos se generan en `.quality/reports`. El repositorio incluye código, locks, tests, documentación y herramientas para reproducirlos.
