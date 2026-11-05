# Comparación con la organización anterior

| Aspecto | Organización anterior | Monorepo |
| --- | --- | --- |
| Descarga | Clonar orquestador y ocho repositorios aparte | Un clon con todo el código |
| Versiones compatibles | Ramas independientes, coordinación manual | Un commit del sistema completo |
| Carpetas de servicios | Ignoradas por el orquestador | Archivos normales versionados |
| Arranque | Instrucciones y variables repartidas | Compose único con valores sintéticos |
| Calidad | Configuración por repo y workspace preparado | Pipeline sobre checkout nuevo, sin rutas privadas |
| Benchmark histórico | Otra carpeta e imágenes retenidas localmente | Funciones extraídas con hashes verificables |
| Historial | Nueve grafos independientes | Importación nueva con registro explícito de procedencia |
| Datos | Entorno de modernización aislado | Otro proyecto Docker, imágenes y puertos independientes |

Los procesos, modelos y contratos modernizados se conservan. El cambio de organización no autoriza una migración productiva. La publicación excluye dependencias regenerables, objetos Git históricos, respaldos y secretos; mantiene las atribuciones del proyecto de equipo.

Los resultados históricos de modernización y la nueva validación deben distinguirse: el plan registra las fases completadas de la copia de origen; [monorepo-migration.md](../monorepo-migration.md) registra pruebas y publicación del monorepo. No se ejecutan pruebas destructivas contra el original para obtener una comparación.

Para reproducir: clonar, levantar Compose y ejecutar la [pipeline documentada](../testing.md). `reproduce_clean.py` reconstruye únicamente archivos presentes en el índice Git, usa volúmenes nuevos, repite los contratos HTTP y elimina sus propios recursos desechables. Los resultados se generan en `.quality/reports/`.
